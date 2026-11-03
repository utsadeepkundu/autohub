
from rest_framework import serializers

from apps.used_cars.models import UsedCarListing


class UsedCarListingSerializer(serializers.ModelSerializer):
    """
    Serializer for public used-car listings.

    Converts MongoDB stored used-car records
    into JSON responses.
    """

    id = serializers.SerializerMethodField()

    class Meta:
        model = UsedCarListing

        fields = [
            "id",
            "used_car_id",

            # Vehicle information
            "title",
            "source_url",
            "make",
            "model",
            "model_name",
            "variant",
            "year",
            "fuel",
            "transmission",
            "body_type",

            # Pricing
            "price",
            "formatted_price",
            "market_price",
            "currency",

            # Running information
            "km_driven",
            "owner_count",
            "owner_slug",

            # Location
            "city",
            "city_slug",
            "city_id",
            "locality",

            # Seller
            "seller_type",

            # Images
            "primary_image",
            "images",

            # Additional features
            "emi",
            "trust_tags",
            "ai_tags",
            "ai_price_badge",
            "map_link",

            # Listing status
            "status_text",
            "is_active",

            # Timestamps
            "first_seen_at",
            "last_seen_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields

    def get_id(self, obj):
        """
        Convert MongoDB ObjectId into a JSON-safe string.
        """
        return str(obj.pk)
