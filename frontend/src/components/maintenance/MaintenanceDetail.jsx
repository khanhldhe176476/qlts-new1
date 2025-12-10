import React, { useState, useEffect } from 'react';
import { maintenanceService } from '../../services/maintenanceService';
import './MaintenanceDetail.css';

const MaintenanceDetail = ({ maintenanceId, onEdit, onBack }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [maintenanceId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const result = await maintenanceService.getById(maintenanceId);
      setData(result);
    } catch (error) {
      alert('Lỗi khi tải dữ liệu: ' + error.message);
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
    return reasonMap[reason] || reason || 'N/A';
  };

  const getDamageLevelLabel = (level) => {
    const levelMap = {
      'light': 'Nhẹ',
      'medium': 'Trung bình',
      'heavy': 'Nặng',
    };
    return levelMap[level] || level || 'N/A';
  };

  const getResultStatusLabel = (status) => {
    const statusMap = {
      'passed': 'Đạt',
      'failed': 'Không đạt',
      'need_retry': 'Cần bảo trì lại',
    };
    return statusMap[status] || status || 'N/A';
  };

  const getAssetStatusLabel = (status) => {
    const statusMap = {
      'active': 'Đang sử dụng',
      'maintenance': 'Đang bảo trì',
      'disposed': 'Ngừng sử dụng',
      'broken_light': 'Hỏng nhẹ',
      'broken_heavy': 'Hỏng nặng',
    };
    return statusMap[status] || status || 'N/A';
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

  const getFileUrl = (filePath) => {
    if (!filePath) return null;
    return `/static/${filePath}`;
  };

  const isImageFile = (filePath) => {
    if (!filePath) return false;
    const ext = filePath.toLowerCase().split('.').pop();
    return ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext);
  };

  if (loading) {
    return (
      <div className="maintenance-detail text-center p-4">
        <div className="spinner-border" role="status">
          <span className="sr-only">Đang tải...</span>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="maintenance-detail">
        <div className="alert alert-danger">Không tìm thấy dữ liệu</div>
      </div>
    );
  }

  return (
    <div className="maintenance-detail">
      <div className="detail-header mb-3">
        <div className="d-flex justify-content-between align-items-center">
          <h3>
            <i className="fas fa-tools mr-2"></i>Chi tiết bảo trì thiết bị
          </h3>
          <div>
            {onBack && (
              <button className="btn btn-secondary mr-2" onClick={onBack}>
                <i className="fas fa-arrow-left mr-1"></i>Quay lại
              </button>
            )}
            {onEdit && (
              <button className="btn btn-primary" onClick={() => onEdit(maintenanceId)}>
                <i className="fas fa-edit mr-1"></i>Sửa
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Section A: Thông tin thiết bị */}
      <div className="card mb-3">
        <div className="card-header">
          <h5 className="card-title mb-0">
            <i className="fas fa-box mr-2"></i>A. Thông tin thiết bị
          </h5>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-6">
              <div className="detail-item">
                <label>Mã tài sản:</label>
                <span>{data.asset_code || 'N/A'}</span>
              </div>
            </div>
            <div className="col-md-6">
              <div className="detail-item">
                <label>Tên tài sản:</label>
                <span>{data.asset_name || 'N/A'}</span>
              </div>
            </div>
          </div>
          <div className="row">
            <div className="col-md-4">
              <div className="detail-item">
                <label>Loại tài sản:</label>
                <span>{data.asset_type_name || 'N/A'}</span>
              </div>
            </div>
            <div className="col-md-4">
              <div className="detail-item">
                <label>Người dùng đang sử dụng:</label>
                <span>{data.asset_user || 'N/A'}</span>
              </div>
            </div>
            <div className="col-md-4">
              <div className="detail-item">
                <label>Trạng thái hiện tại:</label>
                <span>{getAssetStatusLabel(data.asset_status)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Section B: Thông tin bảo trì */}
      <div className="card mb-3">
        <div className="card-header">
          <h5 className="card-title mb-0">
            <i className="fas fa-tools mr-2"></i>B. Thông tin bảo trì
          </h5>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-4">
              <div className="detail-item">
                <label>Ngày yêu cầu bảo trì:</label>
                <span>{formatDate(data.request_date)}</span>
              </div>
            </div>
            <div className="col-md-4">
              <div className="detail-item">
                <label>Người yêu cầu:</label>
                <span>{data.requested_by_name || 'N/A'}</span>
              </div>
            </div>
            <div className="col-md-4">
              <div className="detail-item">
                <label>Nguyên nhân bảo trì:</label>
                <span>{getReasonLabel(data.maintenance_reason)}</span>
              </div>
            </div>
          </div>
          {data.condition_before && (
            <div className="row">
              <div className="col-md-12">
                <div className="detail-item">
                  <label>Mô tả tình trạng trước khi bảo trì:</label>
                  <div className="detail-text">{data.condition_before}</div>
                </div>
              </div>
            </div>
          )}
          <div className="row">
            <div className="col-md-6">
              <div className="detail-item">
                <label>Mức độ hỏng:</label>
                <span>{getDamageLevelLabel(data.damage_level)}</span>
              </div>
            </div>
            <div className="col-md-6">
              <div className="detail-item">
                <label>Loại bảo trì:</label>
                <span>{data.type || 'N/A'}</span>
              </div>
            </div>
          </div>
          {data.description && (
            <div className="row">
              <div className="col-md-12">
                <div className="detail-item">
                  <label>Mô tả chi tiết:</label>
                  <div className="detail-text">{data.description}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Section C: Thông tin đơn vị bảo trì */}
      <div className="card mb-3">
        <div className="card-header">
          <h5 className="card-title mb-0">
            <i className="fas fa-building mr-2"></i>C. Thông tin đơn vị/bên thực hiện bảo trì
          </h5>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-6">
              <div className="detail-item">
                <label>Đơn vị bảo trì:</label>
                <span>{data.vendor || 'N/A'}</span>
              </div>
            </div>
            <div className="col-md-6">
              <div className="detail-item">
                <label>Người thực hiện:</label>
                <span>{data.person_in_charge || 'N/A'}</span>
              </div>
            </div>
          </div>
          <div className="row">
            <div className="col-md-6">
              <div className="detail-item">
                <label>Số điện thoại liên hệ:</label>
                <span>{data.vendor_phone || 'N/A'}</span>
              </div>
            </div>
            <div className="col-md-6">
              <div className="detail-item">
                <label>Chi phí dự kiến:</label>
                <span>{formatCurrency(data.estimated_cost)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Section D: Kết quả bảo trì */}
      <div className="card mb-3">
        <div className="card-header">
          <h5 className="card-title mb-0">
            <i className="fas fa-check-circle mr-2"></i>D. Kết quả bảo trì
          </h5>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-4">
              <div className="detail-item">
                <label>Ngày hoàn thành:</label>
                <span>{formatDate(data.completed_date)}</span>
              </div>
            </div>
            <div className="col-md-4">
              <div className="detail-item">
                <label>Chi phí thực tế:</label>
                <span>{formatCurrency(data.cost)}</span>
              </div>
            </div>
            <div className="col-md-4">
              <div className="detail-item">
                <label>Trạng thái sau bảo trì:</label>
                <span>{getResultStatusLabel(data.result_status)}</span>
              </div>
            </div>
          </div>
          {data.replaced_parts && (
            <div className="row">
              <div className="col-md-12">
                <div className="detail-item">
                  <label>Phụ tùng đã thay thế:</label>
                  <div className="detail-text">{data.replaced_parts}</div>
                </div>
              </div>
            </div>
          )}
          {data.result_notes && (
            <div className="row">
              <div className="col-md-12">
                <div className="detail-item">
                  <label>Ghi chú:</label>
                  <div className="detail-text">{data.result_notes}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Section E: File đính kèm */}
      {(data.invoice_file || data.acceptance_file || data.before_image || data.after_image) && (
      <div className="card mb-3">
        <div className="card-header">
            <h5 className="card-title mb-0">
              <i className="fas fa-paperclip mr-2"></i>E. File đính kèm
            </h5>
          </div>
          <div className="card-body">
            <div className="row">
              {data.invoice_file && (
                <div className="col-md-6 mb-3">
                  <div className="detail-item">
                    <label>Hóa đơn:</label>
                    <div>
                      {isImageFile(data.invoice_file) ? (
                        <img
                          src={getFileUrl(data.invoice_file)}
                          alt="Hóa đơn"
                          className="file-preview"
                        />
                      ) : (
                        <a
                          href={getFileUrl(data.invoice_file)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="file-link"
                        >
                          <i className="fas fa-file-pdf mr-1"></i>Xem hóa đơn
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              )}
              {data.acceptance_file && (
                <div className="col-md-6 mb-3">
                  <div className="detail-item">
                    <label>Biên bản nghiệm thu:</label>
                    <div>
                      {isImageFile(data.acceptance_file) ? (
                        <img
                          src={getFileUrl(data.acceptance_file)}
                          alt="Biên bản nghiệm thu"
                          className="file-preview"
                        />
                      ) : (
                        <a
                          href={getFileUrl(data.acceptance_file)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="file-link"
                        >
                          <i className="fas fa-file-pdf mr-1"></i>Xem biên bản
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              )}
              {data.before_image && (
                <div className="col-md-6 mb-3">
                  <div className="detail-item">
                    <label>Hình ảnh trước bảo trì:</label>
                    <div>
                      <img
                        src={getFileUrl(data.before_image)}
                        alt="Trước bảo trì"
                        className="file-preview"
                      />
                    </div>
                  </div>
                </div>
              )}
              {data.after_image && (
                <div className="col-md-6 mb-3">
                  <div className="detail-item">
                    <label>Hình ảnh sau bảo trì:</label>
                    <div>
                      <img
                        src={getFileUrl(data.after_image)}
                        alt="Sau bảo trì"
                        className="file-preview"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Status */}
      <div className="card">
        <div className="card-body">
          <div className="detail-item">
            <label>Trạng thái:</label>
            <span>{getStatusBadge(data.status)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MaintenanceDetail;

