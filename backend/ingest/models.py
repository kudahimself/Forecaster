from django.db import models


class Symbol(models.Model):
    """Universe dimension. One row per ticker we've ever ingested."""

    symbol = models.CharField(max_length=16, primary_key=True)
    name = models.CharField(max_length=255, blank=True, default="")
    sector = models.CharField(max_length=64, blank=True, default="")
    first_seen = models.DateField(null=True, blank=True)
    last_seen = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "dim_symbols"
        ordering = ["symbol"]

    def __str__(self) -> str:
        return self.symbol


class RawPrice(models.Model):
    """Append-only raw OHLCV from yfinance. (symbol, date, source) is unique."""

    symbol = models.CharField(max_length=16, db_index=True)
    date = models.DateField(db_index=True)
    open = models.FloatField(null=True)
    high = models.FloatField(null=True)
    low = models.FloatField(null=True)
    close = models.FloatField(null=True)
    adj_close = models.FloatField(null=True)
    volume = models.BigIntegerField(null=True)
    ingested_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=32, default="yfinance")

    class Meta:
        db_table = "raw_prices"
        constraints = [
            models.UniqueConstraint(
                fields=["symbol", "date", "source"], name="raw_prices_uniq"
            )
        ]
        indexes = [
            models.Index(fields=["date"], name="raw_prices_date_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.symbol} {self.date}"


class RawFactor(models.Model):
    """Fama-French 5-factor + momentum daily series. (date, source) unique."""

    date = models.DateField(db_index=True)
    mkt_rf = models.FloatField(null=True)
    smb = models.FloatField(null=True)
    hml = models.FloatField(null=True)
    rmw = models.FloatField(null=True)
    cma = models.FloatField(null=True)
    mom = models.FloatField(null=True)
    rf = models.FloatField(null=True)
    ingested_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=64, default="ken_french_5f")

    class Meta:
        db_table = "raw_factors"
        constraints = [
            models.UniqueConstraint(fields=["date", "source"], name="raw_factors_uniq")
        ]

    def __str__(self) -> str:
        return f"factors {self.date}"
