"""Port of `compute_portfolio_returns_from_fixed` from ../Finance/test.py,
with entry-delay and holding-period made explicit parameters.

The source code used `end_ts = start_ts + MonthEnd(0)` combined with month-end
rebalance dates, which collapsed the holding window to a single day and
measured the rebalance-day return (incl. pre-signal movement). We keep that
configuration available via params but default to the standard convention:

  - Signal time       : t = rebalance month-end close.
  - Entry             : t + entry_delay_bdays (default 1 = T+1).
  - Exit / hold until : next month-end close (or `holding` business days).

Real-life frictions NOT modelled: transaction costs, slippage, borrow fees,
tax. yfinance data is also survivorship-biased — delisted names aren't
there. Both biases tilt realised returns upward, so treat the numbers as an
upper bound on actually-tradable performance.
"""

from __future__ import annotations

import logging
from typing import Callable, Literal, Union

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

Holding = Union[Literal["next_month"], int]


def compute_portfolio_returns_from_fixed(
    fixed_dates: dict[str, list[str]],
    price_df: pd.DataFrame,
    optimise_weights_func: Callable,
    *,
    short_dates: dict[str, list[str]] | None = None,
    lower_bound_factor: float = 0.5,
    entry_delay_bdays: int = 1,
    holding: Holding = "next_month",
) -> tuple[pd.DataFrame, list[dict]]:
    """Return (daily_returns_df, weights_rows).

    Parameters
    ----------
    fixed_dates
        Mapping "YYYY-MM-DD" -> [tickers], produced by the RF pick step.
    price_df
        Wide adj_close (index = date, columns = symbol).
    optimise_weights_func
        Typically `portfolio.optimiser.optimise_weights`.
    lower_bound_factor
        Passed through to the optimiser as `lower_bound = lb_factor / n`.
    entry_delay_bdays
        Business days between the rebalance date and position entry.
        0 = same-day (source's look-ahead-y behaviour),
        1 = T+1 (realistic default),
        ≥2 = conservative extra slack.
    holding
        "next_month" (default): hold until the next month-end close.
        int N : hold for exactly N business days after entry (N=1 reproduces
        a degenerate 1-day hold; the source's behaviour corresponds roughly
        to `entry_delay_bdays=0, holding=1` but measured *backwards*).

    Returns
    -------
    daily_returns_df : DataFrame indexed by date with a "strategy_return" column.
    weights_rows    : list of dicts {rebalance_date, symbol, weight} for persistence.
    """
    if not fixed_dates and not short_dates:
        return pd.DataFrame(), []

    short_dates = short_dates or {}
    pct = price_df.pct_change()
    bday = pd.tseries.offsets.BDay()

    parts: list[pd.DataFrame] = []
    weights_rows: list[dict] = []

    # Every rebalance date across long + short sides.
    all_dates = sorted(set(fixed_dates.keys()) | set(short_dates.keys()))
    long_short_mode = bool(short_dates)

    for rebalance_str in all_dates:
        try:
            rebalance_ts = pd.to_datetime(rebalance_str)
            entry_ts = rebalance_ts + entry_delay_bdays * bday
            if holding == "next_month":
                exit_ts = rebalance_ts + pd.offsets.MonthEnd(1)
            else:
                exit_ts = entry_ts + int(holding) * bday

            opt_start = (rebalance_ts - pd.DateOffset(months=12)).strftime("%Y-%m-%d")
            opt_end = (rebalance_ts - pd.DateOffset(days=1)).strftime("%Y-%m-%d")

            long_tickers = fixed_dates.get(rebalance_str, [])
            short_tickers = short_dates.get(rebalance_str, [])
            if not long_tickers and not short_tickers:
                continue

            long_w = _optimise_side(
                long_tickers,
                price_df,
                opt_start,
                opt_end,
                optimise_weights_func,
                lower_bound_factor,
                rebalance_str,
                "long",
            )
            short_w = _optimise_side(
                short_tickers,
                price_df,
                opt_start,
                opt_end,
                optimise_weights_func,
                lower_bound_factor,
                rebalance_str,
                "short",
            )

            # Combine into signed weights. In long-short mode each side
            # gets half notional (net=0, gross=1). In long-only mode the
            # long side keeps full notional.
            if long_short_mode and not long_w.empty and not short_w.empty:
                combined = pd.concat([long_w * 0.5, -short_w * 0.5])
            elif long_short_mode and not long_w.empty:
                combined = long_w  # no valid shorts → fall back to long-only notional
            elif long_short_mode and not short_w.empty:
                combined = -short_w  # only shorts → negative-net portfolio
            else:
                combined = long_w

            if combined.empty:
                continue

            holding_returns = pct.loc[
                entry_ts.strftime("%Y-%m-%d") : exit_ts.strftime("%Y-%m-%d"),
                combined.index,
            ]
            if holding_returns.empty:
                continue

            weights = combined.reindex(holding_returns.columns).fillna(0)
            strat = (
                holding_returns.mul(weights, axis=1)
                .sum(axis=1)
                .to_frame("strategy_return")
            )
            parts.append(strat)

            for sym, w in weights.items():
                if w != 0:
                    weights_rows.append(
                        {
                            "rebalance_date": rebalance_ts.date(),
                            "symbol": sym,
                            "weight": float(w),
                        }
                    )
        except Exception as exc:
            log.warning("skip rebalance %s: %s", rebalance_str, exc)
            continue

    if not parts:
        return pd.DataFrame(), weights_rows

    out = pd.concat(parts).sort_index()
    # With monthly rebalances and next-month-end holds, the exit day of one
    # window equals the rebalance of the next. Use last() so we don't
    # double-count the boundary date when parts overlap at the seam.
    out = out.groupby(out.index).last()
    return out, weights_rows


