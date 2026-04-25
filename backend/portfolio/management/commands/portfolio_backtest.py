from django.core.management.base import BaseCommand, CommandError

from portfolio.runner import backtest_run


class Command(BaseCommand):
    help = "Backtest an RF run's picks: optimise weights, compute daily strategy returns, log metrics."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--run-id",
            required=True,
            help="run_id (UUID, with or without dashes) of an RF run that has rf_picks populated.",
        )
        parser.add_argument(
            "--entry-delay-bdays",
            type=int,
            default=1,
            help="Business days between rebalance date and entry (0=same-day, 1=T+1 default).",
        )
        parser.add_argument(
            "--holding",
            default="next_month",
            help="'next_month' (default) or an integer number of business days to hold.",
        )

    def handle(self, *args, **opts) -> None:
        try:
            summary = backtest_run(
                opts["run_id"],
                entry_delay_bdays=opts["entry_delay_bdays"],
                holding=opts["holding"],
            )
        except RuntimeError as exc:
            raise CommandError(str(exc))
        self.stdout.write(self.style.SUCCESS(f"backtest summary: {summary}"))
