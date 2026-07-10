"""Tests for the within-date permutation shuffle and end-to-end runner."""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
from django.db import connection
from django.test import TestCase, TransactionTestCase

from _test_fixtures import seed_raw_data
from features.build import build
from models_rf.runner import run_rf
from permutation.models import PermSummary
from permutation.runner import run_permutation_test
from permutation.shuffle import shuffle_target_within_date


class ShuffleInvariantsTests(TestCase):
    """The shuffle must preserve the marginal distribution on every date
    and break the (features, target) association."""

    def test_preserves_within_date_marginal(self):
        df = pd.DataFrame(
            {
                "symbol": ["A", "B", "C", "A", "B", "C"],
                "date": pd.to_datetime(
                    ["2024-01-31"] * 3 + ["2024-02-29"] * 3
                ),
                "target_1m": [0.01, 0.02, -0.01, 0.05, -0.03, 0.02],
                "x": [1, 2, 3, 4, 5, 6],
            }
        )
        out = shuffle_target_within_date(df, seed=42)
        orig_by_date = (
            df.groupby("date")["target_1m"].apply(lambda s: sorted(s.tolist()))
        )
        new_by_date = (
            out.groupby("date")["target_1m"].apply(lambda s: sorted(s.tolist()))
        )
        for d in orig_by_date.index:
            self.assertEqual(orig_by_date.loc[d], new_by_date.loc[d])

    def test_reproducible_with_seed(self):
        df = pd.DataFrame(
            {
                "symbol": list("ABCDE") * 2,
                "date": pd.to_datetime(["2024-01-31"] * 5 + ["2024-02-29"] * 5),
                "target_1m": np.arange(10, dtype=float),
            }
        )
        out1 = shuffle_target_within_date(df, seed=123)
        out2 = shuffle_target_within_date(df, seed=123)
        pd.testing.assert_series_equal(
            out1["target_1m"].reset_index(drop=True),
            out2["target_1m"].reset_index(drop=True),
        )

    def test_does_shuffle_positions(self):
        df = pd.DataFrame(
            {
                "symbol": list("ABCDEFGHIJ"),
                "date": pd.to_datetime(["2024-01-31"] * 10),
                "target_1m": np.arange(10, dtype=float),
            }
        )
        out = shuffle_target_within_date(df, seed=7)
        moved = (out["target_1m"].values != df["target_1m"].values).sum()
        self.assertGreater(moved, 0)


class PermutationEndToEndTests(TransactionTestCase):
    def setUp(self):
        seed_raw_data(symbols=["AAA", "BBB", "CCC"], start="2021-01-01", end="2024-12-31")
        build()
        os.environ["FORECASTER_DB_PATH"] = str(connection.settings_dict["NAME"])

    def tearDown(self):
        os.environ.pop("FORECASTER_DB_PATH", None)

    def test_permutation_test_persists_summary(self):
        run_id = run_rf(top_k=2, min_train_rows=20, name="perm_test_base")
        summary = run_permutation_test(run_id, n_permutations=3)
        self.assertIn("p_two_sided", summary)
        self.assertEqual(summary["n_permutations"], 3)
        self.assertTrue(PermSummary.objects.filter(run_id=run_id).exists())
        ps = PermSummary.objects.get(run_id=run_id)
        self.assertTrue(ps.artifact_path.endswith(".parquet"))
