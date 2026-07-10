from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from ingest import ff, yf
from ingest.models import RawFactor, RawPrice, Symbol
from ingest.universe import load_universe

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Ingest yfinance OHLCV and Fama-French factors into the raw tables."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--universe",
            default="default",
            help="Universe YAML name under backend/ingest/config/ (default: top100 liquid US).",
        )
        parser.add_argument(
            "--start",
            default="2018-01-01",
            help="Start date (YYYY-MM-DD). Default 2018-01-01.",
        )
        parser.add_argument(
            "--end",
            default=None,
            help="End date (YYYY-MM-DD). Default: today.",
        )
        parser.add_argument("--prices-only", action="store_true")
        parser.add_argument("--factors-only", action="store_true")
        parser.add_argument(
            "--cache",
            action="store_true",
            help="Also write a raw CSV to data/raw_cache/ for audit.",
        )

    def handle(self, *args, **opts) -> None:
        start: str = opts["start"]
        end: str = opts["end"] or (date.today() + timedelta(days=1)).isoformat()
        prices_only: bool = opts["prices_only"]
        factors_only: bool = opts["factors_only"]
        cache: bool = opts["cache"]

        if not factors_only:
            self._ingest_prices(opts["universe"], start, end, cache=cache)
        if not prices_only:
            self._ingest_factors(start, end, cache=cache)

    def _ingest_prices(self, universe_name: str, start: str, end: str, *, cache: bool) -> None:
        u = load_universe(universe_name)
        tickers: list[str] = u["tickers"]
        self.stdout.write(
            f"Fetching prices for universe '{u['name']}' ({len(tickers)} tickers) "
            f"{start} -> {end}"
        )

        df = yf.fetch_prices(tickers, start=start, end=end)
        self.stdout.write(f"  yfinance returned {len(df):,} rows")

        if df.empty:
            self.stdout.write(self.style.WARNING("  no rows returned; skipping insert"))
            return

        if cache:
            self._cache_csv(df, f"yfinance_{datetime.utcnow():%Y%m%dT%H%M%S}.csv")

        rows = [
            RawPrice(
                symbol=r.symbol,
                date=r.date,
                open=_nn(r.open),
                high=_nn(r.high),
                low=_nn(r.low),
                close=_nn(r.close),
                adj_close=_nn(r.adj_close),
                volume=int(r.volume) if r.volume and r.volume == r.volume else None,
                source="yfinance",
            )
            for r in df.itertuples(index=False)
        ]

        with transaction.atomic():
            inserted = RawPrice.objects.bulk_create(
                rows, batch_size=5000, ignore_conflicts=True
            )
            self._upsert_symbols(df)
        self.stdout.write(
            self.style.SUCCESS(
                f"  inserted {len(inserted):,} price rows (conflicts ignored)"
            )
        )

    def _ingest_factors(self, start: str, end: str, *, cache: bool) -> None:
        self.stdout.write(f"Fetching Fama-French factors {start} -> {end}")
        df = ff.fetch_factors(start=start, end=end)
        self.stdout.write(f"  pandas-datareader returned {len(df):,} rows")
        if df.empty:
            self.stdout.write(self.style.WARNING("  no rows returned; skipping insert"))
            return

        if cache:
            self._cache_csv(df, f"famafrench_{datetime.utcnow():%Y%m%dT%H%M%S}.csv")

        rows = [
            RawFactor(
                date=r.date,
                mkt_rf=_nn(r.mkt_rf),
                smb=_nn(r.smb),
                hml=_nn(r.hml),
                rmw=_nn(r.rmw),
                cma=_nn(r.cma),
                mom=_nn(r.mom),
                rf=_nn(r.rf),
                source="ken_french_5f",
            )
            for r in df.itertuples(index=False)
        ]
        inserted = RawFactor.objects.bulk_create(rows, batch_size=5000, ignore_conflicts=True)
        self.stdout.write(
            self.style.SUCCESS(
                f"  inserted {len(inserted):,} factor rows (conflicts ignored)"
            )
        )

    def _upsert_symbols(self, df) -> None:
        """Upsert dim_symbols with first_seen / last_seen derived from what we just pulled."""
        by_symbol = df.groupby("symbol")["date"]
        for sym, dates in by_symbol:
            first, last = dates.min(), dates.max()
            obj, created = Symbol.objects.get_or_create(
                symbol=sym, defaults={"first_seen": first, "last_seen": last}
            )
            if not created:
                changed = False
                if obj.first_seen is None or first < obj.first_seen:
                    obj.first_seen = first
                    changed = True
                if obj.last_seen is None or last > obj.last_seen:
                    obj.last_seen = last
                    changed = True
                if changed:
                    obj.save(update_fields=["first_seen", "last_seen"])

    def _cache_csv(self, df, filename: str) -> None:
        path: Path = settings.RAW_CACHE_DIR / filename
        df.to_csv(path, index=False)
        self.stdout.write(f"  cached -> {path}")


def _nn(v):
    """NaN -> None so Django writes SQL NULL."""
    return None if v is None or v != v else float(v)
