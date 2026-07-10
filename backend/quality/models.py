import uuid

from django.db import models


class DqRun(models.Model):
    """One invocation of `python manage.py validate`."""

    run_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    summary = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "dq_runs"
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"DqRun {self.run_id} {self.started_at:%Y-%m-%d %H:%M}"


class DqCheck(models.Model):
    """Result of a single named check within a DqRun."""

    STATUS_PASS = "pass"
    STATUS_WARN = "warn"
    STATUS_FAIL = "fail"
    STATUS_CHOICES = [
        (STATUS_PASS, "pass"),
        (STATUS_WARN, "warn"),
        (STATUS_FAIL, "fail"),
    ]

    run = models.ForeignKey(
        DqRun, on_delete=models.CASCADE, related_name="checks", db_index=True
    )
    check_name = models.CharField(max_length=128, db_index=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, db_index=True)
    rows_checked = models.BigIntegerField(default=0)
    rows_failed = models.BigIntegerField(default=0)
    details = models.JSONField(default=dict, blank=True)
    ts = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dq_checks"
        ordering = ["-ts"]

    def __str__(self) -> str:
        return f"{self.check_name}: {self.status} ({self.rows_failed}/{self.rows_checked})"
