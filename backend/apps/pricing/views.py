
from math import ceil
from typing import Any, cast

from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import VehicleValuation
from .serializers import (
    VehicleValuationRequestSerializer,
    VehicleValuationHistorySerializer,
)
from .services.valuation import estimate_vehicle_price


class VehicleValuationEstimateView(APIView):
    """
    Public vehicle valuation API.

    Guest users can calculate an estimate.
    Authenticated customers also get their valuation saved
    in MongoDB as personal history.
    """

    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]
    throttle_scope = "valuation_estimate"

    def post(self, request, *args, **kwargs):

        request_serializer = VehicleValuationRequestSerializer(
            data=request.data
        )

        request_serializer.is_valid(
            raise_exception=True
        )

        # Explicit typing prevents Pylance serializer inference errors.
        data = cast(
            dict[str, Any],
            request_serializer.validated_data
        )

        try:
            result = estimate_vehicle_price(
                make=data["make"],
                model=data["model"],
                year=data["year"],
                fuel=data["fuel"],
                transmission=data["transmission"],
                km_driven=data["km_driven"],
                city=data.get("city", ""),
            )

        except ValueError as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Explicitly type the valuation result.
        result = cast(dict[str, Any], result)

        response_data = dict(result)
        response_data["valuation_id"] = None

        # Save valuation history for authenticated users only.
        if request.user.is_authenticated:

            price_range = result.get("price_range")

            minimum_price = None
            maximum_price = None

            if isinstance(price_range, dict):
                minimum_price = price_range.get("lower")
                maximum_price = price_range.get("upper")

            valuation = VehicleValuation.objects.create(
                user=request.user,
                make=data["make"],
                model=data["model"],
                year=data["year"],
                fuel=data["fuel"],
                transmission=data["transmission"],
                km_driven=data["km_driven"],
                city=data.get("city", ""),
                estimated_price=result.get("estimated_price"),
                minimum_price=minimum_price,
                maximum_price=maximum_price,
                comparable_count=result.get(
                    "comparable_count", 0
                ),
                confidence=result.get(
                    "confidence", "insufficient"
                ),
                comparison_scope=result.get(
                    "comparison_scope", ""
                ),
                valuation_status=result["status"],
                result_data=result,
            )

            response_data["valuation_id"] = str(
                valuation.pk
            )

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )


class VehicleValuationHistoryView(APIView):
    """
    Return valuation history belonging to the authenticated user.

    Pagination is handled manually to avoid Pylance conflicts
    with PageNumberPagination configuration.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

    def get(self, request, *args, **kwargs):

        valuations = VehicleValuation.objects.filter(
            user=request.user
        ).order_by("-created_at")

        # Read pagination parameters.
        page_value = request.query_params.get("page", "1")
        page_size_value = request.query_params.get(
            "page_size",
            str(self.DEFAULT_PAGE_SIZE),
        )

        try:
            page = int(page_value)
            page_size = int(page_size_value)

        except (TypeError, ValueError):
            return Response(
                {
                    "detail": (
                        "Page and page_size must be valid integers."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if page < 1:
            return Response(
                {"detail": "Page must be at least 1."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if page_size < 1:
            return Response(
                {"detail": "Page size must be at least 1."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Enforce maximum page size.
        page_size = min(
            page_size,
            self.MAX_PAGE_SIZE,
        )

        total_count = valuations.count()

        total_pages = ceil(
            total_count / page_size
        ) if total_count else 0

        start = (page - 1) * page_size
        end = start + page_size

        page_items = valuations[start:end]

        serializer = VehicleValuationHistorySerializer(
            page_items,
            many=True,
        )

        return Response(
            {
                "count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "next_page": (
                    page + 1
                    if page < total_pages
                    else None
                ),
                "previous_page": (
                    page - 1
                    if page > 1 and total_pages
                    else None
                ),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class VehicleValuationDetailView(APIView):
    """
    Retrieve an individual valuation belonging
    exclusively to the authenticated customer.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, pk, *args, **kwargs):

        valuation = get_object_or_404(
            VehicleValuation,
            pk=pk,
            user=request.user,
        )

        serializer = VehicleValuationHistorySerializer(
            valuation
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
