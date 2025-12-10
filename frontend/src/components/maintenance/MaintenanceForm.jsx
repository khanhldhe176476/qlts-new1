import React, { useState, useEffect } from 'react';
import { maintenanceService } from '../../services/maintenanceService';
import './MaintenanceForm.css';

const MaintenanceForm = ({ maintenanceId, onSave, onCancel, assets = [], users = [] }) => {
  const [formData, setFormData] = useState({
    // Thông tin thiết bị
    asset_id: '',
    
    // Thông tin bảo trì
    request_date: new Date().toISOString().split('T')[0],
    requested_by_id: '',
    maintenance_reason: '',
    condition_before: '',
    damage_level: '',
    
    // Thông tin đơn vị bảo trì
    vendor: '',
    person_in_charge: '',
    vendor_phone: '',
    estimated_cost: '',
    
    // Kết quả bảo trì
    completed_date: '',
    replaced_parts: '',
    cost: '',
    result_notes: '',
    result_status: '',
    
    // Khác
    type: 'maintenance',
    description: '',
    status: 'pending',
  });

  const [selectedAsset, setSelectedAsset] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [fileUploads, setFileUploads] = useState({
    invoice_file: null,
    acceptance_file: null,
    before_image: null,
    after_image: null,
  });

  useEffect(() => {
    if (maintenanceId) {
      loadMaintenance();
    }
  }, [maintenanceId]);

  const loadMaintenance = async () => {
    try {
      setLoading(true);
      const data = await maintenanceService.getById(maintenanceId);
      setFormData({
        asset_id: data.asset_id || '',
        request_date: data.request_date || new Date().toISOString().split('T')[0],
        requested_by_id: data.requested_by_id || '',
        maintenance_reason: data.maintenance_reason || '',
        condition_before: data.condition_before || '',
        damage_level: data.damage_level || '',
        vendor: data.vendor || '',
        person_in_charge: data.person_in_charge || '',
        vendor_phone: data.vendor_phone || '',
        estimated_cost: data.estimated_cost || '',
        completed_date: data.completed_date || '',
        replaced_parts: data.replaced_parts || '',
        cost: data.cost || '',
        result_notes: data.result_notes || '',
        result_status: data.result_status || '',
        type: data.type || 'maintenance',
        description: data.description || '',
        status: data.status || 'pending',
      });
      
      // Load asset info
      if (data.asset_id) {
        const asset = assets.find(a => a.id === data.asset_id);
        if (asset) {
          setSelectedAsset(asset);
        }
      }
    } catch (error) {
      alert('Lỗi khi tải dữ liệu: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAssetChange = (e) => {
    const assetId = e.target.value;
    const asset = assets.find(a => a.id === parseInt(assetId));
    setSelectedAsset(asset);
    setFormData({ ...formData, asset_id: assetId });
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
    // Clear error when user types
    if (errors[name]) {
      setErrors({ ...errors, [name]: '' });
    }
  };

  const handleFileChange = (e, fileType) => {
    const file = e.target.files[0];
    if (file) {
      setFileUploads({ ...fileUploads, [fileType]: file });
    }
  };

  const validate = () => {
    const newErrors = {};
    
    if (!formData.asset_id) {
      newErrors.asset_id = 'Vui lòng chọn tài sản';
    }
    if (!formData.request_date) {
      newErrors.request_date = 'Vui lòng nhập ngày yêu cầu';
    }
    if (!formData.maintenance_reason) {
      newErrors.maintenance_reason = 'Vui lòng chọn nguyên nhân bảo trì';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validate()) {
      return;
    }

    try {
      setLoading(true);
      
      // Prepare data
      const submitData = {
        ...formData,
        asset_id: parseInt(formData.asset_id),
        requested_by_id: formData.requested_by_id ? parseInt(formData.requested_by_id) : null,
        estimated_cost: formData.estimated_cost ? parseFloat(formData.estimated_cost) : 0,
        cost: formData.cost ? parseFloat(formData.cost) : 0,
      };

      let result;
      if (maintenanceId) {
        result = await maintenanceService.update(maintenanceId, submitData);
      } else {
        result = await maintenanceService.create(submitData);
      }

      // Upload files if any
      if (result.id) {
        const uploadPromises = [];
        Object.keys(fileUploads).forEach(fileType => {
          if (fileUploads[fileType]) {
            uploadPromises.push(
              maintenanceService.uploadFile(result.id, fileType, fileUploads[fileType])
            );
          }
        });
        
        if (uploadPromises.length > 0) {
          await Promise.all(uploadPromises);
        }
      }

      alert(maintenanceId ? 'Cập nhật thành công!' : 'Tạo mới thành công!');
      if (onSave) {
        onSave(result);
      }
    } catch (error) {
      alert('Lỗi: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const getAssetStatusLabel = (status) => {
    const statusMap = {
      'active': 'Đang sử dụng',
      'maintenance': 'Đang bảo trì',
      'disposed': 'Ngừng sử dụng',
      'broken_light': 'Hỏng nhẹ',
      'broken_heavy': 'Hỏng nặng',
    };
    return statusMap[status] || status;
  };

  if (loading && maintenanceId) {
    return <div className="text-center p-4">Đang tải...</div>;
  }

  return (
    <form onSubmit={handleSubmit} className="maintenance-form">
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
              <div className="form-group">
                <label htmlFor="asset_id">Tài sản <span className="text-danger">*</span></label>
                <select
                  id="asset_id"
                  name="asset_id"
                  className={`form-control ${errors.asset_id ? 'is-invalid' : ''}`}
                  value={formData.asset_id}
                  onChange={handleAssetChange}
                  required
                >
                  <option value="">-- Chọn tài sản --</option>
                  {assets.map(asset => (
                    <option key={asset.id} value={asset.id}>
                      {asset.name} {asset.device_code ? `(${asset.device_code})` : ''}
                    </option>
                  ))}
                </select>
                {errors.asset_id && <div className="invalid-feedback">{errors.asset_id}</div>}
              </div>
            </div>
            <div className="col-md-6">
              <div className="form-group">
                <label>Mã tài sản</label>
                <input
                  type="text"
                  className="form-control"
                  value={selectedAsset?.device_code || ''}
                  readOnly
                />
              </div>
            </div>
          </div>
          <div className="row">
            <div className="col-md-4">
              <div className="form-group">
                <label>Loại tài sản</label>
                <input
                  type="text"
                  className="form-control"
                  value={selectedAsset?.asset_type_name || ''}
                  readOnly
                />
              </div>
            </div>
            <div className="col-md-4">
              <div className="form-group">
                <label>Người dùng đang sử dụng</label>
                <input
                  type="text"
                  className="form-control"
                  value={selectedAsset?.user_text || selectedAsset?.user_name || ''}
                  readOnly
                />
              </div>
            </div>
            <div className="col-md-4">
              <div className="form-group">
                <label>Trạng thái hiện tại</label>
                <input
                  type="text"
                  className="form-control"
                  value={getAssetStatusLabel(selectedAsset?.status) || ''}
                  readOnly
                />
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
              <div className="form-group">
                <label htmlFor="request_date">Ngày yêu cầu bảo trì <span className="text-danger">*</span></label>
                <input
                  type="date"
                  id="request_date"
                  name="request_date"
                  className={`form-control ${errors.request_date ? 'is-invalid' : ''}`}
                  value={formData.request_date}
                  onChange={handleChange}
                  required
                />
                {errors.request_date && <div className="invalid-feedback">{errors.request_date}</div>}
              </div>
            </div>
            <div className="col-md-4">
              <div className="form-group">
                <label htmlFor="requested_by_id">Người yêu cầu</label>
                <select
                  id="requested_by_id"
                  name="requested_by_id"
                  className="form-control"
                  value={formData.requested_by_id}
                  onChange={handleChange}
                >
                  <option value="">-- Chọn người yêu cầu --</option>
                  {users.map(user => (
                    <option key={user.id} value={user.id}>
                      {user.username} {user.email ? `(${user.email})` : ''}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="col-md-4">
              <div className="form-group">
                <label htmlFor="maintenance_reason">Nguyên nhân bảo trì <span className="text-danger">*</span></label>
                <select
                  id="maintenance_reason"
                  name="maintenance_reason"
                  className={`form-control ${errors.maintenance_reason ? 'is-invalid' : ''}`}
                  value={formData.maintenance_reason}
                  onChange={handleChange}
                  required
                >
                  <option value="">-- Chọn nguyên nhân --</option>
                  <option value="broken">Lỗi kỹ thuật</option>
                  <option value="periodic">Bảo trì định kỳ</option>
                  <option value="calibration">Hiệu chỉnh</option>
                  <option value="other">Khác</option>
                </select>
                {errors.maintenance_reason && <div className="invalid-feedback">{errors.maintenance_reason}</div>}
              </div>
            </div>
          </div>
          <div className="row">
            <div className="col-md-12">
              <div className="form-group">
                <label htmlFor="condition_before">Mô tả tình trạng trước khi bảo trì</label>
                <textarea
                  id="condition_before"
                  name="condition_before"
                  className="form-control"
                  rows="3"
                  value={formData.condition_before}
                  onChange={handleChange}
                  placeholder="Mô tả chi tiết tình trạng thiết bị trước khi bảo trì..."
                />
              </div>
            </div>
          </div>
          <div className="row">
            <div className="col-md-6">
              <div className="form-group">
                <label htmlFor="damage_level">Mức độ hỏng</label>
                <select
                  id="damage_level"
                  name="damage_level"
                  className="form-control"
                  value={formData.damage_level}
                  onChange={handleChange}
                >
                  <option value="">-- Chọn mức độ --</option>
                  <option value="light">Nhẹ</option>
                  <option value="medium">Trung bình</option>
                  <option value="heavy">Nặng</option>
                </select>
              </div>
            </div>
            <div className="col-md-6">
              <div className="form-group">
                <label htmlFor="type">Loại bảo trì</label>
                <select
                  id="type"
                  name="type"
                  className="form-control"
                  value={formData.type}
                  onChange={handleChange}
                >
                  <option value="maintenance">Bảo trì</option>
                  <option value="repair">Sửa chữa</option>
                  <option value="inspection">Kiểm tra</option>
                </select>
              </div>
            </div>
          </div>
          <div className="row">
            <div className="col-md-12">
              <div className="form-group">
                <label htmlFor="description">Mô tả chi tiết</label>
                <textarea
                  id="description"
                  name="description"
                  className="form-control"
                  rows="3"
                  value={formData.description}
                  onChange={handleChange}
                  placeholder="Mô tả chi tiết về yêu cầu bảo trì..."
                />
              </div>
            </div>
          </div>
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
              <div className="form-group">
                <label htmlFor="vendor">Đơn vị bảo trì</label>
                <input
                  type="text"
                  id="vendor"
                  name="vendor"
                  className="form-control"
                  value={formData.vendor}
                  onChange={handleChange}
                  placeholder="Tên đơn vị bảo trì"
                />
              </div>
            </div>
            <div className="col-md-6">
              <div className="form-group">
                <label htmlFor="person_in_charge">Người thực hiện</label>
                <input
                  type="text"
                  id="person_in_charge"
                  name="person_in_charge"
                  className="form-control"
                  value={formData.person_in_charge}
                  onChange={handleChange}
                  placeholder="Tên người thực hiện bảo trì"
                />
              </div>
            </div>
          </div>
          <div className="row">
            <div className="col-md-6">
              <div className="form-group">
                <label htmlFor="vendor_phone">Số điện thoại liên hệ</label>
                <input
                  type="text"
                  id="vendor_phone"
                  name="vendor_phone"
                  className="form-control"
                  value={formData.vendor_phone}
                  onChange={handleChange}
                  placeholder="Số điện thoại"
                />
              </div>
            </div>
            <div className="col-md-6">
              <div className="form-group">
                <label htmlFor="estimated_cost">Chi phí dự kiến (VNĐ)</label>
                <input
                  type="number"
                  id="estimated_cost"
                  name="estimated_cost"
                  className="form-control"
                  value={formData.estimated_cost}
                  onChange={handleChange}
                  min="0"
                  step="1000"
                  placeholder="0"
                />
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
              <div className="form-group">
                <label htmlFor="completed_date">Ngày hoàn thành</label>
                <input
                  type="date"
                  id="completed_date"
                  name="completed_date"
                  className="form-control"
                  value={formData.completed_date}
                  onChange={handleChange}
                />
              </div>
            </div>
            <div className="col-md-4">
              <div className="form-group">
                <label htmlFor="cost">Chi phí thực tế (VNĐ)</label>
                <input
                  type="number"
                  id="cost"
                  name="cost"
                  className="form-control"
                  value={formData.cost}
                  onChange={handleChange}
                  min="0"
                  step="1000"
                  placeholder="0"
                />
              </div>
            </div>
            <div className="col-md-4">
              <div className="form-group">
                <label htmlFor="result_status">Trạng thái sau bảo trì</label>
                <select
                  id="result_status"
                  name="result_status"
                  className="form-control"
                  value={formData.result_status}
                  onChange={handleChange}
                >
                  <option value="">-- Chọn trạng thái --</option>
                  <option value="passed">Đạt</option>
                  <option value="failed">Không đạt</option>
                  <option value="need_retry">Cần bảo trì lại</option>
                </select>
              </div>
            </div>
          </div>
          <div className="row">
            <div className="col-md-12">
              <div className="form-group">
                <label htmlFor="replaced_parts">Phụ tùng đã thay thế</label>
                <textarea
                  id="replaced_parts"
                  name="replaced_parts"
                  className="form-control"
                  rows="2"
                  value={formData.replaced_parts}
                  onChange={handleChange}
                  placeholder="Liệt kê các phụ tùng đã thay thế (mỗi dòng một mục)..."
                />
              </div>
            </div>
          </div>
          <div className="row">
            <div className="col-md-12">
              <div className="form-group">
                <label htmlFor="result_notes">Ghi chú kết quả</label>
                <textarea
                  id="result_notes"
                  name="result_notes"
                  className="form-control"
                  rows="2"
                  value={formData.result_notes}
                  onChange={handleChange}
                  placeholder="Ghi chú về kết quả bảo trì..."
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Section E: File đính kèm */}
      <div className="card mb-3">
        <div className="card-header">
          <h5 className="card-title mb-0">
            <i className="fas fa-paperclip mr-2"></i>E. File đính kèm
          </h5>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-6">
              <div className="form-group">
                <label htmlFor="invoice_file">Hóa đơn</label>
                <input
                  type="file"
                  id="invoice_file"
                  className="form-control-file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={(e) => handleFileChange(e, 'invoice_file')}
                />
              </div>
            </div>
            <div className="col-md-6">
              <div className="form-group">
                <label htmlFor="acceptance_file">Biên bản nghiệm thu</label>
                <input
                  type="file"
                  id="acceptance_file"
                  className="form-control-file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={(e) => handleFileChange(e, 'acceptance_file')}
                />
              </div>
            </div>
          </div>
          <div className="row">
            <div className="col-md-6">
              <div className="form-group">
                <label htmlFor="before_image">Hình ảnh trước bảo trì</label>
                <input
                  type="file"
                  id="before_image"
                  className="form-control-file"
                  accept=".jpg,.jpeg,.png"
                  onChange={(e) => handleFileChange(e, 'before_image')}
                />
              </div>
            </div>
            <div className="col-md-6">
              <div className="form-group">
                <label htmlFor="after_image">Hình ảnh sau bảo trì</label>
                <input
                  type="file"
                  id="after_image"
                  className="form-control-file"
                  accept=".jpg,.jpeg,.png"
                  onChange={(e) => handleFileChange(e, 'after_image')}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Status */}
      <div className="card mb-3">
        <div className="card-body">
          <div className="form-group">
            <label htmlFor="status">Trạng thái <span className="text-danger">*</span></label>
            <select
              id="status"
              name="status"
              className="form-control"
              value={formData.status}
              onChange={handleChange}
              required
            >
              <option value="pending">Chờ xử lý</option>
              <option value="in_progress">Đang thực hiện</option>
              <option value="completed">Hoàn thành</option>
              <option value="failed">Không đạt</option>
              <option value="cancelled">Hủy</option>
            </select>
          </div>
        </div>
      </div>

      {/* Buttons */}
      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={loading}>
          <i className="fas fa-save mr-2"></i>
          {loading ? 'Đang lưu...' : (maintenanceId ? 'Cập nhật' : 'Lưu')}
        </button>
        {onCancel && (
          <button type="button" className="btn btn-secondary ml-2" onClick={onCancel}>
            <i className="fas fa-times mr-2"></i>Hủy
          </button>
        )}
      </div>
    </form>
  );
};

export default MaintenanceForm;

