import uuid

from django.db import models


class IngestRun(models.Model):
    """One execution of a scheduled ingestion job.

    Acts as the audit trail for 'data last arrived at HH:MM on date D' and
    is what the /schedules dashboard page reads. Every wrapped job writes
    exactly one row here: status flips running → completed / failed on exit.
    """

    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_RUNNING, "running"),
        (STATUS_COMPLETED, "completed"),
        (STATUS_FAILED, "failed"),
    ]

    run_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_name = models.CharField(max_length=64, db_index=True)
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_RUNNING, db_index=True
    )
    rows_ingested = models.IntegerField(default=0)
    summary = models.JSONField(default=dict, blank=True)
    error = models.TextField(blank=True, default="")

    class Meta:
        db_table = "ingest_runs"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["job_name", "-started_at"], name="ingest_runs_job_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.job_name} @ {self.started_at:%Y-%m-%d %H:%M} [{self.status}]"

    @property
    def duration_seconds(self) -> float | None:
        if not self.finished_at:
            return None
        return (self.finished_at - self.started_at).total_seconds()
