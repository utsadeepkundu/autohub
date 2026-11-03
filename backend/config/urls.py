from django.contrib import admin
from django.urls import path, include


urlpatterns = [

    # Django administration
    path(
        "admin/",
        admin.site.urls,
    ),

    # Used-car APIs
    path(
        "api/used-cars/",
        include("apps.used_cars.urls"),
    ),

    # Accounts and authentication APIs
    path(
        "api/accounts/",
        include("apps.accounts.urls"),
    ),

    # Dealer APIs
    path(
        "api/dealers/",
        include("apps.dealers.urls"),
    ),

    # Enquiry APIs
    path(
        "api/enquiries/",
        include("apps.enquiries.urls"),
    ),

    # Pricing APIs
    path(
        "api/pricing/",
        include("apps.pricing.urls"),
    ),

    # New-car catalogue and comparison APIs
    path(
        "api/cars/",
        include("apps.cars.urls"),
    ),

]