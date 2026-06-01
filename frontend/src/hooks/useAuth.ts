import { useState, useEffect, useCallback } from 'react'
import { clearAuthToken, fetchAuthMe, logout } from '../api/client'
import type { AuthUser } from '../types'

export function useAuth() {
  const [authLoading, setAuthLoading] = useState(true)
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null)

  const loadCurrentUser = useCallback(async () => {
    try {
      const me = await fetchAuthMe()
      setCurrentUser(me.user)
    } catch {
      clearAuthToken()
      setCurrentUser(null)
    } finally {
      setAuthLoading(false)
    }
  }, [])

  useEffect(() => {
    loadCurrentUser()
  }, [loadCurrentUser])

  const handleLogout = useCallback(async () => {
    await logout()
    setCurrentUser(null)
  }, [])

  const handleLoginSuccess = useCallback((user: AuthUser) => {
    setCurrentUser(user)
  }, [])

  const handlePasswordChanged = useCallback((user: AuthUser) => {
    setCurrentUser(user)
  }, [])

  return {
    authLoading,
    currentUser,
    handleLogout,
    handleLoginSuccess,
    handlePasswordChanged,
    isAdmin: currentUser?.role === 'admin',
    canSubmit: Boolean(currentUser),
  }
}
