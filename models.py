from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from utils.timezone import now_vn, today_vn

db = SQLAlchemy()

# Association table for many-to-many assignments between assets and users
asset_user = db.Table(
    'asset_user',
    db.Column('asset_id', db.Integer, db.ForeignKey('asset.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=now_vn)
    updated_at = db.Column(db.DateTime, default=now_vn, onupdate=now_vn)
    
    # Relationship
    users = db.relationship('User', backref='role', lazy=True)
    
    def __repr__(self):
        return f'<Role {self.name}>'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=True)  # Tên đầy đủ của người dùng
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    deleted_at = db.Column(db.DateTime, nullable=True)  # Soft delete
    asset_quota = db.Column(db.Integer, default=0)  # Số tài sản quản lý (tùy chọn)
    created_at = db.Column(db.DateTime, default=now_vn)
    updated_at = db.Column(db.DateTime, default=now_vn, onupdate=now_vn)
    last_login = db.Column(db.DateTime)
    
    # Relationship
    # Owner relationship (legacy single owner)
    assets = db.relationship('Asset', backref='user', lazy=True)
    # Assigned assets (many-to-many)
    assigned_assets = db.relationship(
        'Asset',
        secondary=asset_user,
        back_populates='assigned_users',
        lazy='subquery'
    )
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Relationship với permissions
    permissions = db.relationship('UserPermission', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def has_permission(self, module, action):
        """Kiểm tra user có quyền thực hiện action trên module không"""
        if self.role.name == 'admin':
            return True
        for perm in self.permissions:
            if perm.permission.module == module and perm.permission.action == action:
                return perm.granted
        return False
    
    def soft_delete(self):
        """Soft delete user"""
        self.deleted_at = now_vn()
        self.is_active = False
    
    def restore(self):
        """Restore deleted user"""
        self.deleted_at = None
        self.is_active = True
    
    def __repr__(self):
        return f'<User {self.username}>'

class AssetType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    deleted_at = db.Column(db.DateTime, nullable=True)  # Soft delete
    created_at = db.Column(db.DateTime, default=now_vn)
    updated_at = db.Column(db.DateTime, default=now_vn, onupdate=now_vn)
    
    # Relationship
    assets = db.relationship('Asset', backref='asset_type', lazy=True)
    
    def soft_delete(self):
        """Soft delete asset type"""
        self.deleted_at = now_vn()
    
    def restore(self):
        """Restore deleted asset type"""
        self.deleted_at = None
    
    def __repr__(self):
        return f'<AssetType {self.name}>'

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='active')  # active, maintenance, disposed
    # New optional fields
    purchase_date = db.Column(db.Date, nullable=True)
    device_code = db.Column(db.String(100), nullable=True)
    condition_label = db.Column(db.String(100), nullable=True)  # e.g., 'Còn tốt', 'Cần kiểm tra'
    display_order = db.Column(db.Integer, nullable=True)  # STT từ Excel để giữ nguyên thứ tự
    asset_type_id = db.Column(db.Integer, db.ForeignKey('asset_type.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # User who created/owns the asset
    user_text = db.Column(db.Text)  # User notes/description
    notes = db.Column(db.Text)  # Admin notes
    deleted_at = db.Column(db.DateTime, nullable=True)  # Soft delete
    created_at = db.Column(db.DateTime, default=now_vn)
    updated_at = db.Column(db.DateTime, default=now_vn, onupdate=now_vn)
    
    # Warranty information
    warranty_contact_name = db.Column(db.String(200), nullable=True)  # Tên người liên hệ bảo hành
    warranty_contact_phone = db.Column(db.String(50), nullable=True)  # Số điện thoại
    warranty_contact_email = db.Column(db.String(200), nullable=True)  # Email
    warranty_website = db.Column(db.String(500), nullable=True)  # Link website
    warranty_start_date = db.Column(db.Date, nullable=True)  # Ngày bắt đầu bảo hành
    warranty_end_date = db.Column(db.Date, nullable=True)  # Ngày kết thúc bảo hành
    warranty_period_months = db.Column(db.Integer, nullable=True)  # Thời gian bảo hành (tháng)
    invoice_file_path = db.Column(db.String(500), nullable=True)  # Đường dẫn file hóa đơn/phiếu giao hàng
    
    # Assigned users (many-to-many)
    assigned_users = db.relationship(
        'User',
        secondary=asset_user,
        back_populates='assigned_assets',
        lazy='subquery'
    )
    
    def soft_delete(self):
        """Soft delete asset"""
        self.deleted_at = now_vn()
        self.status = 'disposed'
    
    def restore(self):
        """Restore deleted asset"""
        self.deleted_at = None
        if self.status == 'disposed':
            self.status = 'active'
    
    def get_warranty_status(self):
        """Trả về trạng thái bảo hành"""
        if not self.warranty_start_date or not self.warranty_end_date:
            return None, "Không có bảo hành"
        
        from datetime import date
        today = date.today()
        
        if today < self.warranty_start_date:
            days_remaining = (self.warranty_end_date - today).days
            return "upcoming", f"Còn {days_remaining} ngày đến hạn bảo hành"
        elif today >= self.warranty_start_date and today <= self.warranty_end_date:
            days_remaining = (self.warranty_end_date - today).days
            return "active", f"Còn {days_remaining} ngày bảo hành"
        else:
            days_expired = (today - self.warranty_end_date).days
            return "expired", f"Đã hết hạn {days_expired} ngày"
    
    def has_warranty(self):
        """Kiểm tra có bảo hành không"""
        return self.warranty_start_date is not None and self.warranty_end_date is not None
    
    def __repr__(self):
        return f'<Asset {self.name}>'

# Audit log model
class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    module = db.Column(db.String(50), nullable=False)  # assets, asset_types, users
    action = db.Column(db.String(20), nullable=False)   # create, update, delete
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=now_vn)

    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))

    def __repr__(self):
        return f'<AuditLog {self.module}:{self.action}#{self.entity_id}>'

# IT Maintenance record
class MaintenanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    
    # Thông tin yêu cầu bảo trì
    request_date = db.Column(db.Date, nullable=False, default=today_vn)  # Ngày yêu cầu
    requested_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Người yêu cầu
    maintenance_reason = db.Column(db.String(50), nullable=True)  # Nguyên nhân: broken, periodic, calibration, other
    condition_before = db.Column(db.Text)  # Mô tả tình trạng trước khi bảo trì
    damage_level = db.Column(db.String(20), nullable=True)  # Mức độ hỏng: light, medium, heavy
    
    # Thông tin bảo trì
    maintenance_date = db.Column(db.Date, nullable=True)  # Ngày thực hiện bảo trì
    type = db.Column(db.String(50), nullable=False, default='maintenance')  # maintenance, repair, inspection
    description = db.Column(db.Text)
    vendor = db.Column(db.String(200))  # Đơn vị bảo trì
    person_in_charge = db.Column(db.String(120))  # Người thực hiện
    vendor_phone = db.Column(db.String(50))  # Số điện thoại liên hệ
    estimated_cost = db.Column(db.Float, default=0.0)  # Chi phí dự kiến
    cost = db.Column(db.Float, default=0.0)  # Chi phí thực tế
    next_due_date = db.Column(db.Date)
    status = db.Column(db.String(30), default='pending')  # pending, in_progress, completed, failed, cancelled
    
    # Kết quả bảo trì
    completed_date = db.Column(db.Date, nullable=True)  # Ngày hoàn thành
    replaced_parts = db.Column(db.Text)  # Phụ tùng đã thay thế
    result_status = db.Column(db.String(20), nullable=True)  # Trạng thái sau bảo trì: passed, failed, need_retry
    result_notes = db.Column(db.Text)  # Ghi chú kết quả
    
    # File đính kèm
    invoice_file = db.Column(db.String(500), nullable=True)  # Hóa đơn
    acceptance_file = db.Column(db.String(500), nullable=True)  # Biên bản nghiệm thu
    before_image = db.Column(db.String(500), nullable=True)  # Hình ảnh trước bảo trì
    after_image = db.Column(db.String(500), nullable=True)  # Hình ảnh sau bảo trì
    
    deleted_at = db.Column(db.DateTime, nullable=True)  # Soft delete
    created_at = db.Column(db.DateTime, default=now_vn)
    updated_at = db.Column(db.DateTime, default=now_vn, onupdate=now_vn)

    asset = db.relationship('Asset', backref=db.backref('maintenance_records', lazy=True))
    requested_by = db.relationship('User', foreign_keys=[requested_by_id], backref=db.backref('maintenance_record_requests', lazy=True))
    
    def soft_delete(self):
        """Soft delete maintenance record"""
        self.deleted_at = now_vn()
    
    def restore(self):
        """Restore deleted maintenance record"""
        self.deleted_at = None

    def __repr__(self):
        return f'<Maintenance #{self.id} asset={self.asset_id}>'


class MaintenanceRequest(db.Model):
    __tablename__ = 'maintenance_request'

    id = db.Column(db.Integer, primary_key=True)
    request_code = db.Column(db.String(30), unique=True, nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    issue_summary = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(20), default='medium')  # low/medium/high/urgent
    status = db.Column(db.String(30), default='created')  # created, pending, approved, in_progress, completed, failed, cancelled
    department = db.Column(db.String(120))
    requested_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_at = db.Column(db.DateTime)
    rejected_reason = db.Column(db.Text)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assignment_note = db.Column(db.Text)
    external_vendor = db.Column(db.String(255))
    external_contact = db.Column(db.String(255))
    expected_finish_date = db.Column(db.Date)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    failed_reason = db.Column(db.Text)
    total_cost = db.Column(db.Float, default=0.0)
    due_date = db.Column(db.Date)  # deadline for request
    recurring = db.Column(db.Boolean, default=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('maintenance_schedule.id'))
    created_at = db.Column(db.DateTime, default=now_vn)
    updated_at = db.Column(db.DateTime, default=now_vn, onupdate=now_vn)

    asset = db.relationship('Asset', backref=db.backref('maintenance_requests', lazy=True))
    requested_by = db.relationship('User', foreign_keys=[requested_by_id], backref='maintenance_requests')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id], backref='maintenance_approvals')
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='maintenance_assignments')

    def can_transition(self, target_status: str) -> bool:
        transitions = {
            'created': ['pending', 'cancelled'],
            'pending': ['approved', 'cancelled'],
            'approved': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'failed'],
            'failed': ['in_progress'],
            'completed': [],
            'cancelled': []
        }
        return target_status in transitions.get(self.status or 'created', [])

    def recalc_total_cost(self):
        self.total_cost = sum(cost.amount or 0 for cost in self.costs)

    def __repr__(self):
        return f'<MaintenanceRequest {self.request_code}>'


