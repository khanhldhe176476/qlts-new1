import api from './api'

export const userService = {
  getAll: (params = {}) => {
    return api.get('/v1/users', { params })
  },
  getById: (id) => {
    return api.get(`/v1/users/${id}`)
  },
  create: (data) => {
    return api.post('/v1/users', data)
  },
  update: (id, data) => {
    return api.put(`/v1/users/${id}`, data)
  },
  delete: (id) => {
    return api.delete(`/v1/users/${id}`)
  },
}

















