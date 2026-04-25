"""Tests for DQ checks — run against seeded fixtures, verify statuses."""

from django.test import TestCase

from _test_fixtures import seed_raw_data
from quality import checks
from quality.models import DqCheck
from quality.runner import run_all_checks


class DqRunnerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_raw_data(symbols=["AAA", "BBB", "CCC"], start="2024-01-01", end="2024-12-31")

    def test_run_all_checks_persists_ten_checks(self):
        run = run_all_checks(universe_name="smoke")
        self.assertEqual(run.checks.count(), 10)
        names = set(run.checks.values_list("check_name", flat=True))
        for name in [
            "schema_raw_prices",
            "schema_raw_factors",
            "freshness_prices",
            "freshness_factors",
            "null_pct_prices",
            "null_pct_factors",
            "duplicate_prices",
            "duplicate_factors",
            "suspicious_returns",
            "universe_coverage",
        ]:
            self.assertIn(name, names)

    def test_schema_passes_on_clean_data(self):
        df = checks.load_prices_df()
        result = checks.check_schema_raw_prices(df)
        self.assertEqual(result.status, DqCheck.STATUS_PASS)

    def test_duplicate_prices_zero_on_clean_data(self):
        df = checks.load_prices_df()
        result = checks.check_duplicate_prices(df)
        self.assertEqual(result.status, DqCheck.STATUS_PASS)
        self.assertEqual(result.rows_failed, 0)

    def test_universe_coverage_flags_missing_symbols(self):
        # Seeded symbols aren't in the `default` universe, so coverage warns.
        result = checks.check_universe_coverage("default")
        self.assertEqual(result.status, DqCheck.STATUS_WARN)
        self.assertGreater(result.rows_failed, 0)
