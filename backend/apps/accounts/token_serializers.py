
from datetime import datetime, timezone as datetime_timezone
from typing import Any, Callable, cast

from django.contrib.auth import get_user_model
from django.db import IntegrityError

from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import RevokedRefreshToken


User = get_user_model()


class MongoTokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs: dict[str, Any]) -> dict[str, str]:
        raw_refresh = attrs.get("refresh")

        if not isinstance(raw_refresh, str) or not raw_refresh:
            raise InvalidToken("A valid refresh token is required.")

        # Validate the signature, expiry and token type.
        try:
            refresh = RefreshToken(cast(Any, raw_refresh))
        except TokenError as exc:
            raise InvalidToken(str(exc)) from exc

        # Read the original token identifier and expiry.
        token_jti = refresh.payload.get("jti")
        token_exp = refresh.payload.get("exp")

        if not isinstance(token_jti, str) or not token_jti:
            raise InvalidToken("The refresh token has no valid identifier.")

        if (
            isinstance(token_exp, bool)
            or not isinstance(token_exp, (int, float))
        ):
            raise InvalidToken("The refresh token has no valid expiry.")

        # Reject tokens that have already been revoked.
        if RevokedRefreshToken.objects.filter(jti=token_jti).exists():
            raise InvalidToken("This refresh token has already been revoked.")

        # Read the user identifier from the refresh token.
        user_id_claim = cast(str, api_settings.USER_ID_CLAIM)
        user_id = refresh.payload.get(user_id_claim)

        if user_id is None:
            raise InvalidToken("The refresh token has no user identifier.")

        # Retrieve the account using the configured SimpleJWT user field.
        user_id_field = cast(str, api_settings.USER_ID_FIELD)

        try:
            user = User.objects.get(**{user_id_field: user_id})
        except User.DoesNotExist as exc:
            raise AuthenticationFailed(
                "No active account found with the given credentials."
            ) from exc

        # Check whether the account is active.
        authentication_rule = cast(
            Callable[[Any], bool],
            api_settings.USER_AUTHENTICATION_RULE,
        )

        if not authentication_rule(user):
            raise AuthenticationFailed(
                "No active account found with the given credentials."
            )

        # Prepare the access token and replacement refresh token.
        access_token = str(refresh.access_token)

        refresh.set_jti()
        refresh.set_exp()
        refresh.set_iat()

        replacement_refresh_token = str(refresh)

        # Convert the original token expiry into a timezone-aware datetime.
        expires_at = datetime.fromtimestamp(
            float(token_exp),
            tz=datetime_timezone.utc,
        )

        # Atomically claim the original token using its unique JTI.
        try:
            RevokedRefreshToken.objects.create(
                jti=token_jti,
                expires_at=expires_at,
            )
        except IntegrityError as exc:
            raise InvalidToken(
                "This refresh token has already been used or revoked."
            ) from exc

        return {
            "access": access_token,
            "refresh": replacement_refresh_token,
        }
