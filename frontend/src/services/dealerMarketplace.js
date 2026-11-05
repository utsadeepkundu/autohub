import { apiRequest } from './api'

function queryString(params = {}) {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== '') query.set(key, String(value))
  })
  const value = query.toString()
  return value ? `?${value}` : ''
}

export function getDealerMarketplaceVehicles(params = {}) {
  return apiRequest(`/dealers/marketplace/${queryString(params)}`)
}

export function getDealerMarketplaceFilters() {
  return apiRequest('/dealers/marketplace/filters/')
}

export function getDealerMarketplaceVehicle(vehicleId) {
  return apiRequest(`/dealers/marketplace/${encodeURIComponent(vehicleId)}/`)
}

export function submitVehicleEnquiry(payload) {
  return apiRequest('/enquiries/', { method: 'POST', body: JSON.stringify(payload) })
}
