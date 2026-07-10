"""Orchestrator: raw_prices -> fct_features (M3a — no betas yet)."""

from __future__ import annotations

import logging

import pandas as pd
from django.db import transaction

from features.betas import calculate_betas, load_monthly_factors
from features.indicators import compute_daily_indicators
from features.models import FctFeature
from features.returns import add_monthly_returns, add_target_1m, to_month_end
from ingest.models import RawPrice

log = logging.getLogger(__name__)

FEATURE_COLS = [
    "rsi",
    "garman_klass_volatility",
    "close_over_open",
    "atr",
    "macd",
    "bb_low",
    "bb_mid",
    "bb_high",
    "return_1m",
    "return_2m",
    "return_3m",
    "return_6m",
    "return_9m",
    "return_12m",
    "beta_mkt_rf",
    "beta_smb",
    "beta_hml",
    "beta_rmw",
    "beta_cma",
]


def load_raw_prices() -> pd.DataFrame:
    qs = RawPrice.objects.all().values(
        "symbol", "date", "open", "high", "low", "close", "adj_close", "volume"
    )
    df = pd.DataFrame.from_records(qs)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    for c in ("open", "high", "low", "close", "adj_close"):
        df[c] = df[c].astype(float)
    return df


def build() -> dict:
    """Runs the full daily→monthly→features→target pipeline and writes fct_features.

    Returns a summary dict."""
    prices = load_raw_prices()
    if prices.empty:
        return {"status": "no_data", "rows": 0}

    log.info("computing daily indicators on %s rows", len(prices))
    daily = compute_daily_indicators(prices)

    log.info("rolling to month-end")
    monthly = to_month_end(daily)

    log.info("adding multi-horizon returns")
    monthly = add_monthly_returns(monthly)

    log.info("adding target_1m (forward shift)")
    monthly = add_target_1m(monthly)

    log.info("computing rolling factor betas (24m window)")
    factors_monthly = load_monthly_factors()
    betas = calculate_betas(monthly, factors_monthly)
    if not betas.empty:
        # Align date dtypes before merge.
        betas["date"] = pd.to_datetime(betas["date"])
        monthly = monthly.merge(betas, on=["symbol", "date"], how="left")
    else:
        for col in ("beta_mkt_rf", "beta_smb", "beta_hml", "beta_rmw", "beta_cma"):
            monthly[col] = None

    # Write. Use a transaction; replace existing rows for any (symbol, date)
    # we're about to insert.
    rows = []
    for r in monthly.itertuples(index=False):
        rows.append(
            FctFeature(
                symbol=r.symbol,
                date=r.date.date(),
                rsi=_nn(getattr(r, "rsi", None)),
                garman_klass_volatility=_nn(getattr(r, "garman_klass_volatility", None)),
                close_over_open=_nn(getattr(r, "close_over_open", None)),
                atr=_nn(getattr(r, "atr", None)),
                macd=_nn(getattr(r, "macd", None)),
                bb_low=_nn(getattr(r, "bb_low", None)),
                bb_mid=_nn(getattr(r, "bb_mid", None)),
                bb_high=_nn(getattr(r, "bb_high", None)),
                return_1m=_nn(getattr(r, "return_1m", None)),
                return_2m=_nn(getattr(r, "return_2m", None)),
                return_3m=_nn(getattr(r, "return_3m", None)),
                return_6m=_nn(getattr(r, "return_6m", None)),
                return_9m=_nn(getattr(r, "return_9m", None)),
                return_12m=_nn(getattr(r, "return_12m", None)),
                beta_mkt_rf=_nn(getattr(r, "beta_mkt_rf", None)),
                beta_smb=_nn(getattr(r, "beta_smb", None)),
                beta_hml=_nn(getattr(r, "beta_hml", None)),
                beta_rmw=_nn(getattr(r, "beta_rmw", None)),
                beta_cma=_nn(getattr(r, "beta_cma", None)),
                target_1m=_nn(getattr(r, "target_1m", None)),
            )
        )

    with transaction.atomic():
        # Full rebuild semantics: truncate then bulk-insert. This is a pure
        # derivation so there is no history to preserve.
        FctFeature.objects.all().delete()
        FctFeature.objects.bulk_create(rows, batch_size=5000)

    # Summary metrics
    n_total = len(rows)
    trainable = monthly.dropna(subset=FEATURE_COLS + ["target_1m"])
    return {
        "status": "ok",
        "rows": n_total,
        "months": int(monthly["date"].nunique()),
        "symbols": int(monthly["symbol"].nunique()),
        "trainable_rows": int(len(trainable)),
        "first_date": str(monthly["date"].min().date()),
        "last_date": str(monthly["date"].max().date()),
    }


def _nn(v):
    if v is None:
        return None
    try:
        if v != v:  # NaN
            return None
    except Exception:
        return None
    return float(v)
