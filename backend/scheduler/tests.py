"""Tests for the scheduler app — verify IngestRun history is written on
success and failure without hitting real yfinance / pandas-datareader."""

from __future__ import annotations

from unittest import mock

from django.test import TestCase

from scheduler import jobs
from scheduler.models import IngestRun


class IngestRunTrackerTests(TestCase):
    def test_run_tracker_writes_completed_on_success(self):
        with jobs._run_tracker("dummy") as run:
            run.rows_ingested = 42
            run.summary = {"foo": "bar"}

        persisted = IngestRun.objects.get(run_id=run.run_id)
        self.assertEqual(persisted.status, IngestRun.STATUS_COMPLETED)
        self.assertIsNotNone(persisted.finished_at)
        self.assertEqual(persisted.rows_ingested, 42)
        self.assertEqual(persisted.summary["foo"], "bar")

    def test_run_tracker_writes_failed_on_exception(self):
        with self.assertRaises(ValueError):
            with jobs._run_tracker("dummy_fail") as run:
                raise ValueError("boom")

        persisted = IngestRun.objects.get(run_id=run.run_id)
        self.assertEqual(persisted.status, IngestRun.STATUS_FAILED)
        self.assertIn("boom", persisted.error)


class IngestPricesJobTests(TestCase):
    def test_ingest_prices_writes_run_with_mocked_fetch(self):
        import pandas as pd

        # Return 3 rows of mock OHLCV for 2 tickers
        fake_df = pd.DataFrame({
            "symbol": ["AAA", "AAA", "BBB"],
            "date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-02"]).date,
            "open": [100.0, 101.0, 50.0],
            "high": [102.0, 103.0, 51.0],
            "low": [99.0, 100.0, 49.0],
            "close": [101.0, 102.0, 50.5],
            "adj_close": [101.0, 102.0, 50.5],
            "volume": [1_000_000, 1_100_000, 500_000],
        })

        with mock.patch("scheduler.jobs.load_universe", return_value={"tickers": ["AAA", "BBB"]}):
            with mock.patch("scheduler.jobs.yf.fetch_prices", return_value=fake_df):
                summary = jobs.ingest_prices(universe="default", start="2024-01-01")

        self.assertEqual(summary["n_api_rows"], 3)
        self.assertEqual(summary["n_inserted"], 3)
        run = IngestRun.objects.get(job_name="yfinance_prices")
        self.assertEqual(run.status, IngestRun.STATUS_COMPLETED)
        self.assertEqual(run.rows_ingested, 3)

    def test_ingest_prices_marks_failed_on_exception(self):
        with mock.patch("scheduler.jobs.load_universe", return_value={"tickers": ["AAA"]}):
            with mock.patch(
                "scheduler.jobs.yf.fetch_prices",
                side_effect=RuntimeError("api down"),
            ):
                with self.assertRaises(RuntimeError):
                    jobs.ingest_prices(universe="default", start="2024-01-01")

        run = IngestRun.objects.get(job_name="yfinance_prices")
        self.assertEqual(run.status, IngestRun.STATUS_FAILED)
        self.assertIn("api down", run.error)
