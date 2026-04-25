from django.db import models


class RfPortfolioWeight(models.Model):
    """Optimised weights per rebalance date (one row per symbol held)."""

    run_id = models.UUIDField(db_index=True)
    rebalance_date = models.DateField(db_index=True)
    symbol = models.CharField(max_length=16)
    weight = models.FloatField()

    class Meta:
        db_table = "rf_portfolio_weights"
        constraints = [
            models.UniqueConstraint(
                fields=["run_id", "rebalance_date", "symbol"], name="rf_port_wt_uniq"
            )
        ]

    def __str__(self) -> str:
        return f"{self.rebalance_date} {self.symbol} w={self.weight:.4f}"


class RfPortfolioReturn(models.Model):
    """Daily strategy return for a backtested run."""

    run_id = models.UUIDField(db_index=True)
    date = models.DateField(db_index=True)
    strategy_return = models.FloatField()

    class Meta:
        db_table = "rf_portfolio_returns"
        constraints = [
            models.UniqueConstraint(
                fields=["run_id", "date"], name="rf_port_ret_uniq"
            )
        ]

    def __str__(self) -> str:
        return f"{self.date} {self.strategy_return:+.5f}"
