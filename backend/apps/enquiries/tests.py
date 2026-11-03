from typing import Any, Protocol, cast

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.dealers.models import DealerProfile, DealerVehicleListing

from .models import CustomerEnquiry


ENQUIRY_URL = "/api/enquiries/"
DEALER_ENQUIRY_URL = "/api/enquiries/dealer/"


class APIResponse(Protocol):
    """Typing interface for responses returned by the DRF test client."""

    status_code: int
    data: Any


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"]
)
class CustomerEnquiryAPITests(APITestCase):
    """Automated tests for customer enquiries and dealer lead management."""

    @property
    def api_client(self) -> APIClient:
        return cast(APIClient, self.client)

    def api_get(self, path: str) -> APIResponse:
        response = self.api_client.get(path)
        return cast(APIResponse, response)

    def api_post(
        self,
        path: str,
        data: dict[str, Any],
    ) -> APIResponse:
        response = self.api_client.post(
            path,
            data,
            format="json",
        )
        return cast(APIResponse, response)

    def api_patch(
        self,
        path: str,
        data: dict[str, Any],
    ) -> APIResponse:
        response = self.api_client.patch(
            path,
            data,
            format="json",
        )
        return cast(APIResponse, response)

    @staticmethod
    def get_response_data(response: APIResponse) -> Any:
        return response.data

    def setUp(self):
        super().setUp()

        # Clear cached DRF throttle counters before each test.
        # This prevents one test's requests from affecting another.
        cache.clear()

        user_model = get_user_model()

        # Customer account
        self.customer = user_model.objects.create_user(
            username="enquiry-customer",
            email="customer@example.com",
            password="Strong-Test-Password-123!",
        )

        # Primary dealer account
        self.dealer_user = user_model.objects.create_user(
            username="enquiry-dealer",
            email="dealer@example.com",
            password="Strong-Test-Password-123!",
        )

        self.dealer = self.create_dealer(
            user=self.dealer_user,
            business_name="AutoHub Test Motors",
            verification_status="approved",
            is_active=True,
        )

        # Published vehicle belonging to the primary dealer
        self.vehicle = self.create_vehicle(
            dealer=self.dealer,
            status="published",
        )

    def create_dealer(
        self,
        user: Any,
        business_name: str,
        verification_status: str = "approved",
        is_active: bool = True,
    ) -> DealerProfile:

        return DealerProfile.objects.create(
            user=user,
            business_name=business_name,
            contact_person="Test Dealer",
            email=user.email,
            phone="9876543210",
            address_line1="Test Business Address",
            city="Kolkata",
            state="West Bengal",
            pincode="700001",
            verification_status=verification_status,
            is_active=is_active,
        )

    def create_vehicle(
        self,
        dealer: DealerProfile,
        status: str = "published",
        **overrides: Any,
    ) -> DealerVehicleListing:

        fields: dict[str, Any] = {
            "dealer": dealer,
            "title": "2018 Maruti Suzuki Swift VXi",
            "make": "Maruti Suzuki",
            "model": "Swift",
            "variant": "VXi",
            "year": 2018,
            "fuel": "Petrol",
            "transmission": "Manual",
            "body_type": "Hatchback",
            "price": 450000,
            "km_driven": 45000,
            "owner_count": 1,
            "city": "Kolkata",
            "state": "West Bengal",
            "status": status,
        }

        fields.update(overrides)

        return DealerVehicleListing.objects.create(**fields)

    def create_enquiry(
        self,
        vehicle: DealerVehicleListing,
        customer_name: str = "Test Customer",
        **overrides: Any,
    ) -> CustomerEnquiry:

        fields: dict[str, Any] = {
            "vehicle": vehicle,
            "dealer": vehicle.dealer,
            "customer_name": customer_name,
            "phone": "9876543210",
            "email": "customer@example.com",
            "message": "I am interested in this vehicle.",
            "preferred_contact_method": "phone",
            "consent_to_contact": True,
            "status": "new",
        }

        fields.update(overrides)

        return CustomerEnquiry.objects.create(**fields)

    def authenticate_user(self, user: Any) -> None:
        access_token = AccessToken.for_user(user)

        self.api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

    def get_enquiry_payload(
        self,
        vehicle: DealerVehicleListing | None = None,
        **overrides: Any,
    ) -> dict[str, Any]:

        selected_vehicle = vehicle or self.vehicle

        payload: dict[str, Any] = {
            "vehicle_id": str(selected_vehicle.pk),
            "customer_name": "Test Customer",
            "phone": "9876543210",
            "email": "customer@example.com",
            "message": "I am interested in this vehicle.",
            "preferred_contact_method": "phone",
            "consent_to_contact": True,
        }

        payload.update(overrides)

        return payload

    def create_other_dealer_and_vehicle(
        self,
    ) -> tuple[Any, DealerProfile, DealerVehicleListing]:

        user_model = get_user_model()

        other_user = user_model.objects.create_user(
            username="other-enquiry-dealer",
            email="otherdealer@example.com",
            password="Strong-Test-Password-123!",
        )

        other_dealer = self.create_dealer(
            user=other_user,
            business_name="Other AutoHub Motors",
        )

        other_vehicle = self.create_vehicle(
            dealer=other_dealer,
            title="2019 Hyundai i20 Sportz",
            make="Hyundai",
            model="i20",
        )

        return other_user, other_dealer, other_vehicle

    # ---------------------------------------------------------
    # CUSTOMER ENQUIRY SUBMISSION TESTS
    # ---------------------------------------------------------

    def test_guest_can_submit_enquiry(self):
        """Guest customers can submit enquiries without registration."""

        response = self.api_post(
            ENQUIRY_URL,
            self.get_enquiry_payload(),
        )

        data = self.get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            data["customer_name"],
            "Test Customer",
        )

        self.assertEqual(
            data["vehicle_title"],
            self.vehicle.title,
        )

        self.assertEqual(
            data["dealer_name"],
            self.dealer.business_name,
        )

        enquiry = CustomerEnquiry.objects.get(
            pk=data["id"]
        )

        self.assertIsNone(enquiry.customer_user)
        self.assertEqual(enquiry.dealer, self.dealer)
        self.assertEqual(enquiry.status, "new")

    def test_authenticated_customer_can_submit_enquiry(self):
        """Registered customers are associated with their enquiry."""

        self.authenticate_user(self.customer)

        response = self.api_post(
            ENQUIRY_URL,
            self.get_enquiry_payload(),
        )

        data = self.get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        enquiry = CustomerEnquiry.objects.get(
            pk=data["id"]
        )

        self.assertEqual(
            enquiry.customer_user,
            self.customer,
        )

        self.assertEqual(enquiry.dealer, self.dealer)

    def test_enquiry_requires_contact_consent(self):
        """An enquiry without consent must be rejected."""

        response = self.api_post(
            ENQUIRY_URL,
            self.get_enquiry_payload(
                consent_to_contact=False,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "consent_to_contact",
            self.get_response_data(response),
        )

        self.assertEqual(
            CustomerEnquiry.objects.count(),
            0,
        )

    def test_enquiry_rejects_invalid_phone(self):
        """Invalid customer phone numbers must be rejected."""

        response = self.api_post(
            ENQUIRY_URL,
            self.get_enquiry_payload(
                phone="invalid-phone",
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "phone",
            self.get_response_data(response),
        )

        self.assertEqual(
            CustomerEnquiry.objects.count(),
            0,
        )

    def test_email_contact_method_requires_email(self):
        """Email must be supplied when email is the preferred method."""

        response = self.api_post(
            ENQUIRY_URL,
            self.get_enquiry_payload(
                email="",
                preferred_contact_method="email",
            ),
        )

        data = self.get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn("email", data)

        self.assertEqual(
            CustomerEnquiry.objects.count(),
            0,
        )

    def test_unpublished_vehicle_cannot_receive_enquiry(self):
        """Customers cannot enquire about unpublished vehicles."""

        unpublished_vehicle = self.create_vehicle(
            dealer=self.dealer,
            status="pending_review",
        )

        response = self.api_post(
            ENQUIRY_URL,
            self.get_enquiry_payload(
                vehicle=unpublished_vehicle,
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "vehicle_id",
            self.get_response_data(response),
        )

        self.assertEqual(
            CustomerEnquiry.objects.count(),
            0,
        )

    def test_inactive_dealer_vehicle_cannot_receive_enquiry(self):
        """Published listings of inactive dealers are unavailable."""

        self.dealer.is_active = False
        self.dealer.save(update_fields=["is_active"])

        response = self.api_post(
            ENQUIRY_URL,
            self.get_enquiry_payload(),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "vehicle_id",
            self.get_response_data(response),
        )

        self.assertEqual(
            CustomerEnquiry.objects.count(),
            0,
        )

    # ---------------------------------------------------------
    # DEALER ENQUIRY ACCESS TESTS
    # ---------------------------------------------------------

    def test_dealer_inbox_requires_authentication(self):
        """Unauthenticated users cannot access the dealer inbox."""

        response = self.api_get(DEALER_ENQUIRY_URL)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_pending_dealer_cannot_access_enquiries(self):
        """Only approved and active dealers can access enquiries."""

        user_model = get_user_model()

        pending_user = user_model.objects.create_user(
            username="pending-enquiry-dealer",
            email="pendingdealer@example.com",
            password="Strong-Test-Password-123!",
        )

        self.create_dealer(
            user=pending_user,
            business_name="Pending AutoHub Motors",
            verification_status="pending",
        )

        self.authenticate_user(pending_user)

        response = self.api_get(DEALER_ENQUIRY_URL)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_dealer_inbox_contains_only_own_enquiries(self):
        """A dealer must see only enquiries assigned to them."""

        self.create_enquiry(
            self.vehicle,
            customer_name="Customer One",
        )

        self.create_enquiry(
            self.vehicle,
            customer_name="Customer Two",
        )

        other_user, other_dealer, other_vehicle = (
            self.create_other_dealer_and_vehicle()
        )

        self.create_enquiry(
            other_vehicle,
            customer_name="Other Dealer Customer",
        )

        self.authenticate_user(self.dealer_user)

        response = self.api_get(DEALER_ENQUIRY_URL)

        data = self.get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(len(data), 2)

        returned_names = {
            item["customer_name"]
            for item in data
        }

        self.assertEqual(
            returned_names,
            {"Customer One", "Customer Two"},
        )

        self.assertNotIn(
            "Other Dealer Customer",
            returned_names,
        )

    def test_dealer_can_retrieve_own_enquiry(self):
        """A dealer can open an enquiry assigned to their business."""

        enquiry = self.create_enquiry(
            self.vehicle,
        )

        self.authenticate_user(self.dealer_user)

        response = self.api_get(
            f"{DEALER_ENQUIRY_URL}{enquiry.pk}/"
        )

        data = self.get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            data["id"],
            str(enquiry.pk),
        )

        self.assertEqual(
            data["customer_name"],
            enquiry.customer_name,
        )

        self.assertEqual(
            data["vehicle_id"],
            str(self.vehicle.pk),
        )

    def test_dealer_cannot_retrieve_another_dealers_enquiry(self):
        """A different dealer must receive 404 for the enquiry."""

        other_user, other_dealer, other_vehicle = (
            self.create_other_dealer_and_vehicle()
        )

        enquiry = self.create_enquiry(
            other_vehicle,
            customer_name="Other Dealer Customer",
        )

        self.authenticate_user(self.dealer_user)

        response = self.api_get(
            f"{DEALER_ENQUIRY_URL}{enquiry.pk}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # ---------------------------------------------------------
    # DEALER ENQUIRY MANAGEMENT TESTS
    # ---------------------------------------------------------

    def test_marking_enquiry_contacted_sets_timestamp(self):
        """Contacted status must automatically set last_contacted_at."""

        enquiry = self.create_enquiry(
            self.vehicle,
        )

        self.authenticate_user(self.dealer_user)

        response = self.api_patch(
            f"{DEALER_ENQUIRY_URL}{enquiry.pk}/",
            {"status": "contacted"},
        )

        data = self.get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            data["status"],
            "contacted",
        )

        enquiry.refresh_from_db()

        self.assertEqual(
            enquiry.status,
            "contacted",
        )

        self.assertIsNotNone(
            enquiry.last_contacted_at,
        )

    def test_dealer_can_convert_and_close_enquiry(self):
        """Dealers can move an enquiry to converted and closed."""

        enquiry = self.create_enquiry(
            self.vehicle,
        )

        self.authenticate_user(self.dealer_user)

        converted_response = self.api_patch(
            f"{DEALER_ENQUIRY_URL}{enquiry.pk}/",
            {"status": "converted"},
        )

        self.assertEqual(
            converted_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            self.get_response_data(converted_response)["status"],
            "converted",
        )

        closed_response = self.api_patch(
            f"{DEALER_ENQUIRY_URL}{enquiry.pk}/",
            {"status": "closed"},
        )

        self.assertEqual(
            closed_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            self.get_response_data(closed_response)["status"],
            "closed",
        )

        enquiry.refresh_from_db()

        self.assertEqual(
            enquiry.status,
            "closed",
        )

    def test_invalid_enquiry_status_is_rejected(self):
        """Dealers cannot set unsupported enquiry statuses."""

        enquiry = self.create_enquiry(
            self.vehicle,
        )

        self.authenticate_user(self.dealer_user)

        response = self.api_patch(
            f"{DEALER_ENQUIRY_URL}{enquiry.pk}/",
            {"status": "new"},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "status",
            self.get_response_data(response),
        )

        enquiry.refresh_from_db()

        self.assertEqual(
            enquiry.status,
            "new",
        )