
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import RevokedRefreshToken


class Command(BaseCommand):
    """
    Delete revoked refresh-token records that have expired.
    """

    help = "Remove expired revoked refresh-token records."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many records would be deleted without deleting them.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        current_time = timezone.now()

        expired_tokens = RevokedRefreshToken.objects.filter(
            expires_at__lt=current_time
        )

        dry_run = bool(options.get("dry_run", False))

        if dry_run:
            expired_count = expired_tokens.count()

            self.stdout.write(
                self.style.WARNING(
                    f"Dry run: {expired_count} expired token records "
                    "would be deleted."
                )
            )
            return

        deleted_count, _ = expired_tokens.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully deleted {deleted_count} expired "
                "revoked-token records."
            )
        )
