from django.core.management.base import BaseCommand
from django.db import transaction

from ingest.models import Symbol
from ingest.universe import load_sectors


class Command(BaseCommand):
    help = "Populate dim_symbols.sector from backend/ingest/config/sectors.yml."

    def handle(self, *args, **opts) -> None:
        mapping = load_sectors()
        updated = 0
        created = 0
        unknown = 0

        with transaction.atomic():
            for symbol, sector in mapping.items():
                obj, was_created = Symbol.objects.get_or_create(
                    symbol=symbol, defaults={"sector": sector}
                )
                if was_created:
                    created += 1
                elif obj.sector != sector:
                    obj.sector = sector
                    obj.save(update_fields=["sector"])
                    updated += 1

            # Report any symbols in dim_symbols that lack sector assignment.
            for s in Symbol.objects.filter(sector=""):
                if s.symbol not in mapping:
                    unknown += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"  no sector mapping for {s.symbol}"
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"populated sectors: {created} created, {updated} updated, "
                f"{unknown} still unknown"
            )
        )
