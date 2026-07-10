"""Job implementations. Each job is a callable that does the work AND
writes to IngestRun. Use the `@job` decorator to wrap any function: it
opens an IngestRun row on entry, updates it on success/failure, and
captures the dict the function returns as `summary`.

Incremental semantics are deliberately simple for v1: every job re-fetches
the full window. The raw tables have UNIQUE constraints + `ignore_conflicts`
so reruns are cheap. A proper 'since last ingest_at' implementation is a
clean follow-up once the history table is proven out.
"""

from __future__ import annotations

import logging
import traceback
from contextlib import contextmanager
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable

from django.utils import timezone

from ingest import ff, yf
from ingest.models import RawFactor, RawPrice, Symbol
from ingest.universe import load_universe
from scheduler.models import IngestRun

log = logging.getLogger(__name__)


@contextmanager
def _run_tracker(job_name: str):
    run = IngestRun.objects.create(job_name=job_name)
    try:
        yield run
    except Exception as exc:
        run.status = IngestRun.STATUS_FAILED
        run.error = "".join(traceback.format_exception_only(type(exc), exc))[:4000]
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "error", "finished_at"])
        raise
    else:
        if run.status == IngestRun.STATUS_RUNNING:
            run.status = IngestRun.STATUS_COMPLETED
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "finished_at", "rows_ingested", "summary"])


def ingest_prices(
    universe: str = "default",
    start: str = "2018-01-01",
    end: str | None = None,
) -> dict[str, Any]:
    """Pull OHLCV from yfinance for the given universe and append to raw_prices."""
    with _run_tracker("yfinance_prices") as run:
        run.summary = {"universe": universe, "start": start, "end": end}
        run.save(update_fields=["summary"])

        u = load_universe(universe)
        tickers = u["tickers"]
        end = end or (datetime.utcnow().date() + timedelta(days=1)).isoformat()

        df = yf.fetch_prices(tickers, start=start, end=end)
        if df.empty:
            run.summary = {**run.summary, "n_api_rows": 0, "n_inserted": 0}
            return run.summary

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
        inserted = RawPrice.objects.bulk_create(
            rows, batch_size=5000, ignore_conflicts=True
        )

        # Upsert Symbol dim rows with observed first/last dates.
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

        run.rows_ingested = len(inserted)
        run.summary = {
            **run.summary,
            "n_tickers": len(tickers),
            "n_api_rows": int(len(df)),
            "n_inserted": len(inserted),
            "date_min": str(df["date"].min()),
            "date_max": str(df["date"].max()),
        }
        return run.summary


def ingest_factors(
    start: str = "2018-01-01",
    end: str | None = None,
) -> dict[str, Any]:
    """Pull Fama-French 5-factor + momentum daily and append to raw_factors."""
    with _run_tracker("famafrench_factors") as run:
        run.summary = {"start": start, "end": end}
        run.save(update_fields=["summary"])

        end = end or (datetime.utcnow().date() + timedelta(days=1)).isoformat()
        df = ff.fetch_factors(start=start, end=end)
        if df.empty:
            run.summary = {**run.summary, "n_api_rows": 0, "n_inserted": 0}
            return run.summary

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
        inserted = RawFactor.objects.bulk_create(
            rows, batch_size=5000, ignore_conflicts=True
        )

        run.rows_ingested = len(inserted)
        run.summary = {
            **run.summary,
            "n_api_rows": int(len(df)),
            "n_inserted": len(inserted),
            "date_min": str(df["date"].min()),
            "date_max": str(df["date"].max()),
        }
        return run.summary


JOBS: dict[str, Callable[..., dict[str, Any]]] = {
    "yfinance_prices": ingest_prices,
    "famafrench_factors": ingest_factors,
}


def _nn(v):
    if v is None:
        return None
    try:
        if v != v:
            return None
    except Exception:
        return None
    return float(v)
