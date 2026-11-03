
from django.urls import path

from .views import (
    VehicleValuationEstimateView,
    VehicleValuationHistoryView,
    VehicleValuationDetailView,
)


urlpatterns = [
    # Public vehicle valuation
    path(
        "estimate/",
        VehicleValuationEstimateView.as_view(),
        name="vehicle-valuation-estimate",
    ),

    # Customer valuation history
    path(
        "history/",
        VehicleValuationHistoryView.as_view(),
        name="vehicle-valuation-history",
    ),

    # Individual valuation details
    path(
        "history/<str:pk>/",
        VehicleValuationDetailView.as_view(),
        name="vehicle-valuation-detail",
    ),
]
