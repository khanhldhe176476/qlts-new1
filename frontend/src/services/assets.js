import api from './api'

export const assetService = {
  getAll: (params = {}) => {
    return api.get('/v1/assets', { params })
  },
  getById: (id) => {
    return api.get(`/v1/assets/${id}`)
  },
  create: (data) => {
    return api.post('/v1/assets', data)
  },
  update: (id, data) => {
    return api.put(`/v1/assets/${id}`, data)
  },
  delete: (id) => {
    return api.delete(`/v1/assets/${id}`)
  },
  import: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/v1/assets/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  export: (params = {}) => {
    return api.get('/v1/assets/export', { params, responseType: 'blob' })
  },
}




















