"""Permutation test orchestrator.

For each of N permutations:
  - shuffle target_1m within date
  - rerun rolling_train_predict_windowed (tune_model=False for speed)
  - collect realized_mean_avg (the same metric the baseline logged)
Then compute p-values, median, effect size; persist perm_summary row;
stash the per-permutation array as a parquet artifact; attach metrics to
the baseline run via the tracker SDK.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from django.conf import settings
from django.db import transaction

import tracker
from ingest.universe import load_sectors
from models_rf.runner import DEFAULT_FEATURES, load_model_df
from models_rf.strategy import rolling_train_predict_windowed
from permutation.models import PermSummary
from permutation.shuffle import shuffle_target_within_date
from tracker_core.models import Run, RunMetric, RunParam

log = logging.getLogger(__name__)

BASELINE_METRIC_KEY = "realized_mean_avg"


def _baseline_params(run_id: str) -> dict[str, Any]:
    """Load the baseline run's params from run_param JSON cells."""
    out: dict[str, Any] = {}
    for p in RunParam.objects.filter(run_id=run_id):
        try:
            out[p.key] = json.loads(p.value_json)
        except Exception:
            out[p.key] = p.value_json
    return out


def _baseline_metric(run_id: str) -> float | None:
    """Most recent value of realized_mean_avg logged against the baseline run."""
    m = (
        RunMetric.objects.filter(run_id=run_id, key=BASELINE_METRIC_KEY)
        .order_by("-ts")
        .first()
    )
    return float(m.value) if m else None


def _run_one_permutation(
    df: pd.DataFrame,
    features: list[str],
    *,
    seed: int,
    top_k: int,
    top_k_short: int,
    window_months: int,
    min_train_rows: int,
    model_type: str,
    sector_map: dict[str, str] | None,
    max_per_sector: int | None,
) -> float:
    perm_df = shuffle_target_within_date(df, seed=seed)
    result = rolling_train_predict_windowed(
        df=perm_df,
        features=features,
        top_k=top_k,
        top_k_short=top_k_short,
        model_type=model_type,
        window_months=window_months,
        min_train_rows=min_train_rows,
        tune_model=False,
        seed=0,  # model seed independent of shuffle seed
        sector_map=sector_map,
        max_per_sector=max_per_sector,
    )
    if result.diagnostics.empty:
        return float("nan")
    return float(result.diagnostics["realized_mean"].mean(skipna=True))


def run_permutation_test(
    run_id: str,
    *,
    n_permutations: int = 100,
    seed_base: int = 42,
) -> dict[str, Any]:
    run_id = run_id.replace("-", "")
    if not Run.objects.filter(run_id=run_id).exists():
        raise RuntimeError(f"baseline run not found: {run_id}")

    baseline = _baseline_metric(run_id)
    if baseline is None:
        raise RuntimeError(
            f"baseline run {run_id} has no `{BASELINE_METRIC_KEY}` metric yet. "
            "Run rf_run first."
        )

    params = _baseline_params(run_id)
    features = params.get("features") or list(DEFAULT_FEATURES)
    top_k = int(params.get("top_k", 15))
    top_k_short = int(params.get("top_k_short", 0))
    window_months = int(params.get("window_months", 12))
    min_train_rows = int(params.get("min_train_rows", 150))
    model_type = params.get("model", "randomforest")
    max_per_sector = params.get("max_per_sector")
    sector_map = load_sectors() if max_per_sector is not None else None

    df = load_model_df()
    if df.empty:
        raise RuntimeError("fct_features is empty; run build_features first.")

    perm_metrics: list[float] = []
    for i in range(n_permutations):
        seed = seed_base + i
        m = _run_one_permutation(
            df,
            features,
            seed=seed,
            top_k=top_k,
            top_k_short=top_k_short,
            window_months=window_months,
            min_train_rows=min_train_rows,
            model_type=model_type,
            sector_map=sector_map,
            max_per_sector=max_per_sector,
        )
        perm_metrics.append(m)
        log.info("perm %d/%d seed=%d metric=%s", i + 1, n_permutations, seed, m)

    arr = np.array(perm_metrics, dtype=float)
    valid = arr[~np.isnan(arr)]

    if valid.size == 0:
        summary = {
            "baseline_metric": baseline,
            "median_perm": None,
            "p_gte": None,
            "p_lte": None,
            "p_two_sided": None,
            "effect_size": None,
            "n_valid": 0,
        }
    else:
        p_gte = float((valid >= baseline).mean())
        p_lte = float((valid <= baseline).mean())
        p_two = min(2 * min(p_gte, p_lte), 1.0)
        median_perm = float(np.median(valid))
        summary = {
            "baseline_metric": float(baseline),
            "median_perm": median_perm,
            "p_gte": p_gte,
            "p_lte": p_lte,
            "p_two_sided": float(p_two),
            "effect_size": float(baseline - median_perm),
            "n_valid": int(valid.size),
        }

    # Persist parquet artifact of the full perm array.
    artifact_dir: Path = settings.ARTIFACT_DIR / run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = artifact_dir / "perm_metrics.parquet"
    pd.DataFrame(
        {
            "perm_index": np.arange(len(arr)),
            "seed": seed_base + np.arange(len(arr)),
            "realized_mean": arr,
        }
    ).to_parquet(parquet_path, index=False)

    with transaction.atomic():
        PermSummary.objects.filter(run_id=run_id).delete()
        PermSummary.objects.create(
            run_id=run_id,
            n_permutations=n_permutations,
            n_valid=summary["n_valid"],
            seed_base=seed_base,
            baseline_metric=summary["baseline_metric"],
            median_perm=summary.get("median_perm"),
            p_gte=summary.get("p_gte"),
            p_lte=summary.get("p_lte"),
            p_two_sided=summary.get("p_two_sided"),
            effect_size=summary.get("effect_size"),
            artifact_path=str(parquet_path),
        )

    with tracker.attach(run_id) as r:
        r.tag("perm_tested")
        r.log_artifact(
            "perm_metrics", str(parquet_path), kind="parquet"
        )
        for key, val in summary.items():
            if isinstance(val, (int, float)) and val is not None:
                r.log_metric(f"perm_{key}", float(val))

    summary["run_id"] = run_id
    summary["n_permutations"] = n_permutations
    summary["artifact_path"] = str(parquet_path)
    return summary
