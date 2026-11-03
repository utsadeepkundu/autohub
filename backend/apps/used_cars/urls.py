
from django.urls import path

from apps.used_cars.views import (
    UsedCarListView,
    UsedCarDetailView,
    UsedCarFilterOptionsView,
)


app_name = "used_cars"


urlpatterns = [

    # Available filter options
    path(
        "filters/",
        UsedCarFilterOptionsView.as_view(),
        name="used-car-filters",
    ),

    # Used-car listing
    path(
        "",
        UsedCarListView.as_view(),
        name="used-car-list",
    ),

    # Individual used-car details
    path(
        "<str:pk>/",
        UsedCarDetailView.as_view(),
        name="used-car-detail",
    ),

]
