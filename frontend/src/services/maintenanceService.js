/**
 * Service để gọi API cho Maintenance
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api/v1';

// Lấy token từ localStorage hoặc session
const getAuthToken = () => {
  return localStorage.getItem('token') || sessionStorage.getItem('token');
};

// Helper function để gọi API
const apiCall = async (endpoint, options = {}) => {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Có lỗi xảy ra' }));
    throw new Error(error.message || 'Có lỗi xảy ra');
  }

  return response.json();
};

// Helper function để upload file
const uploadFile = async (endpoint, formData) => {
  const token = getAuthToken();
  const headers = {};

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Có lỗi xảy ra' }));
    throw new Error(error.message || 'Có lỗi xảy ra');
  }

  return response.json();
};

export const maintenanceService = {
  // Lấy danh sách bảo trì với filter và phân trang
  getList: async (params = {}) => {
    const queryParams = new URLSearchParams();
    
    if (params.page) queryParams.append('page', params.page);
    if (params.per_page) queryParams.append('per_page', params.per_page);
    if (params.asset_id) queryParams.append('asset_id', params.asset_id);
    if (params.asset_type_id) queryParams.append('asset_type_id', params.asset_type_id);
    if (params.status) queryParams.append('status', params.status);
    if (params.type) queryParams.append('type', params.type);
    if (params.vendor) queryParams.append('vendor', params.vendor);
    if (params.date_from) queryParams.append('date_from', params.date_from);
    if (params.date_to) queryParams.append('date_to', params.date_to);
    if (params.search) queryParams.append('search', params.search);

    const queryString = queryParams.toString();
    return apiCall(`/maintenance${queryString ? `?${queryString}` : ''}`);
  },

  // Lấy chi tiết một bảo trì
  getById: async (id) => {
    return apiCall(`/maintenance/${id}`);
  },

  // Tạo mới bảo trì
  create: async (data) => {
    return apiCall('/maintenance', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Cập nhật bảo trì
  update: async (id, data) => {
    return apiCall(`/maintenance/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // Xóa bảo trì
  delete: async (id) => {
    return apiCall(`/maintenance/${id}`, {
      method: 'DELETE',
    });
  },

  // Upload file đính kèm
  uploadFile: async (id, fileType, file) => {
    const formData = new FormData();
    formData.append('file_type', fileType);
    formData.append(fileType, file);
    return uploadFile(`/maintenance/${id}/upload`, formData);
  },

  // Export Excel
  exportExcel: async (params = {}) => {
    const token = getAuthToken();
    const queryParams = new URLSearchParams();
    
    if (params.asset_id) queryParams.append('asset_id', params.asset_id);
    if (params.asset_type_id) queryParams.append('asset_type_id', params.asset_type_id);
    if (params.status) queryParams.append('status', params.status);
    if (params.vendor) queryParams.append('vendor', params.vendor);
    if (params.date_from) queryParams.append('date_from', params.date_from);
    if (params.date_to) queryParams.append('date_to', params.date_to);

    const queryString = queryParams.toString();
    const url = `${API_BASE_URL}/maintenance/export${queryString ? `?${queryString}` : ''}`;
    
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, { headers });
    
    if (!response.ok) {
      throw new Error('Có lỗi khi xuất Excel');
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `bao_tri_${new Date().toISOString().split('T')[0]}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  },
};

