from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from quality import checks
from quality.models import DqCheck, DqRun


def run_all_checks(universe_name: str = "default") -> DqRun:
    """Execute every named check and persist results under a single DqRun."""
    prices = checks.load_prices_df()
    factors = checks.load_factors_df()

    results = [
        checks.check_schema_raw_prices(prices),
        checks.check_freshness_prices(prices),
        checks.check_null_pct_prices(prices),
        checks.check_duplicate_prices(prices),
        checks.check_suspicious_returns(prices),
        checks.check_schema_raw_factors(factors),
        checks.check_freshness_factors(factors),
        checks.check_null_pct_factors(factors),
        checks.check_duplicate_factors(factors),
        checks.check_universe_coverage(universe_name),
    ]

    summary = {
        "total": len(results),
        "pass": sum(1 for r in results if r.status == DqCheck.STATUS_PASS),
        "warn": sum(1 for r in results if r.status == DqCheck.STATUS_WARN),
        "fail": sum(1 for r in results if r.status == DqCheck.STATUS_FAIL),
        "universe": universe_name,
    }

    with transaction.atomic():
        run = DqRun.objects.create(summary=summary)
        DqCheck.objects.bulk_create(
            [DqCheck(run=run, **r.to_model_kwargs()) for r in results]
        )
        run.finished_at = timezone.now()
        run.save(update_fields=["finished_at"])
    return run