class MaintenanceTimeline(db.Model):
    __tablename__ = 'maintenance_timeline'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('maintenance_request.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(30))
    progress_percent = db.Column(db.Integer, default=0)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=now_vn)

    request = db.relationship('MaintenanceRequest', backref=db.backref('timeline_entries', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref='maintenance_timelines')


class MaintenanceAttachment(db.Model):
    __tablename__ = 'maintenance_attachment'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('maintenance_request.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255))
    mime_type = db.Column(db.String(120))
    file_size = db.Column(db.Integer)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=now_vn)

    request = db.relationship('MaintenanceRequest', backref=db.backref('attachments', lazy=True, cascade='all, delete-orphan'))
    uploaded_by = db.relationship('User', backref='maintenance_attachments')


class MaintenanceCost(db.Model):
    __tablename__ = 'maintenance_cost'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('maintenance_request.id'), nullable=False)
    cost_type = db.Column(db.String(50), default='labor')  # labor, parts, service, other
    amount = db.Column(db.Float, nullable=False, default=0.0)
    note = db.Column(db.Text)
    recorded_at = db.Column(db.DateTime, default=now_vn)

    request = db.relationship('MaintenanceRequest', backref=db.backref('costs', lazy=True, cascade='all, delete-orphan'))


class MaintenancePart(db.Model):
    __tablename__ = 'maintenance_part'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('maintenance_request.id'), nullable=False)
    part_name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, default=0.0)
    total_price = db.Column(db.Float, default=0.0)
    note = db.Column(db.Text)
    recorded_at = db.Column(db.DateTime, default=now_vn)

    request = db.relationship('MaintenanceRequest', backref=db.backref('parts', lazy=True, cascade='all, delete-orphan'))


