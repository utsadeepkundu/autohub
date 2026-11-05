
"""
Django settings for AutoHub.

Supports:
- Local development
- MongoDB Atlas
- Django REST Framework
- JWT authentication with custom token revocation
- Environment-based production configuration
- Redis caching and shared API throttling
- Production HTTPS and security settings
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured


# ==========================================================
# BASE CONFIGURATION
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from backend/.env
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    """Read a Boolean environment variable safely."""

    value = os.getenv(name)

    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized in {"true", "1", "yes", "on"}:
        return True

    if normalized in {"false", "0", "no", "off"}:
        return False

    raise ImproperlyConfigured(
        f"{name} must be a valid Boolean value."
    )


def env_list(
    name: str,
    default: tuple[str, ...] = (),
) -> list[str]:
    """Read a comma-separated environment variable."""

    value = os.getenv(name)

    if value is None:
        return list(default)

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


def env_int(name: str, default: int) -> int:
    """Read an integer environment variable safely."""

    value = os.getenv(name)

    if value is None or not value.strip():
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ImproperlyConfigured(
            f"{name} must be a valid integer."
        ) from exc


# ==========================================================
# SECRET KEY AND DEBUG CONFIGURATION
# ==========================================================

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "").strip()

if not SECRET_KEY:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be configured in the environment."
    )


DEBUG = env_bool("DEBUG", False)


# ==========================================================
# ALLOWED HOSTS
# ==========================================================

ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    (
        "localhost",
        "127.0.0.1",
    ) if DEBUG else (),
)

if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "Set ALLOWED_HOSTS before running AutoHub in production."
    )

if not DEBUG and "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "Wildcard ALLOWED_HOSTS is not permitted in production."
    )


# ==========================================================
# APPLICATION DEFINITION
# ==========================================================

INSTALLED_APPS = [
    # MongoDB-compatible Django contrib applications
    "config.apps.MongoAdminConfig",
    "config.apps.MongoAuthConfig",
    "config.apps.MongoContentTypesConfig",

    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party applications
    "rest_framework",
    "corsheaders",
    "django_filters",

    # MongoDB backend
    "django_mongodb_backend",

    # AutoHub applications
    "apps.cars.apps.CarsConfig",
    "apps.used_cars.apps.UsedCarsConfig",
    "apps.accounts.apps.AccountsConfig",
    "apps.dealers.apps.DealersConfig",
    "apps.pricing.apps.PricingConfig",
    "apps.enquiries.apps.EnquiriesConfig",
]


# ==========================================================
# MIDDLEWARE
# ==========================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    # CORS must execute before CommonMiddleware.
    "corsheaders.middleware.CorsMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ==========================================================
# URL AND APPLICATION CONFIGURATION
# ==========================================================

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"

ASGI_APPLICATION = "config.asgi.application"


# ==========================================================
# TEMPLATES
# ==========================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ==========================================================
# MONGODB DATABASE CONFIGURATION
# ==========================================================

MONGODB_URI = os.getenv("MONGODB_URI", "").strip()

MONGODB_NAME = os.getenv("MONGODB_NAME", "").strip()

if not MONGODB_URI:
    raise ImproperlyConfigured(
        "MONGODB_URI is missing from the environment."
    )

if not MONGODB_NAME:
    raise ImproperlyConfigured(
        "MONGODB_NAME is missing from the environment."
    )


DATABASES = {
    "default": {
        "ENGINE": "django_mongodb_backend",
        "HOST": MONGODB_URI,
        "NAME": MONGODB_NAME,
    }
}


# ==========================================================
# MONGODB MIGRATION CONFIGURATION
# ==========================================================

DEFAULT_AUTO_FIELD = (
    "django_mongodb_backend.fields.ObjectIdAutoField"
)

MIGRATION_MODULES = {
    "admin": "mongo_migrations.admin",
    "auth": "mongo_migrations.auth",
    "contenttypes": "mongo_migrations.contenttypes",
}


# ==========================================================
# PASSWORD VALIDATION
# ==========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ==========================================================
# INTERNATIONALIZATION
# ==========================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True


# ==========================================================
# STATIC FILE CONFIGURATION
# ==========================================================
STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

# Static and media file storage configuration.
# Use standard static storage locally and WhiteNoise in production.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}


# ==========================================================
# EMAIL CONFIGURATION
# ==========================================================

# Console backend locally; SMTP backend by default in production.
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    (
        "django.core.mail.backends.console.EmailBackend"
        if DEBUG
        else "django.core.mail.backends.smtp.EmailBackend"
    ),
)

EMAIL_HOST = os.getenv("EMAIL_HOST", "")

EMAIL_PORT = env_int(
    "EMAIL_PORT",
    25 if DEBUG else 587,
)

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")

EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")

EMAIL_USE_TLS = env_bool(
    "EMAIL_USE_TLS",
    not DEBUG,
)

EMAIL_USE_SSL = env_bool(
    "EMAIL_USE_SSL",
    False,
)

EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 10)

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    "webmaster@localhost",
)

SERVER_EMAIL = os.getenv(
    "SERVER_EMAIL",
    DEFAULT_FROM_EMAIL,
)


# ==========================================================
# CORS CONFIGURATION
# ==========================================================

LOCAL_FRONTEND_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)

CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    LOCAL_FRONTEND_ORIGINS if DEBUG else (),
)

# Apply CORS only to API endpoints.
CORS_URLS_REGEX = r"^/api/.*$"

# JWT authentication uses Authorization headers rather than
# cross-origin session cookies.
CORS_ALLOW_CREDENTIALS = env_bool(
    "CORS_ALLOW_CREDENTIALS",
    False,
)


# ==========================================================
# CSRF CONFIGURATION
# ==========================================================

CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    LOCAL_FRONTEND_ORIGINS if DEBUG else (),
)


# ==========================================================
# HTTPS AND SECURITY CONFIGURATION
# ==========================================================

# HTTPS redirection is enabled by default outside DEBUG mode.
SECURE_SSL_REDIRECT = env_bool(
    "SECURE_SSL_REDIRECT",
    not DEBUG,
)

# Use only when your trusted reverse proxy sets this header
# and prevents clients from supplying an untrusted value.
USE_X_FORWARDED_PROTO = env_bool(
    "USE_X_FORWARDED_PROTO",
    False,
)

if USE_X_FORWARDED_PROTO:
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )


# Secure cookies are enabled by default in production.
SESSION_COOKIE_SECURE = env_bool(
    "SESSION_COOKIE_SECURE",
    not DEBUG,
)

CSRF_COOKIE_SECURE = env_bool(
    "CSRF_COOKIE_SECURE",
    not DEBUG,
)


# Keep HSTS disabled until HTTPS and domain configuration
# have been verified in production.
SECURE_HSTS_SECONDS = env_int(
    "SECURE_HSTS_SECONDS",
    0,
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    False,
)

SECURE_HSTS_PRELOAD = env_bool(
    "SECURE_HSTS_PRELOAD",
    False,
)


# Additional browser security headers.
SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_REFERRER_POLICY = "same-origin"

X_FRAME_OPTIONS = "DENY"


# ==========================================================
# REDIS AND CACHE CONFIGURATION
# ==========================================================

REDIS_URL = os.getenv("REDIS_URL", "").strip()

if not DEBUG and not REDIS_URL:
    raise ImproperlyConfigured(
        "REDIS_URL is required in production for shared caching "
        "and consistent API throttling."
    )


if REDIS_URL:
    # Shared Redis cache for production or local Redis development.
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
            "KEY_PREFIX": os.getenv(
                "CACHE_KEY_PREFIX",
                "autohub",
            ),
            "TIMEOUT": 300,
        }
    }
else:
    # Local development cache.
    CACHES = {
        "default": {
            "BACKEND": (
                "django.core.cache.backends.locmem.LocMemCache"
            ),
            "LOCATION": "autohub-local-cache",
            "TIMEOUT": 300,
        }
    }


# ==========================================================
# DJANGO REST FRAMEWORK CONFIGURATION
# ==========================================================

REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],

    "DEFAULT_THROTTLE_RATES": {
        # Account security
        "registration": "5/hour",
        "login": "10/minute",
        "token_refresh": "30/hour",

        # Public API protection
        "enquiry_create": "5/hour",
        "valuation_estimate": "20/hour",
    },
}


# ==========================================================
# JWT AUTHENTICATION CONFIGURATION
# ==========================================================

SIMPLE_JWT = {
    # Access token lifetime
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),

    # Refresh token lifetime
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),

    # Custom MongoDB-based refresh-token rotation
    "ROTATE_REFRESH_TOKENS": True,

    # SimpleJWT blacklist app is not being used.
    # Revocation is handled by AutoHub's custom model.
    "BLACKLIST_AFTER_ROTATION": False,

    "UPDATE_LAST_LOGIN": False,

    "AUTH_HEADER_TYPES": ("Bearer",),
}


# ==========================================================
# DEFAULT REQUEST CONFIGURATION
# ==========================================================

APPEND_SLASH = True

# Keep Django admin and other pages from being embedded
# in external frames.
X_FRAME_OPTIONS = "DENY"
