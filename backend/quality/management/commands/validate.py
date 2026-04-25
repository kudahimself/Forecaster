from django.core.management.base import BaseCommand

from quality.models import DqCheck
from quality.runner import run_all_checks


class Command(BaseCommand):
    help = "Run all data-quality checks against the raw tables and persist results."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--universe",
            default="default",
            help="Universe YAML name used for coverage check (default: top100).",
        )

    def handle(self, *args, **opts) -> None:
        run = run_all_checks(universe_name=opts["universe"])
        self.stdout.write(f"DqRun {run.run_id}  summary={run.summary}")
        width = max(len(c.check_name) for c in run.checks.all())
        for c in run.checks.all().order_by("check_name"):
            color = {
                DqCheck.STATUS_PASS: self.style.SUCCESS,
                DqCheck.STATUS_WARN: self.style.WARNING,
                DqCheck.STATUS_FAIL: self.style.ERROR,
            }[c.status]
            self.stdout.write(
                f"  {c.check_name.ljust(width)}  "
                f"{color(c.status.upper()):<8}  "
                f"failed={c.rows_failed:<6}  checked={c.rows_checked}"
            )