class MaintenanceSchedule(db.Model):
    __tablename__ = 'maintenance_schedule'

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    frequency = db.Column(db.String(30), nullable=False)  # monthly, quarterly, semiannual, annual, custom
    interval_days = db.Column(db.Integer, nullable=True)
    next_due_date = db.Column(db.Date, nullable=False)
    last_completed_date = db.Column(db.Date)
    notify_before_days = db.Column(db.Integer, default=7)
    auto_create_request = db.Column(db.Boolean, default=True)
    priority = db.Column(db.String(20), default='medium')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_vn)
    updated_at = db.Column(db.DateTime, default=now_vn, onupdate=now_vn)

    asset = db.relationship('Asset', backref=db.backref('maintenance_schedules', lazy=True))
    requests = db.relationship('MaintenanceRequest', backref='schedule', lazy=True)


class MaintenanceNotification(db.Model):
    __tablename__ = 'maintenance_notification'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('maintenance_request.id'))
    schedule_id = db.Column(db.Integer, db.ForeignKey('maintenance_schedule.id'))
    notification_type = db.Column(db.String(50))  # due_date, overdue, budget, pending
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, sent, dismissed
    channel = db.Column(db.String(20), default='inapp')  # inapp, email
    created_at = db.Column(db.DateTime, default=now_vn)
    sent_at = db.Column(db.DateTime)

    request = db.relationship('MaintenanceRequest', backref=db.backref('notifications', lazy=True, cascade='all, delete-orphan'))
    schedule = db.relationship('MaintenanceSchedule', backref=db.backref('notifications', lazy=True, cascade='all, delete-orphan'))

