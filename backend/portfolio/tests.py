"""Tests for the optimiser + backtest + compound pipeline."""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
from django.db import connection
from django.test import TestCase, TransactionTestCase

from _test_fixtures import seed_raw_data
from features.build import build
from models_rf.runner import run_rf
from portfolio.backtest import compute_portfolio_returns_from_fixed, summarise_returns
from portfolio.models import RfPortfolioReturn, RfPortfolioWeight
from portfolio.optimiser import optimise_weights
from portfolio.runner import backtest_run


class OptimiserUnitTests(TestCase):
    def test_weights_sum_to_one(self):
        dates = pd.date_range("2023-01-02", periods=252, freq="B")
        rng = np.random.default_rng(0)
        prices = pd.DataFrame(
            {
                "A": 100 * np.exp(np.cumsum(rng.normal(0.0008, 0.01, len(dates)))),
                "B": 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.012, len(dates)))),
                "C": 100 * np.exp(np.cumsum(rng.normal(0.0011, 0.013, len(dates)))),
            },
            index=dates,
        )
        weights = optimise_weights(prices, lower_bound=0.05, per_asset_cap=0.7)
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=3)
        for w in weights.values():
            self.assertGreaterEqual(w, 0.0)
            self.assertLessEqual(w, 0.7 + 1e-6)


class BacktestUnitTests(TestCase):
    def test_long_only_backtest_produces_returns(self):
        dates = pd.date_range("2023-01-02", "2024-12-31", freq="B")
        rng = np.random.default_rng(1)
        prices = pd.DataFrame(
            {
                f"T{i}": 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.011, len(dates))))
                for i in range(4)
            },
            index=dates,
        )
        fixed = {
            "2024-01-31": ["T0", "T1"],
            "2024-02-29": ["T1", "T2"],
            "2024-03-29": ["T2", "T3"],
        }
        daily, weight_rows = compute_portfolio_returns_from_fixed(
            fixed, prices, optimise_weights
        )
        self.assertFalse(daily.empty)
        self.assertIn("strategy_return", daily.columns)
        self.assertGreater(len(weight_rows), 0)

    def test_long_short_weights_dollar_neutral(self):
        dates = pd.date_range("2023-01-02", "2024-12-31", freq="B")
        rng = np.random.default_rng(2)
        prices = pd.DataFrame(
            {
                f"T{i}": 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.012, len(dates))))
                for i in range(4)
            },
            index=dates,
        )
        long_dates = {"2024-02-29": ["T0", "T1"]}
        short_dates = {"2024-02-29": ["T2", "T3"]}
        _, weight_rows = compute_portfolio_returns_from_fixed(
            long_dates, prices, optimise_weights, short_dates=short_dates
        )
        total = sum(w["weight"] for w in weight_rows)
        self.assertAlmostEqual(total, 0.0, places=2)
        gross = sum(abs(w["weight"]) for w in weight_rows)
        self.assertAlmostEqual(gross, 1.0, places=2)

    def test_summarise_returns_shapes(self):
        r = pd.Series(np.random.default_rng(3).normal(0.0005, 0.01, 252))
        s = summarise_returns(r)
        for k in ("cum_return", "ann_return", "ann_vol", "ann_sharpe", "max_drawdown", "hit_rate_days"):
            self.assertIn(k, s)


class BacktestRunnerTests(TransactionTestCase):
    def setUp(self):
        seed_raw_data(symbols=["AAA", "BBB", "CCC"], start="2021-01-01", end="2024-12-31")
        build()
        os.environ["FORECASTER_DB_PATH"] = str(connection.settings_dict["NAME"])

    def tearDown(self):
        os.environ.pop("FORECASTER_DB_PATH", None)

    def test_backtest_run_persists_and_logs(self):
        run_id = run_rf(top_k=2, min_train_rows=20, name="bt_test")
        summary = backtest_run(run_id)
        self.assertIn("cum_return", summary)
        self.assertGreater(RfPortfolioReturn.objects.filter(run_id=run_id).count(), 0)
        self.assertGreater(RfPortfolioWeight.objects.filter(run_id=run_id).count(), 0)
