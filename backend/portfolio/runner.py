"""Orchestrator: rf_picks + raw_prices -> rf_portfolio_{weights,returns} +
logged metrics against the RF run that produced the picks."""

from __future__ import annotations

import logging

import pandas as pd
from django.db import transaction

import tracker
from ingest.models import RawPrice
from models_rf.models import RfPick
from portfolio.backtest import compute_portfolio_returns_from_fixed, summarise_returns
from portfolio.models import RfPortfolioReturn, RfPortfolioWeight
from portfolio.optimiser import optimise_weights

log = logging.getLogger(__name__)


def _load_wide_prices() -> pd.DataFrame:
    """Return adj_close pivoted wide: index=date, columns=symbol."""
    qs = RawPrice.objects.all().values("date", "symbol", "adj_close")
    df = pd.DataFrame.from_records(qs)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    wide = df.pivot_table(
        index="date", columns="symbol", values="adj_close", aggfunc="last"
    )
    return wide.sort_index()


def _load_fixed_dates(
    run_id: str,
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Return (long_dates, short_dates) mappings: "YYYY-MM-DD" -> [symbols]."""
    picks = (
        RfPick.objects.filter(run_id=run_id)
        .order_by("rebalance_date", "direction", "picked_rank")
        .values("rebalance_date", "symbol", "direction")
    )
    longs: dict[str, list[str]] = {}
    shorts: dict[str, list[str]] = {}
    for p in picks:
        key = p["rebalance_date"].strftime("%Y-%m-%d")
        if p["direction"] == -1:
            shorts.setdefault(key, []).append(p["symbol"])
        else:
            longs.setdefault(key, []).append(p["symbol"])
    return longs, shorts


def backtest_run(
    run_id: str,
    *,
    entry_delay_bdays: int = 1,
    holding: str = "next_month",  # "next_month" or int-as-str
) -> dict:
    """Backtest the RF run identified by `run_id`. Persists daily returns and
    per-rebalance weights; logs summary metrics + backtest params back to the
    run via tracker.attach."""
    run_id = run_id.replace("-", "")

    longs, shorts = _load_fixed_dates(run_id)
    if not longs and not shorts:
        raise RuntimeError(
            f"No rf_picks found for run_id={run_id}. Run rf_run first."
        )

    prices = _load_wide_prices()
    if prices.empty:
        raise RuntimeError("raw_prices is empty; run `make ingest` first.")

    holding_arg: object = holding
    if holding != "next_month":
        try:
            holding_arg = int(holding)
        except (TypeError, ValueError):
            raise RuntimeError(
                f"--holding must be 'next_month' or an int, got {holding!r}"
            )

    daily_df, weight_rows = compute_portfolio_returns_from_fixed(
        longs,
        prices,
        optimise_weights,
        short_dates=shorts or None,
        entry_delay_bdays=entry_delay_bdays,
        holding=holding_arg,
    )

    # Clear any previous backtest for this run so reruns are idempotent.
    with transaction.atomic():
        RfPortfolioReturn.objects.filter(run_id=run_id).delete()
        RfPortfolioWeight.objects.filter(run_id=run_id).delete()

        if not daily_df.empty:
            RfPortfolioReturn.objects.bulk_create(
                [
                    RfPortfolioReturn(
                        run_id=run_id,
                        date=idx.date() if hasattr(idx, "date") else idx,
                        strategy_return=float(val),
                    )
                    for idx, val in daily_df["strategy_return"].items()
                ],
                batch_size=5000,
            )

        if weight_rows:
            RfPortfolioWeight.objects.bulk_create(
                [RfPortfolioWeight(run_id=run_id, **row) for row in weight_rows],
                batch_size=5000,
            )

    if daily_df.empty:
        summary = {"status": "empty"}
    else:
        summary = summarise_returns(daily_df["strategy_return"])
        summary["n_rebalance_dates"] = len(set(longs) | set(shorts))
        summary["long_short_mode"] = bool(shorts)

        with tracker.attach(run_id) as r:
            r.tag("backtested")
            # Record the backtest configuration as run params so different
            # configurations are comparable side-by-side on the leaderboard.
            r.param("backtest_entry_delay_bdays", entry_delay_bdays)
            r.param("backtest_holding", holding)
            for k, v in summary.items():
                if isinstance(v, (int, float)):
                    r.log_metric(f"portfolio_{k}", float(v))

    return {
        "run_id": run_id,
        "n_days_returns": int(len(daily_df)),
        "n_weight_rows": len(weight_rows),
        **summary,
    }
