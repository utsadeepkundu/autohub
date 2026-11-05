import { apiRequest } from './api'

export function registerCustomer(payload) {
  return apiRequest('/accounts/register/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function loginCustomer(payload) {
  return apiRequest('/accounts/login/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getCurrentUser() {
  return apiRequest('/accounts/me/')
}

export function logoutCustomer(refresh) {
  return apiRequest('/accounts/logout/', {
    method: 'POST',
    body: JSON.stringify({ refresh }),
  })
}
