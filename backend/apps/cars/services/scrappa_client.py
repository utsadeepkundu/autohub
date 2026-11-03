
import os
import requests

BASE_URL = "https://scrappa.co/api/cardekho/v1"


class ScrappaAPIError(Exception):
    """Raised when the Scrappa API request fails."""


def _request(endpoint, params=None):
    api_key = os.getenv("SCRAPPA_API_KEY")

    if not api_key:
        raise ScrappaAPIError(
            "SCRAPPA_API_KEY is missing from backend .env"
        )

    url = f"{BASE_URL}/{endpoint.lstrip('/')}"

    headers = {
        "X-API-KEY": api_key,
        "Accept": "application/json",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

    except requests.Timeout as exc:
        raise ScrappaAPIError(
            "Scrappa API request timed out."
        ) from exc

    except requests.HTTPError as exc:
        status = (
            exc.response.status_code
            if exc.response is not None
            else "unknown"
        )
        raise ScrappaAPIError(
            f"Scrappa returned HTTP {status}."
        ) from exc

    except ValueError as exc:
        raise ScrappaAPIError(
            "Scrappa returned invalid JSON."
        ) from exc

    if not isinstance(data, dict) or data.get("success") is not True:
        raise ScrappaAPIError(
            "Scrappa returned an unsuccessful response."
        )

    return data


def fetch_new_car(brand, model):
    return _request(
        "new-cars",
        params={
            "brand": brand,
            "model": model,
        },
    )



def search_used_cars(
    city=None,
    make=None,
    model=None,
    page=1,
    price_min=None,
    price_max=None,
    year_min=None,
    year_max=None,
    km_max=None,
    fuel=None,
    transmission=None,
    body_type=None,
    owner=None,
    seats=None,
    sort=None,
    sort_direction=None,
):
    """
    Search used car listings through Scrappa.

    Pagination starts at page 1.
    Listings must be deduplicated using used_car_sku_id.
    """

    page = int(page)

    if not 1 <= page <= 500:
        raise ValueError("Page must be between 1 and 500.")

    values = {
        "city": city,
        "make": make,
        "model": model,
        "price_min": price_min,
        "price_max": price_max,
        "year_min": year_min,
        "year_max": year_max,
        "km_max": km_max,
        "fuel": fuel,
        "transmission": transmission,
        "body_type": body_type,
        "owner": owner,
        "seats": seats,
        "sort": sort,
        "sort_direction": sort_direction,
        "page": page,
    }

    params = {
        key: value
        for key, value in values.items()
        if value is not None and value != ""
    }

    return _request("used-cars", params=params)


def fetch_cities(query):
    """Search available city names and their provider slugs."""

    if not query or len(query.strip()) < 2:
        raise ValueError("Enter at least two characters.")

    return _request(
        "cities",
        params={"q": query.strip()},
    )



def fetch_makes():
    """
    Fetch manufacturer taxonomy from Scrappa.
    Primarily used for used-car discovery.
    """
    return _request("makes")


def fetch_models(make_slug):
    """
    Fetch new-car models belonging to one manufacturer.
    Example: maruti, tata, hyundai.
    """
    if not make_slug:
        raise ValueError("A manufacturer slug is required.")

    return _request(
        "models",
        params={"make": make_slug},
    )


def fetch_used_car_filters():
    """
    Fetch used-car filters, including available brands
    and their associated model slugs.
    """
    return _request("used-cars/filters")
