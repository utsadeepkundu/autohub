
import { apiRequest } from './api';

const buildQuery = (params = {}) => {
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (
      value !== undefined &&
      value !== null &&
      value !== ''
    ) {
      query.append(key, String(value));
    }
  });

  return query.toString();
};

// Get used car listings with search, filters, sorting and pagination.
export const getUsedCars = (params = {}) => {
  const query = buildQuery(params);
  const endpoint = query
    ? `/used-cars/?${query}`
    : '/used-cars/';

  return apiRequest(endpoint);
};

// Get all available filter options.
// Get available filter options.
// Supports optional manufacturer-specific model filtering.
export const getUsedCarFilters = (params = {}) => {
  const query = buildQuery(params);

  const endpoint = query
    ? `/used-cars/filters/?${query}`
    : '/used-cars/filters/';

  return apiRequest(endpoint);
};
// Get details of a particular used car.
export const getUsedCarDetails = (carId) => {
  if (!carId) {
    throw new Error('A valid used car ID is required.');
  }

  return apiRequest(`/used-cars/${encodeURIComponent(carId)}/`);
};
