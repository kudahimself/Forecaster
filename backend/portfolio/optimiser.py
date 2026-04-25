"""Port of `optimise_weights` from ../Finance/utils/portfolio copy.py.

Max-Sharpe efficient frontier with per-asset cap + adaptive lower bound,
solver fallbacks, and equal-weight safety net if everything fails.
"""

from __future__ import annotations

import logging

import pandas as pd
from pypfopt import expected_returns, risk_models
from pypfopt.efficient_frontier import EfficientFrontier

log = logging.getLogger(__name__)


def optimise_weights(
    prices: pd.DataFrame,
    *,
    lower_bound: float = 0.0,
    per_asset_cap: float = 0.7,
    solver: str = "SCS",
) -> dict[str, float]:
    """Given a wide daily-price DataFrame (index=date, columns=tickers), return
    {ticker: weight} that maximises Sharpe under `weight_bounds=(lower, upper)`.

    If feasibility fails even after relaxing bounds, returns equal weights."""
    prices = prices.dropna(axis=1, how="all").dropna(axis=0, how="all")
    n = prices.shape[1]
    if n == 0:
        raise ValueError("No tickers to optimise")

    returns = expected_returns.mean_historical_return(prices, frequency=252)
    cov = risk_models.sample_cov(prices, frequency=252)

    upper = per_asset_cap
    if upper * n < 1.0:
        upper = max(upper, 1.0 / n)
    lower = min(lower_bound, upper)

    # Quick feasibility guard: can weights in [lower, upper] sum to 1?
    if lower * n > 1.0 + 1e-12 or upper * n < 1.0 - 1e-12:
        return {col: 1.0 / n for col in prices.columns}

    for s in (solver, "ECOS", "OSQP"):
        try:
            ef = EfficientFrontier(
                returns, cov_matrix=cov, weight_bounds=(lower, upper), solver=s
            )
            ef.max_sharpe()
            return ef.clean_weights()
        except Exception:
            continue

    # Fallback: relaxed bounds.
    try:
        ef = EfficientFrontier(
            returns, cov_matrix=cov, weight_bounds=(0.0, 0.5), solver=solver
        )
        ef.max_sharpe()
        return ef.clean_weights()
    except Exception as exc:
        log.warning(
            "Optimisation failed; returning equal weights (err=%s)", exc
        )
        return {col: 1.0 / n for col in prices.columns}
