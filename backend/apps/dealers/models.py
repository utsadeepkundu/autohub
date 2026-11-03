
from django.conf import settings
from django.db import models


class DealerProfile(models.Model):
    """
    Business profile associated with one Django user.

    A registered customer can apply to become a dealer.
    New dealer applications require admin approval.
    """

    VERIFICATION_STATUS = [
        ("pending", "Pending Verification"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("suspended", "Suspended"),
    ]

    # Account relationship
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dealer_profile",
    )

    # Business information
    business_name = models.CharField(max_length=200)

    contact_person = models.CharField(
        max_length=150,
    )

    email = models.EmailField()

    phone = models.CharField(
        max_length=20,
    )

    alternate_phone = models.CharField(
        max_length=20,
        blank=True,
    )

    website = models.URLField(
        max_length=500,
        blank=True,
    )

    business_description = models.TextField(
        blank=True,
    )

    # Business address
    address_line1 = models.CharField(
        max_length=250,
    )

    address_line2 = models.CharField(
        max_length=250,
        blank=True,
    )

    locality = models.CharField(
        max_length=150,
        blank=True,
    )

    city = models.CharField(
        max_length=100,
        db_index=True,
    )

    state = models.CharField(
        max_length=100,
    )

    pincode = models.CharField(
        max_length=10,
    )

    # Business verification
    gstin = models.CharField(
        max_length=15,
        blank=True,
    )

    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS,
        default="pending",
        db_index=True,
    )

    verification_notes = models.TextField(
        blank=True,
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Business branding
    logo_url = models.URLField(
        max_length=1000,
        blank=True,
    )

    # Account status
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "dealer_profiles"

        indexes = [
            models.Index(
                fields=["verification_status", "city"],
                name="dealer_status_city_idx",
            ),
            models.Index(
                fields=["is_active"],
                name="dealer_active_idx",
            ),
        ]

        ordering = ["-created_at"]

    def __str__(self):
        return self.business_name


class DealerVehicleListing(models.Model):

    FUEL_CHOICES = [
        ("Petrol", "Petrol"),
        ("Diesel", "Diesel"),
        ("CNG", "CNG"),
        ("LPG", "LPG"),
        ("Electric", "Electric"),
        ("Hybrid", "Hybrid"),
        ("Other", "Other"),
    ]

    TRANSMISSION_CHOICES = [
        ("Manual", "Manual"),
        ("Automatic", "Automatic"),
        ("AMT", "AMT"),
        ("CVT", "CVT"),
        ("DCT", "DCT"),
    ]

    BODY_TYPE_CHOICES = [
        ("Hatchback", "Hatchback"),
        ("Sedan", "Sedan"),
        ("SUV", "SUV"),
        ("MUV", "MUV"),
        ("Coupe", "Coupe"),
        ("Convertible", "Convertible"),
        ("Pickup", "Pickup"),
        ("Van", "Van"),
        ("Other", "Other"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending_review", "Pending Review"),
        ("published", "Published"),
        ("rejected", "Rejected"),
        ("sold", "Sold"),
        ("archived", "Archived"),
    ]

    dealer = models.ForeignKey(
        DealerProfile,
        on_delete=models.CASCADE,
        related_name="vehicle_listings",
    )

    title = models.CharField(max_length=200)

    make = models.CharField(max_length=100, db_index=True)
    model = models.CharField(max_length=150, db_index=True)
    variant = models.CharField(max_length=150, blank=True)

    year = models.PositiveSmallIntegerField()
    fuel = models.CharField(max_length=20, choices=FUEL_CHOICES)
    transmission = models.CharField(
        max_length=20,
        choices=TRANSMISSION_CHOICES,
    )
    body_type = models.CharField(
        max_length=30,
        choices=BODY_TYPE_CHOICES,
    )

    price = models.PositiveBigIntegerField()
    km_driven = models.PositiveIntegerField()
    owner_count = models.PositiveSmallIntegerField(default=1)

    color = models.CharField(max_length=50, blank=True)
    engine_cc = models.PositiveIntegerField(null=True, blank=True)
    seating_capacity = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    description = models.TextField(blank=True)

    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100)
    locality = models.CharField(max_length=150, blank=True)
    pincode = models.CharField(max_length=10, blank=True)

    primary_image = models.URLField(max_length=1000, blank=True)

    images = models.JSONField(default=list, blank=True)
    features = models.JSONField(default=list, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending_review",
        db_index=True,
    )

    rejection_reason = models.TextField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dealer_vehicle_listings"

        indexes = [
            models.Index(
                fields=["dealer", "status"],
                name="dealer_inv_status_idx",
            ),
            models.Index(
                fields=["make", "model"],
                name="dealer_inv_make_model_idx",
            ),
            models.Index(
                fields=["city", "status"],
                name="dealer_inv_city_status_idx",
            ),
            models.Index(
                fields=["year"],
                name="dealer_inv_year_idx",
            ),
        ]

        ordering = ["-created_at"]

    def __str__(self):
        return self.title
