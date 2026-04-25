"""Rolling OLS factor betas — port of calculate_betas from ../Finance/utils/models.py.

Per-ticker 24-month rolling regression of return_1m on
  [mkt_rf, smb, hml, rmw, cma]
with min_nobs = (n_factors + 1) = 6. Betas are shifted one month per ticker
so they are strictly past-information (no lookahead into the month they label).
"""

from __future__ import annotations

import logging

import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.rolling import RollingOLS

from ingest.models import RawFactor

log = logging.getLogger(__name__)

FACTOR_COLS = ["mkt_rf", "smb", "hml", "rmw", "cma"]
WINDOW_MONTHS = 24


def load_monthly_factors() -> pd.DataFrame:
    """Daily Fama-French -> monthly by compounding: (1+r).prod() - 1 per month."""
    qs = RawFactor.objects.all().values("date", *FACTOR_COLS)
    daily = pd.DataFrame.from_records(qs)
    if daily.empty:
        return daily
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date").set_index("date")
    for c in FACTOR_COLS:
        daily[c] = daily[c].astype(float)
    # Month-end compounded return per factor column.
    monthly = (1 + daily[FACTOR_COLS]).resample("ME").prod() - 1
    monthly = monthly.reset_index().rename(columns={"date": "date"})
    monthly["date"] = monthly["date"].dt.date  # align w/ fct_features date column
    return monthly


def calculate_betas(
    features_df: pd.DataFrame, monthly_factors: pd.DataFrame
) -> pd.DataFrame:
    """Given fct_features (must include `return_1m`) and monthly factor returns,
    produce a frame indexed by (symbol, date) with columns
    [beta_mkt_rf, beta_smb, beta_hml, beta_rmw, beta_cma].

    Betas are shifted one month per ticker (strictly past-information).
    """
    if features_df.empty or monthly_factors.empty:
        return _empty_betas_df()

    f = monthly_factors.copy()
    f["date"] = pd.to_datetime(f["date"])
    df = features_df[["symbol", "date", "return_1m"]].copy()
    df["date"] = pd.to_datetime(df["date"])
    merged = df.merge(f, on="date", how="inner").dropna(
        subset=FACTOR_COLS + ["return_1m"]
    )
    if merged.empty:
        return _empty_betas_df()

    parts = []
    for sym, g in merged.groupby("symbol", sort=False):
        g = g.sort_values("date")
        n = len(g)
        if n < len(FACTOR_COLS) + 2:  # need enough obs for min_nobs + 1
            continue
        endog = g["return_1m"].values
        exog = sm.add_constant(g[FACTOR_COLS].values)
        win = min(WINDOW_MONTHS, n)
        try:
            fit = RollingOLS(
                endog=endog,
                exog=exog,
                window=win,
                min_nobs=len(FACTOR_COLS) + 1,
            ).fit(params_only=True)
        except Exception as exc:  # pragma: no cover - defensive
            log.warning("RollingOLS failed for %s: %s", sym, exc)
            continue
        params = fit.params  # shape (n, n_factors+1); col 0 is const
        betas = pd.DataFrame(
            params[:, 1:],
            index=g["date"].values,
            columns=[f"beta_{c}" for c in FACTOR_COLS],
        )
        betas["symbol"] = sym
        parts.append(betas)

    if not parts:
        return _empty_betas_df()

    out = pd.concat(parts).reset_index().rename(columns={"index": "date"})
    out = out.sort_values(["symbol", "date"])
    # One-month shift per ticker so beta at month M uses info up to M-1.
    beta_cols = [f"beta_{c}" for c in FACTOR_COLS]
    out[beta_cols] = out.groupby("symbol")[beta_cols].shift(1)
    out["date"] = pd.to_datetime(out["date"]).dt.date
    return out[["symbol", "date", *beta_cols]].reset_index(drop=True)


def _empty_betas_df() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["symbol", "date", *[f"beta_{c}" for c in FACTOR_COLS]]
    )
