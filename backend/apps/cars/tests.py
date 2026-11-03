
from typing import Any, cast

from django.test import override_settings

from rest_framework import status
from rest_framework.response import Response as DRFResponse
from rest_framework.test import APITestCase

from apps.cars.models import CarBrand, CarModel, CarVariant


def get_response_data(response: object) -> dict[str, Any]:
    """Safely retrieve dictionary data from a DRF response."""

    drf_response = cast(DRFResponse, response)
    response_data = drf_response.data

    if not isinstance(response_data, dict):
        raise AssertionError(
            "Expected the API response to contain a JSON object."
        )

    return response_data


def get_response_list(response: object) -> list[dict[str, Any]]:
    """Safely retrieve a list of serialized objects."""

    drf_response = cast(DRFResponse, response)
    response_data = drf_response.data

    if not isinstance(response_data, list):
        raise AssertionError(
            "Expected the API response to contain a JSON array."
        )

    return cast(list[dict[str, Any]], response_data)


def get_paginated_results(
    response: object,
) -> list[dict[str, Any]]:
    """Retrieve results from a paginated catalogue response."""

    response_data = get_response_data(response)
    results = response_data.get("results")

    if not isinstance(results, list):
        raise AssertionError(
            "Expected the response to contain paginated results."
        )

    return cast(list[dict[str, Any]], results)


