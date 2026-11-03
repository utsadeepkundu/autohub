
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Customer registration serializer.
    """

    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        trim_whitespace=False,
    )

    password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    class Meta:
        model = User

        fields = [
            "first_name",
            "last_name",
            "email",
            "password",
            "password_confirm",
        ]

    def validate_email(self, value):

        value = value.strip().lower()

        # Built-in Django User has a username limit of 150.
        if len(value) > 150:
            raise serializers.ValidationError(
                "Email must not exceed 150 characters."
            )

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "This email cannot be used as a username."
            )

        return value

    def validate(self, attrs):

        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })

        validate_password(attrs["password"])

        return attrs

    def create(self, validated_data):

        validated_data.pop("password_confirm")

        email = validated_data.pop("email")
        password = validated_data.pop("password")

        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            password=password,
        )

        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Login using email instead of username.
    """

    email = serializers.EmailField(write_only=True)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Remove the default username input.
        self.fields.pop(self.username_field, None)

    def validate(self, attrs):

        email = attrs.pop("email").strip().lower()

        user = User.objects.filter(
            email__iexact=email
        ).first()

        if user is None:
            raise AuthenticationFailed(
                "No active account found with these credentials."
            )

        # Translate email into the built-in username field.
        attrs[self.username_field] = user.get_username()

        return super().validate(attrs)


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Publicly safe authenticated user profile.
    """

    id = serializers.SerializerMethodField()

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
        ]

        read_only_fields = [
            "id",
            "username",
            "email",
            "date_joined",
        ]

    def get_id(self, obj):
        return str(obj.pk)
