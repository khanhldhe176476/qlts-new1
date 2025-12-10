import api from './api'

export const maintenanceService = {
  getAll: (params = {}) => {
    return api.get('/v1/maintenance', { params })
  },
  getById: (id) => {
    return api.get(`/v1/maintenance/${id}`)
  },
  create: (data) => {
    return api.post('/v1/maintenance', data)
  },
  update: (id, data) => {
    return api.put(`/v1/maintenance/${id}`, data)
  },
  delete: (id) => {
    return api.delete(`/v1/maintenance/${id}`)
  },
}

















