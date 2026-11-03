
from django.urls import path

from apps.accounts.views import (
    RegisterView,
    EmailLoginView,
    RefreshTokenView,
    UserProfileView,
    LogoutView,
)



app_name = "accounts"


urlpatterns = [

    path(
        "register/",
        RegisterView.as_view(),
        name="register",
    ),

    path(
        "login/",
        EmailLoginView.as_view(),
        name="login",
    ),

    path(
        "token/refresh/",
        RefreshTokenView.as_view(),
        name="token-refresh",
    ),

    path(
        "me/",
        UserProfileView.as_view(),
        name="profile",
    ),

    path("logout/", LogoutView.as_view(), name="logout"),

]
