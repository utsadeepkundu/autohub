
from django.utils import timezone

from apps.used_cars.models import UsedCarListing
from apps.cars.services.scrappa_client import search_used_cars


def safe_integer(value):
    """Safely convert a value into an integer."""

    if value is None or value == "":
        return None

    try:
        if isinstance(value, str):
            value = value.replace(",", "").strip()

        return int(float(value))

    except (TypeError, ValueError, OverflowError):
        return None


def sync_used_car_page(
    city,
    make=None,
    model=None,
    page=1,
    seen_ids=None,
    sort="created_date",
    sort_direction="desc",
):
    """
    Import one page of used-car listings from Scrappa.

    Supports:
        - Custom sorting
        - Duplicate detection across pages
        - Existing listing updates
    """

    if seen_ids is None:
        seen_ids = set()

    response = search_used_cars(
        city=city,
        make=make,
        model=model,
        page=page,
        sort=sort,
        sort_direction=sort_direction,
    )

    data = response.get("data", {})
    listings = data.get("listings", [])
    pagination = data.get("pagination", {})

    if not isinstance(listings, list):
        raise ValueError("Invalid listings response.")

    created = 0
    updated = 0
    skipped = 0
    duplicates = 0

    now = timezone.now()

    for item in listings:

        if not isinstance(item, dict):
            skipped += 1
            continue

        external_id = (
            item.get("used_car_sku_id")
            or item.get("listing_id")
        )

        title = item.get("title")
        location = item.get("location") or {}

        if not external_id or not title:
            skipped += 1
            continue

        external_id = str(external_id)

        # Prevent duplicate processing across overlapping pages.
        if external_id in seen_ids:
            duplicates += 1
            continue

        seen_ids.add(external_id)

        price_data = item.get("price") or {}
        km_data = item.get("km") or {}
        owner_data = item.get("owner") or {}
        seller = item.get("seller") or {}
        images = item.get("images") or {}
        flags = item.get("flags") or {}
        status = item.get("status") or {}

        active_value = flags.get("active")

        if active_value is None:
            active_value = (
                status.get("text", "").lower() == "active"
            )

        defaults = {
            "used_car_id": safe_integer(
                item.get("used_car_id")
            ),

            "title": title,
            "source_url": item.get("url") or "",

            "make": item.get("make") or "Unknown",
            "model": item.get("model") or "",
            "model_name": item.get("model_name") or "",
            "variant": item.get("variant") or "",

            "central_variant_id": safe_integer(
                item.get("central_variant_id")
            ),

            "year": safe_integer(item.get("year")),

            "fuel": item.get("fuel") or "",
            "transmission": item.get("transmission") or "",
            "body_type": item.get("body_type") or "",

            "price": safe_integer(
                price_data.get("value")
            ),
            "formatted_price": (
                price_data.get("formatted") or ""
            ),
            "market_price": safe_integer(
                price_data.get("market_price")
            ),
            "currency": price_data.get("currency") or "INR",

            "km_driven": safe_integer(
                km_data.get("value")
            ),

            "owner_count": safe_integer(
                owner_data.get("count")
            ),
            "owner_slug": owner_data.get("slug") or "",

            "city": location.get("city") or city.title(),
            "city_slug": city,
            "city_id": str(location.get("city_id") or ""),
            "locality": location.get("locality") or "",

            "seller_type": seller.get("type") or "",
            "dealer_id": safe_integer(
                seller.get("dealer_id")
            ),
            "store_id": str(seller.get("store_id") or ""),
            "corporate_id": str(
                seller.get("corporate_id") or ""
            ),
            "inventory_type": (
                seller.get("inventory_type") or ""
            ),
            "inventory_label": (
                seller.get("inventory_label") or ""
            ),

            "primary_image": images.get("primary") or "",
            "images": images,

            "flags": flags,
            "emi": item.get("emi") or {},
            "trust_tags": item.get("trust_tags") or [],
            "ai_tags": item.get("ai_tags") or [],

            "ai_price_badge": (
                item.get("ai_price_badge") or ""
            ),
            "map_link": item.get("map_link") or "",

            "additional": item.get("additional") or {},
            "provider_data": item,

            "inventory_status": safe_integer(
                status.get("inventory")
            ),
            "status_text": status.get("text") or "",

            "is_active": bool(active_value),

            "last_seen_at": now,
            "last_synced_at": now,
        }

        _, was_created = UsedCarListing.objects.update_or_create(
            provider="scrappa",
            external_id=external_id,
            defaults=defaults,
        )

        if was_created:
            created += 1
        else:
            updated += 1

    return {
        "success": True,
        "page": page,
        "sort": sort,
        "sort_direction": sort_direction,
        "listings_received": len(listings),
        "listings_created": created,
        "listings_updated": updated,
        "listings_skipped": skipped,
        "duplicates_skipped": duplicates,
        "total_available": pagination.get("total", 0),
        "has_more": pagination.get("has_more", False),
        "window_overlap": pagination.get(
            "window_overlap", False
        ),
    }


