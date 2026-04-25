"""Technical indicators computed per-ticker on daily prices.

Port targets (from testing_supervised_permutations.ipynb):
  - rsi(length=20) on adj_close
  - bb_low / bb_mid / bb_high from pandas_ta.bbands on log1p(adj_close), length=20
  - atr(length=14) via pandas_ta on (high, low, adj_close)
  - macd (pandas_ta default fast=12/slow=26, signal-normalized then standardized)
  - garman_klass_volatility (the notebook's formula, which reads as typo'd — see below)
  - close_over_open

Implementations here are from scratch (no pandas_ta) to avoid numpy 2.x /
pandas_ta packaging fights. They match pandas_ta behavior to within
floating-point tolerance.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def rsi(close: pd.Series, length: int = 20) -> pd.Series:
    """Wilder's RSI (EWM with alpha=1/length; same as pandas_ta default)."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    # pandas_ta uses Wilder's smoothing: alpha = 1/length (not adjust=False EMA with span=length)
    avg_gain = gain.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def bbands(close: pd.Series, length: int = 20, std: float = 2.0) -> pd.DataFrame:
    """Bollinger Bands on the given series. Returns columns bb_low/bb_mid/bb_high.

    Per notebook: applied to log1p(adj_close), length=20.
    """
    mid = close.rolling(length, min_periods=length).mean()
    sd = close.rolling(length, min_periods=length).std(ddof=0)
    return pd.DataFrame(
        {
            "bb_low": mid - std * sd,
            "bb_mid": mid,
            "bb_high": mid + std * sd,
        }
    )


def atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    """Wilder's Average True Range."""
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()


def macd(close: pd.Series, fast: int = 12, slow: int = 26) -> pd.Series:
    """MACD line = EMA(fast) - EMA(slow). Then standardized per-ticker to match
    the notebook's `compute_macd` which subtracts mean and divides by std."""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    line = ema_fast - ema_slow
    return (line - line.mean()) / line.std()


def garman_klass_volatility(
    high: pd.Series, low: pd.Series, open_: pd.Series, adj_close: pd.Series
) -> pd.Series:
    """Port of the notebook formula *exactly*:

        ((log(high - log(low)**2))/2
         - (2*log(2) - 1) * (log(adj_close) - log(open)**2))

    This reads like a typo of the canonical Garman-Klass estimator
    (0.5*log(h/l)^2 - (2*ln2-1)*log(c/o)^2), but the source research uses
    this expression so we preserve it. Fix via a separate commit if desired.
    """
    return (
        np.log(high - np.log(low) ** 2) / 2.0
        - (2 * np.log(2) - 1) * (np.log(adj_close) - np.log(open_) ** 2)
    )


def close_over_open(open_: pd.Series, adj_close: pd.Series) -> pd.Series:
    """Log-return-style daily open-to-close, per notebook convention."""
    return np.log(adj_close) - np.log(open_)


def compute_daily_indicators(prices: pd.DataFrame) -> pd.DataFrame:
    """Given a daily OHLCV frame sorted by (symbol, date), append all 8 technicals.

    Input columns: symbol, date, open, high, low, close, adj_close, volume
    Output: same rows with indicator columns appended. Per-ticker groupby,
    so leakage across symbols is impossible.
    """
    df = prices.sort_values(["symbol", "date"]).copy()

    def _per_ticker(g: pd.DataFrame) -> pd.DataFrame:
        g = g.copy()
        g["rsi"] = rsi(g["adj_close"], length=20)
        bb = bbands(np.log1p(g["adj_close"]), length=20)
        g["bb_low"] = bb["bb_low"].values
        g["bb_mid"] = bb["bb_mid"].values
        g["bb_high"] = bb["bb_high"].values
        g["atr"] = atr(g["high"], g["low"], g["adj_close"], length=14)
        g["macd"] = macd(g["adj_close"])
        g["garman_klass_volatility"] = garman_klass_volatility(
            g["high"], g["low"], g["open"], g["adj_close"]
        )
        g["close_over_open"] = close_over_open(g["open"], g["adj_close"])
        return g

    parts = [_per_ticker(g) for _, g in df.groupby("symbol", sort=False)]
    return pd.concat(parts, ignore_index=True) if parts else df
