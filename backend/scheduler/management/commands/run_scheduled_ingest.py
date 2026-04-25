from django.core.management.base import BaseCommand, CommandError

from scheduler.jobs import JOBS, ingest_factors, ingest_prices


class Command(BaseCommand):
    help = (
        "Execute one or more scheduled ingest jobs. Each run is logged to "
        "ingest_runs with start/end timestamps and row counts. "
        "Wrap with cron / Windows Task Scheduler / Docker `scheduler` "
        "service for recurring execution."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--job",
            default="all",
            help=f"Job to run — one of {list(JOBS.keys()) + ['all']}. Default: all.",
        )
        parser.add_argument("--universe", default="default", help="Universe YAML name (prices only).")
        parser.add_argument("--start", default="2018-01-01")
        parser.add_argument("--end", default=None)

    def handle(self, *args, **opts) -> None:
        job = opts["job"]
        jobs_to_run = list(JOBS.keys()) if job == "all" else [job]
        for j in jobs_to_run:
            if j not in JOBS:
                raise CommandError(f"unknown job: {j}. Known: {list(JOBS.keys())}")

        for j in jobs_to_run:
            self.stdout.write(self.style.NOTICE(f"[{j}] starting..."))
            try:
                if j == "yfinance_prices":
                    summary = ingest_prices(
                        universe=opts["universe"],
                        start=opts["start"],
                        end=opts["end"],
                    )
                else:
                    summary = ingest_factors(
                        start=opts["start"], end=opts["end"]
                    )
                self.stdout.write(
                    self.style.SUCCESS(f"[{j}] done · {summary}")
                )
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"[{j}] failed: {exc}"))
                raise
