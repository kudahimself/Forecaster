from pathlib import Path

import pandas as pd
from django.conf import settings
from django.db.models import Count, Max, Min
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.serializers import (
    ExperimentSerializer,
    RunDetailSerializer,
    RunListSerializer,
)
from ingest.models import RawFactor, RawPrice, Symbol
from permutation.models import PermSummary
from portfolio.models import RfPortfolioReturn
from quality.models import DqCheck, DqRun
from scheduler.models import IngestRun
from tracker_core.models import Experiment, Run, RunFeatureImportance


@api_view(["GET"])
def health(_request):
    return Response(
        {
            "status": "ok",
            "warehouse": str(settings.WAREHOUSE_PATH),
            "warehouse_exists": settings.WAREHOUSE_PATH.exists(),
        }
    )


class RunListView(generics.ListAPIView):
    """GET /api/runs/ — paginated list of runs with flattened params/metrics/tags."""

    serializer_class = RunListSerializer

    def get_queryset(self):
        qs = (
            Run.objects.select_related("experiment")
            .prefetch_related("params", "metrics", "tags")
            .order_by("-started_at")
        )
        experiment = self.request.query_params.get("experiment")
        if experiment:
            qs = qs.filter(experiment__name=experiment)
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs


class RunDetailView(generics.RetrieveAPIView):
    """GET /api/runs/<run_id>/ — full detail including importances + artifacts."""

    serializer_class = RunDetailSerializer
    lookup_field = "run_id"

    def get_queryset(self):
        return Run.objects.select_related("experiment").prefetch_related(
            "params", "metrics", "tags", "feature_importances", "artifacts"
        )

    def get_object(self):
        # Accept run_id with or without dashes.
        raw = self.kwargs[self.lookup_field]
        normalized = raw.replace("-", "")
        qs = self.get_queryset().filter(run_id=normalized)
        obj = qs.first()
        if obj is None:
            from rest_framework.exceptions import NotFound

            raise NotFound(f"run_id {raw} not found")
        return obj


class ExperimentListView(generics.ListAPIView):
    """GET /api/experiments/"""

    serializer_class = ExperimentSerializer
    pagination_class = None  # small table, no paging needed

    def get_queryset(self):
        return Experiment.objects.all().order_by("name")


def _norm(run_id: str) -> str:
    return run_id.replace("-", "")


@api_view(["GET"])
def run_portfolio_returns(_request, run_id: str):
    """GET /api/runs/<run_id>/portfolio-returns/ — daily strategy returns + cumulative."""
    rid = _norm(run_id)
    rows = list(
        RfPortfolioReturn.objects.filter(run_id=rid)
        .order_by("date")
        .values("date", "strategy_return")
    )
    if not rows:
        return Response({"run_id": rid, "points": []})

    df = pd.DataFrame(rows)
    df["cum_return"] = (1.0 + df["strategy_return"]).cumprod() - 1.0
    return Response(
        {
            "run_id": rid,
            "points": [
                {
                    "date": r["date"].isoformat(),
                    "strategy_return": float(r["strategy_return"]),
                    "cum_return": float(c),
                }
                for r, c in zip(rows, df["cum_return"].tolist())
            ],
        }
    )


@api_view(["GET"])
def feature_importance_aggregation(_request):
    """GET /api/feature-importance/ — aggregate feature importance across runs.

    For each feature: n_runs it appears in, mean/median/std importance, mean rank.
    Sorted by mean_importance descending. Answers the "which features
    consistently help?" question for the overfitting dashboard."""
    qs = RunFeatureImportance.objects.values("feature", "importance", "rank")
    df = pd.DataFrame.from_records(qs)
    if df.empty:
        return Response({"features": []})

    g = df.groupby("feature")
    agg = (
        pd.DataFrame(
            {
                "n_runs": g.size(),
                "mean_importance": g["importance"].mean(),
                "median_importance": g["importance"].median(),
                "std_importance": g["importance"].std(ddof=0),
                "mean_rank": g["rank"].mean(),
                "best_rank": g["rank"].min(),
                "worst_rank": g["rank"].max(),
            }
        )
        .reset_index()
        .sort_values("mean_importance", ascending=False)
    )
    # Clean NaNs before serialising.
    agg = agg.where(pd.notna(agg), None)
    features = []
    for row in agg.itertuples(index=False):
        features.append(
            {
                "feature": row.feature,
                "n_runs": int(row.n_runs),
                "mean_importance": None if row.mean_importance is None else float(row.mean_importance),
                "median_importance": None if row.median_importance is None else float(row.median_importance),
                "std_importance": None if row.std_importance is None else float(row.std_importance),
                "mean_rank": None if row.mean_rank is None else float(row.mean_rank),
                "best_rank": None if row.best_rank is None else int(row.best_rank),
                "worst_rank": None if row.worst_rank is None else int(row.worst_rank),
            }
        )
    return Response({"features": features, "n_total_runs": int(df.groupby("feature").size().max())})


