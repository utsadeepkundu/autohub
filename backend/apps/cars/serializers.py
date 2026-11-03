
from rest_framework import serializers

from .models import CarBrand, CarModel, CarVariant


class CarBrandSerializer(serializers.ModelSerializer):

    id = serializers.SerializerMethodField()

    class Meta:
        model = CarBrand

        fields = [
            "id",
            "name",
            "slug",
            "logo_url",
        ]

        read_only_fields = fields

    def get_id(self, obj):
        return str(obj.pk)


class CarModelListSerializer(serializers.ModelSerializer):

    id = serializers.SerializerMethodField()

    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = CarModel

        fields = [
            "id",
            "brand_name",
            "name",
            "slug",
            "price_range",
            "rating",
            "review_count",
            "primary_image",
        ]

        read_only_fields = fields

    def get_id(self, obj):
        return str(obj.pk)

    def get_primary_image(self, obj):

        images = obj.images

        if not isinstance(images, dict):
            return None

        exterior_images = images.get("exteriorimages", [])

        if not isinstance(exterior_images, list):
            return None

        for image in exterior_images:

            if not isinstance(image, dict):
                continue

            image_url = (
                image.get("imageUrl")
                or image.get("webpImage")
                or image.get("image")
            )

            if image_url:
                return image_url

        return None


class CarModelDetailSerializer(serializers.ModelSerializer):

    id = serializers.SerializerMethodField()

    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = CarModel

        fields = [
            "id",
            "brand_name",
            "name",
            "slug",
            "price_range",
            "rating",
            "review_count",
            "mileage_data",
            "images",
            "primary_image",
            "key_specs",
            "city_prices",
        ]

        read_only_fields = fields

    def get_id(self, obj):
        return str(obj.pk)

    def get_primary_image(self, obj):

        images = obj.images

        if not isinstance(images, dict):
            return None

        exterior_images = images.get("exteriorimages", [])

        if not isinstance(exterior_images, list):
            return None

        for image in exterior_images:

            if not isinstance(image, dict):
                continue

            image_url = (
                image.get("imageUrl")
                or image.get("webpImage")
                or image.get("image")
            )

            if image_url:
                return image_url

        return None


class CarVariantSerializer(serializers.ModelSerializer):

    id = serializers.SerializerMethodField()

    class Meta:
        model = CarVariant

        fields = [
            "id",
            "brand_name",
            "model_name",
            "model_slug",
            "name",
            "short_name",
            "slug",
            "source_url",
            "ex_showroom_price",
            "ex_showroom_formatted",
            "on_road_price",
            "on_road_formatted",
            "pricing_city",
            "fuel",
            "transmission",
            "engine_displacement_cc",
            "mileage_arai",
            "body_type",
            "summary",
            "specs",
            "key_features",
            "missing_features",
            "images",
            "tag",
            "status",
            "waiting_period",
        ]

        read_only_fields = fields

    def get_id(self, obj):
        return str(obj.pk)
