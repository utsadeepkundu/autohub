
from django.urls import path

from .views import (
    CustomerEnquiryCreateView,
    DealerEnquiryListView,
    DealerEnquiryDetailView,
)


urlpatterns = [
    # Customer enquiry submission
    path(
        "",
        CustomerEnquiryCreateView.as_view(),
        name="customer-enquiry-create",
    ),

    # Dealer enquiry inbox
    path(
        "dealer/",
        DealerEnquiryListView.as_view(),
        name="dealer-enquiry-list",
    ),

    # Individual dealer enquiry
    path(
        "dealer/<str:pk>/",
        DealerEnquiryDetailView.as_view(),
        name="dealer-enquiry-detail",
    ),
]
