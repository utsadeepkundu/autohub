
from datetime import date
from statistics import median, quantiles

from django.db.models import Q

from apps.used_cars.models import UsedCarListing


MIN_COMPARABLES = 5


def _get_prices(queryset):
    """
    Extract valid asking prices from comparable listings.
    """

    values = queryset.values_list("price", flat=True)

    return sorted(
        int(value)
        for value in values
        if value is not None and value > 0
    )


def _get_confidence(comparable_count):
    """
    Determine confidence from the number of comparable listings.
    """

    if comparable_count >= 15:
        return "high"

    if comparable_count >= 8:
        return "medium"

    if comparable_count >= MIN_COMPARABLES:
        return "low"

    return "insufficient"


def _build_result(prices, queryset, scope):
    """
    Build the final statistical valuation response.
    """

    comparable_count = len(prices)

    if comparable_count < MIN_COMPARABLES:
        return {
            "status": "insufficient_data",
            "message": (
                "Not enough comparable vehicles are available "
                "to provide a reliable valuation."
            ),
            "comparable_count": comparable_count,
            "minimum_required": MIN_COMPARABLES,
            "estimated_price": None,
            "price_range": None,
            "confidence": "insufficient",
            "comparison_scope": scope,
            "currency": "INR",
        }

    q1, q2, q3 = quantiles(
        prices,
        n=4,
        method="inclusive",
    )

    year_values = list(
        queryset.values_list("year", flat=True)
    )

    cities = sorted(
        set(
            queryset.values_list("city", flat=True)
        )
    )

    return {
        "status": "estimated",
        "estimated_price": int(round(median(prices))),
        "price_range": {
            "lower": int(round(q1)),
            "upper": int(round(q3)),
        },
        "currency": "INR",
        "confidence": _get_confidence(comparable_count),
        "comparable_count": comparable_count,
        "comparison_scope": scope,
        "market_data": {
            "year_min": min(year_values),
            "year_max": max(year_values),
            "cities": cities,
        },
        "method": (
            "Median and interquartile range of comparable "
            "active used-car asking prices."
        ),
        "data_note": (
            "Provider market_price is excluded because "
            "it differs from asking price in some imported records."
        ),
    }


def estimate_vehicle_price(
    make,
    model,
    year,
    fuel,
    transmission,
    km_driven,
    city=None,
):
    """
    Estimate a vehicle's indicative market value using
    comparable active listings from the AutoHub catalogue.

    The function does not modify any database records.
    """

    # Basic input validation
    make = str(make or "").strip()
    model = str(model or "").strip()
    fuel = str(fuel or "").strip()
    transmission = str(transmission or "").strip()
    city = str(city or "").strip()

    try:
        year = int(year)
        km_driven = int(km_driven)
    except (TypeError, ValueError):
        raise ValueError(
            "Year and kilometres driven must be integers."
        )

    current_year = date.today().year

    if not make or not model or not fuel or not transmission:
        raise ValueError(
            "Make, model, fuel and transmission are required."
        )

    if year < 1886 or year > current_year + 1:
        raise ValueError("Please provide a valid manufacturing year.")

    if km_driven < 0:
        raise ValueError(
            "Kilometres driven cannot be negative."
        )

    # Base comparable vehicle queryset
    base_queryset = UsedCarListing.objects.filter(
        is_active=True,
        make__iexact=make,
        fuel__iexact=fuel,
        transmission__iexact=transmission,
        price__gt=0,
        year__isnull=False,
        km_driven__isnull=False,
    ).filter(
        Q(model__iexact=model)
        | Q(model_name__iexact=model)
    )

    # Build progressively wider comparison searches.
    stages = []

    if city:
        city_queryset = base_queryset.filter(
            city__iexact=city
        )

        # Stage 1: Same city, year +/- 2,
        # and similar kilometres driven.
        km_tolerance = min(
            50000,
            max(15000, int(km_driven * 0.35)),
        )

        stages.append(
            (
                "same_city_year_and_mileage",
                city_queryset.filter(
                    year__gte=year - 2,
                    year__lte=year + 2,
                    km_driven__gte=max(
                        0,
                        km_driven - km_tolerance,
                    ),
                    km_driven__lte=(
                        km_driven + km_tolerance
                    ),
                ),
            )
        )

        # Stage 2: Same city, year +/- 3.
        stages.append(
            (
                "same_city_year_window",
                city_queryset.filter(
                    year__gte=year - 3,
                    year__lte=year + 3,
                ),
            )
        )

    # Stage 3: Include nearby catalogue cities,
    # year +/- 3.
    stages.append(
        (
            "all_cities_year_window",
            base_queryset.filter(
                year__gte=year - 3,
                year__lte=year + 3,
            ),
        )
    )

    # Stage 4: Wider regional comparison, year +/- 5.
    stages.append(
        (
            "all_cities_extended_year_window",
            base_queryset.filter(
                year__gte=year - 5,
                year__lte=year + 5,
            ),
        )
    )

    selected_prices = []
    selected_queryset = None
    selected_scope = None

    best_prices = []
    best_queryset = None
    best_scope = None

    for scope, queryset in stages:

        prices = _get_prices(queryset)

        if len(prices) > len(best_prices):
            best_prices = prices
            best_queryset = queryset
            best_scope = scope

        if len(prices) >= MIN_COMPARABLES:
            selected_prices = prices
            selected_queryset = queryset
            selected_scope = scope
            break

    # If no stage provides enough comparables,
    # return an honest insufficient-data result.
    if selected_queryset is None:

        if best_queryset is not None:
            return _build_result(
                best_prices,
                best_queryset,
                best_scope,
            )

        return {
            "status": "insufficient_data",
            "message": (
                "No comparable vehicles were found."
            ),
            "comparable_count": 0,
            "minimum_required": MIN_COMPARABLES,
            "estimated_price": None,
            "price_range": None,
            "confidence": "insufficient",
            "currency": "INR",
        }

    return _build_result(
        selected_prices,
        selected_queryset,
        selected_scope,
    )
