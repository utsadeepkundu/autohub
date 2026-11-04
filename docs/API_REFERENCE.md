# AutoHub API Reference

**Document purpose:** Frontend integration reference for the AutoHub backend.

> This document describes the routes and behaviour visible in the current backend implementation. All endpoints use JSON unless otherwise stated. Paths include the trailing slash used by Django URL routing.

## 1. Base URL and authentication

### Base URL

For a local Django development server, the usual base URL is:

```text
http://127.0.0.1:8000/api
```

Change this for the deployed backend. Do not hard-code the URL in frontend components; use a Vite environment variable such as `VITE_API_BASE_URL`.

Example `.env` in the React/Vite frontend:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

### JWT authentication

Private endpoints use JWT access tokens. Send the access token in the request header:

```http
Authorization: Bearer <access_token>
```

The configured access-token lifetime is **5 minutes** and refresh-token lifetime is **1 day**. Login and refresh responses contain both `access` and `refresh` tokens. The refresh endpoint rotates the refresh token. Use the newly returned refresh token for the next refresh; the previous refresh token is rejected after use.

Public endpoints do not require a token. Enquiry creation and vehicle valuation accept guests and can also identify a logged-in customer when a valid Bearer access token is supplied.

### Common request headers

For JSON requests:

```http
Content-Type: application/json
Accept: application/json
```

Add `Authorization` only for protected endpoints or optional-auth requests where the customer is signed in.

## 2. Endpoint index

| Area | Method | Endpoint | Authentication |
|---|---|---|---|
| Accounts | POST | `/accounts/register/` | Public |
| Accounts | POST | `/accounts/login/` | Public |
| Accounts | POST | `/accounts/token/refresh/` | Public, refresh token in body |
| Accounts | GET, PATCH | `/accounts/me/` | JWT required |
| Accounts | POST | `/accounts/logout/` | Public, refresh token in body |
| New cars | GET | `/cars/brands/` | Public |
| New cars | GET | `/cars/brands/{brand_slug}/models/` | Public |
| New cars | GET | `/cars/search/` | Public |
| New cars | GET | `/cars/brands/{brand_slug}/models/{model_slug}/` | Public |
| New cars | GET | `/cars/brands/{brand_slug}/models/{model_slug}/variants/` | Public |
| New cars | GET | `/cars/brands/{brand_slug}/models/{model_slug}/variants/{variant_slug}/` | Public |
| New cars | POST | `/cars/compare/` | Public |
| Used cars | GET | `/used-cars/` | Public |
| Used cars | GET | `/used-cars/filters/` | Public |
| Used cars | GET | `/used-cars/{id}/` | Public |
| Dealers | POST | `/dealers/apply/` | JWT required |
| Dealers | GET, PATCH | `/dealers/profile/` | JWT required |
| Dealers | GET, POST | `/dealers/inventory/` | JWT required |
| Dealers | GET, PATCH | `/dealers/inventory/{pk}/` | JWT required; own listing only |
| Dealers | GET | `/dealers/marketplace/` | Public |
| Dealers | GET | `/dealers/marketplace/filters/` | Public |
| Dealers | GET | `/dealers/marketplace/{pk}/` | Public |
| Enquiries | POST | `/enquiries/` | Public; optional JWT |
| Enquiries | GET | `/enquiries/dealer/` | JWT + approved active dealer |
| Enquiries | GET, PATCH | `/enquiries/dealer/{pk}/` | JWT + approved active dealer; own enquiry only |
| Pricing | POST | `/pricing/estimate/` | Public; optional JWT |
| Pricing | GET | `/pricing/history/` | JWT required |
| Pricing | GET | `/pricing/history/{pk}/` | JWT required; own record only |

The `/api/` prefix is omitted from the endpoint column to keep the table readable. For example, `/accounts/login/` means `/api/accounts/login/`.

## 3. Pagination formats

The backend currently uses more than one pagination response format. The frontend should not assume that every list endpoint has the same envelope.

