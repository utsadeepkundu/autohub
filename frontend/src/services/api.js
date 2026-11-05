const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  'http://127.0.0.1:8000/api'
).replace(/\/+$/, '')

const ACCESS_TOKEN_KEY = 'autohub_access_token'
const REFRESH_TOKEN_KEY = 'autohub_refresh_token'
let refreshInFlight = null

export function getAccessToken() {
  return window.sessionStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken() {
  return window.sessionStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setAuthTokens(tokens = {}) {
  if (tokens.access) {
    window.sessionStorage.setItem(ACCESS_TOKEN_KEY, tokens.access)
  }
  if (tokens.refresh) {
    window.sessionStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh)
  }
}

export function clearAuthTokens() {
  window.sessionStorage.removeItem(ACCESS_TOKEN_KEY)
  window.sessionStorage.removeItem(REFRESH_TOKEN_KEY)
}

async function parseResponse(response) {
  const responseText = await response.text()
  if (!responseText) return null

  try {
    return JSON.parse(responseText)
  } catch {
    return responseText
  }
}

function getErrorMessage(data, statusCode) {
  if (typeof data === 'string' && data.trim()) return data
  if (data?.detail) return String(data.detail)

  if (data && typeof data === 'object') {
    const messages = Object.entries(data).map(([field, errors]) => {
      const values = Array.isArray(errors) ? errors : [errors]
      return `${field}: ${values.map(String).join(', ')}`
    })
    if (messages.length) return messages.join(' | ')
  }

  return `API request failed (${statusCode})`
}

async function refreshAccessToken() {
  if (refreshInFlight) return refreshInFlight

  const refresh = getRefreshToken()
  if (!refresh) return null

  refreshInFlight = (async () => {
    const response = await fetch(`${API_BASE_URL}/accounts/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    })
    const data = await parseResponse(response)

    if (!response.ok || !data?.access || !data?.refresh) {
      clearAuthTokens()
      throw new Error(getErrorMessage(data, response.status))
    }

    setAuthTokens(data)
    return data.access
  })()

  try {
    return await refreshInFlight
  } finally {
    refreshInFlight = null
  }
}

export async function apiRequest(path, options = {}) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const url = `${API_BASE_URL}${normalizedPath}`
  const requestHeaders = new Headers(options.headers || {})

  if (options.body && !(options.body instanceof FormData) && !requestHeaders.has('Content-Type')) {
    requestHeaders.set('Content-Type', 'application/json')
  }

  const token = getAccessToken()
  if (token && !requestHeaders.has('Authorization')) {
    requestHeaders.set('Authorization', `Bearer ${token}`)
  }

  const send = () => fetch(url, { ...options, headers: requestHeaders })
  let response = await send()

  const canRefresh = response.status === 401 &&
    !normalizedPath.startsWith('/accounts/login/') &&
    !normalizedPath.startsWith('/accounts/register/') &&
    !normalizedPath.startsWith('/accounts/token/refresh/') &&
    !normalizedPath.startsWith('/accounts/logout/') &&
    Boolean(getRefreshToken())

  if (canRefresh) {
    try {
      const newAccess = await refreshAccessToken()
      if (newAccess) {
        requestHeaders.set('Authorization', `Bearer ${newAccess}`)
        response = await send()
      }
    } catch {
      clearAuthTokens()
    }
  }

  const data = await parseResponse(response)
  if (!response.ok) {
    const error = new Error(getErrorMessage(data, response.status))
    error.status = response.status
    error.data = data
    throw error
  }

  return data
}

export default API_BASE_URL
