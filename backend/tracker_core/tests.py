"""Tests for tracker_core + the SDK — SDK writes via raw sqlite3, Django
ORM reads. The fact that both sides agree is the integration test."""

from __future__ import annotations

import os

from django.db import connection
from django.test import TransactionTestCase

from tracker_core.models import (
    Experiment,
    Run,
    RunArtifact,
    RunFeatureImportance,
    RunMetric,
    RunParam,
    RunTag,
)


def _sdk_db_path():
    return connection.settings_dict["NAME"]


class TrackerSDKIntegrationTests(TransactionTestCase):
    """Use tracker SDK end-to-end against Django's test DB, then verify
    Django ORM sees the writes."""

    def setUp(self):
        os.environ["FORECASTER_DB_PATH"] = str(_sdk_db_path())

    def tearDown(self):
        os.environ.pop("FORECASTER_DB_PATH", None)

    def test_basic_run_roundtrip(self):
        import tracker

        with tracker.run(
            experiment="test_exp",
            params={"top_k": 5, "features": ["a", "b", "c"]},
            tags=["unit", "roundtrip"],
            name="test_run",
        ) as r:
            r.log_metric("sharpe", 1.5)
            r.log_metric("mae", 0.02)
            r.log_importance({"a": 0.2, "b": 0.15, "c": 0.1})
            r.log_artifact("dummy", str(_sdk_db_path()), kind="test")
            run_id = r.run_id

        exp = Experiment.objects.get(name="test_exp")
        run = Run.objects.get(run_id=run_id)
        self.assertEqual(run.experiment, exp)
        self.assertEqual(run.status, Run.STATUS_COMPLETED)
        self.assertEqual(run.name, "test_run")
        self.assertIsNotNone(run.finished_at)

        params = {p.key: p.value_json for p in RunParam.objects.filter(run=run)}
        self.assertEqual(params["top_k"], "5")
        self.assertIn("a", params["features"])

        metrics = {m.key: m.value for m in RunMetric.objects.filter(run=run)}
        self.assertAlmostEqual(metrics["sharpe"], 1.5)
        self.assertAlmostEqual(metrics["mae"], 0.02)

        tags = set(RunTag.objects.filter(run=run).values_list("tag", flat=True))
        self.assertEqual(tags, {"unit", "roundtrip"})

        imps = list(RunFeatureImportance.objects.filter(run=run).order_by("rank"))
        self.assertEqual([fi.feature for fi in imps], ["a", "b", "c"])
        self.assertEqual(imps[0].rank, 1)

        arts = list(RunArtifact.objects.filter(run=run))
        self.assertEqual(len(arts), 1)
        self.assertEqual(arts[0].name, "dummy")

    def test_failed_run_captured(self):
        import tracker

        run_id = None
        with self.assertRaises(RuntimeError):
            with tracker.run(experiment="fail_exp", tags=["unit"]) as r:
                run_id = r.run_id
                r.log_metric("early", 0.1)
                raise RuntimeError("simulated")

        run = Run.objects.get(run_id=run_id)
        self.assertEqual(run.status, Run.STATUS_FAILED)
        self.assertIn("simulated", run.error)
        self.assertEqual(
            RunMetric.objects.filter(run=run, key="early").count(), 1
        )

    def test_attach_to_existing_run(self):
        """`tracker.attach` appends metrics without changing status."""
        import tracker

        with tracker.run(experiment="attach_exp") as r:
            r.log_metric("x", 1.0)
            run_id = r.run_id

        run_before = Run.objects.get(run_id=run_id)
        finished_before = run_before.finished_at

        with tracker.attach(run_id) as r2:
            r2.log_metric("y", 2.0)
            r2.tag("later")

        run_after = Run.objects.get(run_id=run_id)
        self.assertEqual(run_after.status, Run.STATUS_COMPLETED)
        self.assertEqual(run_after.finished_at, finished_before)
        metrics = {m.key for m in RunMetric.objects.filter(run=run_after)}
        self.assertEqual(metrics, {"x", "y"})
        self.assertIn(
            "later", RunTag.objects.filter(run=run_after).values_list("tag", flat=True)
        )
