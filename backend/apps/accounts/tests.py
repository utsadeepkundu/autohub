
from typing import Any, cast

from django.contrib.auth import get_user_model
from django.test import override_settings

from rest_framework import status
from rest_framework.response import Response as DRFResponse
from rest_framework.test import APIClient, APITestCase


User = get_user_model()

TEST_PASSWORD = "T7!kQ9#vR4@xM2"


def get_response_data(response: object) -> dict[str, Any]:
    """
    Safely retrieve dictionary data from a DRF response.
    """

    drf_response = cast(DRFResponse, response)
    response_data = drf_response.data

    if not isinstance(response_data, dict):
        raise AssertionError(
            "Expected the API response to contain a JSON object."
        )

    return response_data


@override_settings(
    ALLOWED_HOSTS=[
        "testserver",
        "localhost",
        "127.0.0.1",
    ]
)
class AccountAPITests(APITestCase):
    """
    Automated tests for registration, JWT authentication,
    refresh-token rotation, logout and customer profile APIs.
    """

    register_url = "/api/accounts/register/"
    login_url = "/api/accounts/login/"
    refresh_url = "/api/accounts/token/refresh/"
    profile_url = "/api/accounts/me/"
    logout_url = "/api/accounts/logout/"

    def create_user(
        self,
        email: str,
        password: str = TEST_PASSWORD,
        first_name: str = "Test",
        last_name: str = "Customer",
    ) -> Any:
        """
        Create a test customer using Django's built-in User model.
        """

        return User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

    def registration_payload(
        self,
        email: str = "new.customer@example.com",
        password: str = TEST_PASSWORD,
        password_confirm: str | None = None,
    ) -> dict[str, str]:
        """
        Generate registration request data.
        """

        return {
            "first_name": "New",
            "last_name": "Customer",
            "email": email,
            "password": password,
            "password_confirm": (
                password_confirm
                if password_confirm is not None
                else password
            ),
        }

    def login(
        self,
        email: str,
        password: str = TEST_PASSWORD,
    ) -> dict[str, Any]:
        """
        Authenticate a customer and return the token response.
        """

        response = self.client.post(
            self.login_url,
            {
                "email": email,
                "password": password,
            },
            format="json",
        )

        if response.status_code != status.HTTP_200_OK:
            raise AssertionError(
                f"Login failed with HTTP {response.status_code}."
            )

        return get_response_data(response)

    def authenticate_user(self, email: str) -> None:
        """
        Authenticate API requests using a real JWT access token.
        """

        token_data = self.login(email)

        access_token = token_data.get("access")

        if not isinstance(access_token, str):
            raise AssertionError(
                "Login did not return a valid access token."
            )

        api_client = cast(APIClient, self.client)

        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

    # --------------------------------------------------
    # REGISTRATION TESTS
    # --------------------------------------------------

    def test_customer_registration(self) -> None:
        """
        A customer should be able to register successfully.
        """

        response = self.client.post(
            self.register_url,
            self.registration_payload(),
            format="json",
        )

        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            data["email"],
            "new.customer@example.com",
        )

        self.assertNotIn("password", data)
        self.assertNotIn("password_confirm", data)

        user_exists = User.objects.filter(
            email="new.customer@example.com"
        ).exists()

        self.assertTrue(user_exists)

        user = User.objects.get(
            email="new.customer@example.com"
        )

        self.assertTrue(
            user.check_password(TEST_PASSWORD)
        )

    def test_registration_normalizes_email(self) -> None:
        """
        Registration should normalize email to lowercase.
        """

        response = self.client.post(
            self.register_url,
            self.registration_payload(
                email="NEW.CUSTOMER@EXAMPLE.COM"
            ),
            format="json",
        )

        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            data["email"],
            "new.customer@example.com",
        )

    def test_registration_rejects_duplicate_email(self) -> None:
        """
        Existing email addresses cannot register again.
        """

        self.create_user("existing@example.com")

        response = self.client.post(
            self.register_url,
            self.registration_payload(
                email="existing@example.com"
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_registration_rejects_password_mismatch(self) -> None:
        """
        Password and confirmation must match.
        """

        response = self.client.post(
            self.register_url,
            self.registration_payload(
                password=TEST_PASSWORD,
                password_confirm="DifferentPassword123!",
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        data = get_response_data(response)

        self.assertIn(
            "password_confirm",
            data,
        )

    def test_registration_rejects_numeric_password(self) -> None:
        """
        Numeric-only passwords must fail Django validation.
        """

        response = self.client.post(
            self.register_url,
            self.registration_payload(
                password="12345678",
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    # --------------------------------------------------
    # LOGIN TESTS
    # --------------------------------------------------

    def test_email_login_returns_jwt_tokens(self) -> None:
        """
        Valid email and password should return access
        and refresh tokens.
        """

        self.create_user("login@example.com")

        response = self.client.post(
            self.login_url,
            {
                "email": "login@example.com",
                "password": TEST_PASSWORD,
            },
            format="json",
        )

        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIsInstance(data.get("access"), str)
        self.assertIsInstance(data.get("refresh"), str)

    def test_login_rejects_incorrect_password(self) -> None:
        """
        Incorrect credentials must not authenticate a customer.
        """

        self.create_user("wrong.password@example.com")

        response = self.client.post(
            self.login_url,
            {
                "email": "wrong.password@example.com",
                "password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_login_rejects_unknown_email(self) -> None:
        """
        Unknown email addresses must not receive tokens.
        """

        response = self.client.post(
            self.login_url,
            {
                "email": "unknown@example.com",
                "password": TEST_PASSWORD,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    # --------------------------------------------------
    # REFRESH TOKEN TESTS
    # --------------------------------------------------

    def test_refresh_token_returns_new_access_token(self) -> None:
        """
        A valid refresh token should generate new tokens.
        The original refresh token must not be reusable.
        """

        self.create_user("refresh@example.com")

        login_data = self.login("refresh@example.com")
        original_refresh = login_data["refresh"]

        # First refresh request.
        response = self.client.post(
            self.refresh_url,
            {
                "refresh": original_refresh,
            },
            format="json",
        )

        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIsInstance(data.get("access"), str)
        self.assertIsInstance(data.get("refresh"), str)

        # The replacement refresh token must be different.
        self.assertNotEqual(
            data["refresh"],
            original_refresh,
        )

        # Attempt to reuse the original refresh token.
        reuse_response = self.client.post(
            self.refresh_url,
            {
                "refresh": original_refresh,
            },
            format="json",
        )

        self.assertEqual(
            reuse_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_refresh_rejects_invalid_token(self) -> None:
        """
        An invalid refresh token must be rejected.
        """

        response = self.client.post(
            self.refresh_url,
            {
                "refresh": "invalid.refresh.token",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    # --------------------------------------------------
    # LOGOUT TESTS
    # --------------------------------------------------

    def test_logout_revokes_refresh_token(self) -> None:
        """
        Logout should revoke the refresh token so it cannot
        be reused.
        """

        self.create_user("logout@example.com")

        login_data = self.login("logout@example.com")
        original_refresh = login_data["refresh"]

        # Send logout request.
        logout_response = self.client.post(
            self.logout_url,
            {
                "refresh": original_refresh,
            },
            format="json",
        )

        self.assertEqual(
            logout_response.status_code,
            status.HTTP_205_RESET_CONTENT,
        )

        # Try using the same refresh token after logout.
        refresh_response = self.client.post(
            self.refresh_url,
            {
                "refresh": original_refresh,
            },
            format="json",
        )

        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


    def test_logout_rejects_missing_refresh_token(self) -> None:
        """
        Logout must reject requests without a refresh token.
        """

        response = self.client.post(
            self.logout_url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_logout_rejects_invalid_refresh_token(self) -> None:
        """
        Logout must reject malformed refresh tokens.
        """

        response = self.client.post(
            self.logout_url,
            {
                "refresh": "invalid.refresh.token",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_logout_is_idempotent(self) -> None:
        """
        Repeated logout requests with the same token should be safe.
        """

        self.create_user("repeat.logout@example.com")

        login_data = self.login("repeat.logout@example.com")
        refresh_token = login_data["refresh"]

        first_response = self.client.post(
            self.logout_url,
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        second_response = self.client.post(
            self.logout_url,
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_205_RESET_CONTENT,
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_205_RESET_CONTENT,
        )


    # --------------------------------------------------
    # PROFILE TESTS
    # --------------------------------------------------

    def test_profile_requires_authentication(self) -> None:
        """
        Unauthenticated users cannot access their profile.
        """

        response = self.client.get(self.profile_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_authenticated_user_can_view_profile(self) -> None:
        """
        An authenticated customer should see their own profile.
        """

        self.create_user(
            "profile@example.com",
            first_name="Profile",
            last_name="Customer",
        )

        self.authenticate_user("profile@example.com")

        response = self.client.get(self.profile_url)
        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            data["email"],
            "profile@example.com",
        )

        self.assertEqual(
            data["first_name"],
            "Profile",
        )

        self.assertEqual(
            data["last_name"],
            "Customer",
        )

        self.assertNotIn("password", data)

    def test_authenticated_user_can_update_profile(self) -> None:
        """
        A customer can update editable profile information.
        """

        self.create_user(
            "update@example.com",
            first_name="Original",
            last_name="Customer",
        )

        self.authenticate_user("update@example.com")

        response = self.client.patch(
            self.profile_url,
            {
                "first_name": "Updated",
                "last_name": "Name",
                "email": "changed@example.com",
            },
            format="json",
        )

        data = get_response_data(response)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            data["first_name"],
            "Updated",
        )

        self.assertEqual(
            data["last_name"],
            "Name",
        )

        # Email is read-only in UserProfileSerializer.
        self.assertEqual(
            data["email"],
            "update@example.com",
        )

        user = User.objects.get(
            email="update@example.com"
        )

        self.assertEqual(user.first_name, "Updated")
        self.assertEqual(user.email, "update@example.com")

    def test_users_can_only_view_their_own_profiles(self) -> None:
        """
        JWT authentication should keep user profiles isolated.
        """

        self.create_user(
            "customer.a@example.com",
            first_name="Customer A",
        )

        self.create_user(
            "customer.b@example.com",
            first_name="Customer B",
        )

        self.authenticate_user("customer.a@example.com")

        first_response = self.client.get(self.profile_url)
        first_data = get_response_data(first_response)

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            first_data["email"],
            "customer.a@example.com",
        )

        self.authenticate_user("customer.b@example.com")

        second_response = self.client.get(self.profile_url)
        second_data = get_response_data(second_response)

        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            second_data["email"],
            "customer.b@example.com",
        )

        self.assertNotEqual(
            first_data["id"],
            second_data["id"],
        )
