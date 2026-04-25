"""Individual DQ checks. Each check function returns a dict matching the DqCheck
schema: {check_name, status, rows_checked, rows_failed, details}."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd

from ingest.models import RawFactor, RawPrice, Symbol
from ingest.universe import load_universe
from quality.models import DqCheck
from quality.schemas import raw_factors_schema, raw_prices_schema


@dataclass
class CheckResult:
    check_name: str
    status: str  # 'pass' | 'warn' | 'fail'
    rows_checked: int = 0
    rows_failed: int = 0
    details: dict[str, Any] = field(default_factory=dict)

    def to_model_kwargs(self) -> dict[str, Any]:
        return {
            "check_name": self.check_name,
            "status": self.status,
            "rows_checked": self.rows_checked,
            "rows_failed": self.rows_failed,
            "details": self.details,
        }


# ---------- loaders ----------


def load_prices_df() -> pd.DataFrame:
    qs = RawPrice.objects.all().values(
        "symbol", "date", "open", "high", "low", "close", "adj_close", "volume"
    )
    df = pd.DataFrame.from_records(qs)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    for c in ("open", "high", "low", "close", "adj_close"):
        df[c] = df[c].astype(float)
    df["volume"] = df["volume"].astype("Int64")
    return df


def load_factors_df() -> pd.DataFrame:
    qs = RawFactor.objects.all().values(
        "date", "mkt_rf", "smb", "hml", "rmw", "cma", "mom", "rf"
    )
    df = pd.DataFrame.from_records(qs)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    for c in ("mkt_rf", "smb", "hml", "rmw", "cma", "mom", "rf"):
        df[c] = df[c].astype(float)
    return df


# ---------- schema ----------


def check_schema_raw_prices(df: pd.DataFrame) -> CheckResult:
    name = "schema_raw_prices"
    if df.empty:
        return CheckResult(name, DqCheck.STATUS_WARN, details={"note": "no rows"})
    try:
        raw_prices_schema.validate(df, lazy=True)
        return CheckResult(name, DqCheck.STATUS_PASS, rows_checked=len(df))
    except Exception as exc:  # pandera.errors.SchemaErrors or related
        return CheckResult(
            name,
            DqCheck.STATUS_FAIL,
            rows_checked=len(df),
            details={"error": str(exc)[:2000]},
        )


def check_schema_raw_factors(df: pd.DataFrame) -> CheckResult:
    name = "schema_raw_factors"
    if df.empty:
        return CheckResult(name, DqCheck.STATUS_WARN, details={"note": "no rows"})
    try:
        raw_factors_schema.validate(df, lazy=True)
        return CheckResult(name, DqCheck.STATUS_PASS, rows_checked=len(df))
    except Exception as exc:
        return CheckResult(
            name,
            DqCheck.STATUS_FAIL,
            rows_checked=len(df),
            details={"error": str(exc)[:2000]},
        )


# ---------- freshness ----------


def check_freshness_prices(
    df: pd.DataFrame, warn_after_business_days: int = 7
) -> CheckResult:
    name = "freshness_prices"
    if df.empty:
        return CheckResult(name, DqCheck.STATUS_WARN, details={"note": "no rows"})
    latest = df["date"].max().date()
    today = date.today()
    gap = _business_days_between(latest, today)
    status = (
        DqCheck.STATUS_PASS if gap <= warn_after_business_days else DqCheck.STATUS_WARN
    )
    return CheckResult(
        name,
        status,
        rows_checked=len(df),
        details={
            "latest_date": latest.isoformat(),
            "today": today.isoformat(),
            "business_day_gap": gap,
            "threshold_bdays": warn_after_business_days,
        },
    )


def check_freshness_factors(
    df: pd.DataFrame, warn_after_business_days: int = 14
) -> CheckResult:
    name = "freshness_factors"
    if df.empty:
        return CheckResult(name, DqCheck.STATUS_WARN, details={"note": "no rows"})
    latest = df["date"].max().date()
    today = date.today()
    gap = _business_days_between(latest, today)
    status = (
        DqCheck.STATUS_PASS if gap <= warn_after_business_days else DqCheck.STATUS_WARN
    )
    return CheckResult(
        name,
        status,
        rows_checked=len(df),
        details={
            "latest_date": latest.isoformat(),
            "today": today.isoformat(),
            "business_day_gap": gap,
            "threshold_bdays": warn_after_business_days,
        },
    )


# ---------- null% ----------


def check_null_pct_prices(
    df: pd.DataFrame, warn_pct: float = 5.0
) -> CheckResult:
    name = "null_pct_prices"
    if df.empty:
        return CheckResult(name, DqCheck.STATUS_WARN, details={"note": "no rows"})
    nulls = df["adj_close"].isna().sum()
    total = len(df)
    pct = float(100.0 * nulls / total) if total else 0.0
    status = DqCheck.STATUS_PASS if pct <= warn_pct else DqCheck.STATUS_WARN
    return CheckResult(
        name,
        status,
        rows_checked=total,
        rows_failed=int(nulls),
        details={"null_pct_adj_close": round(pct, 4), "threshold_pct": warn_pct},
    )


def check_null_pct_factors(df: pd.DataFrame) -> CheckResult:
    name = "null_pct_factors"
    if df.empty:
        return CheckResult(name, DqCheck.STATUS_WARN, details={"note": "no rows"})
    cols = ["mkt_rf", "smb", "hml", "rmw", "cma", "rf"]
    null_counts = {c: int(df[c].isna().sum()) for c in cols}
    total_nulls = sum(null_counts.values())
    # Factors should not have any nulls; momentum occasionally missing is tolerated.
    status = DqCheck.STATUS_PASS if total_nulls == 0 else DqCheck.STATUS_WARN
    return CheckResult(
        name,
        status,
        rows_checked=len(df),
        rows_failed=total_nulls,
        details={"null_counts": null_counts},
    )


# ---------- duplicates ----------


def check_duplicate_prices(df: pd.DataFrame) -> CheckResult:
    name = "duplicate_prices"
    if df.empty:
        return CheckResult(name, DqCheck.STATUS_WARN, details={"note": "no rows"})
    dup_mask = df.duplicated(subset=["symbol", "date"], keep=False)
    dup = int(dup_mask.sum())
    status = DqCheck.STATUS_PASS if dup == 0 else DqCheck.STATUS_FAIL
    return CheckResult(
        name, status, rows_checked=len(df), rows_failed=dup, details={}
    )


def check_duplicate_factors(df: pd.DataFrame) -> CheckResult:
    name = "duplicate_factors"
    if df.empty:
        return CheckResult(name, DqCheck.STATUS_WARN, details={"note": "no rows"})
    dup_mask = df.duplicated(subset=["date"], keep=False)
    dup = int(dup_mask.sum())
    status = DqCheck.STATUS_PASS if dup == 0 else DqCheck.STATUS_FAIL
    return CheckResult(
        name, status, rows_checked=len(df), rows_failed=dup, details={}
    )


# ---------- suspicious returns ----------


def check_suspicious_returns(
    df: pd.DataFrame, threshold: float = 0.5
) -> CheckResult:
    name = "suspicious_returns"
    if df.empty:
        return CheckResult(name, DqCheck.STATUS_WARN, details={"note": "no rows"})
    # |daily adj_close return| > threshold
    df2 = df.sort_values(["symbol", "date"]).copy()
    df2["ret"] = df2.groupby("symbol")["adj_close"].pct_change()
    suspicious = df2[df2["ret"].abs() > threshold]
    rows_failed = int(len(suspicious))
    status = DqCheck.STATUS_PASS if rows_failed == 0 else DqCheck.STATUS_WARN
    # Top offenders (limit to 20 for a readable details payload).
    top = (
        suspicious.nlargest(20, "ret", keep="all")
        .assign(date=lambda x: x["date"].dt.date.astype(str))
        [["symbol", "date", "ret"]]
        .to_dict(orient="records")
    )
    return CheckResult(
        name,
        status,
        rows_checked=len(df2),
        rows_failed=rows_failed,
        details={"threshold": threshold, "top_offenders": top},
    )


# ---------- universe coverage ----------


def check_universe_coverage(universe_name: str = "default") -> CheckResult:
    name = "universe_coverage"
    u = load_universe(universe_name)
    expected = set(u["tickers"])
    present = set(Symbol.objects.values_list("symbol", flat=True))
    missing = sorted(expected - present)
    status = DqCheck.STATUS_PASS if not missing else DqCheck.STATUS_WARN
    return CheckResult(
        name,
        status,
        rows_checked=len(expected),
        rows_failed=len(missing),
        details={"universe": universe_name, "missing": missing},
    )


# ---------- helpers ----------


def _business_days_between(d1: date, d2: date) -> int:
    """Count business days strictly between d1 and d2 (exclusive of d1, inclusive of d2)."""
    if d1 >= d2:
        return 0
    return int(np.busday_count(d1, d2))
