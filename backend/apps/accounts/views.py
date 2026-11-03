
from django.contrib.auth import get_user_model

from rest_framework import generics, status

from datetime import datetime, timezone as datetime_timezone
from typing import Any, cast

from rest_framework import status
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import RevokedRefreshToken

from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.token_serializers import MongoTokenRefreshSerializer

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from apps.accounts.serializers import (
    RegisterSerializer,
    EmailTokenObtainPairSerializer,
    UserProfileSerializer,
)


User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    POST /api/accounts/register/

    Creates a new customer account.
    """

    queryset = User.objects.none()

    serializer_class = RegisterSerializer

    permission_classes = [AllowAny]

    authentication_classes = []

    throttle_scope = "registration"


class EmailLoginView(TokenObtainPairView):
    """
    POST /api/accounts/login/

    Authenticates using email and password.
    Returns access and refresh tokens.
    """

    serializer_class = EmailTokenObtainPairSerializer

    permission_classes = [AllowAny]

    authentication_classes = []

    throttle_scope = "login"


class RefreshTokenView(TokenRefreshView):
    """
    POST /api/accounts/token/refresh/

    Generates a new access token.
    """
    serializer_class = MongoTokenRefreshSerializer

    permission_classes = [AllowAny]

    authentication_classes = []

    throttle_scope = "token_refresh"


class UserProfileView(APIView):
    """
    GET /api/accounts/me/

    PATCH /api/accounts/me/

    Retrieves or updates the authenticated user's profile.
    """

    permission_classes = [IsAuthenticated]

    authentication_classes = [JWTAuthentication]

    def get(self, request):
        """
        Return the authenticated user's profile.
        """

        serializer = UserProfileSerializer(
            request.user
        )

        return Response(serializer.data)

    def patch(self, request):
        """
        Update the authenticated user's profile.
        """

        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(serializer.data)

class LogoutView(APIView):
    """
    Revoke a customer's refresh token during logout.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        raw_refresh = request.data.get("refresh")

        if not isinstance(raw_refresh, str) or not raw_refresh.strip():
            return Response(
                {"detail": "A refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate the supplied refresh token.
        try:
            refresh = RefreshToken(cast(Any, raw_refresh))
        except TokenError:
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_jti = refresh.payload.get("jti")
        token_exp = refresh.payload.get("exp")

        if not isinstance(token_jti, str) or not token_jti:
            return Response(
                {"detail": "Invalid refresh token identifier."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            isinstance(token_exp, bool)
            or not isinstance(token_exp, (int, float))
        ):
            return Response(
                {"detail": "Invalid refresh token expiry."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expires_at = datetime.fromtimestamp(
            float(token_exp),
            tz=datetime_timezone.utc,
        )

        # Store the token identifier only.
        # Repeated logout requests are safe because jti is unique.
        RevokedRefreshToken.objects.get_or_create(
            jti=token_jti,
            defaults={"expires_at": expires_at},
        )

        return Response(
            status=status.HTTP_205_RESET_CONTENT,
        )
