"""Tests for feature engineering — technicals, monthly rollup, returns,
target shift, and rolling factor betas."""

from __future__ import annotations

import numpy as np
import pandas as pd
from django.test import TestCase

from _test_fixtures import seed_raw_data
from features.build import FEATURE_COLS, build
from features.indicators import compute_daily_indicators, rsi
from features.models import FctFeature
from features.returns import add_target_1m, to_month_end


class IndicatorUnitTests(TestCase):
    def test_rsi_is_in_valid_range(self):
        # Random walk with some volatility — RSI should be non-NaN and in [0, 100]
        rng = np.random.default_rng(0)
        s = pd.Series(100 + np.cumsum(rng.normal(0.05, 1.0, 200)))
        out = rsi(s, length=14)
        last_fifty = out.iloc[-50:]
        self.assertFalse(last_fifty.isna().any(), "RSI shouldn't be NaN post-warmup")
        self.assertTrue((last_fifty >= 0).all() and (last_fifty <= 100).all())

    def test_rsi_reacts_to_drift(self):
        rng = np.random.default_rng(1)
        # Strong positive drift → RSI elevated on average
        up = pd.Series(100 + np.cumsum(rng.normal(0.6, 0.4, 200)))
        # Strong negative drift → RSI depressed on average
        down = pd.Series(100 + np.cumsum(rng.normal(-0.6, 0.4, 200)))
        self.assertGreater(rsi(up, 14).iloc[-50:].mean(), rsi(down, 14).iloc[-50:].mean() + 20)

    def test_compute_daily_indicators_appends_expected_columns(self):
        df = pd.DataFrame(
            {
                "symbol": ["A"] * 50 + ["B"] * 50,
                "date": pd.concat(
                    [pd.Series(pd.date_range("2024-01-01", periods=50))] * 2,
                    ignore_index=True,
                ),
                "open": np.linspace(100, 110, 100),
                "high": np.linspace(101, 112, 100),
                "low": np.linspace(99, 108, 100),
                "close": np.linspace(100, 110, 100),
                "adj_close": np.linspace(100, 110, 100),
                "volume": 1_000_000,
            }
        )
        out = compute_daily_indicators(df)
        self.assertEqual(len(out), 100)
        for col in (
            "rsi",
            "bb_low",
            "bb_mid",
            "bb_high",
            "atr",
            "macd",
            "garman_klass_volatility",
            "close_over_open",
        ):
            self.assertIn(col, out.columns)


class MonthlyRollupTests(TestCase):
    def test_to_month_end_keeps_last_trading_day_per_month(self):
        df = pd.DataFrame(
            {
                "symbol": ["A"] * 10,
                "date": pd.date_range("2024-01-02", periods=10, freq="B"),
                "adj_close": np.arange(10.0),
                "open": 1.0,
                "high": 1.0,
                "low": 1.0,
                "close": 1.0,
                "volume": 1,
            }
        )
        monthly = to_month_end(df)
        self.assertEqual(len(monthly), 1)
        self.assertEqual(monthly["date"].iloc[0], pd.Timestamp("2024-01-31"))
        self.assertEqual(monthly["adj_close"].iloc[0], 9.0)

    def test_add_target_1m_shifts_per_ticker(self):
        df = pd.DataFrame(
            {
                "symbol": ["A", "A", "A", "B", "B"],
                "date": pd.to_datetime(
                    ["2024-01-31", "2024-02-29", "2024-03-31", "2024-01-31", "2024-02-29"]
                ),
                "return_1m": [0.01, 0.02, 0.03, -0.01, -0.02],
            }
        )
        out = add_target_1m(df)
        self.assertAlmostEqual(
            out.loc[out["symbol"] == "A"].iloc[0]["target_1m"], 0.02
        )
        self.assertTrue(np.isnan(out.loc[out["symbol"] == "A"].iloc[-1]["target_1m"]))
        self.assertTrue(np.isnan(out.loc[out["symbol"] == "B"].iloc[-1]["target_1m"]))


class FullBuildTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_raw_data(symbols=["AAA", "BBB", "CCC"], start="2021-01-01", end="2024-12-31")

    def test_build_populates_fct_features(self):
        summary = build()
        self.assertEqual(summary["status"], "ok")
        self.assertEqual(summary["symbols"], 3)
        self.assertGreater(summary["months"], 24)
        self.assertEqual(FctFeature.objects.count(), summary["rows"])

    def test_betas_populated_after_warmup(self):
        build()
        n_with_betas = FctFeature.objects.filter(beta_mkt_rf__isnull=False).count()
        self.assertGreater(n_with_betas, 30)

    def test_trainable_rows_have_all_features_non_null(self):
        build()
        trainable = FctFeature.objects.filter(
            target_1m__isnull=False,
            beta_mkt_rf__isnull=False,
            return_12m__isnull=False,
        )
        self.assertGreater(trainable.count(), 0)
        for row in trainable[:5]:
            for col in FEATURE_COLS:
                self.assertIsNotNone(getattr(row, col), f"{col} is None on {row}")

    def test_every_symbol_has_some_betas(self):
        build()
        for sym in ["AAA", "BBB", "CCC"]:
            count = FctFeature.objects.filter(
                symbol=sym, beta_mkt_rf__isnull=False
            ).count()
            self.assertGreater(count, 0, f"{sym} has no beta rows")
