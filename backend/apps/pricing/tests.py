from datetime import date
from typing import Any, cast

from django.contrib.auth import get_user_model
from django.test import override_settings

from rest_framework import status
from rest_framework.response import Response as DRFResponse
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.used_cars.models import UsedCarListing

from .models import VehicleValuation
from .services.valuation import estimate_vehicle_price


ESTIMATE_URL = "/api/pricing/estimate/"
HISTORY_URL = "/api/pricing/history/"


class PricingTestCase(APITestCase):
    """Base test case with typed API helpers and isolated pricing fixtures."""

    @property
    def api_client(self) -> APIClient:
        """Return the DRF test client with an explicit static type."""
        return cast(APIClient, self.client)

    def api_get(
        self,
        path: str,
        data: dict[str, Any] | None = None,
    ) -> DRFResponse:
        """Perform a GET request and expose the DRF response type to Pylance."""
        response = self.api_client.get(path, data=data)
        return cast(DRFResponse, response)

    def api_post(
        self,
        path: str,
        data: dict[str, Any],
        *,
        format: str = "json",
    ) -> DRFResponse:
        """Perform a POST request and expose the DRF response type to Pylance."""
        response = self.api_client.post(path, data, format=format)
        return cast(DRFResponse, response)

    def create_listing(
        self,
        index: int,
        **overrides: Any,
    ) -> UsedCarListing:
        fields: dict[str, Any] = {
            "provider": "pricing-test",
            "external_id": f"pricing-test-{index}",
            "title": f"Maruti Suzuki Swift Test {index}",
            "make": "Maruti Suzuki",
            "model": "swift",
            "model_name": "Swift",
            "year": 2017,
            "fuel": "Petrol",
            "transmission": "Manual",
            "price": index * 100000,
            # Deliberately different: valuation must use asking price.
            "market_price": 9000000 + (index * 100000),
            "km_driven": 70000,
            "city": "Kolkata",
            "is_active": True,
        }
        fields.update(overrides)
        return UsedCarListing.objects.create(**fields)

    def create_comparables(
        self,
        count: int,
        *,
        start_index: int = 1,
        **overrides: Any,
    ) -> list[UsedCarListing]:
        listings: list[UsedCarListing] = []

        for offset in range(count):
            listings.append(
                self.create_listing(
                    start_index + offset,
                    **overrides,
                )
            )

        return listings

    def authenticate_user(self, user: Any) -> None:
        access_token = AccessToken.for_user(user)
        self.api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

    def create_customer(self, username: str = "pricing-customer") -> Any:
        user_model = get_user_model()
        return user_model.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="Strong-Test-Password-123!",
        )

    def create_valuation(
        self,
        user: Any,
        index: int,
    ) -> VehicleValuation:
        return VehicleValuation.objects.create(
            user=user,
            make="Maruti Suzuki",
            model=f"Swift Test {index}",
            year=2017,
            fuel="Petrol",
            transmission="Manual",
            km_driven=70000,
            city="Kolkata",
            estimated_price=300000 + (index * 10000),
            minimum_price=250000,
            maximum_price=350000,
            comparable_count=5,
            confidence="low",
            comparison_scope="same_city_year_and_mileage",
            valuation_status="estimated",
            result_data={"status": "estimated", "currency": "INR"},
        )

    @staticmethod
    def get_response_data(response: DRFResponse) -> dict[str, Any]:
        data = response.data
        if isinstance(data, dict):
            return cast(dict[str, Any], data)
        return {}


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"]
)
class VehicleValuationServiceTests(PricingTestCase):
    """Tests for comparable selection and statistical valuation."""

    def test_five_comparables_return_median_and_interquartile_range(self):
        self.create_comparables(5)

        result = estimate_vehicle_price(
            make="Maruti Suzuki",
            model="swift",
            year=2017,
            fuel="Petrol",
            transmission="Manual",
            km_driven=70000,
            city="Kolkata",
        )

        self.assertEqual(result["status"], "estimated")
        self.assertEqual(result["estimated_price"], 300000)
        self.assertEqual(
            result["price_range"],
            {"lower": 200000, "upper": 400000},
        )
        self.assertEqual(result["comparable_count"], 5)
        self.assertEqual(result["confidence"], "low")
        self.assertEqual(
            result["comparison_scope"],
            "same_city_year_and_mileage",
        )
        self.assertEqual(result["currency"], "INR")

    def test_valuation_uses_asking_price_not_market_price(self):
        self.create_comparables(5)

        result = estimate_vehicle_price(
            make="Maruti Suzuki",
            model="swift",
            year=2017,
            fuel="Petrol",
            transmission="Manual",
            km_driven=70000,
            city="Kolkata",
        )

        self.assertEqual(result["estimated_price"], 300000)
        self.assertIn("asking prices", result["method"])
        self.assertIn("market_price is excluded", result["data_note"])

    def test_four_comparables_return_insufficient_data(self):
        self.create_comparables(4)

        result = estimate_vehicle_price(
            make="Maruti Suzuki",
            model="swift",
            year=2017,
            fuel="Petrol",
            transmission="Manual",
            km_driven=70000,
            city="Kolkata",
        )

        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["comparable_count"], 4)
        self.assertEqual(result["minimum_required"], 5)
        self.assertIsNone(result["estimated_price"])
        self.assertIsNone(result["price_range"])
        self.assertEqual(result["confidence"], "insufficient")

    def test_no_matching_listings_returns_zero_comparables(self):
        result = estimate_vehicle_price(
            make="Maruti Suzuki",
            model="swift",
            year=2017,
            fuel="Petrol",
            transmission="Manual",
            km_driven=70000,
            city="Kolkata",
        )

        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["comparable_count"], 0)
        self.assertEqual(result["minimum_required"], 5)
        self.assertEqual(result["message"], "No comparable vehicles were found.")
        self.assertIsNone(result["estimated_price"])

    def test_inactive_and_invalid_listings_are_excluded(self):
        self.create_comparables(5)
        self.create_listing(101, is_active=False)
        self.create_listing(102, price=0)
        self.create_listing(103, price=-1000)
        self.create_listing(104, km_driven=None)
        self.create_listing(105, year=None)
        self.create_listing(106, make="Honda")
        self.create_listing(107, model="dzire", model_name="Dzire")
        self.create_listing(108, fuel="Diesel")
        self.create_listing(109, transmission="Automatic")

        result = estimate_vehicle_price(
            make="Maruti Suzuki",
            model="swift",
            year=2017,
            fuel="Petrol",
            transmission="Manual",
            km_driven=70000,
            city="Kolkata",
        )

        self.assertEqual(result["status"], "estimated")
        self.assertEqual(result["comparable_count"], 5)

    def test_matching_is_case_insensitive_and_supports_model_name(self):
        self.create_comparables(
            5,
            make="MARUTI SUZUKI",
            model="",
            model_name="Swift",
            fuel="PETROL",
            transmission="MANUAL",
            city="KOLKATA",
        )

        result = estimate_vehicle_price(
            make="maruti suzuki",
            model="SWIFT",
            year=2017,
            fuel="petrol",
            transmission="manual",
            km_driven=70000,
            city="kolkata",
        )

        self.assertEqual(result["status"], "estimated")
        self.assertEqual(result["comparable_count"], 5)

    def test_same_city_year_window_is_used_when_mileage_does_not_match(self):
        self.create_comparables(5, km_driven=140000)

        result = estimate_vehicle_price(
            make="Maruti Suzuki",
            model="swift",
            year=2017,
            fuel="Petrol",
            transmission="Manual",
            km_driven=70000,
            city="Kolkata",
        )

        self.assertEqual(result["status"], "estimated")
        self.assertEqual(result["comparable_count"], 5)
        self.assertEqual(
            result["comparison_scope"],
            "same_city_year_window",
        )

    def test_all_cities_year_window_is_used_when_city_has_too_few_matches(self):
        self.create_comparables(4, start_index=1)
        self.create_listing(101, city="Howrah")

        result = estimate_vehicle_price(
            make="Maruti Suzuki",
            model="swift",
            year=2017,
            fuel="Petrol",
            transmission="Manual",
            km_driven=70000,
            city="Kolkata",
        )

        self.assertEqual(result["status"], "estimated")
        self.assertEqual(result["comparable_count"], 5)
        self.assertEqual(result["comparison_scope"], "all_cities_year_window")

    def test_extended_all_cities_year_window_is_used_as_last_fallback(self):
        self.create_comparables(4, km_driven=140000)
        self.create_listing(101, city="Howrah", year=2022)

        result = estimate_vehicle_price(
            make="Maruti Suzuki",
            model="swift",
            year=2017,
            fuel="Petrol",
            transmission="Manual",
            km_driven=70000,
            city="Kolkata",
        )

        self.assertEqual(result["status"], "estimated")
        self.assertEqual(result["comparable_count"], 5)
        self.assertEqual(
            result["comparison_scope"],
            "all_cities_extended_year_window",
        )

    def test_confidence_is_medium_with_eight_comparables(self):
        self.create_comparables(8)

        result = estimate_vehicle_price(
            make="Maruti Suzuki",
            model="swift",
            year=2017,
            fuel="Petrol",
            transmission="Manual",
            km_driven=70000,
            city="Kolkata",
        )

        self.assertEqual(result["comparable_count"], 8)
        self.assertEqual(result["confidence"], "medium")

    def test_confidence_is_high_with_fifteen_comparables(self):
        self.create_comparables(15)

        result = estimate_vehicle_price(
            make="Maruti Suzuki",
            model="swift",
            year=2017,
            fuel="Petrol",
            transmission="Manual",
            km_driven=70000,
            city="Kolkata",
        )

        self.assertEqual(result["comparable_count"], 15)
        self.assertEqual(result["confidence"], "high")

    def test_service_rejects_missing_vehicle_identity(self):
        with self.assertRaisesMessage(
            ValueError,
            "Make, model, fuel and transmission are required.",
        ):
            estimate_vehicle_price(
                make="",
                model="swift",
                year=2017,
                fuel="Petrol",
                transmission="Manual",
                km_driven=70000,
                city="Kolkata",
            )

    def test_service_rejects_invalid_year(self):
        with self.assertRaisesMessage(
            ValueError,
            "Please provide a valid manufacturing year.",
        ):
            estimate_vehicle_price(
                make="Maruti Suzuki",
                model="swift",
                year=1885,
                fuel="Petrol",
                transmission="Manual",
                km_driven=70000,
                city="Kolkata",
            )

    def test_service_rejects_negative_kilometres(self):
        with self.assertRaisesMessage(
            ValueError,
            "Kilometres driven cannot be negative.",
        ):
            estimate_vehicle_price(
                make="Maruti Suzuki",
                model="swift",
                year=2017,
                fuel="Petrol",
                transmission="Manual",
                km_driven=-1,
                city="Kolkata",
            )

    def test_service_rejects_non_integer_year_or_kilometres(self):
        with self.assertRaisesMessage(
            ValueError,
            "Year and kilometres driven must be integers.",
        ):
            estimate_vehicle_price(
                make="Maruti Suzuki",
                model="swift",
                year="twenty seventeen",
                fuel="Petrol",
                transmission="Manual",
                km_driven=70000,
                city="Kolkata",
            )


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"]
)
class VehicleValuationAPITests(PricingTestCase):
    """Tests for estimate, customer history and detail endpoints."""

    def setUp(self):
        super().setUp()
        self.customer = self.create_customer()
        self.other_customer = self.create_customer("another-pricing-customer")

    @staticmethod
    def valid_payload() -> dict[str, Any]:
        return {
            "make": "Maruti Suzuki",
            "model": "swift",
            "year": 2017,
            "fuel": "Petrol",
            "transmission": "Manual",
            "km_driven": 70000,
            "city": "Kolkata",
        }

    def test_guest_can_receive_valuation_without_creating_history(self):
        self.create_comparables(5)

        response = self.api_post(
            ESTIMATE_URL,
            self.valid_payload(),
            format="json",
        )
        data = self.get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["status"], "estimated")
        self.assertEqual(data["estimated_price"], 300000)
        self.assertIsNone(data["valuation_id"])
        self.assertEqual(VehicleValuation.objects.count(), 0)

    def test_guest_can_receive_insufficient_data_response(self):
        response = self.api_post(
            ESTIMATE_URL,
            self.valid_payload(),
            format="json",
        )
        data = self.get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["status"], "insufficient_data")
        self.assertIsNone(data["estimated_price"])
        self.assertIsNone(data["valuation_id"])
        self.assertEqual(data["comparable_count"], 0)

    def test_authenticated_estimate_is_saved_to_customer_history(self):
        self.create_comparables(5)
        self.authenticate_user(self.customer)

        response = self.api_post(
            ESTIMATE_URL,
            self.valid_payload(),
            format="json",
        )
        data = self.get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["status"], "estimated")
        self.assertTrue(data["valuation_id"])

        valuation = VehicleValuation.objects.get(
            pk=data["valuation_id"],
        )
        self.assertEqual(valuation.user, self.customer)
        self.assertEqual(valuation.make, "Maruti Suzuki")
        self.assertEqual(valuation.model, "swift")
        self.assertEqual(valuation.estimated_price, 300000)
        self.assertEqual(valuation.minimum_price, 200000)
        self.assertEqual(valuation.maximum_price, 400000)
        self.assertEqual(valuation.comparable_count, 5)
        self.assertEqual(valuation.valuation_status, "estimated")
        self.assertEqual(valuation.result_data["status"], "estimated")

    def test_authenticated_insufficient_estimate_is_also_saved(self):
        self.authenticate_user(self.customer)

        response = self.api_post(
            ESTIMATE_URL,
            self.valid_payload(),
            format="json",
        )
        data = self.get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["status"], "insufficient_data")
        self.assertTrue(data["valuation_id"])

        valuation = VehicleValuation.objects.get(
            pk=data["valuation_id"],
        )
        self.assertEqual(valuation.user, self.customer)
        self.assertIsNone(valuation.estimated_price)
        self.assertIsNone(valuation.minimum_price)
        self.assertIsNone(valuation.maximum_price)
        self.assertEqual(valuation.valuation_status, "insufficient_data")

    def test_estimate_rejects_year_before_valid_range(self):
        payload = self.valid_payload()
        payload["year"] = 1885

        response = self.api_post(ESTIMATE_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("year", self.get_response_data(response))

    def test_estimate_rejects_year_beyond_next_calendar_year(self):
        payload = self.valid_payload()
        payload["year"] = date.today().year + 2

        response = self.api_post(ESTIMATE_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("year", self.get_response_data(response))

    def test_estimate_rejects_negative_kilometres(self):
        payload = self.valid_payload()
        payload["km_driven"] = -1

        response = self.api_post(ESTIMATE_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("km_driven", self.get_response_data(response))

    def test_estimate_rejects_blank_make(self):
        payload = self.valid_payload()
        payload["make"] = "   "

        response = self.api_post(ESTIMATE_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("make", self.get_response_data(response))

    def test_estimate_rejects_missing_required_field(self):
        payload = self.valid_payload()
        payload.pop("fuel")

        response = self.api_post(ESTIMATE_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fuel", self.get_response_data(response))

    def test_history_requires_authentication(self):
        response = self.api_get(HISTORY_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_history_contains_only_the_authenticated_customers_records(self):
        self.create_valuation(self.customer, 1)
        self.create_valuation(self.customer, 2)
        self.create_valuation(self.other_customer, 3)
        self.authenticate_user(self.customer)

        response = self.api_get(HISTORY_URL)
        data = self.get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["results"]), 2)
        self.assertTrue(
            all(
                item["make"] == "Maruti Suzuki"
                for item in data["results"]
            )
        )
        returned_ids = {item["id"] for item in data["results"]}
        other_record = VehicleValuation.objects.filter(
            user=self.other_customer,
        ).first()
        self.assertIsNotNone(other_record)
        if other_record is not None:
            self.assertNotIn(str(other_record.pk), returned_ids)

    def test_history_pagination_returns_page_metadata(self):
        self.create_valuation(self.customer, 1)
        self.create_valuation(self.customer, 2)
        self.create_valuation(self.customer, 3)
        self.authenticate_user(self.customer)

        response = self.api_get(
            HISTORY_URL,
            {"page": 2, "page_size": 1},
        )
        data = self.get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["count"], 3)
        self.assertEqual(data["page"], 2)
        self.assertEqual(data["page_size"], 1)
        self.assertEqual(data["total_pages"], 3)
        self.assertEqual(data["next_page"], 3)
        self.assertEqual(data["previous_page"], 1)
        self.assertEqual(len(data["results"]), 1)

    def test_history_rejects_non_integer_pagination_parameters(self):
        self.authenticate_user(self.customer)

        response = self.api_get(
            HISTORY_URL,
            {"page": "first", "page_size": "many"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", self.get_response_data(response))

    def test_history_rejects_page_less_than_one(self):
        self.authenticate_user(self.customer)

        response = self.api_get(HISTORY_URL, {"page": 0})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_history_rejects_page_size_less_than_one(self):
        self.authenticate_user(self.customer)

        response = self.api_get(HISTORY_URL, {"page_size": 0})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_history_caps_page_size_at_one_hundred(self):
        self.create_valuation(self.customer, 1)
        self.authenticate_user(self.customer)

        response = self.api_get(HISTORY_URL, {"page_size": 101})
        data = self.get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["page_size"], 100)

    def test_customer_can_retrieve_own_valuation_detail(self):
        valuation = self.create_valuation(self.customer, 1)
        self.authenticate_user(self.customer)

        response = self.api_get(f"{HISTORY_URL}{valuation.pk}/")
        data = self.get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["id"], str(valuation.pk))
        self.assertEqual(data["model"], "Swift Test 1")
        self.assertEqual(data["estimated_price"], valuation.estimated_price)

    def test_customer_cannot_retrieve_another_customers_valuation(self):
        valuation = self.create_valuation(self.other_customer, 1)
        self.authenticate_user(self.customer)

        response = self.api_get(f"{HISTORY_URL}{valuation.pk}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_valuation_detail_requires_authentication(self):
        valuation = self.create_valuation(self.customer, 1)

        response = self.api_get(f"{HISTORY_URL}{valuation.pk}/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)