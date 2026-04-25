"""Tracker-core Django models. The SDK under ../../sdk/tracker writes directly
to these same tables via raw sqlite3; both sides must agree on schema."""

import uuid

from django.db import models


class Experiment(models.Model):
    experiment_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "experiment"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Run(models.Model):
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_RUNNING, "running"),
        (STATUS_COMPLETED, "completed"),
        (STATUS_FAILED, "failed"),
    ]

    run_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    experiment = models.ForeignKey(
        Experiment, on_delete=models.CASCADE, related_name="runs", db_index=True
    )
    name = models.CharField(max_length=128, blank=True, default="")
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_RUNNING, db_index=True
    )
    started_at = models.DateTimeField(db_index=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    git_sha = models.CharField(max_length=40, blank=True, default="")
    error = models.TextField(blank=True, default="")

    class Meta:
        db_table = "run"
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.experiment.name}:{str(self.run_id)[:8]} ({self.status})"


class RunParam(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="params")
    key = models.CharField(max_length=128, db_index=True)
    value_json = models.TextField()  # always JSON-encoded

    class Meta:
        db_table = "run_param"
        constraints = [
            models.UniqueConstraint(fields=["run", "key"], name="run_param_uniq")
        ]

    def __str__(self) -> str:
        return f"{self.key}={self.value_json}"


class RunMetric(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="metrics")
    key = models.CharField(max_length=128, db_index=True)
    value = models.FloatField()
    step = models.IntegerField(default=0)
    ts = models.DateTimeField()

    class Meta:
        db_table = "run_metric"
        indexes = [
            models.Index(fields=["run", "key"], name="run_metric_run_key_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.key}={self.value} @step={self.step}"


class RunTag(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="tags")
    tag = models.CharField(max_length=64, db_index=True)

    class Meta:
        db_table = "run_tag"
        constraints = [
            models.UniqueConstraint(fields=["run", "tag"], name="run_tag_uniq")
        ]

    def __str__(self) -> str:
        return self.tag


class RunArtifact(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="artifacts")
    name = models.CharField(max_length=128)
    path = models.CharField(max_length=512)  # absolute or repo-relative
    kind = models.CharField(max_length=32, blank=True, default="")
    size_bytes = models.BigIntegerField(default=0)

    class Meta:
        db_table = "run_artifact"
        constraints = [
            models.UniqueConstraint(fields=["run", "name"], name="run_artifact_uniq")
        ]

    def __str__(self) -> str:
        return f"{self.name} -> {self.path}"


class RunFeatureImportance(models.Model):
    run = models.ForeignKey(
        Run, on_delete=models.CASCADE, related_name="feature_importances"
    )
    feature = models.CharField(max_length=128, db_index=True)
    importance = models.FloatField()
    rank = models.IntegerField(default=0)

    class Meta:
        db_table = "run_feature_importance"
        constraints = [
            models.UniqueConstraint(
                fields=["run", "feature"], name="run_feat_imp_uniq"
            )
        ]

    def __str__(self) -> str:
        return f"{self.feature}={self.importance:.4f}"