# Asset Transfer model - Bàn giao tài sản
# ========== MODELS CHO MISA QLTS ==========

class AssetVoucher(db.Model):
    """Chứng từ tài sản (ghi tăng, ghi giảm, đánh giá lại)"""
    __tablename__ = 'asset_voucher'
    
    id = db.Column(db.Integer, primary_key=True)
    voucher_code = db.Column(db.String(50), unique=True, nullable=False)  # Mã chứng từ
    voucher_type = db.Column(db.String(30), nullable=False)  # increase, decrease, reevaluate
    voucher_date = db.Column(db.Date, nullable=False, default=today_vn)
    description = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=now_vn)
    updated_at = db.Column(db.DateTime, default=now_vn, onupdate=now_vn)
    
    # Relationships
    created_by = db.relationship('User', backref='asset_vouchers')
    voucher_items = db.relationship('AssetVoucherItem', backref='voucher', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<AssetVoucher {self.voucher_code}>'

class AssetVoucherItem(db.Model):
    """Chi tiết chứng từ"""
    __tablename__ = 'asset_voucher_item'
    
    id = db.Column(db.Integer, primary_key=True)
    voucher_id = db.Column(db.Integer, db.ForeignKey('asset_voucher.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    old_value = db.Column(db.Float, nullable=True)  # Giá trị cũ (cho đánh giá lại)
    new_value = db.Column(db.Float, nullable=True)  # Giá trị mới
    quantity = db.Column(db.Integer, default=1)
    reason = db.Column(db.Text)  # Lý do
    notes = db.Column(db.Text)
    
    asset = db.relationship('Asset', backref='voucher_items')
    
    def __repr__(self):
        return f'<AssetVoucherItem voucher={self.voucher_id} asset={self.asset_id}>'

class AssetTransferHistory(db.Model):
    """Lịch sử điều chuyển tài sản"""
    __tablename__ = 'asset_transfer_history'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    from_department = db.Column(db.String(200), nullable=True)  # Phòng ban cũ
    to_department = db.Column(db.String(200), nullable=False)  # Phòng ban mới
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    transfer_date = db.Column(db.Date, nullable=False, default=today_vn)
    reason = db.Column(db.Text)
    transfer_code = db.Column(db.String(50), nullable=True)  # Mã chứng từ điều chuyển
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=now_vn)
    
    asset = db.relationship('Asset', backref='transfer_history')
    from_user = db.relationship('User', foreign_keys=[from_user_id], backref='transfers_from')
    to_user = db.relationship('User', foreign_keys=[to_user_id], backref='transfers_to')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='transfers_created')
    
    def __repr__(self):
        return f'<AssetTransferHistory asset={self.asset_id} from={self.from_department} to={self.to_department}>'

class AssetProcessRequest(db.Model):
    """Đề nghị xử lý tài sản (thanh lý/bán/tiêu hủy)"""
    __tablename__ = 'asset_process_request'
    
    id = db.Column(db.Integer, primary_key=True)
    request_code = db.Column(db.String(50), unique=True, nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    request_type = db.Column(db.String(30), nullable=False)  # dispose, sell, destroy
    reason = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft')  # draft, submitted, approved, rejected
    submitted_at = db.Column(db.DateTime, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejected_at = db.Column(db.DateTime, nullable=True)
    rejected_reason = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=now_vn)
    updated_at = db.Column(db.DateTime, default=now_vn, onupdate=now_vn)
    
    asset = db.relationship('Asset', backref='process_requests')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='process_requests_created')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id], backref='process_requests_approved')
    
    def __repr__(self):
        return f'<AssetProcessRequest {self.request_code} status={self.status}>'