def _optimise_side(
    tickers: list[str],
    price_df: pd.DataFrame,
    opt_start: str,
    opt_end: str,
    optimise_weights_func: Callable,
    lower_bound_factor: float,
    rebalance_str: str,
    side_label: str,
) -> pd.Series:
    """Run optimise_weights on one side (all-positive weights summing to 1).
    Returns empty Series if the side is empty or has no clean price data."""
    available = [t for t in tickers if t in price_df.columns]
    if not available:
        return pd.Series(dtype=float)
    opt_prices = price_df.loc[opt_start:opt_end, available].dropna(
        axis=1, how="any"
    )
    if opt_prices.shape[1] == 0:
        return pd.Series(dtype=float)
    try:
        lb = round(1 / opt_prices.shape[1] * lower_bound_factor, 3)
        w = optimise_weights_func(prices=opt_prices, lower_bound=lb)
        if isinstance(w, (list, tuple, np.ndarray)):
            s = pd.Series(w, index=opt_prices.columns)
        else:
            s = pd.Series(w)
            s.index = opt_prices.columns[: len(s)]
    except Exception as exc:
        log.warning(
            "optimise (%s) failed at %s; using equal weights (%s)",
            side_label,
            rebalance_str,
            exc,
        )
        s = pd.Series(1.0 / opt_prices.shape[1], index=opt_prices.columns)
    return s


def summarise_returns(returns: pd.Series, trading_days: int = 252) -> dict[str, float]:
    """Standard portfolio metrics from a daily-return series."""
    r = returns.dropna()
    if r.empty:
        return {}
    cum = float((1 + r).prod() - 1)
    mean = float(r.mean())
    std = float(r.std(ddof=0))
    ann_return = mean * trading_days
    ann_vol = std * np.sqrt(trading_days)
    sharpe = ann_return / ann_vol if ann_vol > 0 else float("nan")

    equity = (1 + r).cumprod()
    peak = equity.cummax()
    drawdown = (equity / peak - 1).min()
    max_dd = float(drawdown) if pd.notna(drawdown) else float("nan")

    hit = float((r > 0).mean())

    return {
        "cum_return": cum,
        "ann_return": ann_return,
        "ann_vol": ann_vol,
        "ann_sharpe": sharpe,
        "max_drawdown": max_dd,
        "hit_rate_days": hit,
        "n_days": int(len(r)),
    }
