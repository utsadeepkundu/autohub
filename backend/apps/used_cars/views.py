
from rest_framework import filters
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from django_filters.rest_framework import DjangoFilterBackend

from apps.used_cars.models import UsedCarListing

from apps.used_cars.serializers import UsedCarListingSerializer
from apps.used_cars.filters import UsedCarFilter


class UsedCarPagination(PageNumberPagination):
    """
    Pagination configuration for used-car listings.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class UsedCarListView(ListAPIView):
    """
    GET /api/used-cars/

    Returns active used-car listings.

    Supports:
        - Manufacturer filtering
        - Model filtering
        - Location filtering
        - Price filtering
        - Year filtering
        - Kilometres-driven filtering
        - Fuel and transmission filtering
        - Keyword search
        - Sorting
        - Pagination
    """

    queryset = UsedCarListing.objects.filter(
        is_active=True
    )

    serializer_class = UsedCarListingSerializer

    permission_classes = [AllowAny]

    pagination_class = UsedCarPagination

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_class = UsedCarFilter

    search_fields = [
        "title",
        "make",
        "model",
        "model_name",
        "variant",
        "city",
        "locality",
    ]

    ordering_fields = [
        "price",
        "year",
        "km_driven",
        "created_at",
        "last_seen_at",
    ]

    ordering = ["-last_seen_at"]


class UsedCarDetailView(RetrieveAPIView):
    """
    GET /api/used-cars/<id>/

    Returns complete public details
    of one active used-car listing.
    """

    queryset = UsedCarListing.objects.filter(
        is_active=True
    )

    serializer_class = UsedCarListingSerializer

    permission_classes = [AllowAny]

    lookup_field = "pk"


class UsedCarFilterOptionsView(APIView):
    """
    GET /api/used-cars/filters/

    Returns available filter options
    from active database records.
    """

    permission_classes = [AllowAny]

    def get(self, request):

        queryset = UsedCarListing.objects.filter(
            is_active=True
        )

        def get_options(field_name):
            values = queryset.values_list(
                field_name,
                flat=True,
            )

            unique_values = {
                value
                for value in values
                if value is not None and value != ""
            }

            return sorted(
                unique_values,
                key=lambda value: str(value).lower(),
            )

        prices = [
            price
            for price in queryset.values_list(
                "price",
                flat=True,
            )
            if price is not None
        ]

        years = {
            year
            for year in queryset.values_list(
                "year",
                flat=True,
            )
            if year is not None
        }

        response_data = {
            "success": True,

            "total_listings": queryset.count(),

            # Manufacturer and model
            "makes": get_options("make"),
            "models": get_options("model_name"),

            # Location
            "cities": get_options("city"),
            "city_slugs": get_options("city_slug"),
            "localities": get_options("locality"),

            # Vehicle specifications
            "fuels": get_options("fuel"),
            "transmissions": get_options("transmission"),
            "body_types": get_options("body_type"),

            # Seller and ownership
            "seller_types": get_options("seller_type"),
            "owner_options": get_options("owner_count"),

            # Manufacturing years
            "years": sorted(
                years,
                reverse=True,
            ),

            # Price range
            "price_range": {
                "minimum": min(prices) if prices else None,
                "maximum": max(prices) if prices else None,
            },
        }

        return Response(response_data)
