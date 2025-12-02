"""
Script để cải thiện tính toàn vẹn dữ liệu
- Thêm transaction handling với rollback
- Thêm validation functions
- Thêm constraints checking
"""

from models import db, Asset, User, AssetType, MaintenanceRecord, Role
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# ========== Validation Functions ==========

def validate_status(status):
    """Validate asset status"""
    valid_statuses = ['active', 'maintenance', 'disposed']
    return status in valid_statuses

def validate_maintenance_type(maintenance_type):
    """Validate maintenance type"""
    valid_types = ['maintenance', 'repair', 'inspection']
    return maintenance_type in valid_types

def validate_maintenance_status(status):
    """Validate maintenance status"""
    valid_statuses = ['completed', 'scheduled', 'in_progress', 'cancelled']
    return status in valid_statuses

def validate_email(email):
    """Basic email validation"""
    if not email or '@' not in email:
        return False
    return len(email) <= 120  # Match database constraint

def validate_username(username):
    """Validate username"""
    if not username or len(username) < 3 or len(username) > 80:
        return False
    # Username should be alphanumeric with underscore
    return username.replace('_', '').replace('-', '').isalnum()

def validate_price(price):
    """Validate price"""
    try:
        price_float = float(price)
        return price_float >= 0
    except (ValueError, TypeError):
        return False

def validate_quantity(quantity):
    """Validate quantity"""
    try:
        qty_int = int(quantity)
        return qty_int > 0
    except (ValueError, TypeError):
        return False

def validate_date_range(start_date, end_date):
    """Validate date range (end_date should be after start_date)"""
    if not start_date or not end_date:
        return True  # Optional dates
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    return end_date >= start_date

# ========== Database Transaction Helper ==========

def safe_db_operation(operation_func, *args, **kwargs):
    """
    Wrapper để đảm bảo transaction safety
    Tự động rollback nếu có lỗi
    """
    try:
        result = operation_func(*args, **kwargs)
        db.session.commit()
        return result, None
    except IntegrityError as e:
        db.session.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        if 'UNIQUE constraint' in error_msg or 'duplicate key' in error_msg.lower():
            return None, {'message': 'Dữ liệu đã tồn tại (trùng lặp)', 'error': 'duplicate'}
        elif 'FOREIGN KEY constraint' in error_msg or 'foreign key' in error_msg.lower():
            return None, {'message': 'Tham chiếu không hợp lệ', 'error': 'foreign_key'}
        else:
            return None, {'message': f'Lỗi toàn vẹn dữ liệu: {error_msg}', 'error': 'integrity'}
    except ValueError as e:
        db.session.rollback()
        return None, {'message': f'Dữ liệu không hợp lệ: {str(e)}', 'error': 'validation'}
    except Exception as e:
        db.session.rollback()
        return None, {'message': f'Lỗi không xác định: {str(e)}', 'error': 'unknown'}

# ========== Data Integrity Checks ==========

def check_foreign_key_exists(model_class, id_value, include_deleted=False):
    """Kiểm tra foreign key có tồn tại không"""
    if include_deleted:
        return model_class.query.get(id_value) is not None
    else:
        # Check if model has deleted_at field
        if hasattr(model_class, 'deleted_at'):
            return model_class.query.filter_by(id=id_value, deleted_at=None).first() is not None
        else:
            return model_class.query.get(id_value) is not None

def check_asset_type_in_use(asset_type_id):
    """Kiểm tra asset type có đang được sử dụng không"""
    return Asset.query.filter_by(asset_type_id=asset_type_id, deleted_at=None).count() > 0

def check_user_has_assets(user_id):
    """Kiểm tra user có tài sản không"""
    return Asset.query.filter_by(user_id=user_id, deleted_at=None).count() > 0

def check_asset_has_maintenance(asset_id):
    """Kiểm tra asset có bản ghi bảo trì không"""
    return MaintenanceRecord.query.filter_by(asset_id=asset_id, deleted_at=None).count() > 0

