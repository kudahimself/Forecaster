"""Deterministic test fixtures. No network, no yfinance.

`seed_raw_data` generates plausible OHLCV (geometric brownian motion) and
Fama-French factor returns for a given set of symbols and date range.
Every test module can call this in setUp() to get a reproducible warehouse.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from ingest.models import RawFactor, RawPrice, Symbol


BUSINESS_DAY = pd.tseries.offsets.BDay()


def seed_raw_data(
    symbols: list[str] | None = None,
    start: str | date = "2020-01-01",
    end: str | date = "2025-06-30",
    seed: int = 0,
) -> dict:
    """Populate raw_prices + raw_factors + dim_symbols deterministically.

    Returns a summary dict with counts and date ranges. Safe to call from
    TestCase.setUpTestData or setUp — tests run against an in-memory SQLite
    with a clean state each transaction.
    """
    symbols = symbols or ["AAA", "BBB", "CCC", "DDD", "EEE"]
    rng = np.random.default_rng(seed)

    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    dates = pd.date_range(start_ts, end_ts, freq=BUSINESS_DAY)

    # --- prices: GBM with per-ticker drift/vol ---
    price_rows: list[RawPrice] = []
    symbol_rows: list[Symbol] = []
    for i, sym in enumerate(symbols):
        drift = 0.05 + 0.04 * i  # 5-25% annualised
        vol = 0.18 + 0.03 * (i % 3)
        daily_drift = drift / 252
        daily_vol = vol / np.sqrt(252)
        start_price = 50.0 + 20.0 * i
        returns = rng.normal(daily_drift, daily_vol, size=len(dates))
        prices = start_price * np.exp(np.cumsum(returns))
        # OHLC from a noisy range around close
        for d, close in zip(dates, prices):
            rng_close_high = rng.uniform(0.002, 0.012)
            rng_close_low = rng.uniform(0.002, 0.012)
            high = float(close * (1 + rng_close_high))
            low = float(close * (1 - rng_close_low))
            open_ = float(close * (1 + rng.uniform(-0.01, 0.01)))
            price_rows.append(
                RawPrice(
                    symbol=sym,
                    date=d.date(),
                    open=open_,
                    high=high,
                    low=low,
                    close=float(close),
                    adj_close=float(close),
                    volume=int(rng.uniform(5e5, 5e6)),
                    source="test",
                )
            )
        symbol_rows.append(
            Symbol(
                symbol=sym,
                name=f"Test {sym}",
                sector="Information Technology" if i % 2 == 0 else "Health Care",
                first_seen=dates[0].date(),
                last_seen=dates[-1].date(),
            )
        )

    RawPrice.objects.bulk_create(price_rows, batch_size=5000)
    # upsert symbols one at a time to tolerate re-runs in the same TX
    for s in symbol_rows:
        Symbol.objects.update_or_create(
            symbol=s.symbol,
            defaults={
                "name": s.name,
                "sector": s.sector,
                "first_seen": s.first_seen,
                "last_seen": s.last_seen,
            },
        )

    # --- factors: small daily returns, correlated weakly to each other ---
    factor_rows: list[RawFactor] = []
    for d in dates:
        factor_rows.append(
            RawFactor(
                date=d.date(),
                mkt_rf=float(rng.normal(0.0003, 0.01)),
                smb=float(rng.normal(0.0, 0.005)),
                hml=float(rng.normal(0.0, 0.005)),
                rmw=float(rng.normal(0.0001, 0.003)),
                cma=float(rng.normal(0.0, 0.003)),
                mom=float(rng.normal(0.0001, 0.006)),
                rf=0.00008,
                source="test",
            )
        )
    RawFactor.objects.bulk_create(factor_rows, batch_size=5000)

    return {
        "n_symbols": len(symbols),
        "n_price_rows": len(price_rows),
        "n_factor_rows": len(factor_rows),
        "first_date": dates[0].date().isoformat(),
        "last_date": dates[-1].date().isoformat(),
    }


def short_window_data() -> dict:
    """~2 years of 3 symbols — enough for features but not much else."""
    return seed_raw_data(
        symbols=["AAA", "BBB", "CCC"],
        start="2023-01-01",
        end="2024-12-31",
        seed=7,
    )
