"""DRF endpoint smoke tests — every endpoint hits real ORM data from fixtures."""

from __future__ import annotations

import os

from django.db import connection
from django.test import TransactionTestCase
from rest_framework import status
from rest_framework.test import APIClient

from _test_fixtures import seed_raw_data
from features.build import build
from models_rf.runner import run_rf
from permutation.runner import run_permutation_test
from portfolio.runner import backtest_run
from quality.runner import run_all_checks


class ApiEndpointTests(TransactionTestCase):
    def setUp(self):
        seed_raw_data(symbols=["AAA", "BBB", "CCC"], start="2021-01-01", end="2024-12-31")
        build()
        self.client = APIClient()
        os.environ["FORECASTER_DB_PATH"] = str(connection.settings_dict["NAME"])

    def tearDown(self):
        os.environ.pop("FORECASTER_DB_PATH", None)

    def test_health(self):
        r = self.client.get("/api/health/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["status"], "ok")

    def test_experiments_endpoint_responds(self):
        r = self.client.get("/api/experiments/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIsInstance(r.json(), list)

    def test_runs_list_responds(self):
        r = self.client.get("/api/runs/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.json()
        self.assertIn("count", data)
        self.assertIn("results", data)

    def test_dq_runs_list(self):
        run_all_checks(universe_name="smoke")
        r = self.client.get("/api/dq/runs/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        rows = r.json()
        self.assertGreater(len(rows), 0)
        self.assertIn("summary", rows[0])

    def test_ingest_status_reports_counts(self):
        r = self.client.get("/api/ingest/status/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.json()
        self.assertGreater(data["prices_total_rows"], 0)
        self.assertGreater(data["factors"]["n_rows"], 0)
        self.assertEqual(len(data["symbols"]["per_symbol"]), 3)

    def test_full_run_flow(self):
        run_id = run_rf(top_k=2, min_train_rows=20, name="api_test")
        backtest_run(run_id)
        run_permutation_test(run_id, n_permutations=3)

        r = self.client.get("/api/runs/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json()["count"], 1)

        r = self.client.get(f"/api/runs/{run_id}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        detail = r.json()
        self.assertEqual(detail["name"], "api_test")
        self.assertIn("params", detail)
        self.assertIn("metrics", detail)
        self.assertIn("feature_importance", detail)

        r = self.client.get(f"/api/runs/{run_id}/portfolio-returns/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.json()
        self.assertGreater(len(data["points"]), 0)
        for p in data["points"][:5]:
            self.assertIn("strategy_return", p)
            self.assertIn("cum_return", p)

        r = self.client.get(f"/api/runs/{run_id}/perm-metrics/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.json()
        self.assertIn("baseline_metric", data)
        self.assertIn("metrics", data)

    def test_feature_importance_aggregation(self):
        run_rf(top_k=2, min_train_rows=20, name="fi_test")
        r = self.client.get("/api/feature-importance/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.json()
        self.assertIn("features", data)
        self.assertGreater(len(data["features"]), 0)

    def test_perm_metrics_404_when_no_perm_test(self):
        run_id = run_rf(top_k=2, min_train_rows=20, name="no_perm")
        r = self.client.get(f"/api/runs/{run_id}/perm-metrics/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)
