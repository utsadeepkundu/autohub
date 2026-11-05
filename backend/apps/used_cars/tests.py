
from typing import Any, cast

from django.test import override_settings

from rest_framework import status
from rest_framework.response import Response as DRFResponse
from rest_framework.test import APITestCase

from apps.used_cars.models import UsedCarListing


def get_response_data(response: object) -> dict[str, Any]:
    """Safely retrieve dictionary data from a DRF response."""

    drf_response = cast(DRFResponse, response)
    response_data = drf_response.data

    if not isinstance(response_data, dict):
        raise AssertionError(
            "Expected the API response to contain a JSON object."
        )

    return response_data


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"]
)
class UsedCarCatalogueAPITests(APITestCase):
    """Automated tests for used-car catalogue APIs."""

    list_url = "/api/used-cars/"
    filters_url = "/api/used-cars/filters/"

    def setUp(self) -> None:
        self.swift_2019 = self.create_listing(
            external_id="test-used-swift-2019",
            title="2019 Maruti Swift VXi Petrol",
            make="Maruti Suzuki",
            model="maruti-swift",
            model_name="Swift",
            variant="VXi",
            year=2019,
            fuel="Petrol",
            transmission="Manual",
            body_type="Hatchback",
            price=350000,
            km_driven=45000,
            owner_count=1,
            city="Kolkata",
            city_slug="kolkata",
            locality="Salt Lake",
            seller_type="Dealer",
            market_price=375000,
        )

        self.swift_2020 = self.create_listing(
            external_id="test-used-swift-2020",
            title="2020 Maruti Swift ZXi Petrol",
            make="Maruti Suzuki",
            model="maruti-swift",
            model_name="Swift",
            variant="ZXi",
            year=2020,
            fuel="Petrol",
            transmission="Automatic",
            body_type="Hatchback",
            price=420000,
            km_driven=25000,
            owner_count=1,
            city="Kolkata",
            city_slug="kolkata",
            locality="New Town",
            seller_type="Individual",
            market_price=445000,
        )

        self.tiago_2018 = self.create_listing(
            external_id="test-used-tiago-2018",
            title="2018 Tata Tiago XT Diesel",
            make="Tata",
            model="tata-tiago",
            model_name="Tiago",
            variant="XT",
            year=2018,
            fuel="Diesel",
            transmission="Manual",
            body_type="Hatchback",
            price=390000,
            km_driven=60000,
            owner_count=2,
            city="Howrah",
            city_slug="howrah",
            locality="Shibpur",
            seller_type="Dealer",
            market_price=410000,
        )

        self.inactive_swift = self.create_listing(
            external_id="test-used-swift-inactive",
            title="2021 Maruti Swift VXi",
            make="Maruti Suzuki",
            model="maruti-swift",
            model_name="Swift",
            variant="VXi",
            year=2021,
            fuel="Petrol",
            transmission="Manual",
            body_type="Hatchback",
            price=320000,
            km_driven=30000,
            owner_count=1,
            city="Kolkata",
            city_slug="kolkata",
            locality="Dum Dum",
            seller_type="Dealer",
            market_price=340000,
            is_active=False,
        )

    def create_listing(
        self,
        *,
        external_id: str,
        title: str,
        make: str,
        model: str,
        model_name: str,
        variant: str,
        year: int,
        fuel: str,
        transmission: str,
        body_type: str,
        price: int,
        km_driven: int,
        owner_count: int,
        city: str,
        city_slug: str,
        locality: str,
        seller_type: str,
        market_price: int,
        is_active: bool = True,
    ) -> UsedCarListing:
        """Create a test listing."""

        return UsedCarListing.objects.create(
            provider="test",
            external_id=external_id,
            title=title,
            make=make,
            model=model,
            model_name=model_name,
            variant=variant,
            year=year,
            fuel=fuel,
            transmission=transmission,
            body_type=body_type,
            price=price,
            formatted_price=str(price),
            market_price=market_price,
            currency="INR",
            km_driven=km_driven,
            owner_count=owner_count,
            city=city,
            city_slug=city_slug,
            locality=locality,
            seller_type=seller_type,
            primary_image="https://example.com/car.jpg",
            is_active=is_active,
        )

    def test_list_active_used_cars(self) -> None:
        response = self.client.get(self.list_url)
        data = get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["count"], 3)
        self.assertEqual(len(data["results"]), 3)

    def test_used_car_pagination(self) -> None:
        response = self.client.get(
            self.list_url,
            {"page": 1, "page_size": 1},
        )

        data = get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["count"], 3)
        self.assertEqual(len(data["results"]), 1)
        self.assertIsNotNone(data["next"])

    def test_get_active_used_car_details(self) -> None:
        url = f"{self.list_url}{self.swift_2019.pk}/"

        response = self.client.get(url)
        data = get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["title"], "2019 Maruti Swift VXi Petrol")
        self.assertEqual(data["price"], 350000)
        self.assertEqual(data["market_price"], 375000)

    def test_inactive_used_car_is_not_publicly_accessible(self) -> None:
        url = f"{self.list_url}{self.inactive_swift.pk}/"

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_make_filter(self) -> None:
        response = self.client.get(
            self.list_url,
            {"make": "maruti suzuki"},
        )

        data = get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["count"], 2)

        for listing in data["results"]:
            self.assertEqual(listing["make"], "Maruti Suzuki")

    def test_model_filter(self) -> None:
        response = self.client.get(
            self.list_url,
            {"model": "Swift"},
        )

        data = get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["count"], 2)

    def test_city_filter_supports_readable_name(self) -> None:
        response = self.client.get(
            self.list_url,
            {"city": "Howrah"},
        )

        data = get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["city"], "Howrah")

    def test_combined_used_car_filters(self) -> None:
        parameters = {
            "make": "Maruti Suzuki",
            "model": "Swift",
            "city": "kolkata",
            "locality": "Salt Lake",
            "min_price": 300000,
            "max_price": 400000,
            "min_year": 2018,
            "max_year": 2020,
            "min_km": 40000,
            "max_km": 50000,
            "fuel": "Petrol",
            "transmission": "Manual",
            "body_type": "Hatchback",
            "seller_type": "Dealer",
            "owner_count": 1,
        }

        response = self.client.get(self.list_url, parameters)
        data = get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["count"], 1)

        self.assertEqual(
            data["results"][0]["title"],
            "2019 Maruti Swift VXi Petrol",
        )

    def test_search_used_cars(self) -> None:
        response = self.client.get(
            self.list_url,
            {"search": "Swift"},
        )

        data = get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["count"], 2)

    def test_order_used_cars_by_price(self) -> None:
        response = self.client.get(
            self.list_url,
            {"ordering": "price"},
        )

        data = get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        prices = [
            listing["price"]
            for listing in data["results"]
        ]

        self.assertEqual(prices, [350000, 390000, 420000])

    def test_descending_price_ordering(self) -> None:
        response = self.client.get(
            self.list_url,
            {"ordering": "-price"},
        )

        data = get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        prices = [
            listing["price"]
            for listing in data["results"]
        ]

        self.assertEqual(prices, [420000, 390000, 350000])

    def test_filter_options_endpoint(self) -> None:
        response = self.client.get(self.filters_url)
        data = get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(data["success"])
        self.assertEqual(data["total_listings"], 3)

        self.assertEqual(
            data["price_range"]["minimum"],
            350000,
        )

        self.assertEqual(
            data["price_range"]["maximum"],
            420000,
        )

        self.assertIn("Maruti Suzuki", data["makes"])
        self.assertIn("Tata", data["makes"])

    def test_filter_options_exclude_inactive_listings(self) -> None:
        response = self.client.get(self.filters_url)
        data = get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertNotIn("Dum Dum", data["localities"])
        self.assertNotIn(2021, data["years"])

    def test_public_serializer_does_not_expose_provider_data(self) -> None:
        url = f"{self.list_url}{self.swift_2019.pk}/"

        response = self.client.get(url)
        data = get_response_data(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertNotIn("provider_data", data)
        self.assertNotIn("dealer_id", data)
        self.assertNotIn("store_id", data)
        self.assertNotIn("external_id", data)

    def test_nonexistent_used_car_returns_404(self) -> None:
        nonexistent_id = "507f1f77bcf86cd799439011"
        url = f"{self.list_url}{nonexistent_id}/"

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
