"""Port of `rolling_train_predict_windowed` from
../Finance/utils/models_old.py.

Strictly walk-forward. For each rebalance date d:
  - train = rows in [d - window_months, d - 1 day] with all features + target
  - skip this d if |train| < min_train_rows
  - StandardScaler fit on train only
  - RandomForest fit on scaled train
  - predict for the cross-section at d
  - select top_k where y_pred > 0

Deliberately no look-ahead: train_end is d - 1 day, so the target_1m rows
available in training are targets that materialised strictly before d.
Scalers fit only on train. Only trained model is called on test.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

log = logging.getLogger(__name__)


def _select_with_sector_cap(
    side_pool: pd.DataFrame,
    *,
    ticker_col: str,
    k: int,
    sector_map: dict[str, str] | None,
    max_per_sector: int | None,
    ascending: bool,
) -> pd.DataFrame:
    """Greedy pick of up to `k` rows from `side_pool`, in y_pred order,
    respecting `max_per_sector` (if set and sector_map provided).

    Unknown-sector tickers are bucketed into a shared "Unknown" sector so
    they don't bypass the constraint accidentally."""
    if k <= 0 or side_pool.empty:
        return side_pool.iloc[0:0].copy()

    sorted_side = side_pool.sort_values("y_pred", ascending=ascending)
    if max_per_sector is None or sector_map is None:
        return sorted_side.head(k).copy()

    picked_idx: list = []
    counts: dict[str, int] = {}
    for idx, row in sorted_side.iterrows():
        sec = sector_map.get(row[ticker_col], "Unknown")
        if counts.get(sec, 0) >= max_per_sector:
            continue
        picked_idx.append(idx)
        counts[sec] = counts.get(sec, 0) + 1
        if len(picked_idx) >= k:
            break
    return sorted_side.loc[picked_idx].copy()


@dataclass
class Result:
    fixed_dates: dict = field(default_factory=dict)  # {"YYYY-MM-DD": [symbols]}
    diagnostics: pd.DataFrame = field(default_factory=pd.DataFrame)
    last_model: object | None = None
    last_scaler: StandardScaler | None = None
    all_predictions: pd.DataFrame = field(default_factory=pd.DataFrame)
    feature_importance: dict[str, float] = field(default_factory=dict)


