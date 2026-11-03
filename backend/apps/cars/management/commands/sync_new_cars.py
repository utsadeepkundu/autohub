
from django.core.management.base import BaseCommand
from apps.cars.services.scrappa_importer import sync_brand_catalogue


DEFAULT_BRANDS = [
    "tata",
    "mahindra",
    "honda",
    "toyota",
]


class Command(BaseCommand):
    help = "Automatically synchronize new-car catalogues."

    def add_arguments(self, parser):
        parser.add_argument(
            "--brands",
            nargs="+",
            default=DEFAULT_BRANDS,
            help="Manufacturer slugs to synchronize.",
        )

    def handle(self, *args, **options):
        brands = options["brands"]

        totals = {
            "brands_processed": 0,
            "models_available": 0,
            "models_imported": 0,
            "models_failed": 0,
            "variants_created": 0,
            "variants_updated": 0,
        }

        self.stdout.write(
            self.style.SUCCESS(
                "\nStarting AutoHub new-car synchronization...\n"
            )
        )

        for brand in brands:
            self.stdout.write(
                f"\nSynchronizing manufacturer: {brand}"
            )

            try:
                result = sync_brand_catalogue(brand)

                totals["brands_processed"] += 1

                for key in (
                    "models_available",
                    "models_imported",
                    "models_failed",
                    "variants_created",
                    "variants_updated",
                ):
                    totals[key] += result.get(key, 0)

                self.stdout.write(
                    f"Models imported: {result['models_imported']}"
                )

                self.stdout.write(
                    f"Variants created: {result['variants_created']}"
                )

                self.stdout.write(
                    f"Variants updated: {result['variants_updated']}"
                )

                if result["models_failed"]:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Model failures: {result['models_failed']}"
                        )
                    )

            except Exception as exc:
                totals["models_failed"] += 1

                self.stderr.write(
                    self.style.ERROR(
                        f"Failed to synchronize {brand}: {exc}"
                    )
                )

        self.stdout.write("\n========== AUT0HUB SYNC REPORT ==========")

        for key, value in totals.items():
            self.stdout.write(f"{key}: {value}")

        self.stdout.write("\nSynchronization completed.")