def sync_used_car_search(
    city,
    make=None,
    model=None,
    max_pages=3,
    start_page=1,
    sort="created_date",
    sort_direction="desc",
):
    """
    Import a limited number of used-car listing pages.

    Parameters:
        city:
            Required city slug.

        make:
            Optional manufacturer slug.

        model:
            Optional model slug.

        max_pages:
            Maximum API requests in this synchronization run.

        start_page:
            First provider page to retrieve.

        sort:
            Sorting field.

        sort_direction:
            asc or desc.

    Example:
        start_page=7, max_pages=3

        Requests pages 7, 8 and 9.

    Protections:
        - Duplicate detection.
        - Maximum page limit.
        - Stops after two consecutive pages without new IDs.
        - Existing listings are updated instead of duplicated.
    """

    if not city:
        raise ValueError("City is required.")

    if not 1 <= max_pages <= 500:
        raise ValueError(
            "max_pages must be between 1 and 500."
        )

    if not 1 <= start_page <= 500:
        raise ValueError(
            "start_page must be between 1 and 500."
        )

    if start_page + max_pages - 1 > 500:
        raise ValueError(
            "The requested page range cannot exceed page 500."
        )

    if sort_direction not in ("asc", "desc"):
        raise ValueError(
            "sort_direction must be either 'asc' or 'desc'."
        )

    seen_ids = set()

    totals = {
        "pages_processed": 0,
        "listings_received": 0,
        "listings_created": 0,
        "listings_updated": 0,
        "listings_skipped": 0,
        "duplicates_skipped": 0,
        "total_available": 0,
    }

    page = start_page
    last_page_processed = None

    pages_without_progress = 0
    has_more = False

    stop_reason = "Provider reported no more listings."

    while totals["pages_processed"] < max_pages:

        previous_count = len(seen_ids)

        result = sync_used_car_page(
            city=city,
            make=make,
            model=model,
            page=page,
            seen_ids=seen_ids,
            sort=sort,
            sort_direction=sort_direction,
        )

        # Record only a successfully processed page.
        last_page_processed = page

        totals["pages_processed"] += 1

        for key in (
            "listings_received",
            "listings_created",
            "listings_updated",
            "listings_skipped",
            "duplicates_skipped",
        ):
            totals[key] += result[key]

        totals["total_available"] = max(
            totals["total_available"],
            result["total_available"],
        )

        has_more = result["has_more"]

        new_ids = len(seen_ids) - previous_count

        print(
            f"Page {page}: "
            f"new={new_ids}, "
            f"created={result['listings_created']}, "
            f"updated={result['listings_updated']}, "
            f"duplicates={result['duplicates_skipped']}"
        )

        # Provider confirms there are no more results.
        if not has_more:
            stop_reason = "All available pages processed."
            break

        if new_ids == 0:
            pages_without_progress += 1
        else:
            pages_without_progress = 0

        # Stop if consecutive pages return no new listings.
        if pages_without_progress >= 2:
            stop_reason = (
                "Stopped after two consecutive pages "
                "without new listing IDs."
            )
            break

        page += 1

    # Calculate the next provider page using the actual
    # last successfully processed page.
    next_page = (
        last_page_processed + 1
        if has_more and last_page_processed is not None
        else None
    )

    # Report when the configured request limit is reached.
    if (
        has_more
        and totals["pages_processed"] >= max_pages
        and pages_without_progress < 2
    ):
        stop_reason = (
            f"Page limit reached. Resume from page {next_page}."
        )

    return {
        "success": totals["pages_processed"] > 0,
        "complete": not has_more,

        "city": city,
        "make": make,
        "model": model,

        "start_page": start_page,
        "last_page_processed": last_page_processed,
        "next_page": next_page,

        "sort": sort,
        "sort_direction": sort_direction,

        **totals,

        "unique_listings_seen": len(seen_ids),
        "stop_reason": stop_reason,
    }
