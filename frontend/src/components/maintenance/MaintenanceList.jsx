import React, { useState, useEffect } from 'react';
import { maintenanceService } from '../../services/maintenanceService';
import './MaintenanceList.css';

const MaintenanceList = ({ onEdit, onView, onDelete, assetTypes = [] }) => {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 20,
    total: 0,
    pages: 0,
  });

  const [filters, setFilters] = useState({
    search: '',
    asset_type_id: '',
    vendor: '',
    status: '',
    date_from: '',
    date_to: '',
  });

  const [vendors, setVendors] = useState([]);

  useEffect(() => {
    loadData();
    loadVendors();
  }, [pagination.page, filters]);

  const loadData = async () => {
    try {
      setLoading(true);
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        ...filters,
      };
      
      // Remove empty filters
      Object.keys(params).forEach(key => {
        if (params[key] === '') {
          delete params[key];
        }
      });

      const response = await maintenanceService.getList(params);
      setRecords(response.items || []);
      setPagination(response.pagination || pagination);
    } catch (error) {
      alert('Lỗi khi tải dữ liệu: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const loadVendors = async () => {
    try {
      const response = await maintenanceService.getList({ per_page: 1000 });
      const uniqueVendors = [...new Set(response.items.map(r => r.vendor).filter(Boolean))];
      setVendors(uniqueVendors);
    } catch (error) {
      console.error('Error loading vendors:', error);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters({ ...filters, [name]: value });
    setPagination({ ...pagination, page: 1 }); // Reset to first page
  };

  const handlePageChange = (newPage) => {
    setPagination({ ...pagination, page: newPage });
  };

  const handleExport = async () => {
    try {
      setLoading(true);
      const params = { ...filters };
      Object.keys(params).forEach(key => {
        if (params[key] === '') {
          delete params[key];
        }
      });
      await maintenanceService.exportExcel(params);
      alert('Xuất Excel thành công!');
    } catch (error) {
      alert('Lỗi khi xuất Excel: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Bạn có chắc muốn xóa bản ghi này?')) {
      return;
    }

    try {
      setLoading(true);
      await maintenanceService.delete(id);
      alert('Xóa thành công!');
      loadData();
    } catch (error) {
      alert('Lỗi khi xóa: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      'pending': { label: 'Chờ xử lý', class: 'badge-warning' },
      'in_progress': { label: 'Đang thực hiện', class: 'badge-info' },
      'completed': { label: 'Hoàn thành', class: 'badge-success' },
      'failed': { label: 'Không đạt', class: 'badge-danger' },
      'cancelled': { label: 'Hủy', class: 'badge-secondary' },
    };
    const statusInfo = statusMap[status] || { label: status, class: 'badge-secondary' };
    return <span className={`badge ${statusInfo.class}`}>{statusInfo.label}</span>;
  };

  const getReasonLabel = (reason) => {
    const reasonMap = {
      'broken': 'Lỗi kỹ thuật',
      'periodic': 'Bảo trì định kỳ',
      'calibration': 'Hiệu chỉnh',
      'other': 'Khác',
    };
    return reasonMap[reason] || reason;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN');
  };

  const formatCurrency = (amount) => {
    if (!amount) return 'N/A';
    return new Intl.NumberFormat('vi-VN').format(amount);
  };

  return (
    <div className="maintenance-list">
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            <i className="fas fa-tools mr-2"></i>Danh sách bảo trì thiết bị
          </h3>
          <div className="card-tools">
            <button
              className="btn btn-success btn-sm mr-2"
              onClick={handleExport}
              disabled={loading}
            >
              <i className="fas fa-file-excel mr-1"></i>Xuất Excel
            </button>
            <button
              className="btn btn-primary btn-sm"
              onClick={() => onEdit && onEdit(null)}
            >
              <i className="fas fa-plus mr-1"></i>Tạo yêu cầu bảo trì
            </button>
          </div>
        </div>
        <div className="card-body">
          {/* Filter Section */}
          <div className="filter-section mb-3">
            <div className="row">
              <div className="col-md-3">
                <div className="form-group">
                  <label>Tìm kiếm</label>
                  <input
                    type="text"
                    name="search"
                    className="form-control"
                    value={filters.search}
                    onChange={handleFilterChange}
                    placeholder="Tên tài sản, mã tài sản..."
                  />
                </div>
              </div>
              <div className="col-md-2">
                <div className="form-group">
                  <label>Loại tài sản</label>
                  <select
                    name="asset_type_id"
                    className="form-control"
                    value={filters.asset_type_id}
                    onChange={handleFilterChange}
                  >
                    <option value="">Tất cả</option>
                    {assetTypes.map(type => (
                      <option key={type.id} value={type.id}>
                        {type.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="col-md-2">
                <div className="form-group">
                  <label>Đơn vị bảo trì</label>
                  <select
                    name="vendor"
                    className="form-control"
                    value={filters.vendor}
                    onChange={handleFilterChange}
                  >
                    <option value="">Tất cả</option>
                    {vendors.map(vendor => (
                      <option key={vendor} value={vendor}>
                        {vendor}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="col-md-2">
                <div className="form-group">
                  <label>Trạng thái</label>
                  <select
                    name="status"
                    className="form-control"
                    value={filters.status}
                    onChange={handleFilterChange}
                  >
                    <option value="">Tất cả</option>
                    <option value="pending">Chờ xử lý</option>
                    <option value="in_progress">Đang thực hiện</option>
                    <option value="completed">Hoàn thành</option>
                    <option value="failed">Không đạt</option>
                    <option value="cancelled">Hủy</option>
                  </select>
                </div>
              </div>
              <div className="col-md-3">
                <div className="row">
                  <div className="col-6">
                    <div className="form-group">
                      <label>Ngày từ</label>
                      <input
                        type="date"
                        name="date_from"
                        className="form-control"
                        value={filters.date_from}
                        onChange={handleFilterChange}
                      />
                    </div>
                  </div>
                  <div className="col-6">
                    <div className="form-group">
                      <label>Ngày đến</label>
                      <input
                        type="date"
                        name="date_to"
                        className="form-control"
                        value={filters.date_to}
                        onChange={handleFilterChange}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Table */}
          <div className="table-responsive">
            <table className="table table-bordered table-striped">
              <thead>
                <tr>
                  <th>STT</th>
                  <th>Mã tài sản</th>
                  <th>Tên tài sản</th>
                  <th>Loại tài sản</th>
                  <th>Ngày yêu cầu</th>
                  <th>Người yêu cầu</th>
                  <th>Nguyên nhân</th>
                  <th>Đơn vị bảo trì</th>
                  <th>Chi phí</th>
                  <th>Trạng thái</th>
                  <th>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="11" className="text-center">
                      <div className="spinner-border spinner-border-sm" role="status">
                        <span className="sr-only">Đang tải...</span>
                      </div>
                    </td>
                  </tr>
                ) : records.length === 0 ? (
                  <tr>
                    <td colSpan="11" className="text-center">Không có dữ liệu</td>
                  </tr>
                ) : (
                  records.map((record, index) => (
                    <tr key={record.id}>
                      <td>{(pagination.page - 1) * pagination.per_page + index + 1}</td>
                      <td>{record.asset_code || 'N/A'}</td>
                      <td>{record.asset_name || 'N/A'}</td>
                      <td>{record.asset_type_name || 'N/A'}</td>
                      <td>{formatDate(record.request_date)}</td>
                      <td>{record.requested_by_name || 'N/A'}</td>
                      <td>{getReasonLabel(record.maintenance_reason)}</td>
                      <td>{record.vendor || 'N/A'}</td>
                      <td>{formatCurrency(record.cost)}</td>
                      <td>{getStatusBadge(record.status)}</td>
                      <td>
                        <div className="btn-group">
                          {onView && (
                            <button
                              className="btn btn-sm btn-info"
                              onClick={() => onView(record.id)}
                              title="Xem chi tiết"
                            >
                              <i className="fas fa-eye"></i>
                            </button>
                          )}
                          {onEdit && (
                            <button
                              className="btn btn-sm btn-warning"
                              onClick={() => onEdit(record.id)}
                              title="Sửa"
                            >
                              <i className="fas fa-edit"></i>
                            </button>
                          )}
                          {onDelete && (
                            <button
                              className="btn btn-sm btn-danger"
                              onClick={() => handleDelete(record.id)}
                              title="Xóa"
                            >
                              <i className="fas fa-trash"></i>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {pagination.pages > 1 && (
            <div className="pagination-section mt-3">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <p className="text-muted mb-0">
                    Hiển thị {(pagination.page - 1) * pagination.per_page + 1} -{' '}
                    {Math.min(pagination.page * pagination.per_page, pagination.total)} trong tổng số{' '}
                    {pagination.total} bản ghi
                  </p>
                </div>
                <nav>
                  <ul className="pagination mb-0">
                    <li className={`page-item ${pagination.page === 1 ? 'disabled' : ''}`}>
                      <button
                        className="page-link"
                        onClick={() => handlePageChange(pagination.page - 1)}
                        disabled={pagination.page === 1}
                      >
                        Trước
                      </button>
                    </li>
                    {[...Array(pagination.pages)].map((_, i) => {
                      const pageNum = i + 1;
                      if (
                        pageNum === 1 ||
                        pageNum === pagination.pages ||
                        (pageNum >= pagination.page - 2 && pageNum <= pagination.page + 2)
                      ) {
                        return (
                          <li
                            key={pageNum}
                            className={`page-item ${pagination.page === pageNum ? 'active' : ''}`}
                          >
                            <button
                              className="page-link"
                              onClick={() => handlePageChange(pageNum)}
                            >
                              {pageNum}
                            </button>
                          </li>
                        );
                      } else if (
                        pageNum === pagination.page - 3 ||
                        pageNum === pagination.page + 3
                      ) {
                        return (
                          <li key={pageNum} className="page-item disabled">
                            <span className="page-link">...</span>
                          </li>
                        );
                      }
                      return null;
                    })}
                    <li
                      className={`page-item ${pagination.page === pagination.pages ? 'disabled' : ''}`}
                    >
                      <button
                        className="page-link"
                        onClick={() => handlePageChange(pagination.page + 1)}
                        disabled={pagination.page === pagination.pages}
                      >
                        Sau
                      </button>
                    </li>
                  </ul>
                </nav>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MaintenanceList;

