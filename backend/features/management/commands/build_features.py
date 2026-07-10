from django.core.management.base import BaseCommand

from features.build import build


class Command(BaseCommand):
    help = (
        "Build fct_features from raw_prices (technicals + monthly returns + target). "
        "Betas are filled by a later command in M3b."
    )

    def handle(self, *args, **opts) -> None:
        summary = build()
        self.stdout.write(f"build summary: {summary}")
