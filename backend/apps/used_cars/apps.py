from django.apps import AppConfig


class UsedCarsConfig(AppConfig):
    default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"
    name = "apps.used_cars"