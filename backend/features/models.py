from django.db import models


class FctFeature(models.Model):
    """Month-end feature row per (symbol, date). Everything needed to train a
    cross-sectional return model. Beta columns are populated by the betas job
    (M3b) and remain null on M3a rows."""

    symbol = models.CharField(max_length=16, db_index=True)
    date = models.DateField(db_index=True)  # month-end observation date

    # --- 8 daily-technical features (last trading day of month) ---
    rsi = models.FloatField(null=True)
    garman_klass_volatility = models.FloatField(null=True)
    close_over_open = models.FloatField(null=True)
    atr = models.FloatField(null=True)
    macd = models.FloatField(null=True)
    bb_low = models.FloatField(null=True)
    bb_mid = models.FloatField(null=True)
    bb_high = models.FloatField(null=True)

    # --- 6 multi-horizon monthly returns (winsorized) ---
    return_1m = models.FloatField(null=True)
    return_2m = models.FloatField(null=True)
    return_3m = models.FloatField(null=True)
    return_6m = models.FloatField(null=True)
    return_9m = models.FloatField(null=True)
    return_12m = models.FloatField(null=True)

    # --- 5 factor betas (filled by M3b) ---
    beta_mkt_rf = models.FloatField(null=True)
    beta_smb = models.FloatField(null=True)
    beta_hml = models.FloatField(null=True)
    beta_rmw = models.FloatField(null=True)
    beta_cma = models.FloatField(null=True)

    # --- label ---
    target_1m = models.FloatField(null=True)  # return_1m shifted -1 per ticker

    built_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "fct_features"
        constraints = [
            models.UniqueConstraint(fields=["symbol", "date"], name="fct_features_uniq")
        ]
        indexes = [
            models.Index(fields=["date"], name="fct_features_date_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.symbol} {self.date}"
