
from datetime import date

from rest_framework import serializers

from .models import DealerProfile, DealerVehicleListing


class DealerProfileSerializer(serializers.ModelSerializer):

    id = serializers.SerializerMethodField()

    class Meta:
        model = DealerProfile

        fields = [
            "id",
            "business_name",
            "contact_person",
            "email",
            "phone",
            "alternate_phone",
            "website",
            "business_description",
            "address_line1",
            "address_line2",
            "locality",
            "city",
            "state",
            "pincode",
            "gstin",
            "logo_url",
            "verification_status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "verification_status",
            "created_at",
            "updated_at",
        ]

    def get_id(self, obj):
        return str(obj.pk)

    def validate_gstin(self, value):
        return value.strip().upper()

    def create(self, validated_data):
        request = self.context.get("request")

        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError(
                "Authentication is required to apply as a dealer."
            )

        if DealerProfile.objects.filter(user=request.user).exists():
            raise serializers.ValidationError(
                "You have already submitted a dealer application."
            )

        return DealerProfile.objects.create(
            user=request.user,
            **validated_data
        )


class DealerVehicleListingSerializer(serializers.ModelSerializer):

    id = serializers.SerializerMethodField()

    dealer_name = serializers.CharField(
        source="dealer.business_name",
        read_only=True
    )

    class Meta:
        model = DealerVehicleListing

        fields = [
            "id",
            "dealer_name",
            "title",
            "make",
            "model",
            "variant",
            "year",
            "fuel",
            "transmission",
            "body_type",
            "price",
            "km_driven",
            "owner_count",
            "color",
            "engine_cc",
            "seating_capacity",
            "description",
            "city",
            "state",
            "locality",
            "pincode",
            "primary_image",
            "images",
            "features",
            "status",
            "rejection_reason",
            "published_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "dealer_name",
            "status",
            "rejection_reason",
            "published_at",
            "created_at",
            "updated_at",
        ]

    def get_id(self, obj):
        return str(obj.pk)

    def validate_year(self, value):
        current_year = date.today().year

        if value < 1886 or value > current_year + 1:
            raise serializers.ValidationError(
                "Enter a valid vehicle manufacturing year."
            )

        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Vehicle price must be greater than zero."
            )

        return value

    def validate_km_driven(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Kilometres driven cannot be negative."
            )

        return value

    def validate_owner_count(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Owner count must be at least 1."
            )

        return value

    def validate_images(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Images must be provided as a list."
            )

        return value

    def validate_features(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Features must be provided as a list."
            )

        return value

    def create(self, validated_data):
        request = self.context.get("request")

        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError(
                "Authentication is required to create a vehicle listing."
            )

        dealer = DealerProfile.objects.filter(
            user=request.user,
            verification_status="approved",
            is_active=True,
        ).first()

        if dealer is None:
            raise serializers.ValidationError(
                "Only approved and active dealers can create vehicle listings."
            )

        return DealerVehicleListing.objects.create(
            dealer=dealer,
            status="pending_review",
            **validated_data
        )


class PublicDealerVehicleSerializer(serializers.ModelSerializer):

    id = serializers.SerializerMethodField()

    dealer_name = serializers.CharField(
        source="dealer.business_name",
        read_only=True
    )

    class Meta:
        model = DealerVehicleListing

        fields = [
            "id",
            "dealer_name",
            "title",
            "make",
            "model",
            "variant",
            "year",
            "fuel",
            "transmission",
            "body_type",
            "price",
            "km_driven",
            "owner_count",
            "color",
            "engine_cc",
            "seating_capacity",
            "description",
            "city",
            "state",
            "locality",
            "pincode",
            "primary_image",
            "images",
            "features",
            "published_at",
            "created_at",
        ]

        read_only_fields = fields

    def get_id(self, obj):
        return str(obj.pk)