### Catalogue and valuation-history pagination

Used by new-car model lists, new-car search, new-car variant lists, and valuation history:

```json
{
  "count": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3,
  "next_page": 2,
  "previous_page": null,
  "results": []
}
```

`next_page` and `previous_page` are page numbers or `null`.

### DRF page-number pagination

Used by the used-car list and public dealer marketplace list:

```json
{
  "count": 42,
  "next": "http://127.0.0.1:8000/api/used-cars/?page=2",
  "previous": null,
  "results": []
}
```

`next` and `previous` are URLs or `null`.

### Pagination defaults

| Endpoint group | Default page | Default page size | Maximum page size |
|---|---:|---:|---:|
| New-car models, search, variants | 1 | 20 | 100 |
| Used cars | 1 | 20 | 100 |
| Public dealer marketplace | 1 | 20 | 100 |
| Valuation history | 1 | 20 | 100 |

Use `page` and `page_size` query parameters where pagination is supported.

## 4. Accounts

### Register

`POST /api/accounts/register/`

Public. Creates a customer account. Registration is limited to 5 requests per hour per throttle identity.

Request body:

```json
{
  "first_name": "Aman",
  "last_name": "Sharma",
  "email": "aman@example.com",
  "password": "Use-a-strong-password",
  "password_confirm": "Use-a-strong-password"
}
```

Fields:

| Field | Behaviour |
|---|---|
| `first_name` | Customer first name |
| `last_name` | Customer last name |
| `email` | Required email; trimmed and stored in lowercase; maximum 150 characters; must be unique |
| `password` | Required; minimum 8 characters and checked by configured Django password validators |
| `password_confirm` | Required; must match `password` |

Successful creation returns HTTP `201 Created`. Password fields are write-only and are not returned. The serializer's response fields are `first_name`, `last_name`, and `email`.

### Login

`POST /api/accounts/login/`

Public. Login uses email and password. Limited to 10 requests per minute.

Request body:

```json
{
  "email": "aman@example.com",
  "password": "Use-a-strong-password"
}
```

Successful response:

```json
{
  "refresh": "<refresh_token>",
  "access": "<access_token>"
}
```

### Refresh access token

`POST /api/accounts/token/refresh/`

Public endpoint; the refresh token is supplied in the JSON body. Limited to 30 requests per hour.

Request body:

```json
{
  "refresh": "<current_refresh_token>"
}
```

Successful response:

```json
{
  "access": "<new_access_token>",
  "refresh": "<replacement_refresh_token>"
}
```

Store and use the replacement refresh token. The token supplied in the request is revoked as part of rotation and cannot be reused.

### Current user's profile

`GET /api/accounts/me/`

`PATCH /api/accounts/me/`

JWT required.

Successful response fields:

```json
{
  "id": "<user_id>",
  "username": "aman@example.com",
  "email": "aman@example.com",
  "first_name": "Aman",
  "last_name": "Sharma",
  "date_joined": "<ISO-8601 timestamp>"
}
```

For `PATCH`, only `first_name` and `last_name` are writable. `id`, `username`, `email`, and `date_joined` are read-only.

Example PATCH body:

```json
{
  "first_name": "Aman Kumar"
}
```

### Logout

`POST /api/accounts/logout/`

Public endpoint; submit the refresh token to revoke it. Authentication is not required by the view.

Request body:

```json
{
  "refresh": "<refresh_token>"
}
```

Successful response is HTTP `205 Reset Content` with no response body. Repeating logout for an already revoked valid token is safe. Logout revokes the refresh token; an already-issued access token may remain usable until its short expiry (up to 5 minutes).

## 5. New-car catalogue

All new-car catalogue endpoints are public and return active catalogue records.

### List brands

`GET /api/cars/brands/`

Returns a plain JSON array (not a pagination envelope):

