"""DRF serializers that flatten the normalised tracker_core tables into
dashboard-friendly JSON shapes. Metrics/params are exposed as dicts keyed
by metric/param name — keeps the frontend code simple."""

from __future__ import annotations

import json
from typing import Any

from rest_framework import serializers

from tracker_core.models import (
    Experiment,
    Run,
    RunFeatureImportance,
    RunMetric,
    RunParam,
)


def _params_to_dict(params_qs) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for p in params_qs:
        try:
            out[p.key] = json.loads(p.value_json)
        except (TypeError, ValueError):
            out[p.key] = p.value_json
    return out


def _metrics_latest(metrics_qs) -> dict[str, float]:
    """Take the most recent value per metric key (later ts wins)."""
    out: dict[str, float] = {}
    for m in sorted(metrics_qs, key=lambda x: x.ts):
        out[m.key] = m.value
    return out


class RunListSerializer(serializers.ModelSerializer):
    experiment = serializers.CharField(source="experiment.name", read_only=True)
    params = serializers.SerializerMethodField()
    metrics = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Run
        fields = [
            "run_id",
            "experiment",
            "name",
            "status",
            "started_at",
            "finished_at",
            "git_sha",
            "error",
            "params",
            "metrics",
            "tags",
        ]

    def get_params(self, obj: Run) -> dict[str, Any]:
        return _params_to_dict(obj.params.all())

    def get_metrics(self, obj: Run) -> dict[str, float]:
        return _metrics_latest(obj.metrics.all())

    def get_tags(self, obj: Run) -> list[str]:
        return [t.tag for t in obj.tags.all()]


class RunDetailSerializer(RunListSerializer):
    feature_importance = serializers.SerializerMethodField()
    artifacts = serializers.SerializerMethodField()

    class Meta(RunListSerializer.Meta):
        fields = RunListSerializer.Meta.fields + [
            "feature_importance",
            "artifacts",
        ]

    def get_feature_importance(self, obj: Run) -> list[dict]:
        return [
            {"feature": fi.feature, "importance": fi.importance, "rank": fi.rank}
            for fi in obj.feature_importances.all().order_by("rank")
        ]

    def get_artifacts(self, obj: Run) -> list[dict]:
        return [
            {
                "name": a.name,
                "path": a.path,
                "kind": a.kind,
                "size_bytes": a.size_bytes,
            }
            for a in obj.artifacts.all()
        ]


class ExperimentSerializer(serializers.ModelSerializer):
    n_runs = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = ["experiment_id", "name", "description", "created_at", "n_runs"]

    def get_n_runs(self, obj: Experiment) -> int:
        return obj.runs.count()