class AssetDepreciation(db.Model):
    """Khấu hao tài sản"""
    __tablename__ = 'asset_depreciation'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    period_year = db.Column(db.Integer, nullable=False)
    period_month = db.Column(db.Integer, nullable=True)  # Null nếu tính theo năm
    original_value = db.Column(db.Float, nullable=False)  # Nguyên giá
    depreciation_amount = db.Column(db.Float, nullable=False)  # Số khấu hao kỳ này
    accumulated_depreciation = db.Column(db.Float, nullable=False)  # Lũy kế khấu hao
    remaining_value = db.Column(db.Float, nullable=False)  # Giá trị còn lại
    method = db.Column(db.String(30), nullable=False)  # straight_line, declining_balance
    depreciation_rate = db.Column(db.Float, nullable=True)  # Tỷ lệ khấu hao (%)
    created_at = db.Column(db.DateTime, default=now_vn)
    
    asset = db.relationship('Asset', backref='depreciations')
    
    def __repr__(self):
        return f'<AssetDepreciation asset={self.asset_id} {self.period_year}/{self.period_month or 0}>'

class AssetAmortization(db.Model):
    """Hao mòn tài sản"""
    __tablename__ = 'asset_amortization'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    period_year = db.Column(db.Integer, nullable=False)
    original_value = db.Column(db.Float, nullable=False)
    amortization_rate = db.Column(db.Float, nullable=False)  # Tỷ lệ hao mòn (%)
    amortization_amount = db.Column(db.Float, nullable=False)  # Giá trị hao mòn
    remaining_value = db.Column(db.Float, nullable=False)
    usage_years = db.Column(db.Integer, nullable=True)  # Số năm sử dụng
    condition_score = db.Column(db.Float, nullable=True)  # Điểm đánh giá tình trạng (0-100)
    created_at = db.Column(db.DateTime, default=now_vn)
    
    asset = db.relationship('Asset', backref='amortizations')
    
    def __repr__(self):
        return f'<AssetAmortization asset={self.asset_id} year={self.period_year}>'

class Inventory(db.Model):
    """Đợt kiểm kê tài sản (phiếu kiểm kê)"""
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    inventory_code = db.Column(db.String(50), unique=True, nullable=False)
    inventory_name = db.Column(db.String(200), nullable=False)

    # Thời điểm kiểm kê chuẩn (dùng để chốt sổ)
    inventory_time = db.Column(db.DateTime, nullable=True)

    # Thời gian thực hiện đợt (kế hoạch)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)

    # Loại kiểm kê: periodic / ad_hoc / full
    inventory_type = db.Column(db.String(20), nullable=True)

    # Phạm vi: toàn phường / theo nơi dùng / theo nhóm tài sản
    scope_type = db.Column(db.String(30), nullable=True)  # all_ward, by_location, by_asset_group
    scope = db.Column(db.String(255), nullable=True)  # mô tả text ngắn
    scope_locations = db.Column(db.Text, nullable=True)  # JSON list id nơi dùng
    scope_asset_groups = db.Column(db.Text, nullable=True)  # JSON list id nhóm tài sản

    # Thông tin quyết định kiểm kê
    decision_number = db.Column(db.String(100), nullable=True)
    decision_date = db.Column(db.Date, nullable=True)
    decision_file_path = db.Column(db.String(255), nullable=True)

    # Trạng thái workflow
    # draft -> in_progress -> submitted -> approved_locked -> closed
    status = db.Column(db.String(30), default='draft', nullable=False)
    locked_at = db.Column(db.DateTime, nullable=True)
    locked_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    closed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=now_vn)
    updated_at = db.Column(db.DateTime, default=now_vn, onupdate=now_vn)
    
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='inventories')
    locked_by = db.relationship('User', foreign_keys=[locked_by_id], backref='inventories_locked')
    closed_by = db.relationship('User', foreign_keys=[closed_by_id], backref='inventories_closed')

    results = db.relationship('InventoryResult', backref='inventory', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Inventory {self.inventory_code}>'

class InventoryResult(db.Model):
    """Kết quả kiểm kê từng tài sản (theo sổ)"""
    __tablename__ = 'inventory_result'
    
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)

    # Snapshot sổ sách tại thời điểm kiểm kê
    book_quantity = db.Column(db.Integer, nullable=False, default=1)
    book_value = db.Column(db.Float, nullable=False)  # Giá trị sổ sách
    book_location_id = db.Column(db.Integer, nullable=True)
    book_asset_type_id = db.Column(db.Integer, nullable=True)
    book_status = db.Column(db.String(20), nullable=True)

    # Kết quả thực tế
    actual_quantity = db.Column(db.Integer, nullable=True)
    actual_condition = db.Column(db.String(20), nullable=True)  # in_use, minor_damage, severe_damage, missing, transferred
    actual_status = db.Column(db.String(20), nullable=True)  # giữ để tương thích cũ
    actual_value = db.Column(db.Float, nullable=True)  # Giá trị thực tế (nếu cần)
    actual_location_id = db.Column(db.Integer, nullable=True)
    actual_serial_plate = db.Column(db.String(100), nullable=True)

    # Chênh lệch & nhận xét
    difference = db.Column(db.Float, nullable=True)  # Chênh lệch giá trị
    notes = db.Column(db.Text)

    checked_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    checked_at = db.Column(db.DateTime, nullable=True)
    
    asset = db.relationship('Asset', backref='inventory_results')
    checked_by = db.relationship('User', backref='inventory_checks')
    
    def __repr__(self):
        return f'<InventoryResult inventory={self.inventory_id} asset={self.asset_id}>'