```json
[
  {
    "id": "<brand_id>",
    "name": "Example Motors",
    "slug": "example-motors",
    "logo_url": "<URL or null>"
  }
]
```

### List models for a brand

`GET /api/cars/brands/{brand_slug}/models/`

Query parameters: `page`, `page_size`.

Uses the catalogue pagination envelope. Each result contains:

- `id`
- `brand_name`
- `name`
- `slug`
- `price_range`
- `rating`
- `review_count`
- `primary_image` (may be `null`)

### Search models and brands

`GET /api/cars/search/?q={search_text}`

Query parameters:

| Parameter | Required | Description |
|---|---|---|
| `q` | Yes | Search text; trimmed; matches active model names or brand names |
| `page` | No | Page number; default 1 |
| `page_size` | No | Default 20; maximum 100 |

A missing or blank `q` returns HTTP `400` with a `detail` message. Results use the catalogue pagination envelope and the model-list fields described above.

### Model details

`GET /api/cars/brands/{brand_slug}/models/{model_slug}/`

Returns one model object with:

- `id`, `brand_name`, `name`, `slug`
- `price_range`, `rating`, `review_count`
- `mileage_data`, `images`, `primary_image`
- `key_specs`, `city_prices`

`primary_image` may be `null` if no usable exterior image URL is present.

### List model variants

`GET /api/cars/brands/{brand_slug}/models/{model_slug}/variants/`

Query parameters:

| Parameter | Description |
|---|---|
| `fuel` | Exact category match, case-insensitive |
| `transmission` | Exact category match, case-insensitive |
| `body_type` | Exact category match, case-insensitive |
| `pricing_city` | Exact city match, case-insensitive |
| `min_price` | Minimum ex-showroom price, integer |
| `max_price` | Maximum ex-showroom price, integer |
| `ordering` | `price`, `-price`, `name`, or `-name`; default `price` |
| `page` | Page number; default 1 |
| `page_size` | Default 20; maximum 100 |

Price filtering uses `ex_showroom_price`, not on-road price. Negative prices, non-integer price values, `min_price` greater than `max_price`, or an unsupported ordering value return HTTP `400`.

Each result contains:

- `id`, `brand_name`, `model_name`, `model_slug`
- `name`, `short_name`, `slug`, `source_url`
- `ex_showroom_price`, `ex_showroom_formatted`
- `on_road_price`, `on_road_formatted`, `pricing_city`
- `fuel`, `transmission`, `engine_displacement_cc`, `mileage_arai`, `body_type`
- `summary`, `specs`, `key_features`, `missing_features`, `images`
- `tag`, `status`, `waiting_period`

Results use the catalogue pagination envelope.

### Variant details

`GET /api/cars/brands/{brand_slug}/models/{model_slug}/variants/{variant_slug}/`

Returns one variant object with the same fields as a variant-list result.

### Compare variants

`POST /api/cars/compare/`

Public. Provide between 2 and 3 distinct active variant IDs. IDs must be strings containing valid MongoDB ObjectIds.

Request body:

```json
{
  "variant_ids": [
    "<variant_object_id_1>",
    "<variant_object_id_2>"
  ]
}
```

Successful response shape:

```json
{
  "variant_count": 2,
  "variants": [],
  "price_comparison": {
    "ex_showroom": {
      "comparable": true,
      "lowest": {
        "variant_id": "<id>",
        "variant_name": "<name>",
        "price": 0
      },
      "highest": {
        "variant_id": "<id>",
        "variant_name": "<name>",
        "price": 0
      },
      "difference": 0,
      "pricing_city": null,
      "reason": null
    },
    "on_road": {
      "comparable": false,
      "lowest": null,
      "highest": null,
      "difference": null,
      "pricing_city": null,
      "reason": "<reason when not comparable>"
    }
  }
}
```

The `variants` array contains complete variant serializer objects in the same order as the submitted IDs. Ex-showroom comparison requires prices for every selected variant. On-road comparison additionally requires every selected variant to have a price for the same non-empty pricing city. If a comparison cannot be made, the corresponding fields are `null` and `reason` explains why.

