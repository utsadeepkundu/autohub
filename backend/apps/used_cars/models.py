
from django.db import models


class UsedCarListing(models.Model):

    # Provider identification
    provider = models.CharField(max_length=50, default="scrappa")
    external_id = models.CharField(max_length=150)

    used_car_id = models.BigIntegerField(null=True, blank=True)

    # Vehicle information
    title = models.CharField(max_length=250)
    source_url = models.URLField(max_length=600, blank=True)

    make = models.CharField(max_length=150, db_index=True)
    model = models.CharField(max_length=180, blank=True)
    model_name = models.CharField(max_length=180, blank=True)
    variant = models.CharField(max_length=180, blank=True)

    central_variant_id = models.BigIntegerField(
        null=True,
        blank=True,
    )

    year = models.PositiveSmallIntegerField(null=True, blank=True)

    fuel = models.CharField(max_length=50, blank=True)
    transmission = models.CharField(max_length=50, blank=True)
    body_type = models.CharField(max_length=80, blank=True)

    # Price information (INR)
    price = models.BigIntegerField(null=True, blank=True)
    formatted_price = models.CharField(max_length=100, blank=True)
    market_price = models.BigIntegerField(null=True, blank=True)
    currency = models.CharField(max_length=10, default="INR")

    # Running information
    km_driven = models.PositiveBigIntegerField(null=True, blank=True)

    owner_count = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    owner_slug = models.CharField(max_length=80, blank=True)

    # Location information
    city = models.CharField(max_length=100, db_index=True)
    city_slug = models.CharField(max_length=100, blank=True)
    city_id = models.CharField(max_length=50, blank=True)
    locality = models.CharField(max_length=150, blank=True)

    # Seller information
    seller_type = models.CharField(max_length=50, blank=True)
    dealer_id = models.BigIntegerField(null=True, blank=True)
    store_id = models.CharField(max_length=100, blank=True)
    corporate_id = models.CharField(max_length=100, blank=True)
    inventory_type = models.CharField(max_length=100, blank=True)
    inventory_label = models.CharField(max_length=100, blank=True)

    # Media
    primary_image = models.CharField(max_length=1000, blank=True)
    images = models.JSONField(default=dict, blank=True)

    # Additional provider information
    flags = models.JSONField(default=dict, blank=True)
    emi = models.JSONField(default=dict, blank=True)

    trust_tags = models.JSONField(default=list, blank=True)
    ai_tags = models.JSONField(default=list, blank=True)

    ai_price_badge = models.CharField(max_length=100, blank=True)

    map_link = models.URLField(max_length=600, blank=True)

    additional = models.JSONField(default=dict, blank=True)

    # Complete original API response
    provider_data = models.JSONField(default=dict, blank=True)

    # Listing status
    inventory_status = models.IntegerField(null=True, blank=True)
    status_text = models.CharField(max_length=80, blank=True)

    is_active = models.BooleanField(default=True)

    # Synchronization timestamps
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "used_car_listings"

        constraints = [
            models.UniqueConstraint(
                fields=["provider", "external_id"],
                name="used_provider_ext_uniq",
            )
        ]

        indexes = [
            models.Index(
                fields=["city", "make", "model"],
                name="used_city_make_model_idx",
            ),
            models.Index(
                fields=["price", "year"],
                name="used_price_year_idx",
            ),
        ]

        ordering = ["-created_at"]

    def __str__(self):
        return self.title
