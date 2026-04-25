"""Monthly aggregation, multi-horizon returns, target_1m."""

from __future__ import annotations

import pandas as pd

LAGS = (1, 2, 3, 6, 9, 12)


def to_month_end(daily: pd.DataFrame) -> pd.DataFrame:
    """Roll daily indicator frame to month-end: last trading day per (ticker, month)."""
    df = daily.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month_end"] = df["date"] + pd.offsets.MonthEnd(0)
    # Take the last observation in each (symbol, month_end) group.
    monthly = (
        df.sort_values(["symbol", "date"])
        .groupby(["symbol", "month_end"], as_index=False)
        .tail(1)
    )
    monthly = monthly.drop(columns=["date"]).rename(columns={"month_end": "date"})
    return monthly.reset_index(drop=True)


def add_monthly_returns(
    monthly: pd.DataFrame, outlier_cutoff: float = 0.005
) -> pd.DataFrame:
    """Compute return_{1,2,3,6,9,12}m on adj_close with symmetric winsorization,
    matching the notebook's `calculate_monthly_returns`."""
    df = monthly.sort_values(["symbol", "date"]).copy()

    def _per_ticker(g: pd.DataFrame) -> pd.DataFrame:
        g = g.copy()
        for lag in LAGS:
            col = f"return_{lag}m"
            r = g["adj_close"].pct_change(lag)
            low, high = r.quantile(outlier_cutoff), r.quantile(1 - outlier_cutoff)
            # clip only if we have enough history for the quantiles to be meaningful.
            if pd.notna(low) and pd.notna(high):
                r = r.clip(lower=low, upper=high)
            g[col] = r
        return g

    parts = [_per_ticker(g) for _, g in df.groupby("symbol", sort=False)]
    return pd.concat(parts, ignore_index=True) if parts else df


def add_target_1m(monthly: pd.DataFrame) -> pd.DataFrame:
    """target_1m = next-month return_1m (per ticker). Strictly forward-looking,
    so `dropna(subset=[target_1m])` at train time removes the last month.
    """
    df = monthly.sort_values(["symbol", "date"]).copy()
    df["target_1m"] = df.groupby("symbol")["return_1m"].shift(-1)
    return df
