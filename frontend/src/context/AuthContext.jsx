import { useCallback, useEffect, useMemo, useState } from 'react'
import { AuthContext } from './AuthContext'
import {
  clearAuthTokens,
  getAccessToken,
  getRefreshToken,
  setAuthTokens,
} from '../services/api'
import {
  getCurrentUser,
  loginCustomer,
  logoutCustomer,
  registerCustomer,
} from '../services/auth'


export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadUser = useCallback(async () => {
    const hasTokens = getAccessToken() || getRefreshToken()
    if (!hasTokens) {
      setUser(null)
      setLoading(false)
      return null
    }

    try {
      const profile = await getCurrentUser()
      setUser(profile)
      return profile
    } catch {
      clearAuthTokens()
      setUser(null)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let active = true
    Promise.resolve().then(() => {
      if (active) loadUser()
    })
    return () => { active = false }
  }, [loadUser])

  const login = useCallback(async (credentials) => {
    const tokens = await loginCustomer(credentials)
    setAuthTokens(tokens)
    const profile = await getCurrentUser()
    setUser(profile)
    return profile
  }, [])

  const register = useCallback(async (details) => {
    await registerCustomer(details)
    return login({ email: details.email, password: details.password })
  }, [login])

  const logout = useCallback(async () => {
    const refresh = getRefreshToken()
    try {
      if (refresh) await logoutCustomer(refresh)
    } finally {
      clearAuthTokens()
      setUser(null)
    }
  }, [])

  const value = useMemo(() => ({
    user,
    loading,
    isAuthenticated: Boolean(user),
    login,
    register,
    logout,
    refreshUser: loadUser,
  }), [user, loading, login, register, logout, loadUser])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