class InventoryTeam(db.Model):
    """Tổ kiểm kê"""
    __tablename__ = 'inventory_team'

    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    leader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=now_vn)
    updated_at = db.Column(db.DateTime, default=now_vn, onupdate=now_vn)

    inventory = db.relationship('Inventory', backref='teams')
    leader = db.relationship('User', backref='inventory_teams_lead')


class InventoryTeamMember(db.Model):
    """Thành viên tổ kiểm kê"""
    __tablename__ = 'inventory_team_member'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('inventory_team.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(50), nullable=True)  # leader, member

    team = db.relationship('InventoryTeam', backref='members')
    user = db.relationship('User', backref='inventory_team_memberships')


class InventorySurplusAsset(db.Model):
    """Tài sản thừa trong kiểm kê (có thực tế nhưng chưa có trong sổ)"""
    __tablename__ = 'inventory_surplus_asset'

    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('inventory_team.id'), nullable=True)

    name = db.Column(db.String(255), nullable=False)
    asset_type_id = db.Column(db.Integer, nullable=True)
    location_id = db.Column(db.Integer, nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    estimated_start_year = db.Column(db.Integer, nullable=True)
    origin = db.Column(db.String(100), nullable=True)  # received, donated, purchased_not_recorded, other
    status = db.Column(db.String(20), nullable=False, default='surplus')  # surplus, proposed_increase, increased
    notes = db.Column(db.Text, nullable=True)

    increase_voucher_id = db.Column(db.Integer, nullable=True)

    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=now_vn)
    updated_at = db.Column(db.DateTime, default=now_vn, onupdate=now_vn)

    inventory = db.relationship('Inventory', backref='surplus_assets')
    team = db.relationship('InventoryTeam', backref='surplus_assets')