@override_settings(
    ALLOWED_HOSTS=[
        "testserver",
        "localhost",
        "127.0.0.1",
    ]
)
class CarCatalogueAPITests(APITestCase):
    """
    Automated tests for the new-car catalogue,
    model variants, search and comparison APIs.
    """

    brands_url = "/api/cars/brands/"
    search_url = "/api/cars/search/"
    comparison_url = "/api/cars/compare/"

    def setUp(self) -> None:
        super().setUp()

        # Manufacturers
        self.brand = CarBrand.objects.create(
            provider="test",
            source_slug="maruti-suzuki",
            name="Maruti Suzuki",
            slug="maruti-suzuki",
            is_active=True,
        )

        self.other_brand = CarBrand.objects.create(
            provider="test",
            source_slug="honda",
            name="Honda",
            slug="honda",
            is_active=True,
        )

        # Models
        self.swift = self.create_model(
            brand=self.brand,
            external_id="test-swift-001",
            name="Swift",
            slug="swift",
            images={
                "exteriorimages": [
                    {
                        "imageUrl": (
                            "https://example.com/swift.jpg"
                        )
                    }
                ]
            },
        )

        self.baleno = self.create_model(
            brand=self.brand,
            external_id="test-baleno-001",
            name="Baleno",
            slug="baleno",
        )

        self.city = self.create_model(
            brand=self.other_brand,
            external_id="test-city-001",
            name="City",
            slug="city",
        )

        # Variants
        self.petrol_manual = self.create_variant(
            model=self.swift,
            external_id="test-swift-manual-001",
            name="Swift LXi Petrol",
            slug="swift-lxi-petrol",
            ex_showroom_price=600000,
            on_road_price=720000,
            fuel="Petrol",
            transmission="Manual",
            pricing_city="Kolkata",
        )

        self.petrol_automatic = self.create_variant(
            model=self.swift,
            external_id="test-swift-auto-001",
            name="Swift VXi Petrol",
            slug="swift-vxi-petrol",
            ex_showroom_price=800000,
            on_road_price=960000,
            fuel="Petrol",
            transmission="AMT",
            pricing_city="Kolkata",
        )

        self.diesel_manual = self.create_variant(
            model=self.swift,
            external_id="test-swift-diesel-001",
            name="Swift ZDi Diesel",
            slug="swift-zdi-diesel",
            ex_showroom_price=900000,
            on_road_price=1050000,
            fuel="Diesel",
            transmission="Manual",
            pricing_city="Delhi",
        )

    def create_model(
        self,
        brand: CarBrand,
        external_id: str,
        name: str,
        slug: str,
        is_active: bool = True,
        images: dict[str, Any] | None = None,
    ) -> CarModel:
        """Create a new-car model for testing."""

        return CarModel.objects.create(
            provider="test",
            external_id=external_id,
            brand_source_slug=brand.source_slug,
            brand_name=brand.name,
            source_slug=slug,
            name=name,
            slug=slug,
            images=images if images is not None else {},
            is_active=is_active,
        )

    def create_variant(
        self,
        model: CarModel,
        external_id: str,
        name: str,
        slug: str,
        ex_showroom_price: int,
        on_road_price: int,
        fuel: str,
        transmission: str,
        pricing_city: str = "Kolkata",
        body_type: str = "Hatchback",
        is_active: bool = True,
    ) -> CarVariant:
        """Create a car variant for testing."""

        return CarVariant.objects.create(
            provider="test",
            external_id=external_id,
            model_external_id=model.external_id,
            model_slug=model.slug,
            brand_source_slug=model.brand_source_slug,
            brand_name=model.brand_name,
            model_name=model.name,
            name=name,
            short_name=name,
            slug=slug,
            ex_showroom_price=ex_showroom_price,
            on_road_price=on_road_price,
            pricing_city=pricing_city,
            fuel=fuel,
            transmission=transmission,
            engine_displacement_cc=1197,
            body_type=body_type,
            summary=f"Test variant: {name}",
            specs=[
                {
                    "label": "Engine",
                    "value": "1197 cc",
                }
            ],
            key_features=["Air Conditioning"],
            images=[
                {
                    "imageUrl": (
                        f"https://example.com/{slug}.jpg"
                    )
                }
            ],
            is_active=is_active,
        )

    def get_brand_models_url(self, brand: CarBrand) -> str:
        return (
            f"/api/cars/brands/{brand.slug}/models/"
        )

    def get_model_detail_url(
        self,
        brand: CarBrand,
        model: CarModel,
    ) -> str:
        return (
            f"/api/cars/brands/{brand.slug}/models/"
            f"{model.slug}/"
        )

    def get_variant_list_url(
        self,
        brand: CarBrand,
        model: CarModel,
    ) -> str:
        return (
            f"/api/cars/brands/{brand.slug}/models/"
            f"{model.slug}/variants/"
        )

    def get_variant_detail_url(
        self,
        brand: CarBrand,
        model: CarModel,
        variant: CarVariant,
    ) -> str:
        return (
            f"/api/cars/brands/{brand.slug}/models/"
            f"{model.slug}/variants/{variant.slug}/"
        )

    # --------------------------------------------------
    # BRAND TESTS
    # --------------------------------------------------

    def test_list_active_brands(self) -> None:
        """Only active brands should appear in the catalogue."""

        CarBrand.objects.create(
            provider="test",
            source_slug="inactive-brand",
            name="Inactive Brand",
            slug="inactive-brand",
            is_active=False,
        )

        response = self.client.get(self.brands_url)
        data = get_response_list(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        names = [item["name"] for item in data]

        self.assertEqual(
            names,
            ["Honda", "Maruti Suzuki"],
        )

    def test_list_active_models_for_brand(self) -> None:
        """Only active models of the selected brand should appear."""

        self.create_model(
            brand=self.brand,
            external_id="test-inactive-model",
            name="Inactive Model",
            slug="inactive-model",
            is_active=False,
        )

        response = self.client.get(
            self.get_brand_models_url(self.brand)
        )

        data = get_response_data(response)
        results = get_paginated_results(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(data["count"], 2)

        names = [item["name"] for item in results]

        self.assertEqual(
            names,
            ["Baleno", "Swift"],
        )

    def test_model_list_pagination(self) -> None:
        """Model catalogue pagination should return correct metadata."""

        response = self.client.get(
            self.get_brand_models_url(self.brand),
            {
                "page": 2,
                "page_size": 1,
            },
        )

        data = get_response_data(response)
        results = get_paginated_results(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(data["count"], 2)
        self.assertEqual(data["page"], 2)
        self.assertEqual(data["page_size"], 1)
        self.assertEqual(data["total_pages"], 2)
        self.assertEqual(data["next_page"], None)
        self.assertEqual(data["previous_page"], 1)

        self.assertEqual(
            results[0]["name"],
            "Swift",
        )

    def test_nonexistent_or_inactive_brand_returns_404(self) -> None:
        """Unknown and inactive manufacturers should return 404."""

        nonexistent_response = self.client.get(
            "/api/cars/brands/unknown-brand/models/"
        )

        self.assertEqual(
            nonexistent_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.other_brand.is_active = False
        self.other_brand.save(update_fields=["is_active"])

        inactive_response = self.client.get(
            self.get_brand_models_url(self.other_brand)
        )

        self.assertEqual(
            inactive_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # --------------------------------------------------
    # MODEL DETAIL TESTS
    # --------------------------------------------------

    def test_model_detail_returns_primary_image(self) -> None:
        """Model detail should expose catalogue information and image."""

        response = self.client.get(
            self.get_model_detail_url(
                self.brand,
                self.swift,
            )
        )

        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(data["name"], "Swift")
        self.assertEqual(data["brand_name"], "Maruti Suzuki")

        self.assertEqual(
            data["primary_image"],
            "https://example.com/swift.jpg",
        )

        self.assertIn("mileage_data", data)
        self.assertIn("key_specs", data)
        self.assertIn("city_prices", data)

    def test_inactive_model_is_not_publicly_accessible(self) -> None:
        """Inactive models must not be exposed through detail APIs."""

        self.swift.is_active = False
        self.swift.save(update_fields=["is_active"])

        response = self.client.get(
            self.get_model_detail_url(
                self.brand,
                self.swift,
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # --------------------------------------------------
    # VARIANT LIST AND FILTER TESTS
    # --------------------------------------------------

    def test_list_active_variants(self) -> None:
        """The variant catalogue should exclude inactive variants."""

        self.create_variant(
            model=self.swift,
            external_id="test-inactive-variant",
            name="Inactive Variant",
            slug="inactive-variant",
            ex_showroom_price=500000,
            on_road_price=600000,
            fuel="CNG",
            transmission="Manual",
            is_active=False,
        )

        response = self.client.get(
            self.get_variant_list_url(
                self.brand,
                self.swift,
            )
        )

        data = get_response_data(response)
        results = get_paginated_results(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(data["count"], 3)

        names = [item["name"] for item in results]

        self.assertEqual(
            names,
            [
                "Swift LXi Petrol",
                "Swift VXi Petrol",
                "Swift ZDi Diesel",
            ],
        )

    def test_variant_categorical_filters(self) -> None:
        """Fuel, transmission, body type and city filters should combine."""

        response = self.client.get(
            self.get_variant_list_url(
                self.brand,
                self.swift,
            ),
            {
                "fuel": "Petrol",
                "transmission": "Manual",
                "body_type": "Hatchback",
                "pricing_city": "kolkata",
            },
        )

        data = get_response_data(response)
        results = get_paginated_results(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(data["count"], 1)

        self.assertEqual(
            results[0]["name"],
            "Swift LXi Petrol",
        )

    def test_variant_price_range_filters(self) -> None:
        """Minimum and maximum ex-showroom prices should work."""

        response = self.client.get(
            self.get_variant_list_url(
                self.brand,
                self.swift,
            ),
            {
                "min_price": 700000,
                "max_price": 850000,
            },
        )

        data = get_response_data(response)
        results = get_paginated_results(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(data["count"], 1)

        self.assertEqual(
            results[0]["name"],
            "Swift VXi Petrol",
        )

        self.assertEqual(
            results[0]["ex_showroom_price"],
            800000,
        )

    def test_variant_descending_price_ordering(self) -> None:
        """Variants should support descending price ordering."""

        response = self.client.get(
            self.get_variant_list_url(
                self.brand,
                self.swift,
            ),
            {
                "ordering": "-price",
            },
        )

        results = get_paginated_results(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        names = [item["name"] for item in results]

        self.assertEqual(
            names,
            [
                "Swift ZDi Diesel",
                "Swift VXi Petrol",
                "Swift LXi Petrol",
            ],
        )

    def test_variant_rejects_invalid_price_filters(self) -> None:
        """Invalid, negative and reversed price ranges must be rejected."""

        url = self.get_variant_list_url(
            self.brand,
            self.swift,
        )

        invalid_parameters = [
            {
                "min_price": "invalid",
            },
            {
                "min_price": "-1",
            },
            {
                "max_price": "-1",
            },
            {
                "min_price": "900000",
                "max_price": "800000",
            },
        ]

        for parameters in invalid_parameters:
            with self.subTest(parameters=parameters):
                response = self.client.get(
                    url,
                    parameters,
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )

    def test_variant_rejects_invalid_ordering(self) -> None:
        """Unsupported variant ordering values should return HTTP 400."""

        response = self.client.get(
            self.get_variant_list_url(
                self.brand,
                self.swift,
            ),
            {
                "ordering": "rating",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # --------------------------------------------------
    # VARIANT DETAIL TESTS
    # --------------------------------------------------

    def test_variant_detail_returns_full_information(self) -> None:
        """Variant detail should return its specifications and prices."""

        response = self.client.get(
            self.get_variant_detail_url(
                self.brand,
                self.swift,
                self.petrol_manual,
            )
        )

        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            data["name"],
            "Swift LXi Petrol",
        )

        self.assertEqual(
            data["ex_showroom_price"],
            600000,
        )

        self.assertEqual(
            data["on_road_price"],
            720000,
        )

        self.assertEqual(data["fuel"], "Petrol")
        self.assertEqual(data["transmission"], "Manual")

        self.assertIn("specs", data)
        self.assertIn("key_features", data)
        self.assertIn("images", data)

    def test_inactive_variant_is_not_publicly_accessible(self) -> None:
        """Inactive variants should return HTTP 404."""

        self.petrol_manual.is_active = False
        self.petrol_manual.save(update_fields=["is_active"])

        response = self.client.get(
            self.get_variant_detail_url(
                self.brand,
                self.swift,
                self.petrol_manual,
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    # --------------------------------------------------
    # SEARCH TESTS
    # --------------------------------------------------

    def test_search_by_model_name_and_brand_name(self) -> None:
        """Search should match model names and manufacturer names."""

        model_response = self.client.get(
            self.search_url,
            {
                "q": "Swift",
            },
        )

        model_results = get_paginated_results(model_response)

        self.assertEqual(
            model_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            [item["name"] for item in model_results],
            ["Swift"],
        )

        brand_response = self.client.get(
            self.search_url,
            {
                "q": "Maruti",
            },
        )

        brand_results = get_paginated_results(brand_response)

        self.assertEqual(
            brand_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(brand_results),
            2,
        )

    def test_search_requires_query(self) -> None:
        """Search must reject missing or blank search terms."""

        responses = [
            self.client.get(self.search_url),
            self.client.get(
                self.search_url,
                {
                    "q": "",
                },
            ),
            self.client.get(
                self.search_url,
                {
                    "q": "   ",
                },
            ),
        ]

        for response in responses:
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
            )

    # --------------------------------------------------
    # VARIANT COMPARISON TESTS
    # --------------------------------------------------

    def test_compare_two_and_three_variants(self) -> None:
        """Comparison should preserve selection order for two or three cars."""

        two_variant_ids = [
            str(self.petrol_automatic.pk),
            str(self.petrol_manual.pk),
        ]

        two_response = self.client.post(
            self.comparison_url,
            {
                "variant_ids": two_variant_ids,
            },
            format="json",
        )

        two_data = get_response_data(two_response)

        self.assertEqual(
            two_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            two_data["variant_count"],
            2,
        )

        self.assertEqual(
            [
                item["id"]
                for item in two_data["variants"]
            ],
            two_variant_ids,
        )

        two_prices = two_data["price_comparison"]["ex_showroom"]

        self.assertTrue(two_prices["comparable"])

        self.assertEqual(
            two_prices["difference"],
            200000,
        )

        self.assertEqual(
            two_prices["lowest"]["variant_name"],
            "Swift LXi Petrol",
        )

        self.assertEqual(
            two_prices["highest"]["variant_name"],
            "Swift VXi Petrol",
        )

        three_variant_ids = [
            str(self.diesel_manual.pk),
            str(self.petrol_automatic.pk),
            str(self.petrol_manual.pk),
        ]

        three_response = self.client.post(
            self.comparison_url,
            {
                "variant_ids": three_variant_ids,
            },
            format="json",
        )

        three_data = get_response_data(three_response)

        self.assertEqual(
            three_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            three_data["variant_count"],
            3,
        )

        self.assertEqual(
            [
                item["id"]
                for item in three_data["variants"]
            ],
            three_variant_ids,
        )

    def test_on_road_price_comparison_requires_same_city(self) -> None:
        """On-road prices from different cities must not be compared."""

        response = self.client.post(
            self.comparison_url,
            {
                "variant_ids": [
                    str(self.petrol_manual.pk),
                    str(self.diesel_manual.pk),
                ],
            },
            format="json",
        )

        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        price_comparison = data["price_comparison"]

        self.assertTrue(
            price_comparison["ex_showroom"]["comparable"]
        )

        self.assertFalse(
            price_comparison["on_road"]["comparable"]
        )

        self.assertIsNone(
            price_comparison["on_road"]["difference"]
        )

        self.assertIsNone(
            price_comparison["on_road"]["pricing_city"]
        )

    def test_comparison_rejects_invalid_payloads(self) -> None:
        """Comparison must reject invalid IDs and selection counts."""

        valid_id = str(self.petrol_manual.pk)
        second_id = str(self.petrol_automatic.pk)

        invalid_payloads = [
            {},
            {
                "variant_ids": [],
            },
            {
                "variant_ids": [valid_id],
            },
            {
                "variant_ids": [
                    valid_id,
                    valid_id,
                ],
            },
            {
                "variant_ids": [
                    "invalid-object-id",
                    second_id,
                ],
            },
            {
                "variant_ids": [
                    valid_id,
                    123,
                ],
            },
            {
                "variant_ids": [
                    valid_id,
                    second_id,
                    str(self.diesel_manual.pk),
                    str(self.city.pk),
                ],
            },
        ]

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post(
                    self.comparison_url,
                    payload,
                    format="json",
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )

    def test_comparison_returns_404_for_missing_or_inactive_variant(self) -> None:
        """Missing and inactive variants should not be comparable."""

        inactive_variant = self.petrol_automatic
        inactive_variant.is_active = False
        inactive_variant.save(update_fields=["is_active"])

        inactive_response = self.client.post(
            self.comparison_url,
            {
                "variant_ids": [
                    str(self.petrol_manual.pk),
                    str(inactive_variant.pk),
                ],
            },
            format="json",
        )

        inactive_data = get_response_data(inactive_response)

        self.assertEqual(
            inactive_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertIn(
            str(inactive_variant.pk),
            inactive_data["missing_variant_ids"],
        )

        unknown_id = "000000000000000000000001"

        missing_response = self.client.post(
            self.comparison_url,
            {
                "variant_ids": [
                    str(self.petrol_manual.pk),
                    unknown_id,
                ],
            },
            format="json",
        )

        self.assertEqual(
            missing_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
