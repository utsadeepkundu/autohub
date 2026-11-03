from django.urls import path

from .views import (
    CarBrandListView,
    CarBrandModelListView,
    CarModelDetailView,
    CarModelVariantListView,
    CarVariantDetailView,
    CarCatalogueSearchView,
    CarVariantComparisonView,
)


urlpatterns = [

    # Compare 2 or 3 car variants
    path(
        "compare/",
        CarVariantComparisonView.as_view(),
        name="car-variant-comparison",
    ),

    # All manufacturers
    path(
        "brands/",
        CarBrandListView.as_view(),
        name="car-brand-list",
    ),

    # Models belonging to a manufacturer
    path(
        "brands/<slug:brand_slug>/models/",
        CarBrandModelListView.as_view(),
        name="car-brand-model-list",
    ),

    # Search new-car models
    path(
        "search/",
        CarCatalogueSearchView.as_view(),
        name="car-catalogue-search",
    ),

    # Individual model details
    path(
        "brands/<slug:brand_slug>/models/<slug:model_slug>/",
        CarModelDetailView.as_view(),
        name="car-model-detail",
    ),

    # Variants belonging to a model
    path(
        "brands/<slug:brand_slug>/models/<slug:model_slug>/variants/",
        CarModelVariantListView.as_view(),
        name="car-model-variant-list",
    ),

    # Individual variant details
    path(
        "brands/<slug:brand_slug>/models/<slug:model_slug>/variants/<slug:variant_slug>/",
        CarVariantDetailView.as_view(),
        name="car-variant-detail",
    ),

]