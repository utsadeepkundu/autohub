
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.dealers.models import DealerProfile

from .models import CustomerEnquiry
from .serializers import (
    CustomerEnquirySerializer,
    DealerEnquirySerializer,
    DealerEnquiryUpdateSerializer,
)


def get_authenticated_dealer(user):
    """
    Return the approved and active dealer
    associated with the authenticated user.
    """

    dealer = DealerProfile.objects.filter(
        user=user,
        verification_status="approved",
        is_active=True,
    ).first()

    if dealer is None:
        raise PermissionDenied(
            "Only approved and active dealers can access enquiries."
        )

    return dealer


class CustomerEnquiryCreateView(APIView):
    """
    Public API for submitting vehicle enquiries.

    Guest customers can submit enquiries without registration.
    Registered customers can optionally authenticate using JWT.
    """

    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]
    throttle_scope = "enquiry_create"

    def post(self, request, *args, **kwargs):

        serializer = CustomerEnquirySerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        enquiry = serializer.save()

        response_serializer = CustomerEnquirySerializer(enquiry)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class DealerEnquiryListView(APIView):
    """
    Return enquiries belonging exclusively
    to the authenticated dealer.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, *args, **kwargs):

        dealer = get_authenticated_dealer(request.user)

        enquiries = CustomerEnquiry.objects.filter(
            dealer=dealer
        ).order_by("-created_at")

        serializer = DealerEnquirySerializer(
            enquiries,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class DealerEnquiryDetailView(APIView):
    """
    Retrieve or update an individual dealer enquiry.

    Dealers can only access enquiries assigned to them.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_dealer_enquiry(self, request, pk):

        dealer = get_authenticated_dealer(request.user)

        return get_object_or_404(
            CustomerEnquiry,
            pk=pk,
            dealer=dealer,
        )

    def get(self, request, pk, *args, **kwargs):

        enquiry = self.get_dealer_enquiry(request, pk)

        serializer = DealerEnquirySerializer(enquiry)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk, *args, **kwargs):

        enquiry = self.get_dealer_enquiry(request, pk)

        serializer = DealerEnquiryUpdateSerializer(
            enquiry,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)

        save_kwargs = {}

        # Use request.data instead of serializer.validated_data.get()
        # to avoid the Pylance type-inference issue.
        if request.data.get("status") == "contacted":
            save_kwargs["last_contacted_at"] = timezone.now()

        serializer.save(**save_kwargs)

        # Return the complete dealer-facing enquiry.
        response_serializer = DealerEnquirySerializer(enquiry)

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )
