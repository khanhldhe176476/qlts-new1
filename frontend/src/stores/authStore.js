import { create } from 'zustand'

// Simple persist using localStorage
const getStoredAuth = () => {
  try {
    const stored = localStorage.getItem('auth-storage')
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    return null
  }
  return null
}

const setStoredAuth = (state) => {
  try {
    localStorage.setItem('auth-storage', JSON.stringify(state))
  } catch (e) {
    console.error('Failed to save auth to localStorage', e)
  }
}

const stored = getStoredAuth()

export const useAuthStore = create((set) => ({
  isAuthenticated: stored?.isAuthenticated || false,
  user: stored?.user || null,
  token: stored?.token || null,
  login: (user, token) => {
    const newState = { isAuthenticated: true, user, token }
    set(newState)
    setStoredAuth(newState)
  },
  logout: () => {
    const newState = { isAuthenticated: false, user: null, token: null }
    set(newState)
    setStoredAuth(newState)
  },
}))

