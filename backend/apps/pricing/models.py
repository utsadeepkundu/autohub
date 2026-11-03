
from django.conf import settings
from django.db import models


class VehicleValuation(models.Model):

    CONFIDENCE_CHOICES = [
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
        ("insufficient", "Insufficient Data"),
    ]

    STATUS_CHOICES = [
        ("estimated", "Estimated"),
        ("insufficient_data", "Insufficient Data"),
    ]

    # Registered customer who requested the valuation.
    # Guest valuations will not create history records.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vehicle_valuations",
    )

    # Vehicle information supplied for valuation.
    make = models.CharField(max_length=150, db_index=True)
    model = models.CharField(max_length=180, db_index=True)

    year = models.PositiveSmallIntegerField()

    fuel = models.CharField(max_length=50)
    transmission = models.CharField(max_length=50)

    km_driven = models.PositiveBigIntegerField()

    city = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
    )

    # Valuation results.
    estimated_price = models.BigIntegerField(
        null=True,
        blank=True,
    )

    minimum_price = models.BigIntegerField(
        null=True,
        blank=True,
    )

    maximum_price = models.BigIntegerField(
        null=True,
        blank=True,
    )

    comparable_count = models.PositiveIntegerField(default=0)

    confidence = models.CharField(
        max_length=20,
        choices=CONFIDENCE_CHOICES,
        default="insufficient",
    )

    comparison_scope = models.CharField(
        max_length=100,
        blank=True,
    )

    valuation_status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="insufficient_data",
        db_index=True,
    )

    # Complete calculation response for historical reference.
    result_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vehicle_valuations"

        indexes = [
            models.Index(
                fields=["user", "created_at"],
                name="valuation_user_date_idx",
            ),
            models.Index(
                fields=["make", "model"],
                name="valuation_make_model_idx",
            ),
        ]

        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.make} {self.model} - {self.year}"