Validation responses include HTTP `400` for malformed bodies, invalid IDs, duplicate IDs, or a count outside 2–3; HTTP `404` is returned when one or more valid IDs do not identify an active variant.

## 6. Used-car marketplace

All used-car endpoints are public. Only active listings are returned.

### List used cars

`GET /api/used-cars/`

Query parameters:

| Parameter | Behaviour |
|---|---|
| `make` | Exact manufacturer match, case-insensitive |
| `model` | Partial match against model slug or readable model name |
| `city` | Exact city-slug match, case-insensitive |
| `locality` | Partial locality match |
| `min_price`, `max_price` | Inclusive asking-price range (`price`) |
| `min_year`, `max_year` | Inclusive manufacturing-year range |
| `min_km`, `max_km` | Inclusive kilometres-driven range |
| `fuel` | Exact match, case-insensitive |
| `transmission` | Exact match, case-insensitive |
| `body_type` | Exact match, case-insensitive |
| `seller_type` | Exact match, case-insensitive |
| `owner_count` | Exact owner count |
| `search` | Search text across title, make, model, model name, variant, city and locality |
| `ordering` | `price`, `year`, `km_driven`, `created_at`, or `last_seen_at`, optionally prefixed with `-` for descending order |
| `page` | Page number; default 1 |
| `page_size` | Default 20; maximum 100 |

Default ordering is `-last_seen_at` (most recently seen first). The range filters use the listing's asking `price`; `market_price` is a separate response field.

Uses the DRF page-number pagination envelope (`count`, `next`, `previous`, `results`).

Each listing result contains:

- `id`, `used_car_id`
- `title`, `source_url`, `make`, `model`, `model_name`, `variant`, `year`
- `fuel`, `transmission`, `body_type`
- `price`, `formatted_price`, `market_price`, `currency`
- `km_driven`, `owner_count`, `owner_slug`
- `city`, `city_slug`, `city_id`, `locality`, `seller_type`
- `primary_image`, `images`
- `emi`, `trust_tags`, `ai_tags`, `ai_price_badge`, `map_link`
- `status_text`, `is_active`
- `first_seen_at`, `last_seen_at`, `created_at`, `updated_at`

### Used-car filter options

`GET /api/used-cars/filters/`

Returns options calculated from active database records:

```json
{
  "success": true,
  "total_listings": 0,
  "makes": [],
  "models": [],
  "cities": [],
  "city_slugs": [],
  "localities": [],
  "fuels": [],
  "transmissions": [],
  "body_types": [],
  "seller_types": [],
  "owner_options": [],
  "years": [],
  "price_range": {
    "minimum": null,
    "maximum": null
  }
}
```

### Used-car details

`GET /api/used-cars/{id}/`

Returns one active listing using the same fields as a used-car list result. The `id` path value is the listing's database identifier.

## 7. Dealer accounts and inventory

Dealer application and private inventory endpoints require a JWT access token. A user can submit only one dealer application. A new application starts pending review; only approved and active dealers can create vehicle listings.

### Apply as a dealer

`POST /api/dealers/apply/`

JWT required. The request fields accepted by the serializer are:

- `business_name`, `contact_person`, `email`, `phone`, `alternate_phone`
- `website`, `business_description`
- `address_line1`, `address_line2`, `locality`, `city`, `state`, `pincode`
- `gstin`, `logo_url`

`gstin` is trimmed and converted to uppercase. The application response uses the dealer-profile fields below. The backend assigns the user and manages `verification_status`; do not submit those as client-controlled fields.

### Dealer profile

`GET /api/dealers/profile/`

`PATCH /api/dealers/profile/`

JWT required. Returns the logged-in user's own dealer profile:

