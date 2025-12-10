import api from './api'

export const transferService = {
  getAll: (params = {}) => {
    return api.get('/v1/transfers', { params })
  },
  getById: (id) => {
    return api.get(`/v1/transfers/${id}`)
  },
  create: (data) => {
    return api.post('/v1/transfers', data)
  },
  confirm: (token, data) => {
    return api.post(`/v1/transfers/confirm/${token}`, data)
  },
  cancel: (id) => {
    return api.post(`/v1/transfers/${id}/cancel`)
  },
}




