def rolling_train_predict_windowed(
    df: pd.DataFrame,
    features: list[str],
    *,
    date_col: str = "date",
    ticker_col: str = "symbol",
    target_col: str = "target_1m",
    top_k: int = 15,
    top_k_short: int = 0,
    model_type: str = "randomforest",
    window_months: int = 12,
    min_train_rows: int = 150,
    tune_model: bool = False,
    seed: int = 0,
    sector_map: dict[str, str] | None = None,
    max_per_sector: int | None = None,
) -> Result:
    """Faithful port of models_old.rolling_train_predict_windowed + long-short
    extension + capture of every prediction (not just picks) for persistence.

    Long side: up to `top_k` tickers with highest y_pred > 0.
    Short side: up to `top_k_short` tickers with most-negative y_pred < 0.
    When top_k_short = 0 the behaviour is identical to the long-only port.

    `realized_mean` in the diagnostics DataFrame is the *signed* mean
    (direction * target_1m) so long-only and long-short runs both use the
    same metric as the permutation-test baseline — a long-short strategy
    that predicts nothing useful still averages zero, not target's mean.
    """

    fixed_dates: dict[str, list[str]] = {}
    diagnostics: list[dict] = []
    all_preds: list[pd.DataFrame] = []
    last_model = None
    last_scaler: StandardScaler | None = None

    # Ensure date is datetime for arithmetic.
    work = df.copy()
    work[date_col] = pd.to_datetime(work[date_col])
    dates = sorted(work[date_col].unique())

    for d in dates:
        d_ts = pd.to_datetime(d)
        train_start = (d_ts - pd.DateOffset(months=window_months)).normalize()
        train_end = (d_ts - pd.DateOffset(days=1)).normalize()

        mask = (work[date_col] >= train_start) & (work[date_col] <= train_end)
        train = work[mask].dropna(subset=features + [target_col])
        if train.shape[0] < min_train_rows:
            continue

        X_train = train[features]
        y_train = train[target_col]

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)

        if model_type == "ridge":
            model = Ridge(random_state=seed)
            param_grid = {"alpha": [0.1, 1.0, 10.0]} if tune_model else None
        else:
            model = RandomForestRegressor(random_state=seed, n_jobs=-1)
            param_grid = (
                {"n_estimators": [100, 200], "max_depth": [None, 6, 12]}
                if tune_model
                else None
            )

        if tune_model and param_grid:
            tscv = TimeSeriesSplit(n_splits=3)
            try:
                if sum(len(v) for v in param_grid.values()) > 12:
                    search = RandomizedSearchCV(
                        model,
                        param_distributions=param_grid,
                        n_iter=12,
                        cv=tscv,
                        n_jobs=-1,
                        scoring="neg_mean_squared_error",
                        random_state=seed,
                    )
                else:
                    search = GridSearchCV(
                        model,
                        param_grid,
                        cv=tscv,
                        n_jobs=-1,
                        scoring="neg_mean_squared_error",
                    )
                search.fit(X_train_s, y_train)
                model = search.best_estimator_
            except Exception as exc:
                log.warning(
                    "hyperparam search failed at %s: %s; using base estimator", d, exc
                )
                model.fit(X_train_s, y_train)
        else:
            model.fit(X_train_s, y_train)

        last_model = model
        last_scaler = scaler

        pool = work[work[date_col] == d_ts].dropna(subset=features).copy()
        if pool.empty:
            continue

        X_pool = scaler.transform(pool[features])
        y_pred = model.predict(X_pool)
        pool = pool.assign(y_pred=y_pred)
        pool = pool.sort_values("y_pred", ascending=False).reset_index(drop=True)
        pool["rank"] = range(1, len(pool) + 1)

        # Long side: up to top_k with positive prediction.
        long_pool = pool[pool["y_pred"] > 0]
        longs = _select_with_sector_cap(
            long_pool,
            ticker_col=ticker_col,
            k=top_k,
            sector_map=sector_map,
            max_per_sector=max_per_sector,
            ascending=False,  # highest y_pred first
        )

        # Short side: up to top_k_short with negative prediction (most negative first).
        if top_k_short > 0:
            short_pool = pool[pool["y_pred"] < 0]
            shorts = _select_with_sector_cap(
                short_pool,
                ticker_col=ticker_col,
                k=top_k_short,
                sector_map=sector_map,
                max_per_sector=max_per_sector,
                ascending=True,  # most negative y_pred first
            )
        else:
            shorts = pool.iloc[0:0].copy()

        # Combined selection, annotated with direction (+1 long, -1 short).
        longs["direction"] = 1
        shorts["direction"] = -1
        sel = pd.concat([longs, shorts], ignore_index=True)

        # Reflect direction on the full pool for persistence (0 = not picked).
        pool["direction"] = 0
        if not longs.empty:
            pool.loc[pool[ticker_col].isin(longs[ticker_col]), "direction"] = 1
        if not shorts.empty:
            pool.loc[pool[ticker_col].isin(shorts[ticker_col]), "direction"] = -1
        pool["picked"] = pool["direction"] != 0
        pool["rebalance_date"] = d_ts

        fixed_dates[d_ts.strftime("%Y-%m-%d")] = longs[ticker_col].tolist()

        keep_cols = [
            ticker_col,
            "rebalance_date",
            "y_pred",
            "rank",
            "picked",
            "direction",
            target_col,
        ]
        all_preds.append(pool[keep_cols].copy())

        # Signed realised return: long = +target, short = -target.
        signed_return = sel["direction"] * sel[target_col]
        diagnostics.append(
            {
                "date": d_ts,
                "n_pool": int(pool.shape[0]),
                "n_train": int(train.shape[0]),
                "n_long": int(len(longs)),
                "n_short": int(len(shorts)),
                "pred_mean": float((sel["direction"] * sel["y_pred"]).mean())
                if not sel.empty
                else float("nan"),
                "realized_mean": float(signed_return.mean())
                if not sel.empty
                else float("nan"),
            }
        )

    diag_df = (
        pd.DataFrame(diagnostics).set_index("date") if diagnostics else pd.DataFrame()
    )
    all_preds_df = pd.concat(all_preds, ignore_index=True) if all_preds else pd.DataFrame()

    fi: dict[str, float] = {}
    if last_model is not None and hasattr(last_model, "feature_importances_"):
        fi = dict(zip(features, map(float, last_model.feature_importances_)))
    elif last_model is not None and hasattr(last_model, "coef_"):
        fi = dict(zip(features, map(float, np.abs(last_model.coef_))))

    return Result(
        fixed_dates=fixed_dates,
        diagnostics=diag_df,
        last_model=last_model,
        last_scaler=last_scaler,
        all_predictions=all_preds_df,
        feature_importance=fi,
    )
