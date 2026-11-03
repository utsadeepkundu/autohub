
from django.urls import path

from .views import (
    DealerApplicationView,
    DealerProfileView,
    DealerVehicleListingListCreateView,
    DealerVehicleListingDetailView,
    PublicMarketplaceVehicleListView,
    PublicMarketplaceVehicleDetailView,
    PublicMarketplaceFilterOptionsView,
)


urlpatterns = [
    # Dealer application and profile
    path(
        "apply/",
        DealerApplicationView.as_view(),
        name="dealer-application",
    ),
    path(
        "profile/",
        DealerProfileView.as_view(),
        name="dealer-profile",
    ),

    # Dealer vehicle inventory
    path(
        "inventory/",
        DealerVehicleListingListCreateView.as_view(),
        name="dealer-vehicle-list",
    ),
    path(
        "inventory/<str:pk>/",
        DealerVehicleListingDetailView.as_view(),
        name="dealer-vehicle-detail",
    ),

    # Public marketplace
    path(
        "marketplace/",
        PublicMarketplaceVehicleListView.as_view(),
        name="public-marketplace-vehicles",
    ),

    # Keep this static route before the dynamic vehicle detail route.
    path(
        "marketplace/filters/",
        PublicMarketplaceFilterOptionsView.as_view(),
        name="public-marketplace-filter-options",
    ),
    path(
        "marketplace/<str:pk>/",
        PublicMarketplaceVehicleDetailView.as_view(),
        name="public-marketplace-vehicle-detail",
    ),
]
