from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import date

import pandas as pd
import yfinance as yf

log = logging.getLogger(__name__)


@dataclass
class PriceRow:
    symbol: str
    date: date
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    adj_close: float | None
    volume: int | None


def fetch_prices(
    tickers: list[str],
    start: str,
    end: str,
    *,
    max_attempts: int = 3,
    backoff_seconds: float = 2.0,
) -> pd.DataFrame:
    """Bulk-fetch daily OHLCV for all tickers in one yfinance call.

    Returns a long-format DataFrame with columns:
    [symbol, date, open, high, low, close, adj_close, volume].
    Rows with all-NaN OHLCV are dropped.
    """
    if not tickers:
        return _empty_long_df()

    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            df = yf.download(
                tickers=" ".join(tickers),
                start=start,
                end=end,
                group_by="ticker",
                auto_adjust=False,
                progress=False,
                threads=True,
            )
            break
        except Exception as exc:  # pragma: no cover - network
            last_err = exc
            log.warning(
                "yfinance fetch attempt %s/%s failed: %s", attempt, max_attempts, exc
            )
            if attempt == max_attempts:
                raise
            time.sleep(backoff_seconds * attempt)
    else:  # pragma: no cover - defensive
        raise RuntimeError(f"yfinance fetch failed after {max_attempts} attempts: {last_err}")

    if df is None or df.empty:
        return _empty_long_df()

    return _to_long(df, tickers)


def _empty_long_df() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["symbol", "date", "open", "high", "low", "close", "adj_close", "volume"]
    )


def _to_long(wide: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """yfinance returns a wide MultiIndex DataFrame (ticker, field). Melt to long."""
    frames = []
    if isinstance(wide.columns, pd.MultiIndex):
        available = wide.columns.get_level_values(0).unique().tolist()
        for t in tickers:
            if t not in available:
                continue
            sub = wide[t].copy()
            sub["symbol"] = t
            frames.append(sub)
    else:
        # Single-ticker call would return a flat DataFrame.
        sub = wide.copy()
        sub["symbol"] = tickers[0] if tickers else ""
        frames.append(sub)

    if not frames:
        return _empty_long_df()

    out = pd.concat(frames)
    out = out.reset_index().rename(
        columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adj_close",
            "Volume": "volume",
        }
    )
    out["date"] = pd.to_datetime(out["date"]).dt.date
    # Drop rows with no price info at all (delisted on that day etc.)
    price_cols = ["open", "high", "low", "close", "adj_close"]
    existing = [c for c in price_cols if c in out.columns]
    out = out.dropna(subset=existing, how="all")
    cols = ["symbol", "date", "open", "high", "low", "close", "adj_close", "volume"]
    for c in cols:
        if c not in out.columns:
            out[c] = None
    return out[cols].sort_values(["symbol", "date"]).reset_index(drop=True)