- `id`, `business_name`, `contact_person`, `email`, `phone`, `alternate_phone`
- `website`, `business_description`
- `address_line1`, `address_line2`, `locality`, `city`, `state`, `pincode`
- `gstin`, `logo_url`
- `verification_status`, `created_at`, `updated_at`

For PATCH, send only the fields to change. `id`, `verification_status`, `created_at`, and `updated_at` are read-only.

### Dealer inventory list and creation

`GET /api/dealers/inventory/`

JWT required. Returns a plain JSON array containing the logged-in dealer's listings. If the account has no dealer profile, the endpoint returns an empty array.

`POST /api/dealers/inventory/`

JWT required. Only approved and active dealers can create listings. New listings are assigned `pending_review` status by the backend.

Writable listing fields:

- `title`, `make`, `model`, `variant`, `year`
- `fuel`, `transmission`, `body_type`, `price`, `km_driven`, `owner_count`
- `color`, `engine_cc`, `seating_capacity`, `description`
- `city`, `state`, `locality`, `pincode`
- `primary_image`, `images`, `features`

Read-only response fields include `id`, `dealer_name`, `status`, `rejection_reason`, `published_at`, `created_at`, and `updated_at`.

Validation includes: year must be between 1886 and the current year plus one; price must be greater than zero; kilometres driven cannot be negative; owner count must be at least one; `images` and `features` must be lists.

Creation returns HTTP `201 Created` and a dealer inventory listing object.

### Retrieve or edit one dealer listing

`GET /api/dealers/inventory/{pk}/`

`PATCH /api/dealers/inventory/{pk}/`

JWT required. The listing must belong to the logged-in dealer. Dealers cannot directly change listing status or delete listings; no DELETE method is provided by this endpoint.

PATCH accepts writable listing fields. Any edit automatically resets the listing to `pending_review`, clears `published_at`, and clears `rejection_reason`, so administrator review is required again.

### Public dealer marketplace list

`GET /api/dealers/marketplace/`

Public. Only published listings from approved and active dealers are visible.

Query parameters:

| Parameter | Behaviour |
|---|---|
| `search` | Case-insensitive substring search across title, make, model, variant and city |
| `make`, `model`, `city` | Exact match, case-insensitive |
| `fuel`, `transmission`, `body_type` | Exact match, case-insensitive |
| `min_price`, `max_price` | Inclusive price bounds; non-negative integers |
| `min_year`, `max_year` | Inclusive manufacturing-year bounds; integers |
| `ordering` | `price`, `-price`, `year`, `-year`, `km_driven`, `-km_driven`, `published_at`, or `-published_at`; default `-published_at` |
| `page` | Page number; default 1 |
| `page_size` | Default 20; maximum 100 |

Invalid integers, negative price bounds, minimum greater than maximum, or an unsupported ordering value return HTTP `400`. Uses the DRF page-number pagination envelope.

Public result fields:

- `id`, `dealer_name`, `title`, `make`, `model`, `variant`, `year`
- `fuel`, `transmission`, `body_type`, `price`, `km_driven`, `owner_count`
- `color`, `engine_cc`, `seating_capacity`, `description`
- `city`, `state`, `locality`, `pincode`
- `primary_image`, `images`, `features`
- `published_at`, `created_at`

The public serializer does not expose internal moderation fields such as `status` or `rejection_reason`.

### Public dealer marketplace filter options

`GET /api/dealers/marketplace/filters/`

Returns filter options calculated only from currently public listings:

```json
{
  "total_listings": 0,
  "makes": [],
  "models": [],
  "cities": [],
  "fuels": [],
  "transmissions": [],
  "body_types": [],
  "years": [],
  "price_range": {
    "min": null,
    "max": null
  }
}
```

Unlike `/api/used-cars/filters/`, this response does not include a `success` field. The price-range keys are `min` and `max`.

### Public dealer listing detail

`GET /api/dealers/marketplace/{pk}/`

Returns one published listing from an approved and active dealer, using the public result fields described above.

## 8. Customer enquiries

