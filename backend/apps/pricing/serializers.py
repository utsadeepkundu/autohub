
from datetime import date

from rest_framework import serializers

from .models import VehicleValuation


class VehicleValuationRequestSerializer(serializers.Serializer):

    make = serializers.CharField(
        max_length=150,
        trim_whitespace=True,
    )

    model = serializers.CharField(
        max_length=180,
        trim_whitespace=True,
    )

    year = serializers.IntegerField()

    fuel = serializers.CharField(
        max_length=50,
        trim_whitespace=True,
    )

    transmission = serializers.CharField(
        max_length=50,
        trim_whitespace=True,
    )

    km_driven = serializers.IntegerField(
        min_value=0,
    )

    city = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default="",
        trim_whitespace=True,
    )

    def validate_make(self, value):
        if not value:
            raise serializers.ValidationError(
                "Vehicle manufacturer is required."
            )

        return value

    def validate_model(self, value):
        if not value:
            raise serializers.ValidationError(
                "Vehicle model is required."
            )

        return value

    def validate_year(self, value):

        current_year = date.today().year

        if value < 1886 or value > current_year + 1:
            raise serializers.ValidationError(
                "Enter a valid vehicle manufacturing year."
            )

        return value

    def validate_fuel(self, value):
        if not value:
            raise serializers.ValidationError(
                "Fuel type is required."
            )

        return value

    def validate_transmission(self, value):
        if not value:
            raise serializers.ValidationError(
                "Transmission type is required."
            )

        return value


class VehicleValuationHistorySerializer(serializers.ModelSerializer):

    id = serializers.SerializerMethodField()

    class Meta:
        model = VehicleValuation

        fields = [
            "id",
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
        ]

        read_only_fields = fields

    def get_id(self, obj):
        return str(obj.pk)
