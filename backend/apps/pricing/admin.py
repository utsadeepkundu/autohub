
from django.contrib import admin

from .models import VehicleValuation


@admin.register(VehicleValuation)
class VehicleValuationAdmin(admin.ModelAdmin):

    list_display = (
        "make",
        "model",
        "year",
        "user",
        "estimated_price",
        "comparable_count",
        "confidence",
        "valuation_status",
        "created_at",
    )

    list_filter = (
        "valuation_status",
        "confidence",
        "fuel",
        "transmission",
        "city",
        "created_at",
    )

    search_fields = (
        "make",
        "model",
        "city",
        "user__email",
    )

    readonly_fields = (
        "user",
        "make",
        "model",
        "year",
        "fuel",
        "transmission",
        "km_driven",
        "city",
        "estimated_price",
        "minimum_price",
        "maximum_price",
        "comparable_count",
        "confidence",
        "comparison_scope",
        "valuation_status",
        "result_data",
        "created_at",
    )

    raw_id_fields = ("user",)

    ordering = ("-created_at",)

    date_hierarchy = "created_at"

    list_per_page = 25

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
