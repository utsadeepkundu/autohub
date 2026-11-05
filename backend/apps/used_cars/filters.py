
import django_filters
from django.db.models import Q

from apps.used_cars.models import UsedCarListing


class UsedCarFilter(django_filters.FilterSet):
    """
    Advanced filters for used-car listings.
    """

    # Manufacturer and model
    make = django_filters.CharFilter(
        field_name="make",
        lookup_expr="iexact",
    )

    model = django_filters.CharFilter(
        method="filter_model",
    )

    # Location
    city = django_filters.CharFilter(
        method="filter_city",
    )

    locality = django_filters.CharFilter(
        field_name="locality",
        lookup_expr="icontains",
    )

    # Price range
    min_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="gte",
    )

    max_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="lte",
    )

    # Manufacturing year
    min_year = django_filters.NumberFilter(
        field_name="year",
        lookup_expr="gte",
    )

    max_year = django_filters.NumberFilter(
        field_name="year",
        lookup_expr="lte",
    )

    # Kilometres driven
    min_km = django_filters.NumberFilter(
        field_name="km_driven",
        lookup_expr="gte",
    )

    max_km = django_filters.NumberFilter(
        field_name="km_driven",
        lookup_expr="lte",
    )

    # Vehicle specifications
    fuel = django_filters.CharFilter(
        field_name="fuel",
        lookup_expr="iexact",
    )

    transmission = django_filters.CharFilter(
        field_name="transmission",
        lookup_expr="iexact",
    )

    body_type = django_filters.CharFilter(
        field_name="body_type",
        lookup_expr="iexact",
    )

    # Seller and ownership
    seller_type = django_filters.CharFilter(
        field_name="seller_type",
        lookup_expr="iexact",
    )

    owner_count = django_filters.NumberFilter(
        field_name="owner_count",
        lookup_expr="exact",
    )

    def filter_city(self, queryset, name, value):
        """Accept either the readable city name or its source slug."""
        cleaned = str(value or "").strip()
        return queryset.filter(
            Q(city__iexact=cleaned)
            | Q(city_slug__iexact=cleaned)
        )

    def filter_model(self, queryset, name, value):
        """
        Search both model slug and readable model name.
        """
        return queryset.filter(
            Q(model__icontains=value)
            | Q(model_name__icontains=value)
        )

    class Meta:
        model = UsedCarListing

        fields = [
            "make",
            "model",
            "city",
            "locality",
            "min_price",
            "max_price",
            "min_year",
            "max_year",
            "min_km",
            "max_km",
            "fuel",
            "transmission",
            "body_type",
            "seller_type",
            "owner_count",
        ]
