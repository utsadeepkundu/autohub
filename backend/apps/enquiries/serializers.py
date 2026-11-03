
import re

from rest_framework import serializers

from apps.dealers.models import DealerVehicleListing

from .models import CustomerEnquiry


class CustomerEnquirySerializer(serializers.ModelSerializer):

    id = serializers.SerializerMethodField()

    vehicle_id = serializers.CharField(write_only=True)

    vehicle_title = serializers.CharField(
        source="vehicle.title",
        read_only=True
    )

    dealer_name = serializers.CharField(
        source="dealer.business_name",
        read_only=True
    )

    class Meta:
        model = CustomerEnquiry

        fields = [
            "id",
            "vehicle_id",
            "vehicle_title",
            "dealer_name",
            "customer_name",
            "phone",
            "email",
            "message",
            "preferred_contact_method",
            "consent_to_contact",
            "status",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "vehicle_title",
            "dealer_name",
            "status",
            "created_at",
        ]

    def get_id(self, obj):
        return str(obj.pk)

    def validate_vehicle_id(self, value):
        try:
            vehicle = DealerVehicleListing.objects.get(
                pk=value,
                status="published",
            )

        except (DealerVehicleListing.DoesNotExist, ValueError, TypeError):
            raise serializers.ValidationError(
                "This vehicle is not available for enquiries."
            )

        if (
            vehicle.dealer.verification_status != "approved"
            or not vehicle.dealer.is_active
        ):
            raise serializers.ValidationError(
                "This vehicle is not currently available for enquiries."
            )

        return vehicle

    def validate_customer_name(self, value):
        value = value.strip()

        if len(value) < 2:
            raise serializers.ValidationError(
                "Please enter a valid customer name."
            )

        return value

    def validate_phone(self, value):
        phone = re.sub(r"[\s().-]", "", value.strip())

        if not re.fullmatch(r"\+?[0-9]{7,15}", phone):
            raise serializers.ValidationError(
                "Enter a valid phone number containing 7 to 15 digits."
            )

        return phone

    def validate_email(self, value):
        return value.strip().lower()

    def validate_consent_to_contact(self, value):
        if not value:
            raise serializers.ValidationError(
                "Consent is required before submitting an enquiry."
            )

        return value

    def validate(self, attrs):
        if (
            attrs.get("preferred_contact_method") == "email"
            and not attrs.get("email")
        ):
            raise serializers.ValidationError({
                "email": (
                    "Email is required when email is your "
                    "preferred contact method."
                )
            })

        return attrs

    def create(self, validated_data):
        vehicle = validated_data.pop("vehicle_id")

        request = self.context.get("request")
        customer_user = None

        if request and request.user.is_authenticated:
            customer_user = request.user

        return CustomerEnquiry.objects.create(
            vehicle=vehicle,
            dealer=vehicle.dealer,
            customer_user=customer_user,
            status="new",
            **validated_data
        )


class DealerEnquirySerializer(serializers.ModelSerializer):

    id = serializers.SerializerMethodField()

    vehicle_id = serializers.SerializerMethodField()

    vehicle_title = serializers.CharField(
        source="vehicle.title",
        read_only=True
    )

    dealer_name = serializers.CharField(
        source="dealer.business_name",
        read_only=True
    )

    class Meta:
        model = CustomerEnquiry

        fields = [
            "id",
            "vehicle_id",
            "vehicle_title",
            "dealer_name",
            "customer_name",
            "phone",
            "email",
            "message",
            "preferred_contact_method",
            "consent_to_contact",
            "status",
            "dealer_notes",
            "last_contacted_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields

    def get_id(self, obj):
        return str(obj.pk)

    def get_vehicle_id(self, obj):
        return str(obj.vehicle_id)


class DealerEnquiryUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerEnquiry

        fields = [
            "status",
            "dealer_notes",
        ]

    def validate_status(self, value):

        allowed_statuses = {
            "contacted",
            "converted",
            "closed",
        }

        if value not in allowed_statuses:
            raise serializers.ValidationError(
                "Select a valid lead status: contacted, converted or closed."
            )

        return value
