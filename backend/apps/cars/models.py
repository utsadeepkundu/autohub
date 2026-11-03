
from django.db import models


class CarBrand(models.Model):
    provider = models.CharField(max_length=50, default="scrappa")
    source_slug = models.CharField(max_length=150)

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180)

    logo_url = models.URLField(blank=True)

    is_active = models.BooleanField(default=True)

    provider_data = models.JSONField(default=dict, blank=True)

    last_synced_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "car_brands"
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "source_slug"],
                name="brand_prov_src_uniq",
            )
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name


class CarModel(models.Model):
    provider = models.CharField(max_length=50, default="scrappa")
    external_id = models.CharField(max_length=150)

    brand_source_slug = models.CharField(max_length=150)
    brand_name = models.CharField(max_length=150)

    source_slug = models.CharField(max_length=180)
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200)

    city = models.CharField(max_length=100, blank=True)
    city_id = models.CharField(max_length=100, blank=True)

    status = models.CharField(max_length=50, blank=True)

    price_range = models.CharField(max_length=100, blank=True)

    rating = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
    )

    review_count = models.PositiveIntegerField(default=0)

    # Flexible provider data
    mileage_data = models.JSONField(default=dict, blank=True)
    images = models.JSONField(default=dict, blank=True)
    key_specs = models.JSONField(default=list, blank=True)
    quick_overview = models.JSONField(default=dict, blank=True)
    city_prices = models.JSONField(default=list, blank=True)
    seo_data = models.JSONField(default=dict, blank=True)

    # Original provider response for future synchronization
    provider_data = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)

    last_synced_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "car_models"

        constraints = [
            models.UniqueConstraint(
                fields=["provider", "external_id"],
                name="model_prov_ext_uniq",
            )
        ]

        indexes = [
            models.Index(
                fields=["brand_source_slug", "slug"],
                name="cars_model_brand_slug_idx",
            ),
        ]

        ordering = ["brand_name", "name"]

    def __str__(self):
        return f"{self.brand_name} {self.name}"


class CarVariant(models.Model):
    provider = models.CharField(max_length=50, default="scrappa")
    external_id = models.CharField(max_length=150)

    model_external_id = models.CharField(max_length=150, db_index=True)
    model_slug = models.CharField(max_length=180)

    brand_source_slug = models.CharField(max_length=150)
    brand_name = models.CharField(max_length=150)
    model_name = models.CharField(max_length=180)

    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=150, blank=True)
    slug = models.SlugField(max_length=220)

    source_url = models.URLField(blank=True)

    # Prices are stored in INR
    ex_showroom_price = models.BigIntegerField(null=True, blank=True)
    ex_showroom_formatted = models.CharField(max_length=100, blank=True)

    on_road_price = models.BigIntegerField(null=True, blank=True)
    on_road_formatted = models.CharField(max_length=100, blank=True)

    pricing_city = models.CharField(max_length=100, blank=True)

    fuel = models.CharField(max_length=50, blank=True)
    transmission = models.CharField(max_length=50, blank=True)

    engine_displacement_cc = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    summary = models.TextField(blank=True)

    specs = models.JSONField(default=list, blank=True)

    mileage_arai = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    tag = models.CharField(max_length=100, blank=True)

    status = models.CharField(max_length=50, blank=True)

    waiting_period = models.CharField(max_length=100, blank=True)

    body_type = models.CharField(max_length=80, blank=True)

    key_features = models.JSONField(default=list, blank=True)
    missing_features = models.JSONField(default=list, blank=True)

    images = models.JSONField(default=list, blank=True)

    # Preserve all original provider fields
    provider_data = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)

    last_synced_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "car_variants"

        constraints = [
            models.UniqueConstraint(
                fields=["provider", "external_id"],
                name="variant_prov_ext_uniq",
            )
        ]

        indexes = [
            models.Index(
                fields=["brand_source_slug", "model_slug"],
                name="cars_var_brand_model_idx",
            ),
            models.Index(
                fields=["fuel", "body_type"],
                name="cars_var_fuel_body_idx",
            ),
        ]

        ordering = ["brand_name", "model_name", "name"]

    def __str__(self):
        return self.name
