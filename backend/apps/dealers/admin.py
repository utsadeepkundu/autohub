
from django.contrib import admin, messages
from django.utils import timezone

from .models import DealerProfile, DealerVehicleListing

@admin.register(DealerProfile)
class DealerProfileAdmin(admin.ModelAdmin):

    list_display = (
        "business_name",
        "contact_person",
        "email",
        "phone",
        "city",
        "state",
        "verification_status",
        "is_active",
        "created_at",
    )

    list_filter = (
        "verification_status",
        "is_active",
        "state",
        "city",
    )

    search_fields = (
        "business_name",
        "contact_person",
        "email",
        "phone",
        "city",
        "gstin",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "verified_at",
    )

    raw_id_fields = ("user",)

    ordering = ("-created_at",)

    list_per_page = 25

    actions = (
        "approve_selected_dealers",
        "reject_selected_dealers",
    )

    fieldsets = (
        (
            "Account Information",
            {
                "fields": (
                    "user",
                    "is_active",
                )
            },
        ),
        (
            "Business Information",
            {
                "fields": (
                    "business_name",
                    "contact_person",
                    "email",
                    "phone",
                    "alternate_phone",
                    "website",
                    "business_description",
                )
            },
        ),
        (
            "Business Address",
            {
                "fields": (
                    "address_line1",
                    "address_line2",
                    "locality",
                    "city",
                    "state",
                    "pincode",
                )
            },
        ),
        (
            "Verification",
            {
                "fields": (
                    "gstin",
                    "verification_status",
                    "verification_notes",
                    "verified_at",
                )
            },
        ),
        (
            "Business Branding",
            {
                "fields": (
                    "logo_url",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.action(
        description="Approve selected dealer applications"
    )
    def approve_selected_dealers(
        self,
        request,
        queryset,
    ):

        now = timezone.now()
        updated = 0

        for dealer in queryset:
            dealer.verification_status = "approved"
            dealer.verified_at = now

            dealer.save(
                update_fields=[
                    "verification_status",
                    "verified_at",
                    "updated_at",
                ]
            )

            updated += 1

        self.message_user(
            request,
            f"{updated} dealer application(s) approved.",
            messages.SUCCESS,
        )

    @admin.action(
        description="Reject selected dealer applications"
    )
    def reject_selected_dealers(
        self,
        request,
        queryset,
    ):

        updated = 0

        for dealer in queryset:
            dealer.verification_status = "rejected"
            dealer.verified_at = None

            dealer.save(
                update_fields=[
                    "verification_status",
                    "verified_at",
                    "updated_at",
                ]
            )

            updated += 1

        self.message_user(
            request,
            f"{updated} dealer application(s) rejected.",
            messages.WARNING,
        )


@admin.register(DealerVehicleListing)
class DealerVehicleListingAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "dealer",
        "make",
        "model",
        "year",
        "price",
        "city",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "fuel",
        "transmission",
        "body_type",
        "city",
        "created_at",
    )

    search_fields = (
        "title",
        "make",
        "model",
        "variant",
        "dealer__business_name",
        "dealer__email",
        "city",
    )

    readonly_fields = (
        "published_at",
        "created_at",
        "updated_at",
    )

    raw_id_fields = ("dealer",)

    ordering = ("-created_at",)

    actions = (
        "publish_selected_listings",
        "reject_selected_listings",
    )

    fieldsets = (
        (
            "Dealer Information",
            {
                "fields": ("dealer",),
            },
        ),
        (
            "Vehicle Information",
            {
                "fields": (
                    "title",
                    "make",
                    "model",
                    "variant",
                    "year",
                    "fuel",
                    "transmission",
                    "body_type",
                ),
            },
        ),
        (
            "Vehicle Specifications",
            {
                "fields": (
                    "km_driven",
                    "owner_count",
                    "color",
                    "engine_cc",
                    "seating_capacity",
                    "description",
                ),
            },
        ),
        (
            "Pricing and Location",
            {
                "fields": (
                    "price",
                    "city",
                    "state",
                    "locality",
                    "pincode",
                ),
            },
        ),
        (
            "Images and Features",
            {
                "fields": (
                    "primary_image",
                    "images",
                    "features",
                ),
            },
        ),
        (
            "Listing Review",
            {
                "fields": (
                    "status",
                    "rejection_reason",
                    "published_at",
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

    @admin.action(description="Approve and publish selected listings")
    def publish_selected_listings(self, request, queryset):

        now = timezone.now()
        published = 0
        skipped = 0

        for listing in queryset.select_related("dealer"):

            if (
                listing.dealer.verification_status != "approved"
                or not listing.dealer.is_active
            ):
                skipped += 1
                continue

            listing.status = "published"
            listing.published_at = now
            listing.rejection_reason = ""

            listing.save(
                update_fields=[
                    "status",
                    "published_at",
                    "rejection_reason",
                    "updated_at",
                ]
            )

            published += 1

        self.message_user(
            request,
            f"{published} listing(s) published. "
            f"{skipped} skipped because their dealer is not approved and active.",
            level=messages.WARNING if skipped else messages.SUCCESS,
        )

    @admin.action(description="Reject selected listings")
    def reject_selected_listings(self, request, queryset):

        rejected = 0

        for listing in queryset:

            listing.status = "rejected"
            listing.published_at = None

            if not listing.rejection_reason:
                listing.rejection_reason = "Rejected by administrator."

            listing.save(
                update_fields=[
                    "status",
                    "published_at",
                    "rejection_reason",
                    "updated_at",
                ]
            )

            rejected += 1

        self.message_user(
            request,
            f"{rejected} listing(s) rejected.",
            level=messages.SUCCESS,
        )