### Create an enquiry

`POST /api/enquiries/`

Public. Guests can submit an enquiry. A signed-in customer may optionally send a valid JWT access token; when provided, the enquiry is associated with that user. Limited to 5 requests per hour.

Request body fields:

```json
{
  "vehicle_id": "<published_dealer_listing_id>",
  "customer_name": "Aman Sharma",
  "phone": "9876543210",
  "email": "aman@example.com",
  "message": "I would like to know more about this car.",
  "preferred_contact_method": "phone",
  "consent_to_contact": true
}
```

`vehicle_id` must identify a published vehicle whose dealer is approved and active. Customer name is trimmed and must contain at least 2 characters. Phone is normalized and must contain 7–15 digits, with an optional leading `+`. Email is trimmed and lowercased. `consent_to_contact` must be `true`. If `preferred_contact_method` is `email`, an email address is required.

Successful response is HTTP `201 Created` with:

- `id`, `vehicle_id`, `vehicle_title`, `dealer_name`
- `customer_name`, `phone`, `email`, `message`
- `preferred_contact_method`, `consent_to_contact`
- `status`, `created_at`

The backend sets the initial status to `new`.

### Dealer enquiry inbox

`GET /api/enquiries/dealer/`

JWT required. Only approved and active dealers can access the inbox. Returns a plain JSON array of the dealer's enquiries, newest first. Each item contains:

- `id`, `vehicle_id`, `vehicle_title`, `dealer_name`
- `customer_name`, `phone`, `email`, `message`
- `preferred_contact_method`, `consent_to_contact`, `status`
- `dealer_notes`, `last_contacted_at`, `created_at`, `updated_at`

### Retrieve or update one enquiry

`GET /api/enquiries/dealer/{pk}/`

`PATCH /api/enquiries/dealer/{pk}/`

JWT required. Only the assigned approved and active dealer can access the enquiry.

PATCH accepts:

```json
{
  "status": "contacted",
  "dealer_notes": "Called the customer; follow-up planned."
}
```

Allowed status values are `contacted`, `converted`, and `closed`. The initial `new` status is set by the backend. When status is changed to `contacted`, the backend updates `last_contacted_at`. The response is the complete dealer-facing enquiry object.

## 9. Vehicle price valuation

### Estimate a used-car value

`POST /api/pricing/estimate/`

Public. Guests can calculate an estimate. When a valid JWT access token is supplied, the result is also saved in the signed-in customer's valuation history. Limited to 20 requests per hour.

Request body:

```json
{
  "make": "Maruti Suzuki",
  "model": "Swift",
  "year": 2022,
  "fuel": "Petrol",
  "transmission": "Manual",
  "km_driven": 25000,
  "city": "Kolkata"
}
```

Required fields: `make`, `model`, `year`, `fuel`, `transmission`, and `km_driven`. `city` is optional and defaults to an empty string. Year must be between 1886 and the current year plus one; `km_driven` must be non-negative. Text fields have maximum lengths defined by the serializer.

The response contains the valuation service's result fields plus `valuation_id`:

- The view explicitly uses `estimated_price`, `price_range.lower`, `price_range.upper`, `comparable_count`, `confidence`, `comparison_scope`, and `status` from the valuation result.
- `valuation_id` is `null` for a guest; for an authenticated customer it is the ID of the saved history record.

The precise full response shape is defined by `estimate_vehicle_price()` in `apps/pricing/services/valuation.py`; that service output was not included in the source excerpt used to prepare this document. Check a live response or that service file before building a strongly typed frontend interface for every nested result field.

A `ValueError` raised by the valuation service is returned as HTTP `400` with a `detail` field.

### Valuation history

`GET /api/pricing/history/`

JWT required. Returns only the authenticated customer's own records, newest first. Query parameters: `page` (default 1) and `page_size` (default 20, maximum 100).

Response envelope:

