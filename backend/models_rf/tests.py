"""Tests for the RF walk-forward strategy + runner."""

from __future__ import annotations

import os

from django.db import connection
from django.test import TestCase, TransactionTestCase

from _test_fixtures import seed_raw_data
from features.build import build
from models_rf.models import RfPick, RfPrediction
from models_rf.runner import run_rf
from models_rf.strategy import rolling_train_predict_windowed
from tracker_core.models import Run


class RfStrategyUnitTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_raw_data(symbols=["AAA", "BBB", "CCC"], start="2021-01-01", end="2024-12-31")
        build()

    def _load_model_df(self):
        from models_rf.runner import load_model_df

        return load_model_df()

    def test_long_only_smoke(self):
        df = self._load_model_df()
        result = rolling_train_predict_windowed(
            df=df,
            features=[
                "return_1m",
                "return_3m",
                "return_12m",
                "rsi",
                "atr",
                "beta_mkt_rf",
            ],
            top_k=2,
            min_train_rows=20,
            tune_model=False,
        )
        self.assertFalse(result.diagnostics.empty)
        self.assertGreater(len(result.fixed_dates), 0)
        self.assertIn("rebalance_date", result.all_predictions.columns)
        picks = result.all_predictions[result.all_predictions["picked"]]
        self.assertTrue((picks["direction"] == 1).all())

    def test_long_short_produces_shorts(self):
        df = self._load_model_df()
        result = rolling_train_predict_windowed(
            df=df,
            features=["return_1m", "return_3m", "return_12m", "rsi", "atr"],
            top_k=1,
            top_k_short=1,
            min_train_rows=20,
            tune_model=False,
        )
        picks = result.all_predictions[result.all_predictions["picked"]]
        self.assertTrue((picks["direction"] == -1).any(), "no shorts recorded")
        self.assertTrue((picks["direction"] == 1).any(), "no longs recorded")

    def test_sector_cap_enforced(self):
        sector_map = {
            "AAA": "Information Technology",
            "BBB": "Information Technology",
            "CCC": "Information Technology",
        }
        df = self._load_model_df()
        result = rolling_train_predict_windowed(
            df=df,
            features=["return_1m", "return_3m", "return_12m", "rsi"],
            top_k=3,
            min_train_rows=20,
            tune_model=False,
            sector_map=sector_map,
            max_per_sector=1,
        )
        for _, tickers in result.fixed_dates.items():
            self.assertLessEqual(len(tickers), 1, f"sector cap violated: {tickers}")


class RfRunnerIntegrationTests(TransactionTestCase):
    """Uses SDK which opens its own sqlite3 connection; needs TransactionTestCase
    so those commits are visible to subsequent ORM reads."""

    def setUp(self):
        seed_raw_data(symbols=["AAA", "BBB", "CCC"], start="2021-01-01", end="2024-12-31")
        build()
        os.environ["FORECASTER_DB_PATH"] = str(connection.settings_dict["NAME"])

    def tearDown(self):
        os.environ.pop("FORECASTER_DB_PATH", None)

    def test_run_rf_end_to_end_persists_all_tables(self):
        run_id = run_rf(
            top_k=2, min_train_rows=20, seed=0, name="test_rf", tags=["unit"]
        )
        self.assertIsNotNone(run_id)
        self.assertTrue(Run.objects.filter(run_id=run_id).exists())
        self.assertGreater(RfPrediction.objects.filter(run_id=run_id).count(), 0)
        self.assertGreater(RfPick.objects.filter(run_id=run_id).count(), 0)
        run = Run.objects.get(run_id=run_id)
        metric_keys = set(run.metrics.values_list("key", flat=True))
        self.assertIn("realized_mean_avg", metric_keys)
        self.assertIn("n_rebalance_dates", metric_keys)