class InventoryLinePhoto(db.Model):
    """Ảnh minh chứng cho kết quả kiểm kê"""
    __tablename__ = 'inventory_line_photo'

    id = db.Column(db.Integer, primary_key=True)
    inventory_result_id = db.Column(db.Integer, db.ForeignKey('inventory_result.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=now_vn)

    inventory_result = db.relationship('InventoryResult', backref='photos')
    uploaded_by = db.relationship('User', backref='inventory_photos')


class InventoryLog(db.Model):
    """Nhật ký thao tác trong module kiểm kê"""
    __tablename__ = 'inventory_log'

    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    from_status = db.Column(db.String(30), nullable=True)
    to_status = db.Column(db.String(30), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    payload = db.Column(db.Text, nullable=True)  # JSON string

    actor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=now_vn)

    inventory = db.relationship('Inventory', backref='logs')
    actor = db.relationship('User', backref='inventory_logs')

class AssetTransfer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transfer_code = db.Column(db.String(50), unique=True, nullable=False)  # Mã bàn giao
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Người bàn giao
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Người nhận
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)  # Số lượng bàn giao
    expected_quantity = db.Column(db.Integer, nullable=False)  # Số lượng dự kiến
    confirmed_quantity = db.Column(db.Integer, default=0)  # Số lượng đã xác nhận
    notes = db.Column(db.Text)  # Ghi chú
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, rejected, cancelled
    confirmation_token = db.Column(db.String(100), unique=True, nullable=False)  # Token xác nhận
    token_expires_at = db.Column(db.DateTime, nullable=False)  # Token hết hạn
    confirmed_at = db.Column(db.DateTime, nullable=True)  # Thời gian xác nhận
    created_at = db.Column(db.DateTime, default=now_vn)
    updated_at = db.Column(db.DateTime, default=now_vn, onupdate=now_vn)
    
    # Relationships
    from_user = db.relationship('User', foreign_keys=[from_user_id], backref='transfers_sent')
    to_user = db.relationship('User', foreign_keys=[to_user_id], backref='transfers_received')
    asset = db.relationship('Asset', backref='transfers')
    
    def is_token_valid(self):
        """Kiểm tra token còn hiệu lực không"""
        return now_vn() < self.token_expires_at
    
    def is_fully_confirmed(self):
        """Kiểm tra đã xác nhận đầy đủ chưa"""
        return self.confirmed_quantity >= self.expected_quantity
    
    def __repr__(self):
        return f'<AssetTransfer #{self.id} {self.transfer_code}>'

# Model cho phân quyền chi tiết
class Permission(db.Model):
    """Bảng lưu các quyền có sẵn trong hệ thống"""
    __tablename__ = 'permission'
    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(100), nullable=False)  # Module: assets, users, maintenance, etc.
    action = db.Column(db.String(50), nullable=False)  # Action: add, view, edit, delete, full
    name = db.Column(db.String(200), nullable=False)  # Tên hiển thị
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)  # Nhóm quyền
    created_at = db.Column(db.DateTime, default=now_vn)
    
    # Relationship
    user_permissions = db.relationship('UserPermission', backref='permission', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Permission {self.module}.{self.action}>'
    
    @staticmethod
    def get_default_permissions():
        """Trả về danh sách quyền mặc định của hệ thống"""
        return [
            # Quản lý tài sản
            {'module': 'assets', 'action': 'add', 'name': 'Thêm tài sản', 'category': 'Quản lý tài sản'},
            {'module': 'assets', 'action': 'view', 'name': 'Xem tài sản', 'category': 'Quản lý tài sản'},
            {'module': 'assets', 'action': 'edit', 'name': 'Chỉnh sửa tài sản', 'category': 'Quản lý tài sản'},
            {'module': 'assets', 'action': 'delete', 'name': 'Xóa tài sản', 'category': 'Quản lý tài sản'},
            {'module': 'assets', 'action': 'full', 'name': 'Toàn quyền tài sản', 'category': 'Quản lý tài sản'},
            # Quản lý loại tài sản
            {'module': 'asset_types', 'action': 'add', 'name': 'Thêm loại tài sản', 'category': 'Quản lý loại tài sản'},
            {'module': 'asset_types', 'action': 'view', 'name': 'Xem loại tài sản', 'category': 'Quản lý loại tài sản'},
            {'module': 'asset_types', 'action': 'edit', 'name': 'Chỉnh sửa loại tài sản', 'category': 'Quản lý loại tài sản'},
            {'module': 'asset_types', 'action': 'delete', 'name': 'Xóa loại tài sản', 'category': 'Quản lý loại tài sản'},
            {'module': 'asset_types', 'action': 'full', 'name': 'Toàn quyền loại tài sản', 'category': 'Quản lý loại tài sản'},
            # Quản lý người dùng
            {'module': 'users', 'action': 'add', 'name': 'Thêm người dùng', 'category': 'Quản lý người dùng'},
            {'module': 'users', 'action': 'view', 'name': 'Xem người dùng', 'category': 'Quản lý người dùng'},
            {'module': 'users', 'action': 'edit', 'name': 'Chỉnh sửa người dùng', 'category': 'Quản lý người dùng'},
            {'module': 'users', 'action': 'delete', 'name': 'Xóa người dùng', 'category': 'Quản lý người dùng'},
            {'module': 'users', 'action': 'full', 'name': 'Toàn quyền người dùng', 'category': 'Quản lý người dùng'},
            # Bảo trì thiết bị
            {'module': 'maintenance', 'action': 'add', 'name': 'Thêm bảo trì', 'category': 'Bảo trì thiết bị'},
            {'module': 'maintenance', 'action': 'view', 'name': 'Xem bảo trì', 'category': 'Bảo trì thiết bị'},
            {'module': 'maintenance', 'action': 'edit', 'name': 'Chỉnh sửa bảo trì', 'category': 'Bảo trì thiết bị'},
            {'module': 'maintenance', 'action': 'delete', 'name': 'Xóa bảo trì', 'category': 'Bảo trì thiết bị'},
            {'module': 'maintenance', 'action': 'full', 'name': 'Toàn quyền bảo trì', 'category': 'Bảo trì thiết bị'},
            # Bàn giao tài sản
            {'module': 'transfer', 'action': 'add', 'name': 'Tạo bàn giao', 'category': 'Bàn giao tài sản'},
            {'module': 'transfer', 'action': 'view', 'name': 'Xem bàn giao', 'category': 'Bàn giao tài sản'},
            {'module': 'transfer', 'action': 'edit', 'name': 'Chỉnh sửa bàn giao', 'category': 'Bàn giao tài sản'},
            {'module': 'transfer', 'action': 'delete', 'name': 'Xóa bàn giao', 'category': 'Bàn giao tài sản'},
            {'module': 'transfer', 'action': 'full', 'name': 'Toàn quyền bàn giao', 'category': 'Bàn giao tài sản'},
            # Báo cáo
            {'module': 'reports', 'action': 'view', 'name': 'Xem báo cáo', 'category': 'Báo cáo'},
            {'module': 'reports', 'action': 'export', 'name': 'Xuất báo cáo', 'category': 'Báo cáo'},
            {'module': 'reports', 'action': 'full', 'name': 'Toàn quyền báo cáo', 'category': 'Báo cáo'},
            # Nhật ký
            {'module': 'audit_logs', 'action': 'view', 'name': 'Xem nhật ký', 'category': 'Nhật ký hệ thống'},
            {'module': 'audit_logs', 'action': 'full', 'name': 'Toàn quyền nhật ký', 'category': 'Nhật ký hệ thống'},
        ]

class UserPermission(db.Model):
    """Bảng trung gian lưu quyền của từng user"""
    __tablename__ = 'user_permission'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permission.id'), nullable=False)
    granted = db.Column(db.Boolean, default=True)  # True = có quyền, False = không có quyền
    created_at = db.Column(db.DateTime, default=now_vn)
    updated_at = db.Column(db.DateTime, default=now_vn, onupdate=now_vn)
    
    # Unique constraint để mỗi user chỉ có 1 record cho mỗi permission
    __table_args__ = (db.UniqueConstraint('user_id', 'permission_id', name='_user_permission_uc'),)
    
    def __repr__(self):
        return f'<UserPermission user_id={self.user_id} permission_id={self.permission_id} granted={self.granted}>'

class SystemSetting(db.Model):
    """Cấu hình hệ thống"""
    __tablename__ = 'system_setting'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)  # Tên key cấu hình
    value = db.Column(db.Text, nullable=True)  # Giá trị cấu hình (JSON hoặc text)
    description = db.Column(db.String(500), nullable=True)  # Mô tả
    created_at = db.Column(db.DateTime, default=now_vn)
    updated_at = db.Column(db.DateTime, default=now_vn, onupdate=now_vn)
    
    def __repr__(self):
        return f'<SystemSetting key={self.key} value={self.value}>'
    
    @staticmethod
    def get_setting(key, default=None):
        """Lấy giá trị cấu hình"""
        setting = SystemSetting.query.filter_by(key=key).first()
        if setting:
            return setting.value
        return default
    
    @staticmethod
    def set_setting(key, value, description=None):
        """Thiết lập giá trị cấu hình"""
        setting = SystemSetting.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            if description:
                setting.description = description
            setting.updated_at = now_vn()
        else:
            setting = SystemSetting(key=key, value=value, description=description)
            db.session.add(setting)
        db.session.commit()
        return setting