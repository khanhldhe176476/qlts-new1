import api from './api'

export const authService = {
  login: (username, password) => {
    return api.post('/v1/auth/login', { username, password })
  },
  logout: () => {
    return api.post('/v1/auth/logout')
  },
  getCurrentUser: () => {
    return api.get('/v1/auth/me')
  },
  refreshToken: (refreshToken) => {
    return api.post('/v1/auth/refresh', { refresh_token: refreshToken })
  },
}




