@api_view(["GET"])
def dq_runs_list(_request):
    """GET /api/dq/runs/ — recent DQ runs with pass/warn/fail summary."""
    rows = []
    for r in DqRun.objects.all()[:50]:
        rows.append(
            {
                "run_id": str(r.run_id),
                "started_at": r.started_at.isoformat(),
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                "summary": r.summary,
            }
        )
    return Response(rows)


@api_view(["GET"])
def dq_run_detail(_request, run_id: str):
    """GET /api/dq/runs/<id>/ — checks for one DQ run."""
    rid = _norm(run_id)
    run = DqRun.objects.filter(run_id=rid).first()
    if not run:
        return Response(
            {"detail": f"dq run not found: {run_id}"},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(
        {
            "run_id": str(run.run_id),
            "started_at": run.started_at.isoformat(),
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "summary": run.summary,
            "checks": [
                {
                    "check_name": c.check_name,
                    "status": c.status,
                    "rows_checked": c.rows_checked,
                    "rows_failed": c.rows_failed,
                    "details": c.details,
                }
                for c in run.checks.all().order_by("check_name")
            ],
        }
    )


@api_view(["GET"])
def scheduler_runs(_request):
    """GET /api/scheduler/runs/ — history of scheduled ingest executions,
    grouped in the frontend by job_name."""
    rows = []
    for r in IngestRun.objects.all()[:200]:
        rows.append(
            {
                "run_id": str(r.run_id),
                "job_name": r.job_name,
                "started_at": r.started_at.isoformat(),
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                "duration_seconds": r.duration_seconds,
                "status": r.status,
                "rows_ingested": r.rows_ingested,
                "summary": r.summary,
                "error": r.error,
            }
        )
    return Response(rows)


@api_view(["GET"])
def ingest_status(_request):
    """GET /api/ingest/status/ — warehouse freshness and per-symbol coverage."""
    per_symbol = list(
        RawPrice.objects.values("symbol")
        .annotate(
            first=Min("date"),
            last=Max("date"),
            n=Count("id"),
            last_ingest=Max("ingested_at"),
        )
        .order_by("symbol")
    )

    factors = RawFactor.objects.aggregate(
        first=Min("date"),
        last=Max("date"),
        n=Count("id"),
        last_ingest=Max("ingested_at"),
    )

    total_prices = RawPrice.objects.count()
    n_symbols_known = Symbol.objects.count()

    return Response(
        {
            "symbols": {
                "known_in_dim": n_symbols_known,
                "ingested": len(per_symbol),
                "per_symbol": [
                    {
                        "symbol": s["symbol"],
                        "first_date": s["first"].isoformat() if s["first"] else None,
                        "last_date": s["last"].isoformat() if s["last"] else None,
                        "n_rows": s["n"],
                        "last_ingest": s["last_ingest"].isoformat() if s["last_ingest"] else None,
                    }
                    for s in per_symbol
                ],
            },
            "prices_total_rows": total_prices,
            "factors": {
                "n_rows": factors["n"] or 0,
                "first_date": factors["first"].isoformat() if factors["first"] else None,
                "last_date": factors["last"].isoformat() if factors["last"] else None,
                "last_ingest": factors["last_ingest"].isoformat() if factors["last_ingest"] else None,
            },
        }
    )


@api_view(["GET"])
def run_perm_metrics(_request, run_id: str):
    """GET /api/runs/<run_id>/perm-metrics/ — permutation distribution read from parquet."""
    rid = _norm(run_id)
    summary = PermSummary.objects.filter(run_id=rid).first()
    if not summary:
        return Response(
            {"detail": "no permutation test for this run"},
            status=status.HTTP_404_NOT_FOUND,
        )

    metrics: list[float] = []
    path = Path(summary.artifact_path) if summary.artifact_path else None
    if path and path.exists():
        df = pd.read_parquet(path)
        if "realized_mean" in df.columns:
            metrics = [
                float(x) for x in df["realized_mean"].dropna().tolist()
            ]

    return Response(
        {
            "run_id": rid,
            "baseline_metric": summary.baseline_metric,
            "median_perm": summary.median_perm,
            "p_gte": summary.p_gte,
            "p_lte": summary.p_lte,
            "p_two_sided": summary.p_two_sided,
            "effect_size": summary.effect_size,
            "n_valid": summary.n_valid,
            "n_permutations": summary.n_permutations,
            "metrics": metrics,
        }
    )