```json
{
  "count": 0,
  "page": 1,
  "page_size": 20,
  "total_pages": 0,
  "next_page": null,
  "previous_page": null,
  "results": []
}
```

Each result contains:

- `id`, `make`, `model`, `year`, `fuel`, `transmission`, `km_driven`, `city`
- `estimated_price`, `minimum_price`, `maximum_price`
- `comparable_count`, `confidence`, `comparison_scope`, `valuation_status`
- `result_data`, `created_at`

### Valuation history detail

`GET /api/pricing/history/{pk}/`

JWT required. Returns one valuation history record belonging to the authenticated customer, using the fields described above. A record belonging to another user is not exposed.

## 10. Error handling

The backend uses DRF responses. Common patterns include:

### Custom/manual error

```json
{
  "detail": "A human-readable explanation of the error."
}
```

### Serializer validation error

Validation errors can be field-keyed, for example:

```json
{
  "email": ["Enter a valid email address."]
}
```

Do not assume every validation response uses only a `detail` property. The frontend should display field-level errors when the response body contains field names and a general message for non-field errors.

### Common HTTP statuses

| Status | Meaning / frontend action |
|---:|---|
| `200` | Successful retrieval or update |
| `201` | Resource created successfully |
| `205` | Logout succeeded; clear local token state |
| `400` | Invalid input, malformed request, or validation failure |
| `401` | Missing, invalid or expired access token; attempt refresh only when appropriate |
| `403` | Authenticated user lacks permission, for example a dealer is not approved/active |
| `404` | Resource does not exist or is not visible to the current user |
| `429` | Request throttled; show a retry message and avoid immediate repeated requests |

## 11. Configured rate limits

These are the configured DRF throttle scopes:

| Operation | Limit |
|---|---:|
| Customer registration | 5/hour |
| Login | 10/minute |
| Token refresh | 30/hour |
| Customer enquiry creation | 5/hour |
| Vehicle valuation estimate | 20/hour |

When the limit is exceeded, expect HTTP `429 Too Many Requests`.

## 12. Frontend integration notes

1. Keep the API base URL in `VITE_API_BASE_URL` and centralize HTTP requests in one API client.
2. Store the access and refresh tokens using the frontend's chosen security approach. Never put tokens in a URL or log them. Avoid long-lived token storage in browser local storage when a safer architecture is available.
3. Add `Authorization: Bearer ...` only when a valid access token is available. Enquiry creation and valuation should still work for guests.
4. On refresh, replace **both** token values with the newly returned `access` and `refresh` tokens. Do not retry refresh forever; a rejected refresh token requires the user to sign in again.
5. Handle both pagination formats: `next`/`previous` URLs for used cars and dealer marketplace; page-number fields for the new-car catalogue and valuation history.
6. Build filter controls from `/used-cars/filters/` and `/dealers/marketplace/filters/` rather than hard-coding available values.
7. A dealer listing may be pending review after creation or edit. Do not assume that it will immediately appear in the public marketplace.
8. Do not expose dealer moderation fields in public vehicle cards; the public serializer intentionally omits them.
9. Treat image URLs and external source URLs as data returned by the API. Confirm licensing and redistribution rights before using third-party catalogue/listing images commercially.
10. Do not infer that a city has on-road pricing merely because a model or variant exists. The API may return missing on-road price values or indicate that selected variants cannot be compared for the same city.

## 13. Implementation notes and items to verify before frontend typing

- The exact nested response contract for `POST /api/pricing/estimate/` should be confirmed from `apps/pricing/services/valuation.py` or a live response; this document lists the result keys directly referenced by the view and the saved-history serializer.
- Model-level required/optional flags and choice values for dealer profile/listing fields are not fully visible in serializer/view excerpts. Use the Django model definitions or a live validation response before marking every such form field as mandatory or building fixed dropdown choices.
- The API reference describes the backend implementation captured during documentation preparation. Update this file when routes, serializers, permissions, throttles, or response envelopes change.
