
import re
from decimal import Decimal, InvalidOperation

from django.utils import timezone
from django.utils.text import slugify

from apps.cars.models import CarBrand, CarModel, CarVariant
from .scrappa_client import fetch_models, fetch_new_car


def to_integer(value):
    """Convert a provider value into an integer safely."""
    if value is None or isinstance(value, bool):
        return None

    try:
        return int(Decimal(str(value).replace(",", "").strip()))
    except (InvalidOperation, ValueError, TypeError):
        return None


def to_decimal(value):
    """Convert numeric values into Decimal safely."""
    if value is None:
        return None

    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        return None


def extract_engine_cc(summary):
    """Extract engine displacement from a variant summary."""
    if not summary:
        return None

    match = re.search(r"([\d,]+)\s*cc", summary, re.IGNORECASE)

    if match:
        return to_integer(match.group(1))

    return None


def extract_transmission(specs):
    """Identify transmission from the provider specification list."""
    transmission_types = (
        "manual",
        "automatic",
        "amt",
        "cvt",
        "dct",
        "imt",
    )

    for item in specs or []:
        value = str(item).strip()

        if any(term in value.lower() for term in transmission_types):
            return value

    return ""


def sync_new_car(brand_slug, model_slug):
    """
    Import or update one car model and all its available variants.

    Existing records are updated using provider identifiers.
    """

    response = fetch_new_car(brand_slug, model_slug)
    data = response.get("data", {})

    if not data:
        raise ValueError("Provider returned no vehicle data.")

    brand_name = data.get("brand")

    model_name = data.get("name")

    model_external_id = data.get("model_id")

    if not brand_name or not model_name or model_external_id is None:
        raise ValueError("Required brand or model identifiers are missing.")

    now = timezone.now()

    # --------------------------------------------------
    # 1. Create or update brand
    # --------------------------------------------------

    brand, brand_created = CarBrand.objects.update_or_create(
        provider="scrappa",
        source_slug=brand_slug,
        defaults={
            "name": brand_name,
            "slug": slugify(brand_name),
            "is_active": True,
            "last_synced_at": now,
            "provider_data": {
                "source_provider": "scrappa",
                "brand_name": brand_name,
            },
        },
    )

    # --------------------------------------------------
    # 2. Create or update model
    # --------------------------------------------------

    model_external_id = str(model_external_id)

    generated_model_slug = slugify(
        f"{brand_slug}-{model_name}"
    )

    model_source_slug = model_slug

    model, model_created = CarModel.objects.update_or_create(
        provider="scrappa",
        external_id=model_external_id,
        defaults={
            "brand_source_slug": brand_slug,
            "brand_name": brand_name,
            "source_slug": model_source_slug,
            "name": model_name,
            "slug": generated_model_slug,
            "city": data.get("city") or "",
            "city_id": str(data.get("city_id") or ""),
            "status": data.get("status") or "",
            "price_range": data.get("price_range") or "",
            "rating": to_decimal(data.get("rating")),
            "review_count": to_integer(
                data.get("review_count")
            ) or 0,
            "mileage_data": data.get("mileage") or {},
            "images": data.get("images") or {},
            "key_specs": data.get("key_specs") or [],
            "quick_overview": data.get("quick_overview") or {},
            "city_prices": data.get("city_prices") or [],
            "seo_data": data.get("seo") or {},
            "provider_data": data,
            "is_active": True,
            "last_synced_at": now,
        },
    )

    # --------------------------------------------------
    # 3. Create or update variants
    # --------------------------------------------------

    variants_created = 0
    variants_updated = 0
    variants_skipped = 0

    for item in data.get("variants", []):

        variant_name = item.get("name")

        external_variant_id = (
            item.get("central_variant_id")
            or item.get("slug")
        )

        if not variant_name or not external_variant_id:
            variants_skipped += 1
            continue

        external_variant_id = str(external_variant_id)

        variant_specs = item.get("specs") or []

        summary = item.get("summary") or ""

        status = item.get("status") or ""

        engine_cc = extract_engine_cc(summary)

        transmission = extract_transmission(variant_specs)

        variant_is_active = status.upper() not in {
            "DISCONTINUED",
            "INACTIVE",
            "DELETED",
        }

        _, created = CarVariant.objects.update_or_create(
            provider="scrappa",
            external_id=external_variant_id,
            defaults={
                "model_external_id": model_external_id,
                "model_slug": model.slug,
                "brand_source_slug": brand_slug,
                "brand_name": brand_name,
                "model_name": model_name,
                "name": variant_name,
                "short_name": item.get("short_name") or "",
                "slug": item.get("slug") or slugify(variant_name),
                "source_url": item.get("url") or "",
                "ex_showroom_price": to_integer(
                    item.get("ex_showroom_price")
                ),
                "ex_showroom_formatted": (
                    item.get("ex_showroom_formatted") or ""
                ),
                "on_road_price": to_integer(
                    item.get("on_road_price")
                ),
                "on_road_formatted": (
                    item.get("on_road_formatted") or ""
                ),
                "pricing_city": data.get("city") or "",
                "fuel": item.get("fuel") or "",
                "transmission": transmission,
                "engine_displacement_cc": engine_cc,
                "summary": summary,
                "specs": variant_specs,
                "mileage_arai": to_decimal(
                    item.get("mileage_arai")
                ),
                "tag": item.get("tag") or "",
                "status": status,
                "waiting_period": item.get("waiting_period") or "",
                "body_type": item.get("body_type") or "",
                "key_features": item.get("key_features") or [],
                "missing_features": item.get("missing_features") or [],
                "images": item.get("images") or [],
                "provider_data": item,
                "is_active": variant_is_active,
                "last_synced_at": now,
            },
        )

        if created:
            variants_created += 1
        else:
            variants_updated += 1

    return {
        "provider": "scrappa",
        "brand": brand_name,
        "brand_created": brand_created,
        "model": model_name,
        "model_created": model_created,
        "variants_received": len(data.get("variants", [])),
        "variants_created": variants_created,
        "variants_updated": variants_updated,
        "variants_skipped": variants_skipped,
        "pricing_city": data.get("city"),
        "success": True,
    }


def sync_brand_catalogue(brand_slug, limit=None):
    """
    Discover all models for a manufacturer and import
    their detailed information and variants.

    limit=None imports all discovered models.
    Use a small limit for initial testing.
    """

    response = fetch_models(brand_slug)
    data = response.get("data", {})

    models = data.get("models", [])

    if not isinstance(models, list):
        raise ValueError("Invalid models response from provider.")

    if not models:
        raise ValueError(
            f"No models found for manufacturer: {brand_slug}"
        )

    selected_models = models if limit is None else models[:limit]

    results = []
    failures = []

    for item in selected_models:
        model_slug = item.get("slug")
        model_name = item.get("name")

        if not model_slug:
            failures.append({
                "model": model_name,
                "error": "Missing model slug",
            })
            continue

        try:
            result = sync_new_car(brand_slug, model_slug)

            results.append(result)

        except Exception as exc:
            failures.append({
                "model": model_name or model_slug,
                "error": str(exc),
            })

    return {
        "provider": "scrappa",
        "brand": data.get("brand"),
        "models_available": data.get("total", len(models)),
        "models_attempted": len(selected_models),
        "models_imported": len(results),
        "models_failed": len(failures),
        "variants_created": sum(
            item["variants_created"] for item in results
        ),
        "variants_updated": sum(
            item["variants_updated"] for item in results
        ),
        "failures": failures,
        "success": len(results) > 0,
    }
