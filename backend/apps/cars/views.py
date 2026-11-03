
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from typing import Any

from bson import ObjectId

from .models import CarBrand, CarModel, CarVariant
from .serializers import (
    CarBrandSerializer,
    CarModelListSerializer,
    CarModelDetailSerializer,
    CarVariantSerializer,
)


def paginate_catalogue(queryset, serializer_class, request):
    """
    Paginate catalogue results without GenericAPIView
    or PageNumberPagination typing conflicts.
    """

    try:
        page = int(request.query_params.get("page", "1"))
        page_size = int(request.query_params.get("page_size", "20"))

    except (TypeError, ValueError):
        return Response(
            {"detail": "Page and page_size must be valid integers."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if page < 1 or page_size < 1:
        return Response(
            {"detail": "Page and page_size must be positive integers."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    page_size = min(page_size, 100)

    total_count = queryset.count()
    total_pages = (
        (total_count + page_size - 1) // page_size
        if total_count else 0
    )

    start = (page - 1) * page_size
    end = start + page_size

    items = queryset[start:end]

    serializer = serializer_class(
        items,
        many=True,
    )

    return Response({
        "count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "next_page": page + 1 if page < total_pages else None,
        "previous_page": page - 1 if page > 1 and total_pages else None,
        "results": serializer.data,
    })


class CarBrandListView(APIView):
    """
    Return all active car manufacturers.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):

        brands = CarBrand.objects.filter(
            is_active=True
        ).order_by("name")

        serializer = CarBrandSerializer(
            brands,
            many=True,
        )

        return Response(serializer.data)


class CarBrandModelListView(APIView):
    """
    Return all active models belonging to a manufacturer.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, brand_slug, *args, **kwargs):

        brand = get_object_or_404(
            CarBrand.objects.filter(is_active=True),
            slug=brand_slug,
        )

        models = CarModel.objects.filter(
            brand_source_slug=brand.source_slug,
            is_active=True,
        ).order_by("name")

        return paginate_catalogue(
            models,
            CarModelListSerializer,
            request,
        )


class CarModelDetailView(APIView):
    """
    Return detailed information about a specific car model.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, brand_slug, model_slug, *args, **kwargs):

        brand = get_object_or_404(
            CarBrand.objects.filter(is_active=True),
            slug=brand_slug,
        )

        car_model = get_object_or_404(
            CarModel.objects.filter(
                brand_source_slug=brand.source_slug,
                is_active=True,
            ),
            slug=model_slug,
        )

        serializer = CarModelDetailSerializer(car_model)

        return Response(serializer.data)


class CarModelVariantListView(APIView):
    """
    Return available variants of a particular car model.

    Supports fuel, transmission, body type, pricing city
    and ex-showroom price filters.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, brand_slug, model_slug, *args, **kwargs):

        brand = get_object_or_404(
            CarBrand.objects.filter(is_active=True),
            slug=brand_slug,
        )

        car_model = get_object_or_404(
            CarModel.objects.filter(
                brand_source_slug=brand.source_slug,
                is_active=True,
            ),
            slug=model_slug,
        )

        variants = CarVariant.objects.filter(
            model_external_id=car_model.external_id,
            is_active=True,
        )

        # Exact categorical filters
        for parameter in (
            "fuel",
            "transmission",
            "body_type",
            "pricing_city",
        ):
            value = request.query_params.get(parameter)

            if value:
                variants = variants.filter(
                    **{f"{parameter}__iexact": value.strip()}
                )

        # Price filters use ex-showroom price.
        try:
            min_price = request.query_params.get("min_price")
            max_price = request.query_params.get("max_price")

            min_price_value = (
                int(min_price) if min_price not in (None, "") else None
            )

            max_price_value = (
                int(max_price) if max_price not in (None, "") else None
            )

        except (TypeError, ValueError):
            return Response(
                {"detail": "Price filters must be valid integers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if min_price_value is not None and min_price_value < 0:
            return Response(
                {"detail": "Minimum price cannot be negative."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if max_price_value is not None and max_price_value < 0:
            return Response(
                {"detail": "Maximum price cannot be negative."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            min_price_value is not None
            and max_price_value is not None
            and min_price_value > max_price_value
        ):
            return Response(
                {"detail": "Minimum price cannot exceed maximum price."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if min_price_value is not None:
            variants = variants.filter(
                ex_showroom_price__gte=min_price_value
            )

        if max_price_value is not None:
            variants = variants.filter(
                ex_showroom_price__lte=max_price_value
            )

        # Sorting
        ordering_options = {
            "price": "ex_showroom_price",
            "-price": "-ex_showroom_price",
            "name": "name",
            "-name": "-name",
        }

        ordering = request.query_params.get(
            "ordering",
            "price",
        )

        if ordering not in ordering_options:
            return Response(
                {"detail": "Invalid variant ordering parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        variants = variants.order_by(
            ordering_options[ordering]
        )

        return paginate_catalogue(
            variants,
            CarVariantSerializer,
            request,
        )


class CarVariantDetailView(APIView):
    """
    Return full information about an individual car variant.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(
        self,
        request,
        brand_slug,
        model_slug,
        variant_slug,
        *args,
        **kwargs
    ):

        brand = get_object_or_404(
            CarBrand.objects.filter(is_active=True),
            slug=brand_slug,
        )

        car_model = get_object_or_404(
            CarModel.objects.filter(
                brand_source_slug=brand.source_slug,
                is_active=True,
            ),
            slug=model_slug,
        )

        variant = get_object_or_404(
            CarVariant.objects.filter(
                model_external_id=car_model.external_id,
                is_active=True,
            ),
            slug=variant_slug,
        )

        serializer = CarVariantSerializer(variant)

        return Response(serializer.data)


class CarCatalogueSearchView(APIView):
    """
    Search active new-car models and their manufacturers.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):

        search_query = request.query_params.get("q", "").strip()

        if not search_query:
            return Response(
                {"detail": "Search query parameter 'q' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        matching_models = CarModel.objects.filter(
            Q(name__icontains=search_query)
            | Q(brand_name__icontains=search_query),
            is_active=True,
        ).order_by("brand_name", "name")

        return paginate_catalogue(
            matching_models,
            CarModelListSerializer,
            request,
        )

def build_price_comparison(
    variants: list[CarVariant],
    price_field: str,
    require_same_city: bool = False,
) -> dict[str, Any]:
    """
    Compare prices across selected variants.

    On-road comparisons require all variants to have prices
    from the same pricing city.
    """

    price_records: list[tuple[CarVariant, int]] = []

    for variant in variants:
        price = getattr(variant, price_field, None)

        if isinstance(price, int):
            price_records.append((variant, price))

    if len(price_records) != len(variants):
        return {
            "comparable": False,
            "lowest": None,
            "highest": None,
            "difference": None,
            "pricing_city": None,
            "reason": "Price information is unavailable for one or more variants.",
        }

    if require_same_city:
        cities = {
            variant.pricing_city.strip().casefold()
            for variant, price in price_records
        }

        if len(cities) != 1 or "" in cities:
            return {
                "comparable": False,
                "lowest": None,
                "highest": None,
                "difference": None,
                "pricing_city": None,
                "reason": (
                    "On-road prices can only be compared when "
                    "all variants have pricing information for "
                    "the same city."
                ),
            }

    lowest_variant, lowest_price = min(
        price_records,
        key=lambda item: item[1],
    )

    highest_variant, highest_price = max(
        price_records,
        key=lambda item: item[1],
    )

    return {
        "comparable": True,
        "lowest": {
            "variant_id": str(lowest_variant.pk),
            "variant_name": lowest_variant.name,
            "price": lowest_price,
        },
        "highest": {
            "variant_id": str(highest_variant.pk),
            "variant_name": highest_variant.name,
            "price": highest_price,
        },
        "difference": highest_price - lowest_price,
        "pricing_city": (
            lowest_variant.pricing_city
            if require_same_city
            else None
        ),
        "reason": None,
    }


class CarVariantComparisonView(APIView):
    """
    Compare 2 or 3 active car variants.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):

        payload = request.data

        if not isinstance(payload, dict):
            return Response(
                {"detail": "Request body must be a JSON object."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_variant_ids = payload.get("variant_ids")

        if (
            not isinstance(raw_variant_ids, list)
            or len(raw_variant_ids) < 2
            or len(raw_variant_ids) > 3
        ):
            return Response(
                {
                    "detail": (
                        "Provide between 2 and 3 variant IDs "
                        "in the variant_ids list."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        variant_ids: list[str] = []

        for variant_id in raw_variant_ids:

            if not isinstance(variant_id, str):
                return Response(
                    {"detail": "Every variant ID must be a string."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cleaned_id = variant_id.strip()

            if not ObjectId.is_valid(cleaned_id):
                return Response(
                    {"detail": "One or more variant IDs are invalid."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            variant_ids.append(cleaned_id)

        if len(set(variant_ids)) != len(variant_ids):
            return Response(
                {"detail": "Duplicate variant IDs are not allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        object_ids = [
            ObjectId(variant_id)
            for variant_id in variant_ids
        ]

        found_variants = CarVariant.objects.filter(
            pk__in=object_ids,
            is_active=True,
        )

        variants_by_id: dict[str, CarVariant] = {
            str(variant.pk): variant
            for variant in found_variants
        }

        missing_ids = [
            variant_id
            for variant_id in variant_ids
            if variant_id not in variants_by_id
        ]

        if missing_ids:
            return Response(
                {
                    "detail": (
                        "One or more variants were not found "
                        "or are inactive."
                    ),
                    "missing_variant_ids": missing_ids,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Preserve the same order in which the user selected variants.
        selected_variants = [
            variants_by_id[variant_id]
            for variant_id in variant_ids
        ]

        variant_serializer = CarVariantSerializer(
            selected_variants,
            many=True,
        )

        price_comparison = {
            "ex_showroom": build_price_comparison(
                selected_variants,
                "ex_showroom_price",
            ),
            "on_road": build_price_comparison(
                selected_variants,
                "on_road_price",
                require_same_city=True,
            ),
        }

        return Response(
            {
                "variant_count": len(selected_variants),
                "variants": variant_serializer.data,
                "price_comparison": price_comparison,
            },
            status=status.HTTP_200_OK,
        )