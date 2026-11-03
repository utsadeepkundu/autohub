
from django.http import Http404
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.db.models import Q

from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from .models import DealerProfile, DealerVehicleListing
from .serializers import (
    DealerProfileSerializer,
    DealerVehicleListingSerializer,
    PublicDealerVehicleSerializer,
)

class DealerApplicationView(generics.CreateAPIView):
    """
    Submit a new dealer application.
    Requires JWT authentication.
    """

    queryset = DealerProfile.objects.all()
    serializer_class = DealerProfileSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]


class DealerProfileView(APIView):
    """
    Retrieve or update the logged-in user's own dealer profile.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, *args, **kwargs):
        dealer_profile = get_object_or_404(
            DealerProfile,
            user=request.user
        )

        serializer = DealerProfileSerializer(dealer_profile)

        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        dealer_profile = get_object_or_404(
            DealerProfile,
            user=request.user
        )

        serializer = DealerProfileSerializer(
            dealer_profile,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class DealerVehicleListingListCreateView(APIView):
    """
    List the logged-in dealer's vehicles or create a new listing.
    Only approved and active dealers can create listings.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, *args, **kwargs):
        dealer = DealerProfile.objects.filter(
            user=request.user
        ).first()

        if dealer is None:
            return Response([])

        listings = DealerVehicleListing.objects.filter(
            dealer=dealer
        ).order_by("-created_at")

        serializer = DealerVehicleListingSerializer(
            listings,
            many=True
        )

        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        dealer = DealerProfile.objects.filter(
            user=request.user,
            verification_status="approved",
            is_active=True,
        ).first()

        if dealer is None:
            return Response(
                {
                    "detail": (
                        "Only approved and active dealers "
                        "can create vehicle listings."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = DealerVehicleListingSerializer(
            data=request.data,
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


class DealerVehicleListingDetailView(APIView):
    """
    Retrieve or update a vehicle belonging to the logged-in dealer.
    Dealers cannot directly change listing status or delete listings.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_dealer_listing(self, request, pk):
        dealer = DealerProfile.objects.filter(
            user=request.user
        ).first()

        if dealer is None:
            raise Http404("Dealer profile not found.")

        return get_object_or_404(
            DealerVehicleListing,
            pk=pk,
            dealer=dealer
        )

    def get(self, request, pk, *args, **kwargs):
        listing = self.get_dealer_listing(request, pk)

        serializer = DealerVehicleListingSerializer(listing)

        return Response(serializer.data)

    def patch(self, request, pk, *args, **kwargs):
        listing = self.get_dealer_listing(request, pk)

        serializer = DealerVehicleListingSerializer(
            listing,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)

        # Any dealer edit requires administrator review again.
        serializer.save(
            status="pending_review",
            published_at=None,
            rejection_reason=""
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


def get_active_approved_dealer_ids():
    """
    Return IDs of approved and active dealers.
    """

    dealers = DealerProfile.objects.filter(
        verification_status="approved",
        is_active=True,
    )

    return [dealer.pk for dealer in dealers]


def parse_optional_integer(request, parameter):
    """
    Safely parse optional integer query parameters.
    """

    value = request.query_params.get(parameter)

    if value is None or value == "":
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"{parameter} must be a valid integer."
        )


class PublicVehiclePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class PublicMarketplaceVehicleListView(APIView):
    """
    Public marketplace vehicle listing API.

    Shows only published vehicles belonging to
    approved and active dealers.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):

        dealer_ids = get_active_approved_dealer_ids()

        if not dealer_ids:
            queryset = DealerVehicleListing.objects.none()
        else:
            queryset = DealerVehicleListing.objects.filter(
                status="published",
                dealer_id__in=dealer_ids,
            )

        # Text search
        search = request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(make__icontains=search)
                | Q(model__icontains=search)
                | Q(variant__icontains=search)
                | Q(city__icontains=search)
            )

        # Exact category filters
        for parameter in [
            "make",
            "model",
            "city",
            "fuel",
            "transmission",
            "body_type",
        ]:
            value = request.query_params.get(parameter)

            if value:
                queryset = queryset.filter(
                    **{f"{parameter}__iexact": value}
                )

        # Numeric filters
        try:
            min_price = parse_optional_integer(request, "min_price")
            max_price = parse_optional_integer(request, "max_price")
            min_year = parse_optional_integer(request, "min_year")
            max_year = parse_optional_integer(request, "max_year")

        except ValueError as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_400_BAD_REQUEST
            )

        if min_price is not None:
            if min_price < 0:
                return Response(
                    {"detail": "min_price cannot be negative."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            queryset = queryset.filter(price__gte=min_price)

        if max_price is not None:
            if max_price < 0:
                return Response(
                    {"detail": "max_price cannot be negative."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            queryset = queryset.filter(price__lte=max_price)

        if min_year is not None:
            queryset = queryset.filter(year__gte=min_year)

        if max_year is not None:
            queryset = queryset.filter(year__lte=max_year)

        if (
            min_price is not None
            and max_price is not None
            and min_price > max_price
        ):
            return Response(
                {"detail": "min_price cannot exceed max_price."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if (
            min_year is not None
            and max_year is not None
            and min_year > max_year
        ):
            return Response(
                {"detail": "min_year cannot exceed max_year."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Sorting
        allowed_ordering = [
            "price",
            "-price",
            "year",
            "-year",
            "km_driven",
            "-km_driven",
            "published_at",
            "-published_at",
        ]

        ordering = request.query_params.get(
            "ordering",
            "-published_at"
        )

        if ordering not in allowed_ordering:
            return Response(
                {"detail": "Invalid ordering parameter."},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = queryset.order_by(ordering)

        # Pagination
        paginator = PublicVehiclePagination()

        page = paginator.paginate_queryset(
            queryset,
            request,
            view=self
        )

        serializer = PublicDealerVehicleSerializer(
            page,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )


class PublicMarketplaceVehicleDetailView(APIView):
    """
    Public details of a single published vehicle.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, pk, *args, **kwargs):

        dealer_ids = get_active_approved_dealer_ids()

        if not dealer_ids:
            raise Http404("Vehicle listing not found.")

        listing = get_object_or_404(
            DealerVehicleListing.objects.filter(
                status="published",
                dealer_id__in=dealer_ids,
            ),
            pk=pk
        )

        serializer = PublicDealerVehicleSerializer(listing)

        return Response(serializer.data)


class PublicMarketplaceFilterOptionsView(APIView):
    """
    Return filter options based only on publicly visible vehicles.
    No JWT authentication required.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get_distinct_values(self, queryset, field_name):
        return list(
            queryset
            .exclude(**{f"{field_name}__isnull": True})
            .exclude(**{field_name: ""})
            .order_by(field_name)
            .values_list(field_name, flat=True)
            .distinct()
        )

    def get(self, request, *args, **kwargs):

        dealer_ids = get_active_approved_dealer_ids()

        if not dealer_ids:
            queryset = DealerVehicleListing.objects.none()
        else:
            queryset = DealerVehicleListing.objects.filter(
                status="published",
                dealer_id__in=dealer_ids,
            )

        min_price = (
            queryset.order_by("price")
            .values_list("price", flat=True)
            .first()
        )

        max_price = (
            queryset.order_by("-price")
            .values_list("price", flat=True)
            .first()
        )

        options = {
            "total_listings": queryset.count(),

            "makes": self.get_distinct_values(queryset, "make"),
            "models": self.get_distinct_values(queryset, "model"),
            "cities": self.get_distinct_values(queryset, "city"),
            "fuels": self.get_distinct_values(queryset, "fuel"),
            "transmissions": self.get_distinct_values(
                queryset, "transmission"
            ),
            "body_types": self.get_distinct_values(
                queryset, "body_type"
            ),

            "years": list(
                queryset
                .values_list("year", flat=True)
                .distinct()
                .order_by("-year")
            ),

            "price_range": {
                "min": min_price,
                "max": max_price,
            },
        }

        return Response(options)
