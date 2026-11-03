
from django.conf import settings
from django.db import models

from apps.dealers.models import DealerProfile, DealerVehicleListing


class CustomerEnquiry(models.Model):

    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("converted", "Converted"),
        ("closed", "Closed"),
    ]

    CONTACT_METHOD_CHOICES = [
        ("phone", "Phone"),
        ("email", "Email"),
        ("whatsapp", "WhatsApp"),
    ]

    # Vehicle and dealer information
    vehicle = models.ForeignKey(
        DealerVehicleListing,
        on_delete=models.PROTECT,
        related_name="customer_enquiries",
    )

    dealer = models.ForeignKey(
        DealerProfile,
        on_delete=models.PROTECT,
        related_name="customer_enquiries",
    )

    # Optional link to a registered customer.
    # Guest customers can also submit enquiries.
    customer_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vehicle_enquiries",
    )

    # Customer contact information
    customer_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(max_length=254, blank=True)

    message = models.TextField(blank=True)

    preferred_contact_method = models.CharField(
        max_length=20,
        choices=CONTACT_METHOD_CHOICES,
        default="phone",
    )

    consent_to_contact = models.BooleanField(default=False)

    # Dealer lead management
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",
        db_index=True,
    )

    dealer_notes = models.TextField(blank=True)

    last_contacted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customer_enquiries"

        indexes = [
            models.Index(
                fields=["dealer", "status"],
                name="enq_dealer_status_idx",
            ),
            models.Index(
                fields=["vehicle", "created_at"],
                name="enq_vehicle_created_idx",
            ),
            models.Index(
                fields=["created_at"],
                name="enq_created_idx",
            ),
        ]

        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.customer_name} - "
            f"{self.vehicle.title}"
        )
