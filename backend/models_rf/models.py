from django.db import models


class RfPrediction(models.Model):
    """Predicted y_pred for every (run, rebalance_date, symbol). Not FK to
    tracker_core.Run — we want a loose reference so dropping a run doesn't
    cascade-delete model predictions (or vice versa)."""

    run_id = models.UUIDField(db_index=True)
    rebalance_date = models.DateField(db_index=True)
    symbol = models.CharField(max_length=16, db_index=True)
    y_pred = models.FloatField()
    rank = models.IntegerField()  # 1-based, descending y_pred within (run, date)

    class Meta:
        db_table = "rf_predictions"
        constraints = [
            models.UniqueConstraint(
                fields=["run_id", "rebalance_date", "symbol"], name="rf_pred_uniq"
            )
        ]

    def __str__(self) -> str:
        return f"{self.rebalance_date} {self.symbol} yp={self.y_pred:.4f} r={self.rank}"


class RfPick(models.Model):
    """Picks per rebalance_date. In long-only mode all rows have direction=+1
    (top_k by y_pred > 0). In long-short mode there are additionally direction=-1
    rows (top_k_short by most-negative y_pred)."""

    LONG = 1
    SHORT = -1
    DIRECTION_CHOICES = [(LONG, "long"), (SHORT, "short")]

    run_id = models.UUIDField(db_index=True)
    rebalance_date = models.DateField(db_index=True)
    symbol = models.CharField(max_length=16)
    y_pred = models.FloatField()
    picked_rank = models.IntegerField()  # 1..k within (run, date, direction)
    direction = models.SmallIntegerField(default=LONG, choices=DIRECTION_CHOICES)
    target_1m = models.FloatField(null=True, blank=True)  # realized OOS target

    class Meta:
        db_table = "rf_picks"
        constraints = [
            models.UniqueConstraint(
                fields=["run_id", "rebalance_date", "symbol"], name="rf_pick_uniq"
            )
        ]

    def __str__(self) -> str:
        side = "L" if self.direction == self.LONG else "S"
        return f"{self.rebalance_date} {self.symbol} {side}{self.picked_rank}"
