
from django.contrib import admin, messages
from django.utils import timezone

from .models import CustomerEnquiry


@admin.register(CustomerEnquiry)
class CustomerEnquiryAdmin(admin.ModelAdmin):

    list_display = (
        "customer_name",
        "vehicle",
        "dealer",
        "phone",
        "preferred_contact_method",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "preferred_contact_method",
        "created_at",
    )

    search_fields = (
        "customer_name",
        "phone",
        "email",
        "vehicle__title",
        "vehicle__make",
        "vehicle__model",
        "dealer__business_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    raw_id_fields = (
        "vehicle",
        "dealer",
        "customer_user",
    )

    ordering = ("-created_at",)

    date_hierarchy = "created_at"

    list_per_page = 25

    actions = (
        "mark_as_contacted",
        "mark_as_converted",
        "mark_as_closed",
    )

    fieldsets = (
        (
            "Vehicle and Dealer",
            {
                "fields": (
                    "vehicle",
                    "dealer",
                    "customer_user",
                ),
            },
        ),
        (
            "Customer Information",
            {
                "fields": (
                    "customer_name",
                    "phone",
                    "email",
                    "message",
                    "preferred_contact_method",
                    "consent_to_contact",
                ),
            },
        ),
        (
            "Lead Management",
            {
                "fields": (
                    "status",
                    "dealer_notes",
                    "last_contacted_at",
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    @admin.action(description="Mark selected enquiries as contacted")
    def mark_as_contacted(self, request, queryset):

        now = timezone.now()
        updated = 0

        for enquiry in queryset:
            enquiry.status = "contacted"
            enquiry.last_contacted_at = now

            enquiry.save(
                update_fields=[
                    "status",
                    "last_contacted_at",
                    "updated_at",
                ]
            )

            updated += 1

        self.message_user(
            request,
            f"{updated} enquiry(s) marked as contacted.",
            messages.SUCCESS,
        )

    @admin.action(description="Mark selected enquiries as converted")
    def mark_as_converted(self, request, queryset):

        updated = 0

        for enquiry in queryset:
            enquiry.status = "converted"

            enquiry.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            updated += 1

        self.message_user(
            request,
            f"{updated} enquiry(s) marked as converted.",
            messages.SUCCESS,
        )

    @admin.action(description="Close selected enquiries")
    def mark_as_closed(self, request, queryset):

        updated = 0

        for enquiry in queryset:
            enquiry.status = "closed"

            enquiry.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            updated += 1

        self.message_user(
            request,
            f"{updated} enquiry(s) closed.",
            messages.SUCCESS,
        )
