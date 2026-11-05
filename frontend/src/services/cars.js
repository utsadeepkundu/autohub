
import { apiRequest } from './api'

/**
 * Get all active car manufacturers.
 * GET /api/cars/brands/
 */
export function getCarBrands() {
  return apiRequest('/cars/brands/')
}

/**
 * Get models belonging to a manufacturer.
 * Supports pagination.
 *
 * GET /api/cars/brands/{brand_slug}/models/
 */
export function getBrandModels(brandSlug, params = {}) {
  const query = buildQuery(params)

  return apiRequest(
    `/cars/brands/${encodeURIComponent(brandSlug)}/models/${query}`
  )
}

/**
 * Search active car models and manufacturers.
 *
 * GET /api/cars/search/?q=...
 */
export function searchCars(searchTerm, params = {}) {
  const query = buildQuery({
    q: searchTerm,
    ...params,
  })

  return apiRequest(`/cars/search/${query}`)
}

/**
 * Get complete details of a car model.
 *
 * GET /api/cars/brands/{brand_slug}/models/{model_slug}/
 */
export function getCarModelDetails(brandSlug, modelSlug) {
  return apiRequest(
    `/cars/brands/${encodeURIComponent(brandSlug)}/models/${encodeURIComponent(modelSlug)}/`
  )
}

/**
 * Get model variants with filters, sorting and pagination.
 *
 * Supported filters:
 * fuel, transmission, body_type, pricing_city,
 * min_price, max_price, ordering, page, page_size
 */
export function getCarVariants(brandSlug, modelSlug, params = {}) {
  const query = buildQuery(params)

  return apiRequest(
    `/cars/brands/${encodeURIComponent(brandSlug)}/models/${encodeURIComponent(modelSlug)}/variants/${query}`
  )
}

/**
 * Get details of an individual car variant.
 *
 * GET /api/cars/brands/{brand_slug}/models/{model_slug}/variants/{variant_slug}/
 */
export function getCarVariantDetails(
  brandSlug,
  modelSlug,
  variantSlug
) {
  return apiRequest(
    `/cars/brands/${encodeURIComponent(brandSlug)}/models/${encodeURIComponent(modelSlug)}/variants/${encodeURIComponent(variantSlug)}/`
  )
}

/**
 * Compare two or three car variants.
 *
 * POST /api/cars/compare/
 */
export function compareCarVariants(variantIds) {
  return apiRequest('/cars/compare/', {
    method: 'POST',
    body: JSON.stringify({
      variant_ids: variantIds,
    }),
  })
}

/**
 * Build query strings while ignoring empty values.
 */
function buildQuery(params) {
  const searchParams = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (
      value !== undefined &&
      value !== null &&
      String(value).trim() !== ''
    ) {
      searchParams.set(key, String(value))
    }
  })

  const queryString = searchParams.toString()

  return queryString ? `?${queryString}` : ''
}
