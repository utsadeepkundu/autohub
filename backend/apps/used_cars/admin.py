
from django.contrib import admin

from .models import UsedCarListing


@admin.register(UsedCarListing)
class UsedCarListingAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "make",
        "year",
        "price",
        "km_driven",
        "city",
        "seller_type",
        "is_active",
        "last_synced_at",
    )

    list_filter = (
        "city",
        "make",
        "fuel",
        "transmission",
        "seller_type",
        "is_active",
    )

    search_fields = (
        "title",
        "make",
        "model",
        "variant",
        "city",
        "locality",
        "external_id",
    )

    readonly_fields = (
        "first_seen_at",
        "last_seen_at",
        "last_synced_at",
        "created_at",
        "updated_at",
    )

    ordering = ("-last_synced_at",)
