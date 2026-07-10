from django.db import models


class PermSummary(models.Model):
    """Aggregated permutation-test result for one baseline run.

    Stored per-baseline: rerunning the permutation test replaces the summary
    row. The per-permutation `realized_mean` array is kept separately as a
    parquet artifact under data/artifacts/<run_id>/perm_metrics.parquet.
    """

    run_id = models.UUIDField(primary_key=True)  # references the baseline Run
    n_permutations = models.IntegerField()
    n_valid = models.IntegerField(default=0)
    seed_base = models.IntegerField(default=42)
    baseline_metric = models.FloatField()
    median_perm = models.FloatField(null=True, blank=True)
    p_gte = models.FloatField(null=True, blank=True)
    p_lte = models.FloatField(null=True, blank=True)
    p_two_sided = models.FloatField(null=True, blank=True)
    effect_size = models.FloatField(null=True, blank=True)
    artifact_path = models.CharField(max_length=512, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "perm_summary"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return (
            f"perm run_id={self.run_id} baseline={self.baseline_metric:.5f} "
            f"p2={self.p_two_sided} n={self.n_valid}/{self.n_permutations}"
        )
