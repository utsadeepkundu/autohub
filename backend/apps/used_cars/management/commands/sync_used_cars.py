
from django.core.management.base import BaseCommand, CommandError

from apps.used_cars.services.scrappa_importer import (
    sync_used_car_search,
)


class Command(BaseCommand):
    help = "Synchronize used-car listings from Scrappa."

    def add_arguments(self, parser):

        parser.add_argument(
            "--city",
            required=True,
            help="City slug, for example kolkata.",
        )

        parser.add_argument(
            "--make",
            default=None,
            help="Manufacturer slug, for example maruti.",
        )

        parser.add_argument(
            "--model",
            default=None,
            help="Model slug, for example swift.",
        )

        parser.add_argument(
            "--max-pages",
            type=int,
            default=3,
            help="Maximum number of API pages to retrieve in this run.",
        )

        parser.add_argument(
            "--start-page",
            type=int,
            default=1,
            help="First provider page to retrieve.",
        )

        parser.add_argument(
            "--sort",
            default="created_date",
            help="Sorting field for Scrappa listings.",
        )

        parser.add_argument(
            "--sort-direction",
            choices=["asc", "desc"],
            default="desc",
            help="Sorting direction.",
        )

    def handle(self, *args, **options):

        self.stdout.write(
            self.style.SUCCESS(
                "\nStarting AutoHub used-car synchronization...\n"
            )
        )

        try:
            result = sync_used_car_search(
                city=options["city"],
                make=options["make"],
                model=options["model"],
                max_pages=options["max_pages"],
                start_page=options["start_page"],
                sort=options["sort"],
                sort_direction=options["sort_direction"],
            )

        except Exception as exc:
            raise CommandError(
                f"Used-car synchronization failed: {exc}"
            ) from exc

        self.stdout.write(
            "\n========== SYNC REPORT =========="
        )

        for key, value in result.items():
            self.stdout.write(f"{key}: {value}")

        if result["complete"]:
            self.stdout.write(
                self.style.SUCCESS(
                    "\nUsed-car synchronization completed."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "\nSynchronization stopped before "
                    "all available listings were confirmed."
                )
            )
