"""Orchestrator: load fct_features -> strategy -> tracker SDK + rf_* tables."""

from __future__ import annotations

import logging
from typing import Iterable

import pandas as pd
from django.db import transaction

import tracker
from features.build import FEATURE_COLS
from features.models import FctFeature
from ingest.universe import load_sectors
from models_rf.models import RfPick, RfPrediction
from models_rf.strategy import Result, rolling_train_predict_windowed

log = logging.getLogger(__name__)

DEFAULT_FEATURES = list(FEATURE_COLS)


def load_model_df() -> pd.DataFrame:
    fields = ["symbol", "date", *DEFAULT_FEATURES, "target_1m"]
    qs = FctFeature.objects.all().values(*fields)
    df = pd.DataFrame.from_records(qs)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


def run_rf(
    *,
    experiment: str = "rf_crosssectional_us",
    top_k: int = 15,
    top_k_short: int = 0,
    window_months: int = 12,
    min_train_rows: int = 150,
    tune_model: bool = False,
    model_type: str = "randomforest",
    seed: int = 0,
    features: list[str] | None = None,
    universe: str = "default",
    max_per_sector: int | None = None,
    tags: Iterable[str] | None = None,
    name: str = "",
) -> str:
    """Execute a walk-forward RF run, log via tracker SDK, persist predictions/picks."""
    features = list(features or DEFAULT_FEATURES)

    df = load_model_df()
    if df.empty:
        raise RuntimeError(
            "fct_features is empty — run `make build-features` first."
        )

    sector_map = load_sectors() if max_per_sector is not None else None

    params = {
        "model": model_type,
        "top_k": top_k,
        "top_k_short": top_k_short,
        "long_short": top_k_short > 0,
        "window_months": window_months,
        "min_train_rows": min_train_rows,
        "tune_model": tune_model,
        "seed": seed,
        "universe": universe,
        "features": features,
        "max_per_sector": max_per_sector,
        "n_symbols": int(df["symbol"].nunique()),
        "n_months": int(df["date"].nunique()),
    }

    tag_list = list(tags) if tags else ["rf_walk_forward"]
    if top_k_short > 0 and "long_short" not in tag_list:
        tag_list.append("long_short")
    if max_per_sector is not None and "sector_capped" not in tag_list:
        tag_list.append("sector_capped")

    with tracker.run(
        experiment=experiment,
        params=params,
        tags=tag_list,
        name=name,
    ) as r:
        result = rolling_train_predict_windowed(
            df=df,
            features=features,
            top_k=top_k,
            top_k_short=top_k_short,
            model_type=model_type,
            window_months=window_months,
            min_train_rows=min_train_rows,
            tune_model=tune_model,
            seed=seed,
            sector_map=sector_map,
            max_per_sector=max_per_sector,
        )

        _persist(r.run_id, result)
        _log_metrics(r, result)

        if result.feature_importance:
            r.log_importance(result.feature_importance)

        log.info(
            "run %s: %d rebalance dates, %d pick-months",
            r.run_id,
            0 if result.diagnostics.empty else len(result.diagnostics),
            len(result.fixed_dates),
        )

    return r.run_id


def _log_metrics(r, result: Result) -> None:
    diag = result.diagnostics
    if diag.empty:
        r.log_metric("n_rebalance_dates", 0)
        return
    r.log_metric("n_rebalance_dates", int(len(diag)))
    r.log_metric("pred_mean_avg", float(diag["pred_mean"].mean(skipna=True)))
    r.log_metric("realized_mean_avg", float(diag["realized_mean"].mean(skipna=True)))
    r.log_metric("n_train_avg", float(diag["n_train"].mean()))
    if "n_long" in diag.columns:
        r.log_metric("n_long_avg", float(diag["n_long"].mean()))
        r.log_metric("n_short_avg", float(diag["n_short"].mean()))
    last_real = diag["realized_mean"].dropna()
    if not last_real.empty:
        r.log_metric("realized_mean_last", float(last_real.iloc[-1]))
    gap = float(
        (diag["pred_mean"] - diag["realized_mean"]).abs().mean(skipna=True)
    )
    r.log_metric("pred_realized_abs_gap_avg", gap)


def _persist(run_id: str, result: Result) -> None:
    preds = result.all_predictions
    if preds.empty:
        return

    pred_rows = []
    for row in preds.itertuples(index=False):
        pred_rows.append(
            RfPrediction(
                run_id=run_id,
                rebalance_date=_to_date(row.rebalance_date),
                symbol=row.symbol,
                y_pred=float(row.y_pred),
                rank=int(row.rank),
            )
        )

    picks_df = preds[preds["picked"]].copy()
    # Rank separately within (rebalance_date, direction): long side sorted
    # desc by y_pred, short side sorted asc (most negative first).
    longs = (
        picks_df[picks_df["direction"] == 1]
        .sort_values(["rebalance_date", "y_pred"], ascending=[True, False])
    )
    shorts = (
        picks_df[picks_df["direction"] == -1]
        .sort_values(["rebalance_date", "y_pred"], ascending=[True, True])
    )
    longs = longs.assign(
        picked_rank=longs.groupby("rebalance_date").cumcount() + 1
    )
    shorts = shorts.assign(
        picked_rank=shorts.groupby("rebalance_date").cumcount() + 1
    )
    picks_df = pd.concat([longs, shorts], ignore_index=True)

    pick_rows = []
    for row in picks_df.itertuples(index=False):
        target = getattr(row, "target_1m", None)
        target_f = None if (target is None or target != target) else float(target)
        pick_rows.append(
            RfPick(
                run_id=run_id,
                rebalance_date=_to_date(row.rebalance_date),
                symbol=row.symbol,
                y_pred=float(row.y_pred),
                picked_rank=int(row.picked_rank),
                direction=int(row.direction),
                target_1m=target_f,
            )
        )

    with transaction.atomic():
        RfPrediction.objects.bulk_create(pred_rows, batch_size=5000)
        RfPick.objects.bulk_create(pick_rows, batch_size=5000)


def _to_date(v):
    if hasattr(v, "date"):
        return v.date()
    return v
