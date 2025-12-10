import api from './api'

export const assetTypeService = {
  getAll: () => {
    return api.get('/v1/asset-types')
  },
  getById: (id) => {
    return api.get(`/v1/asset-types/${id}`)
  },
  create: (data) => {
    return api.post('/v1/asset-types', data)
  },
  update: (id, data) => {
    return api.put(`/v1/asset-types/${id}`, data)
  },
  delete: (id) => {
    return api.delete(`/v1/asset-types/${id}`)
  },
}




