# ========== Comprehensive Validation ==========

def validate_asset_data(data, is_update=False):
    """Validate asset data comprehensively"""
    errors = []
    
    # Required fields for create
    if not is_update:
        if not data.get('name'):
            errors.append('Tên tài sản là bắt buộc')
        if data.get('price') is None:
            errors.append('Giá là bắt buộc')
        if not data.get('asset_type_id'):
            errors.append('Loại tài sản là bắt buộc')
    
    # Validate price
    if 'price' in data and not validate_price(data['price']):
        errors.append('Giá phải là số dương')
    
    # Validate quantity
    if 'quantity' in data and not validate_quantity(data.get('quantity', 1)):
        errors.append('Số lượng phải lớn hơn 0')
    
    # Validate status
    if 'status' in data and not validate_status(data['status']):
        errors.append(f'Trạng thái không hợp lệ. Phải là một trong: active, maintenance, disposed')
    
    # Validate date range
    if 'warranty_start_date' in data and 'warranty_end_date' in data:
        if not validate_date_range(data['warranty_start_date'], data['warranty_end_date']):
            errors.append('Ngày kết thúc bảo hành phải sau ngày bắt đầu')
    
    # Validate asset_type_id exists
    if 'asset_type_id' in data:
        if not check_foreign_key_exists(AssetType, data['asset_type_id']):
            errors.append('Loại tài sản không tồn tại')
    
    # Validate user_id exists (if provided)
    if 'user_id' in data and data.get('user_id'):
        if not check_foreign_key_exists(User, data['user_id']):
            errors.append('Người dùng không tồn tại')
    
    return errors

def validate_user_data(data, is_update=False):
    """Validate user data comprehensively"""
    errors = []
    
    # Required fields for create
    if not is_update:
        if not data.get('username'):
            errors.append('Username là bắt buộc')
        if not data.get('email'):
            errors.append('Email là bắt buộc')
        if not data.get('password'):
            errors.append('Password là bắt buộc')
        if not data.get('role_id'):
            errors.append('Role là bắt buộc')
    
    # Validate username
    if 'username' in data and not validate_username(data['username']):
        errors.append('Username phải từ 3-80 ký tự và chỉ chứa chữ, số, gạch dưới, gạch ngang')
    
    # Validate email
    if 'email' in data and not validate_email(data['email']):
        errors.append('Email không hợp lệ')
    
    # Validate role_id exists
    if 'role_id' in data:
        if not check_foreign_key_exists(Role, data['role_id']):
            errors.append('Role không tồn tại')
    
    return errors

def validate_maintenance_data(data, is_update=False):
    """Validate maintenance record data comprehensively"""
    errors = []
    
    # Required fields for create
    if not is_update:
        if not data.get('asset_id'):
            errors.append('Asset ID là bắt buộc')
        if not data.get('type'):
            errors.append('Loại bảo trì là bắt buộc')
    
    # Validate asset_id exists
    if 'asset_id' in data:
        if not check_foreign_key_exists(Asset, data['asset_id']):
            errors.append('Tài sản không tồn tại')
    
    # Validate type
    if 'type' in data and not validate_maintenance_type(data['type']):
        errors.append(f'Loại bảo trì không hợp lệ. Phải là một trong: maintenance, repair, inspection')
    
    # Validate status
    if 'status' in data and not validate_maintenance_status(data['status']):
        errors.append(f'Trạng thái không hợp lệ. Phải là một trong: completed, scheduled, in_progress, cancelled')
    
    # Validate cost
    if 'cost' in data:
        try:
            cost = float(data['cost'])
            if cost < 0:
                errors.append('Chi phí không được âm')
        except (ValueError, TypeError):
            errors.append('Chi phí phải là số')
    
    # Validate date range
    if 'maintenance_date' in data and 'next_due_date' in data:
        if not validate_date_range(data['maintenance_date'], data['next_due_date']):
            errors.append('Ngày đến hạn tiếp theo phải sau ngày bảo trì')
    
    return errors





