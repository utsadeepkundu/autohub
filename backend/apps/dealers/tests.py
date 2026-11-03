
from typing import Any, cast

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response as DRFResponse
from rest_framework.test import APITestCase, APIClient

from rest_framework_simplejwt.tokens import RefreshToken

from apps.dealers.models import DealerProfile, DealerVehicleListing


User = get_user_model()


def get_response_data(response: object) -> dict[str, Any]:
    """Safely retrieve dictionary data from a DRF response."""

    drf_response = cast(DRFResponse, response)
    response_data = drf_response.data

    if not isinstance(response_data, dict):
        raise AssertionError(
            "Expected the API response to contain a JSON object."
        )

    return response_data


def get_response_list(response: object) -> list[Any]:
    """Safely retrieve list data from a DRF response."""

    drf_response = cast(DRFResponse, response)
    response_data = drf_response.data

    if not isinstance(response_data, list):
        raise AssertionError(
            "Expected the API response to contain a list."
        )

    return response_data


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"]
)
class DealerManagementAPITests(APITestCase):
    """
    Automated tests for dealer applications, profiles,
    inventory management and public marketplace APIs.
    """

    application_url = "/api/dealers/apply/"
    profile_url = "/api/dealers/profile/"
    inventory_url = "/api/dealers/inventory/"
    marketplace_url = "/api/dealers/marketplace/"
    marketplace_filters_url = "/api/dealers/marketplace/filters/"

    def setUp(self) -> None:
        """Create isolated test users and dealer profiles."""

        self.pending_user = self.create_user(
            "pending.dealer@example.com"
        )

        self.pending_dealer = self.create_dealer(
            user=self.pending_user,
            business_name="Pending Test Motors",
            verification_status="pending",
        )

        self.approved_user = self.create_user(
            "approved.dealer@example.com"
        )

        self.approved_dealer = self.create_dealer(
            user=self.approved_user,
            business_name="Approved Test Motors",
            verification_status="approved",
        )

        self.second_approved_user = self.create_user(
            "second.dealer@example.com"
        )

        self.second_approved_dealer = self.create_dealer(
            user=self.second_approved_user,
            business_name="Second Test Motors",
            verification_status="approved",
        )

        self.customer_user = self.create_user(
            "customer.dealer.test@example.com"
        )

    def create_user(self, email: str) -> Any:
        """Create a test customer using Django's User model."""

        return User.objects.create_user(
            username=email,
            email=email,
            password="TestPassword!9284",
        )

    def create_dealer(
        self,
        *,
        user: Any,
        business_name: str,
        verification_status: str = "pending",
        is_active: bool = True,
    ) -> DealerProfile:
        """Create a test dealer profile."""

        return DealerProfile.objects.create(
            user=user,
            business_name=business_name,
            contact_person="Test Contact",
            email=user.email,
            phone="9000000001",
            address_line1="10 Test Business Road",
            city="Kolkata",
            state="West Bengal",
            pincode="700001",
            verification_status=verification_status,
            is_active=is_active,
        )

    def authenticate(self, user: Any) -> None:
        """Authenticate the API client using a real JWT."""

        refresh_token = RefreshToken.for_user(user)
        access_token = str(refresh_token.access_token)

        api_client = cast(APIClient, self.client)

        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

    def dealer_application_payload(self) -> dict[str, str]:
        """Return valid dealer application data."""

        return {
            "business_name": "New AutoHub Motors",
            "contact_person": "Test Dealer",
            "email": "new.business@example.com",
            "phone": "9000000002",
            "address_line1": "25 Dealer Street",
            "city": "Kolkata",
            "state": "West Bengal",
            "pincode": "700002",
            "gstin": "22AAAAA0000A1Z5",
        }

    def vehicle_payload(self, **overrides: Any) -> dict[str, Any]:
        """Return valid vehicle inventory request data."""

        payload: dict[str, Any] = {
            "title": "2020 Maruti Swift VXi",
            "make": "Maruti Suzuki",
            "model": "Swift",
            "variant": "VXi",
            "year": 2020,
            "fuel": "Petrol",
            "transmission": "Manual",
            "body_type": "Hatchback",
            "price": 450000,
            "km_driven": 25000,
            "owner_count": 1,
            "color": "White",
            "engine_cc": 1197,
            "seating_capacity": 5,
            "description": "Test vehicle listing.",
            "city": "Kolkata",
            "state": "West Bengal",
            "locality": "Salt Lake",
            "pincode": "700091",
            "primary_image": "https://example.com/swift.jpg",
            "images": [
                "https://example.com/swift.jpg",
            ],
            "features": [
                "Air Conditioning",
                "Power Windows",
            ],
        }

        payload.update(overrides)

        return payload

    def create_vehicle(
        self,
        dealer: DealerProfile,
        *,
        title: str = "2020 Maruti Swift VXi",
        make: str = "Maruti Suzuki",
        model: str = "Swift",
        year: int = 2020,
        fuel: str = "Petrol",
        transmission: str = "Manual",
        body_type: str = "Hatchback",
        price: int = 450000,
        km_driven: int = 25000,
        city: str = "Kolkata",
        status_value: str = "pending_review",
        published_at: Any = None,
        rejection_reason: str = "",
    ) -> DealerVehicleListing:
        """Create an inventory record for automated testing."""

        return DealerVehicleListing.objects.create(
            dealer=dealer,
            title=title,
            make=make,
            model=model,
            variant="VXi",
            year=year,
            fuel=fuel,
            transmission=transmission,
            body_type=body_type,
            price=price,
            km_driven=km_driven,
            owner_count=1,
            color="White",
            engine_cc=1197,
            seating_capacity=5,
            description="Automated test vehicle.",
            city=city,
            state="West Bengal",
            locality="Salt Lake",
            pincode="700091",
            primary_image="https://example.com/swift.jpg",
            images=[],
            features=["Air Conditioning"],
            status=status_value,
            published_at=published_at,
            rejection_reason=rejection_reason,
        )

    # --------------------------------------------------
    # DEALER APPLICATION TESTS
    # --------------------------------------------------

    def test_dealer_application_requires_authentication(self) -> None:
        response = self.client.post(
            self.application_url,
            self.dealer_application_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_customer_can_apply_as_dealer(self) -> None:
        self.authenticate(self.customer_user)

        payload = self.dealer_application_payload()

        # Customers must not be able to approve themselves.
        payload["verification_status"] = "approved"

        response = self.client.post(
            self.application_url,
            payload,
            format="json",
        )

        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            data["business_name"],
            "New AutoHub Motors",
        )

        self.assertEqual(
            data["verification_status"],
            "pending",
        )

        dealer = DealerProfile.objects.get(
            user=self.customer_user
        )

        self.assertEqual(
            dealer.verification_status,
            "pending",
        )

    def test_duplicate_dealer_application_is_rejected(self) -> None:
        self.authenticate(self.pending_user)

        response = self.client.post(
            self.application_url,
            self.dealer_application_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # --------------------------------------------------
    # DEALER PROFILE TESTS
    # --------------------------------------------------

    def test_dealer_can_retrieve_own_profile(self) -> None:
        self.authenticate(self.pending_user)

        response = self.client.get(self.profile_url)
        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            data["business_name"],
            "Pending Test Motors",
        )

        self.assertEqual(
            data["verification_status"],
            "pending",
        )

    def test_dealer_can_update_own_profile(self) -> None:
        self.authenticate(self.pending_user)

        response = self.client.patch(
            self.profile_url,
            {
                "business_name": "Updated Test Motors",
                "city": "Howrah",
                "verification_status": "approved",
            },
            format="json",
        )

        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            data["business_name"],
            "Updated Test Motors",
        )

        self.assertEqual(data["city"], "Howrah")

        self.assertEqual(
            data["verification_status"],
            "pending",
        )

    def test_profile_missing_for_user_returns_404(self) -> None:
        self.authenticate(self.customer_user)

        response = self.client.get(self.profile_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # --------------------------------------------------
    # DEALER INVENTORY TESTS
    # --------------------------------------------------

    def test_inventory_requires_authentication(self) -> None:
        response = self.client.get(self.inventory_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_pending_dealer_cannot_create_vehicle(self) -> None:
        self.authenticate(self.pending_user)

        response = self.client.post(
            self.inventory_url,
            self.vehicle_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_approved_dealer_can_create_pending_vehicle(self) -> None:
        self.authenticate(self.approved_user)

        payload = self.vehicle_payload()

        # Attempt to publish directly through the API.
        payload["status"] = "published"

        response = self.client.post(
            self.inventory_url,
            payload,
            format="json",
        )

        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            data["status"],
            "pending_review",
        )

        listing = DealerVehicleListing.objects.get(
            pk=data["id"]
        )

        self.assertEqual(
            listing.dealer.pk,
            self.approved_dealer.pk,
        )

        self.assertEqual(
            listing.status,
            "pending_review",
        )

    def test_dealer_inventory_shows_only_own_listings(self) -> None:
        own_listing = self.create_vehicle(
            self.approved_dealer,
            title="Dealer A Swift",
        )

        self.create_vehicle(
            self.second_approved_dealer,
            title="Dealer B Swift",
        )

        self.authenticate(self.approved_user)

        response = self.client.get(self.inventory_url)
        data = get_response_list(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(len(data), 1)

        self.assertEqual(
            data[0]["title"],
            own_listing.title,
        )

    def test_user_without_dealer_profile_gets_empty_inventory(self) -> None:
        self.authenticate(self.customer_user)

        response = self.client.get(self.inventory_url)
        data = get_response_list(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(data, [])

    def test_dealer_can_view_own_inventory_detail(self) -> None:
        listing = self.create_vehicle(
            self.approved_dealer
        )

        self.authenticate(self.approved_user)

        url = f"{self.inventory_url}{listing.pk}/"

        response = self.client.get(url)
        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            data["title"],
            listing.title,
        )

    def test_dealer_cannot_view_another_dealers_vehicle(self) -> None:
        listing = self.create_vehicle(
            self.second_approved_dealer
        )

        self.authenticate(self.approved_user)

        url = f"{self.inventory_url}{listing.pk}/"

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_editing_vehicle_returns_it_to_pending_review(self) -> None:
        listing = self.create_vehicle(
            self.approved_dealer,
            status_value="published",
            published_at=timezone.now(),
            rejection_reason="Old rejection note",
        )

        self.authenticate(self.approved_user)

        url = f"{self.inventory_url}{listing.pk}/"

        response = self.client.patch(
            url,
            {
                "price": 470000,
                "status": "published",
            },
            format="json",
        )

        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            data["status"],
            "pending_review",
        )

        updated_listing = DealerVehicleListing.objects.get(
            pk=listing.pk
        )

        self.assertEqual(
            updated_listing.price,
            470000,
        )

        self.assertEqual(
            updated_listing.status,
            "pending_review",
        )

        self.assertIsNone(
            updated_listing.published_at
        )

        self.assertEqual(
            updated_listing.rejection_reason,
            "",
        )

    # --------------------------------------------------
    # PUBLIC MARKETPLACE TESTS
    # --------------------------------------------------

    def test_public_marketplace_only_shows_eligible_listings(self) -> None:
        # Published listing from an approved dealer.
        self.create_vehicle(
            self.approved_dealer,
            title="Public Swift",
            status_value="published",
            published_at=timezone.now(),
        )

        # Pending listing from an approved dealer.
        self.create_vehicle(
            self.approved_dealer,
            title="Pending Swift",
            status_value="pending_review",
        )

        # Published listing from a pending dealer.
        self.create_vehicle(
            self.pending_dealer,
            title="Unapproved Dealer Swift",
            status_value="published",
            published_at=timezone.now(),
        )

        # Published listing from an inactive dealer.
        inactive_user = self.create_user(
            "inactive.dealer@example.com"
        )

        inactive_dealer = self.create_dealer(
            user=inactive_user,
            business_name="Inactive Motors",
            verification_status="approved",
            is_active=False,
        )

        self.create_vehicle(
            inactive_dealer,
            title="Inactive Dealer Swift",
            status_value="published",
            published_at=timezone.now(),
        )

        response = self.client.get(self.marketplace_url)
        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(data["count"], 1)

        self.assertEqual(
            data["results"][0]["title"],
            "Public Swift",
        )

    def test_public_marketplace_filtering(self) -> None:
        self.create_vehicle(
            self.approved_dealer,
            title="Kolkata Petrol Swift",
            make="Maruti Suzuki",
            model="Swift",
            fuel="Petrol",
            transmission="Manual",
            price=450000,
            city="Kolkata",
            status_value="published",
            published_at=timezone.now(),
        )

        self.create_vehicle(
            self.approved_dealer,
            title="Howrah Diesel Tiago",
            make="Tata",
            model="Tiago",
            fuel="Diesel",
            transmission="Manual",
            price=350000,
            city="Howrah",
            status_value="published",
            published_at=timezone.now(),
        )

        response = self.client.get(
            self.marketplace_url,
            {
                "make": "Maruti Suzuki",
                "model": "Swift",
                "city": "Kolkata",
                "fuel": "Petrol",
                "transmission": "Manual",
                "body_type": "Hatchback",
                "min_price": 400000,
                "max_price": 500000,
                "min_year": 2019,
                "max_year": 2021,
            },
        )

        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(data["count"], 1)

        self.assertEqual(
            data["results"][0]["title"],
            "Kolkata Petrol Swift",
        )

    def test_public_marketplace_search(self) -> None:
        self.create_vehicle(
            self.approved_dealer,
            title="Maruti Swift in Kolkata",
            status_value="published",
            published_at=timezone.now(),
        )

        self.create_vehicle(
            self.approved_dealer,
            title="Tata Tiago in Kolkata",
            make="Tata",
            model="Tiago",
            status_value="published",
            published_at=timezone.now(),
        )

        response = self.client.get(
            self.marketplace_url,
            {"search": "Swift"},
        )

        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(data["count"], 1)

        self.assertEqual(
            data["results"][0]["title"],
            "Maruti Swift in Kolkata",
        )

    def test_public_vehicle_detail_requires_published_listing(self) -> None:
        listing = self.create_vehicle(
            self.approved_dealer,
            status_value="pending_review",
        )

        url = f"{self.marketplace_url}{listing.pk}/"

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_public_vehicle_detail_returns_published_listing(self) -> None:
        listing = self.create_vehicle(
            self.approved_dealer,
            status_value="published",
            published_at=timezone.now(),
        )

        url = f"{self.marketplace_url}{listing.pk}/"

        response = self.client.get(url)
        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            data["title"],
            listing.title,
        )

        self.assertEqual(
            data["dealer_name"],
            self.approved_dealer.business_name,
        )

        self.assertNotIn("status", data)
        self.assertNotIn("rejection_reason", data)

    # --------------------------------------------------
    # PUBLIC MARKETPLACE VALIDATION TESTS
    # --------------------------------------------------

    def test_reject_invalid_numeric_filter(self) -> None:
        response = self.client.get(
            self.marketplace_url,
            {"min_price": "invalid"},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_reject_negative_price_filter(self) -> None:
        response = self.client.get(
            self.marketplace_url,
            {"min_price": "-100"},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_reject_invalid_price_range(self) -> None:
        response = self.client.get(
            self.marketplace_url,
            {
                "min_price": 800000,
                "max_price": 500000,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_reject_invalid_year_range(self) -> None:
        response = self.client.get(
            self.marketplace_url,
            {
                "min_year": 2022,
                "max_year": 2018,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_reject_invalid_ordering(self) -> None:
        response = self.client.get(
            self.marketplace_url,
            {"ordering": "invalid"},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # --------------------------------------------------
    # PUBLIC FILTER OPTIONS TEST
    # --------------------------------------------------

    def test_public_filter_options_exclude_unpublished_vehicles(self) -> None:
        self.create_vehicle(
            self.approved_dealer,
            title="Published Swift",
            make="Maruti Suzuki",
            status_value="published",
            published_at=timezone.now(),
            price=450000,
        )

        self.create_vehicle(
            self.approved_dealer,
            title="Pending Tata",
            make="Tata",
            status_value="pending_review",
            price=350000,
        )

        response = self.client.get(
            self.marketplace_filters_url
        )

        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            data["total_listings"],
            1,
        )

        self.assertIn(
            "Maruti Suzuki",
            data["makes"],
        )

        self.assertNotIn(
            "Tata",
            data["makes"],
        )

        self.assertEqual(
            data["price_range"]["min"],
            450000,
        )

        self.assertEqual(
            data["price_range"]["max"],
            450000,
        )
