"""Within-date cross-sectional shuffle of the supervised target.

The statistically correct null for a cross-sectional ranking strategy is a
permutation that *preserves the marginal distribution of target_1m on every
date* but destroys the association between (features at ticker i on date t)
and (target at ticker i on date t). A full/global shuffle is wrong because
it destroys the time-series marginal too.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def shuffle_target_within_date(
    df: pd.DataFrame,
    seed: int,
    *,
    date_col: str = "date",
    target_col: str = "target_1m",
) -> pd.DataFrame:
    """Return a copy of `df` with `target_col` shuffled within each `date_col` group."""
    rng = np.random.RandomState(seed)
    out = df.copy()

    def _shuffle(group_vals: np.ndarray) -> np.ndarray:
        idx = np.arange(len(group_vals))
        rng.shuffle(idx)
        return group_vals[idx]

    # Build new target column in place, preserving the DataFrame's row order.
    grouped = out.groupby(date_col, sort=False)
    pieces = []
    for _, g in grouped:
        vals = g[target_col].values.copy()
        pieces.append(pd.Series(_shuffle(vals), index=g.index))
    out[target_col] = pd.concat(pieces).loc[out.index]
    return out
