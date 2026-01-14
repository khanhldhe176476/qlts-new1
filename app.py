# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response, send_from_directory, send_file
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False
    print("Warning: flask-cors not installed. CORS will be disabled.")
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta, date
from calendar import monthrange
import os
import mimetypes
import secrets
import string
import json
from functools import wraps
from werkzeug.utils import secure_filename
from config import Config
from utils.timezone import now_vn, today_vn
from utils.email_sender import send_email_from_config
import pandas as pd

app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for API
if CORS_AVAILABLE:
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

# Configure UTF-8 encoding for Jinja2 templates
app.jinja_env.auto_reload = True
app.jinja_env.add_extension('jinja2.ext.i18n')

# Trạng thái tiếng Việt
STATUS_LABELS_VI = {
    'active': 'Đang sử dụng',
    'inactive': 'Không hoạt động',
    'maintenance': 'Bảo trì',
    'disposed': 'Đã thanh lý',
    'available': 'Sẵn sàng',
    'assigned': 'Đã gán',
    'pending': 'Chờ xử lý',
    'waiting_confirmation': 'Chờ xác nhận',
    'confirmed': 'Đã xác nhận',
    'processing': 'Đang xử lý',
    'completed': 'Hoàn thành',
    'rejected': 'Đã từ chối',
    'draft': 'Nháp'
}


def status_vi(value: str) -> str:
    """Chuyển trạng thái sang tiếng Việt"""
    if not value:
        return ''
    return STATUS_LABELS_VI.get(value.lower(), value.title())


app.jinja_env.filters['status_vi'] = status_vi

# Configure UTF-8 encoding for all responses
@app.after_request
def set_charset(response):
    """Set UTF-8 charset for all HTML and text responses"""
    if response.content_type:
        content_type_lower = response.content_type.lower()
        if content_type_lower.startswith('text/html') or content_type_lower.startswith('text/'):
            if 'charset' not in content_type_lower:
                # Preserve original content type format
                if ';' in response.content_type:
                    response.content_type = response.content_type + '; charset=utf-8'
                else:
                    response.content_type = response.content_type + '; charset=utf-8'
    return response

# Date parsing helpers for compatibility (Python < 3.11)
def parse_iso_datetime(value):
    if not value: return None
    try:
        # Handle YYYY-MM-DD
        if len(value) == 10:
            return datetime.strptime(value, '%Y-%m-%d')
        # Handle ISO with T or space
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except Exception:
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%d/%m/%Y', '%d/%m/%Y %H:%M'):
            try: return datetime.strptime(value, fmt)
            except: continue
    return None

def parse_iso_date(value):
    dt = parse_iso_datetime(value)
    return dt.date() if dt else None

# Ensure upload directory exists
upload_folder = app.config.get('UPLOAD_FOLDER', 'instance/uploads')
if not os.path.isabs(upload_folder):
    upload_folder = os.path.join(app.root_path, upload_folder)
os.makedirs(upload_folder, exist_ok=True)
app.config['UPLOAD_FOLDER'] = upload_folder

IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg', 'tif', 'tiff', 'ico', 'avif'}

def allowed_file(filename):
    """Kiểm tra file có được phép upload không"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config.get('ALLOWED_EXTENSIONS', {
               'pdf',
               'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg', 'tif', 'tiff', 'ico', 'avif',
               'doc', 'docx', 'xls', 'xlsx'
           })

def is_image_file(filename: str) -> bool:
    """Kiểm tra file có phải là ảnh (để hiển thị inline)"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in IMAGE_EXTENSIONS

def save_uploaded_file(file, asset_id):
    """Lưu file upload và trả về đường dẫn"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Tạo tên file unique: asset_id_timestamp_filename
        timestamp = now_vn().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        unique_filename = f"asset_{asset_id}_{timestamp}{ext}"
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        # Trả về đường dẫn relative để lưu vào DB
        return f"uploads/{unique_filename}"
    return None

# If using SQLite, proactively ensure the target directory exists
try:
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI') or ''
    # Print masked DB URI for easier troubleshooting (no secrets)
    try:
        masked = db_uri
        if '@' in db_uri and '://' in db_uri:
            scheme, rest = db_uri.split('://', 1)
            if ':' in rest and '@' in rest:
                head, tail = rest.split('@', 1)
                user = head.split(':', 1)[0]
                masked = f"{scheme}://{user}:***@{tail}"
        print(f"[Config] SQLALCHEMY_DATABASE_URI = {masked}")
    except Exception:
        pass
    # If Postgres URL provided but driver missing, try to coerce or fallback to SQLite
    if 'postgresql' in db_uri or 'postgres' in db_uri:
        # Normalize scheme
        full_uri = db_uri.replace('postgres://', 'postgresql://', 1)
        
        # Test connection with timeout
        try:
            from sqlalchemy import create_engine
            # Handle different drivers
            test_uri = full_uri
            driver_args = {'connect_timeout': 5}
            
            # Try to identify which driver we have
            has_driver = False
            try:
                import psycopg
                if '+psycopg' not in test_uri:
                    test_uri = test_uri.replace('postgresql://', 'postgresql+psycopg://', 1)
                has_driver = True
            except ImportError:
                try:
                    import psycopg2
                    has_driver = True
                except ImportError:
                    pass
            
            if not has_driver:
                raise ImportError("No PostgreSQL driver found (psycopg or psycopg2)")

            test_engine = create_engine(test_uri, pool_pre_ping=True, connect_args=driver_args)
            print(f"[Config] Testing database connection to {test_uri.split('@')[-1]}...")
            with test_engine.connect() as conn:
                print(f"[Config] Database connection successful.")
                app.config['SQLALCHEMY_DATABASE_URI'] = test_uri
                db_uri = test_uri
        except Exception as conn_err:
            fallback = 'sqlite:///./instance/app.db'
            print(f'[Config] PostgreSQL connection failed: {conn_err}')
            print(f'[Config] Falling back to SQLite: {fallback}')
            app.config['SQLALCHEMY_DATABASE_URI'] = fallback
            db_uri = fallback
    
    if db_uri.startswith('sqlite:///'):
        # Support relative and absolute sqlite paths
        import pathlib
        path_part = db_uri.replace('sqlite:///', '', 1)
        db_path = pathlib.Path(path_part)
        if not db_path.is_absolute():
            # resolve relative to project root
            base_dir = pathlib.Path(__file__).resolve().parent
            db_path = (base_dir / db_path).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        normalized_sqlite_uri = f"sqlite:///{db_path}"
        app.config['SQLALCHEMY_DATABASE_URI'] = normalized_sqlite_uri
        db_uri = normalized_sqlite_uri
except Exception:
    # Non-fatal: proceed and let SQLAlchemy raise if anything else is wrong
    pass

# Import db from models
from models import (
    db, Asset, Role, User, AssetType, AuditLog, MaintenanceRecord, AssetTransfer, 
    Permission, UserPermission, AssetVoucher, AssetVoucherItem, AssetTransferHistory,
    AssetProcessRequest, AssetDepreciation, AssetAmortization,
    Inventory, InventoryResult, InventoryTeam, InventoryTeamMember,
    InventorySurplusAsset, InventoryLog, InventoryLinePhoto, asset_user, SystemSetting
)
db.init_app(app)
migrate = Migrate(app, db)

# Context processor để các cấu hình hệ thống có sẵn trong tất cả templates
@app.context_processor
def inject_system_settings():
    """Thêm cấu hình hệ thống vào context của tất cả templates"""
    org_name = SystemSetting.get_setting('org_name', '')
    browser_title = SystemSetting.get_setting('browser_title', 'Quản lý tài sản công')
    logo_path_setting = SystemSetting.get_setting('logo_path', '')
    
    if logo_path_setting:
        logo_path = url_for('uploaded_file', filename=logo_path_setting)
    else:
        logo_path = url_for('static', filename='img/logo.png')
    
    return {
        'system_org_name': org_name,
        'system_browser_title': browser_title,
        'system_logo_path': logo_path
    }

# Import models after db is initialized
# Models đã được import ở trên

# Import API blueprints
try:
    from routes_api import api_bp, jwt
    app.register_blueprint(api_bp)
    jwt.init_app(app)
except ImportError:
    print("Warning: API routes not available")
try:
    from routes_api_misa import api_misa_bp
    app.register_blueprint(api_misa_bp)
except ImportError:
    print("Warning: MISA API routes not available")

# Optional: new_site inventory blueprint (if used)
try:
    from new_site.routes_inventory import inventory_bp
    app.register_blueprint(inventory_bp)
except Exception:
    # Không critical, chỉ là API tài liệu nghiệp vụ
    pass

# Lightweight health endpoint (no auth) to verify server and routing are up
@app.route('/healthz', methods=['GET'])
def healthz():
    return jsonify({'status': 'ok'}), 200

# Reset admin password endpoint (chỉ dùng trong development)
@app.route('/dev/reset-admin-password', methods=['GET', 'POST'])
def dev_reset_admin_password():
    """Reset password cho user admin"""
    try:
        admin_password = app.config.get('ADMIN_PASSWORD', 'admin123')
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Tạo admin nếu chưa có
            admin_role = Role.query.filter_by(name='admin').first()
            if not admin_role:
                admin_role = Role(name='admin', description='Quản trị')
                db.session.add(admin_role)
                db.session.commit()
            
            admin_username = app.config.get('ADMIN_USERNAME', 'admin')
            admin_email = app.config.get('ADMIN_EMAIL', 'admin@company.com')
            admin = User(
                username=admin_username,
                email=admin_email,
                role_id=admin_role.id,
                is_active=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
        else:
            admin.set_password(admin_password)
            admin.is_active = True
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f"Password đã được reset cho user '{admin.username}'",
            'username': admin.username,
            'email': admin.email,
            'is_active': admin.is_active
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Quick diagnostics (no secrets), helps verify DB connectivity and basic models
@app.route('/dev/diag')
def dev_diag():
    try:
        role_count = Role.query.count()
        user_count = User.query.filter(User.deleted_at.is_(None)).count()
        asset_type_count = AssetType.query.filter(AssetType.deleted_at.is_(None)).count()
        asset_count = Asset.query.filter(Asset.deleted_at.is_(None)).count()
        maint_count = MaintenanceRecord.query.filter(MaintenanceRecord.deleted_at.is_(None)).count()
        return jsonify({
            'ok': True,
            'db_uri': ('sqlite' if app.config.get('SQLALCHEMY_DATABASE_URI','').startswith('sqlite') else 'non-sqlite'),
            'counts': {
                'roles': role_count,
                'users': user_count,
                'asset_types': asset_type_count,
                'assets': asset_count,
                'maintenance': maint_count
            }
        }), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

# First-run bootstrap: create roles and an admin account without requiring login.
# Protected by optional INIT_TOKEN; if INIT_TOKEN is set in .env, the same token
# must be provided via querystring (?token=...). Safe to run multiple times (idempotent).
@app.route('/dev/bootstrap')
def dev_bootstrap():
    token_cfg = app.config.get('INIT_TOKEN') or ''
    token_req = request.args.get('token', '')
    if token_cfg and token_req != token_cfg:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    # Create base roles if missing
    created = {'roles': 0, 'users': 0}
    # Bổ sung đầy đủ vai trò nghiệp vụ (idempotent)
    role_defs = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Quản trị viên hệ thống'),
        ('manager', 'Quản lý tài sản / Lãnh đạo phường'),
        ('accountant', 'Kế toán tài sản'),
        ('inventory_leader', 'Tổ trưởng kiểm kê / Đơn vị sử dụng'),
        ('inventory_member', 'Thành viên tổ kiểm kê'),
        ('user', 'Người dùng thông thường'),
    ]
    for name, desc in role_defs:
        if not Role.query.filter_by(name=name).first():
            db.session.add(Role(name=name, description=desc))
            created['roles'] += 1
    db.session.commit()
    # Create admin user if missing
    admin_username = app.config.get('ADMIN_USERNAME', 'admin')
    admin_email = app.config.get('ADMIN_EMAIL', 'admin@example.com')
    admin_password = app.config.get('ADMIN_PASSWORD', 'admin123')
    if User.query.filter_by(username=admin_username).first() is None:
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin', description='Quản trị')
            db.session.add(admin_role)
            db.session.commit()
        u = User(username=admin_username, email=admin_email, role_id=admin_role.id, is_active=True)
        u.set_password(admin_password)
        db.session.add(u)
        db.session.commit()
        created['users'] = 1
    return jsonify({'success': True, 'created': created}), 200

# Friendly minimal error handlers to avoid blank pages
@app.errorhandler(404)
def not_found(e):
    # Keep it simple to avoid template dependency
    return ('Trang không tồn tại (404). '
            'Hãy quay lại /login hoặc /. '
            'Nếu bạn vừa click một liên kết trong giao diện, vui lòng báo lại đường dẫn.'), 404

@app.errorhandler(500)
def internal_error(e):
    import traceback
    error_msg = traceback.format_exc()
    app.logger.error(f"500 Error: {error_msg}")
    print(f"\n{'='*60}")
    print("500 ERROR DETAILS:")
    print(f"{'='*60}")
    print(error_msg)
    print(f"{'='*60}\n")
    # In development, show error details
    if app.config.get('DEBUG', False):
        return f'<pre style="white-space: pre-wrap; font-family: monospace;">Lỗi máy chủ (500):\n\n{error_msg}</pre>', 500
    return ('Lỗi máy chủ (500). Vui lòng thử lại, hoặc truy cập /dev/diag để chẩn đoán nhanh.'), 500

# Jinja filter for Vietnamese date formatting
@app.template_filter('vn_date')
def vn_date(value, include_time: bool = False):
    try:
        if value is None:
            return ''
        # Accept date or datetime
        if hasattr(value, 'strftime'):
            if include_time:
                return value.strftime('%d/%m/%Y %H:%M')
            return value.strftime('%d/%m/%Y')
        return str(value)
    except Exception:
        return ''

@app.template_filter('maintenance_status_vi')
def maintenance_status_vi(value: str):
    mapping = {
        'completed': 'Hoàn thành',
        'scheduled': 'Đã lên lịch',
        'in_progress': 'Đang thực hiện',
        'cancelled': 'Đã hủy'
    }
    key = (value or '').lower()
    return mapping.get(key, value or '')

@app.template_filter('currency')
def currency_format(value):
    """Format số tiền với dấu chấm (.) làm phân cách hàng nghìn"""
    try:
        if value is None:
            return '0'
        num = float(value)
        if num == 0:
            return '0'
        # Format với dấu phẩy trước, sau đó thay bằng dấu chấm
        formatted = "{:,.0f}".format(num)
        return formatted.replace(',', '.')
    except (ValueError, TypeError):
        return '0'

@app.template_filter('maintenance_type_vi')
def maintenance_type_vi(value: str):
    mapping = {
        'maintenance': 'Bảo trì định kỳ',
        'repair': 'Sửa chữa',
        'inspection': 'Kiểm tra',
        'upgrade': 'Nâng cấp',
        'replacement': 'Thay thế'
    }
    key = (value or '').lower()
    return mapping.get(key, value or '')

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Chỉ Admin mới được truy cập"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Bạn không có quyền truy cập chức năng này. Chỉ Admin mới được phép.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    """Manager hoặc Admin được truy cập"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        role = session.get('role')
        if role not in ['admin', 'manager']:
            flash('Bạn không có quyền truy cập chức năng này. Chỉ Quản lý và Admin mới được phép.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_or_manager_required(f):
    """Admin hoặc Manager được truy cập (alias của manager_required)"""
    return manager_required(f)

# Root/index route
@app.route('/')
@login_required
def index():
    """
    Trang chính Dashboard của ứng dụng.
    Hiển thị thống kê tổng quan về tài sản, bảo trì, v.v.
    """
    try:
        from datetime import date
        today = date.today()
        
        # Lấy các loại tài sản
        asset_types = AssetType.query.filter(
            AssetType.deleted_at.is_(None)
        ).all()
        
        # Lấy tất cả tài sản để tính toán thống kê
        all_assets = Asset.query.filter(Asset.deleted_at.is_(None)).all()
        
        # Lấy một số tài sản gần đây
        assets = Asset.query.filter(
            Asset.deleted_at.is_(None)
        ).order_by(Asset.created_at.desc()).limit(10).all()
        
        # Hàm mapping icon theo tên loại thiết bị
        def get_asset_type_icon(type_name):
            """Trả về icon phù hợp với loại thiết bị"""
            if not type_name:
                return 'fa-box'
            type_name_lower = type_name.lower().strip()
            
            icon_map = [
                ('thiết bị văn phòng', 'fa-print'),
                ('thiết bị điện tử', 'fa-microchip'),
                ('thiết bị mạng', 'fa-network-wired'),
                ('thiết bị điện', 'fa-plug'),
                ('thiết bị an ninh', 'fa-shield-alt'),
                ('cây máy tính', 'fa-desktop'),
                ('bàn ghế', 'fa-couch'),
                ('air conditioner', 'fa-snowflake'),
                ('cơ sở dữ liệu', 'fa-database'),
                ('máy chủ', 'fa-server'),
                ('sao lưu', 'fa-hdd'),
                ('máy tính', 'fa-desktop'),
                ('computer', 'fa-desktop'),
                ('pc', 'fa-desktop'),
                ('laptop', 'fa-laptop'),
                ('office', 'fa-print'),
                ('máy in', 'fa-print'),
                ('printer', 'fa-print'),
                ('nội thất', 'fa-couch'),
                ('furniture', 'fa-couch'),
                ('bàn', 'fa-table'),
                ('ghế', 'fa-chair'),
                ('tủ', 'fa-archive'),
                ('kệ', 'fa-archive'),
                ('network', 'fa-network-wired'),
                ('router', 'fa-network-wired'),
                ('switch', 'fa-network-wired'),
                ('wifi', 'fa-wifi'),
                ('điện', 'fa-plug'),
                ('electrical', 'fa-plug'),
                ('điện tử', 'fa-microchip'),
                ('electronic', 'fa-microchip'),
                ('điện thoại', 'fa-mobile-alt'),
                ('phone', 'fa-mobile-alt'),
                ('smartphone', 'fa-mobile-alt'),
                ('phần mềm', 'fa-code'),
                ('software', 'fa-code'),
                ('app', 'fa-code'),
                ('security', 'fa-shield-alt'),
                ('camera', 'fa-video'),
                ('dụng cụ', 'fa-tools'),
                ('tool', 'fa-tools'),
                ('tools', 'fa-tools'),
                ('máy chiếu', 'fa-video'),
                ('projector', 'fa-video'),
                ('màn hình', 'fa-tv'),
                ('monitor', 'fa-tv'),
                ('screen', 'fa-tv'),
                ('máy lạnh', 'fa-snowflake'),
                ('ac', 'fa-snowflake'),
                ('quạt', 'fa-wind'),
                ('fan', 'fa-wind'),
                ('server', 'fa-server'),
                ('database', 'fa-database'),
                ('backup', 'fa-hdd'),
                ('khác', 'fa-box'),
                ('other', 'fa-box'),
            ]
            
            for key, icon in icon_map:
                if key in type_name_lower:
                    return icon
            return 'fa-box'
        
        # Thống kê số lượng thiết bị theo từng loại
        asset_type_stats = []
        for asset_type in asset_types:
            if not asset_type or not asset_type.name:
                continue
            try:
                count = Asset.query.filter(
                    Asset.asset_type_id == asset_type.id,
                    Asset.deleted_at.is_(None),
                    Asset.status != 'disposed'  # Loại bỏ tài sản đã thanh lý
                ).count()
                active_count = Asset.query.filter(
                    Asset.asset_type_id == asset_type.id,
                    Asset.status == 'active',
                    Asset.deleted_at.is_(None)
                ).count()
                inactive_count = Asset.query.filter(
                    Asset.asset_type_id == asset_type.id,
                    Asset.status == 'inactive',
                    Asset.deleted_at.is_(None)
                ).count()
                maintenance_count = Asset.query.filter(
                    Asset.asset_type_id == asset_type.id,
                    Asset.status == 'maintenance',
                    Asset.deleted_at.is_(None)
                ).count()
                asset_type_stats.append({
                    'type_id': asset_type.id,
                    'type_name': asset_type.name or 'Không có tên',
                    'total_count': count,
                    'active_count': active_count,
                    'inactive_count': inactive_count,
                    'maintenance_count': maintenance_count,
                    'icon': get_asset_type_icon(asset_type.name or '')
                })
            except Exception as ex:
                app.logger.warning(f"Error processing asset_type {asset_type.id}: {ex}")
                continue
        
        # Sắp xếp theo số lượng giảm dần
        asset_type_stats.sort(key=lambda x: x['total_count'], reverse=True)
        
        # Tính tổng giá trị tài sản (VNĐ) - loại bỏ tài sản đã thanh lý
        total_value = 0
        try:
            for asset in all_assets:
                # Không tính tài sản đã thanh lý vào tổng giá trị
                if asset.status != 'disposed' and asset.price:
                    total_value += asset.price * (asset.quantity or 1)
        except Exception:
            total_value = 0
        
        # Thống kê tài sản - đếm số lượng (có tính quantity)
        active_count = sum(a.quantity or 1 for a in all_assets if a.status == 'active')
        inactive_count = sum(a.quantity or 1 for a in all_assets if a.status == 'inactive')
        maintenance_count = sum(a.quantity or 1 for a in all_assets if a.status == 'maintenance')
        disposed_count = sum(a.quantity or 1 for a in all_assets if a.status == 'disposed')
        
        # Debug: Log số lượng tài sản đã thanh lý
        disposed_assets_list = [a for a in all_assets if a.status == 'disposed']
        app.logger.info(f"[Dashboard] Disposed assets count: {disposed_count}, actual disposed assets: {len(disposed_assets_list)}")
        if disposed_assets_list:
            app.logger.info(f"[Dashboard] Sample disposed assets: {[(a.id, a.name, a.status) for a in disposed_assets_list[:5]]}")
        # Đếm các status khác (null hoặc status khác, nhưng KHÔNG tính disposed)
        other_count = sum(a.quantity or 1 for a in all_assets 
                         if a.status != 'disposed' and 
                         ((a.status is None) or (a.status not in ['active', 'inactive', 'maintenance', 'disposed'])))
        
        # Tính tổng số từ tất cả các status (KHÔNG bao gồm disposed) để đảm bảo chính xác
        calculated_total = active_count + inactive_count + maintenance_count + other_count
        total_count = calculated_total  # Luôn dùng calculated_total để đảm bảo khớp
        
        # Debug: Kiểm tra tổng số (loại bỏ disposed)
        direct_total = sum(a.quantity or 1 for a in all_assets if a.status != 'disposed')
        if abs(calculated_total - direct_total) > 0:
            app.logger.warning(f"Asset count mismatch: direct_total={direct_total}, calculated={calculated_total}, active={active_count}, inactive={inactive_count}, maintenance={maintenance_count}, disposed={disposed_count}, other={other_count}")
        
        # Đếm số lượng bản ghi bảo trì (khác với maintenance_assets)
        maintenance_record_count = MaintenanceRecord.query.filter(
            MaintenanceRecord.deleted_at.is_(None)
        ).count()
        
        # Tính tổng chi phí bảo trì
        from sqlalchemy import func
        total_maintenance_cost = db.session.query(func.sum(MaintenanceRecord.cost)).filter(
            MaintenanceRecord.deleted_at.is_(None)
        ).scalar() or 0
        
        stats = {
            'total_assets': total_count,
            'active_assets': active_count,
            'inactive_assets': inactive_count,
            'maintenance_assets': maintenance_count,
            'disposed_assets': disposed_count,  # Số lượng tài sản đã thanh lý
            'other_assets': other_count,  # Thêm để debug
            'total_asset_types': len(asset_types),
            'total_users': User.query.filter(User.deleted_at.is_(None)).count(),
            'maintenance_count': maintenance_record_count,  # Số lượng bản ghi bảo trì
            'total_value': total_value,
            'total_maintenance_cost': total_maintenance_cost, # Tổng chi phí bảo trì
            'asset_type_stats': asset_type_stats,
        }
        
        # Lấy các bảo trì sắp đến hạn
        due_records = []
        overdue = 0
        due_soon = 0
        try:
            from datetime import timedelta, datetime
            next_30_days = today + timedelta(days=30)
            
            # Query all records with next_due_date
            all_due_records = MaintenanceRecord.query.filter(
                MaintenanceRecord.deleted_at.is_(None),
                MaintenanceRecord.next_due_date.isnot(None)
            ).all()
            
            # Filter in Python to handle both date and datetime types
            filtered_records = []
            for r in all_due_records:
                if r.next_due_date:
                    try:
                        # Convert to date for comparison
                        r_date = r.next_due_date.date() if isinstance(r.next_due_date, datetime) else r.next_due_date
                        if r_date and r_date <= next_30_days:
                            filtered_records.append(r)
                            # Count overdue and due soon
                            if r_date < today:
                                overdue += 1
                            elif r_date >= today:
                                due_soon += 1
                    except Exception:
                        continue
            
            # Sort by date
            try:
                filtered_records.sort(key=lambda x: x.next_due_date.date() if isinstance(x.next_due_date, datetime) else x.next_due_date)
            except Exception:
                pass  # If sort fails, use unsorted list
            
            due_records = filtered_records[:10]
        except Exception as ex:
            app.logger.warning(f"Error querying due records: {ex}")
            due_records = []
            overdue = 0
            due_soon = 0
        
        # Thêm thống kê bảo trì vào stats
        stats['overdue_maintenance'] = overdue
        stats['due_soon_maintenance'] = due_soon
        
        try:
            if overdue:
                flash(f'{overdue} thiết bị quá hạn bảo trì!', 'warning')
            elif due_soon:
                flash(f'{due_soon} thiết bị sắp đến hạn bảo trì trong 30 ngày.', 'info')
        except Exception:
            pass
        
        return render_template('index.html', assets=assets, stats=stats, asset_types=asset_types, due_records=due_records, today=today)
    except Exception as e:
        app.logger.error(f"Error rendering dashboard: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        app.logger.error(error_trace)
        flash('Có lỗi xảy ra khi tải Dashboard. Vui lòng thử lại.', 'error')
        return redirect(url_for('assets'))


# Login routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    # i18n strings (vi/en) for login page
    lang = session.get('lang', 'vi')
    i18n = {
        'vi': {
            'title': 'Đăng nhập',
            'subtitle': 'Chào mừng bạn trở lại! Vui lòng đăng nhập để tiếp tục',
            'username': 'Tài khoản',
            'password': 'Mật khẩu',
            'remember': 'Ghi nhớ đăng nhập',
            'login': 'Đăng nhập'
        },
        'en': {
            'title': 'Sign in',
            'subtitle': 'Welcome back! Please sign in to continue',
            'username': 'Username',
            'password': 'Password',
            'remember': 'Remember me',
            'login': 'Sign in'
        }
    }[lang]
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember')
        
        # Validate input
        if not username:
            flash('<i class="fas fa-exclamation-triangle mr-2"></i>Tên đăng nhập không được để trống!', 'error')
            return render_template('auth/login.html', i18n=i18n, lang=lang)
        
        if not password:
            flash('<i class="fas fa-exclamation-triangle mr-2"></i>Mật khẩu không được để trống!', 'error')
            return render_template('auth/login.html', i18n=i18n, lang=lang)
        
        user = User.query.filter_by(username=username).first()
        
        # Kiểm tra và thông báo lỗi chi tiết
        if not user:
            flash('<i class="fas fa-user-times mr-2"></i><strong>Tài khoản không tồn tại!</strong><br><small>Vui lòng kiểm tra lại tên đăng nhập.</small>', 'error')
        elif not user.is_active:
            flash('<i class="fas fa-ban mr-2"></i><strong>Tài khoản đã bị vô hiệu hóa!</strong><br><small>Vui lòng liên hệ quản trị viên để được hỗ trợ.</small>', 'error')
        elif not user.check_password(password):
            flash('<i class="fas fa-key mr-2"></i><strong>Mật khẩu không đúng!</strong><br><small>Vui lòng kiểm tra lại mật khẩu. Nếu quên mật khẩu, vui lòng liên hệ quản trị viên.</small>', 'error')
        else:
            # Đăng nhập thành công
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role.name
            
            # Update last login
            user.last_login = now_vn()
            db.session.commit()
            
            flash(f'<i class="fas fa-check-circle mr-2"></i><strong>Đăng nhập thành công!</strong><br><small>Chào mừng {user.username} trở lại hệ thống.</small>', 'success')
            return redirect(url_for('index'))
    
    return render_template('auth/login.html', i18n=i18n, lang=lang)

@app.route('/set-lang/<lang>')
def set_lang(lang: str):
    if lang not in ['vi', 'en']:
        lang = 'vi'
    session['lang'] = lang
    # redirect back to login or referrer
    return redirect(request.referrer or url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Bạn đã đăng xuất thành công!', 'info')
    return redirect(url_for('login'))

@app.route('/trash')
@manager_required
def trash():
    """Thùng rác - hiển thị các bản ghi đã xóa mềm"""
    module = request.args.get('module', 'all')
    per_page = 10
    page_assets = request.args.get('page_assets', 1, type=int)
    page_asset_types = request.args.get('page_asset_types', 1, type=int)
    page_users = request.args.get('page_users', 1, type=int)
    page_maintenance = request.args.get('page_maintenance', 1, type=int)

    assets_paginate = Asset.query.filter(Asset.deleted_at.isnot(None))\
        .order_by(Asset.deleted_at.desc())\
        .paginate(page=page_assets, per_page=per_page, error_out=False)

    asset_types_paginate = AssetType.query.filter(AssetType.deleted_at.isnot(None))\
        .order_by(AssetType.deleted_at.desc())\
        .paginate(page=page_asset_types, per_page=per_page, error_out=False)

    users_paginate = User.query.filter(User.deleted_at.isnot(None))\
        .order_by(User.deleted_at.desc())\
        .paginate(page=page_users, per_page=per_page, error_out=False)

    maintenance_paginate = MaintenanceRecord.query.filter(MaintenanceRecord.deleted_at.isnot(None))\
        .order_by(MaintenanceRecord.deleted_at.desc())\
        .paginate(page=page_maintenance, per_page=per_page, error_out=False)

    return render_template(
        'trash/list.html',
        module=module,
        assets_paginate=assets_paginate,
        asset_types_paginate=asset_types_paginate,
        users_paginate=users_paginate,
        maintenance_paginate=maintenance_paginate,
        page_assets=page_assets,
        page_asset_types=page_asset_types,
        page_users=page_users,
        page_maintenance=page_maintenance
    )

@app.route('/trash/restore', methods=['POST'])
@manager_required
def trash_restore():
    """Khôi phục bản ghi đã xóa mềm"""
    module = request.form.get('module') or request.args.get('module')
    id_str = request.form.get('id') or request.args.get('id')
    try:
        entity_id = int(id_str)
    except Exception:
        flash('Yêu cầu không hợp lệ.', 'error')
        return redirect(url_for('trash', module=module or 'all'))
    model_map = {
        'asset': Asset,
        'asset_type': AssetType,
        'user': User,
        'maintenance': MaintenanceRecord
    }
    model = model_map.get(module)
    if not model:
        flash('Phân hệ không hợp lệ.', 'error')
        return redirect(url_for('trash', module='all'))
    obj = model.query.get(entity_id)
    if not obj:
        flash('Không tìm thấy bản ghi.', 'error')
        return redirect(url_for('trash', module=module))
    if hasattr(obj, 'restore'):
        obj.restore()
        if module == 'asset':
            # Khôi phục các bản ghi bảo trì đi kèm
            for rec in obj.maintenance_records:
                if rec.deleted_at is not None and hasattr(rec, 'restore'):
                    rec.restore()
        db.session.commit()

        # Ghi nhật ký hoạt động
        module_map = {
            'asset': 'assets',
            'asset_type': 'asset_types',
            'user': 'users',
            'maintenance': 'maintenance'
        }
        try:
            uid = session.get('user_id')
            if uid:
                db.session.add(AuditLog(
                    user_id=uid,
                    module=module_map.get(module, module),
                    action='restore',
                    entity_id=entity_id,
                    details=f'restored_from_trash module={module}'
                ))
                db.session.commit()
        except Exception:
            db.session.rollback()

        flash('Khôi phục thành công.', 'success')
    else:
        flash('Bản ghi không hỗ trợ khôi phục.', 'error')
    return redirect(url_for('trash', module=module))

@app.route('/trash/bulk-restore', methods=['POST'])
@manager_required
def trash_bulk_restore():
    """Khôi phục nhiều bản ghi cùng lúc"""
    module = request.form.get('module')
    ids = request.form.getlist('ids')
    
    if not ids:
        flash('Vui lòng chọn ít nhất một mục.', 'error')
        return redirect(url_for('trash', module=module or 'all'))
        
    model_map = {
        'asset': Asset,
        'asset_type': AssetType,
        'user': User,
        'maintenance': MaintenanceRecord
    }
    model = model_map.get(module)
    if not model:
        flash('Phân hệ không hợp lệ.', 'error')
        return redirect(url_for('trash', module='all'))
        
    count = 0
    uid = session.get('user_id')
    
    module_map = {
        'asset': 'assets',
        'asset_type': 'asset_types',
        'user': 'users',
        'maintenance': 'maintenance'
    }

    for entity_id in ids:
        try:
            obj = model.query.get(int(entity_id))
            if obj and hasattr(obj, 'restore'):
                obj.restore()
                if module == 'asset':
                    for rec in obj.maintenance_records:
                        if rec.deleted_at is not None and hasattr(rec, 'restore'):
                            rec.restore()
                
                if uid:
                    db.session.add(AuditLog(
                        user_id=uid,
                        module=module_map.get(module, module),
                        action='restore',
                        entity_id=int(entity_id),
                        details=f'bulk_restored_from_trash module={module}'
                    ))
                count += 1
        except Exception:
            continue
            
    try:
        db.session.commit()
        flash(f'Đã khôi phục thành công {count} bản ghi.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi khôi phục: {str(e)}', 'error')
        
    return redirect(url_for('trash', module=module))

@app.route('/trash/bulk-delete', methods=['POST'])
@manager_required
def trash_bulk_delete():
    """Xóa vĩnh viễn nhiều bản ghi cùng lúc"""
    module = request.form.get('module')
    ids = request.form.getlist('ids')
    
    if not ids:
        flash('Vui lòng chọn ít nhất một mục.', 'error')
        return redirect(url_for('trash', module=module or 'all'))
        
    model_map = {
        'asset': Asset,
        'asset_type': AssetType,
        'user': User,
        'maintenance': MaintenanceRecord
    }
    model = model_map.get(module)
    if not model:
        flash('Phân hệ không hợp lệ.', 'error')
        return redirect(url_for('trash', module='all'))
        
    count = 0
    uid = session.get('user_id')
    
    module_map = {
        'asset': 'assets',
        'asset_type': 'asset_types',
        'user': 'users',
        'maintenance': 'maintenance'
    }

    for entity_id in ids:
        try:
            entity_id_int = int(entity_id)
            obj = model.query.get(entity_id_int)
            if not obj:
                continue
                
            if module == 'asset':
                for rec in obj.maintenance_records:
                    db.session.delete(rec)
                if obj.invoice_file_path:
                    try:
                        clean_filename = obj.invoice_file_path.replace('uploads/', '')
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], clean_filename)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    except Exception:
                        pass
            elif module == 'asset_type':
                related_assets = Asset.query.filter(Asset.asset_type_id == entity_id_int).all()
                if related_assets:
                    alternative_type = AssetType.query.filter(
                        AssetType.id != entity_id_int,
                        AssetType.deleted_at.is_(None)
                    ).first()
                    if alternative_type:
                        for asset in related_assets:
                            asset.asset_type_id = alternative_type.id
                    else:
                        continue # Skip deleting this type if no alternative
            
            db.session.delete(obj)
            if uid:
                db.session.add(AuditLog(
                    user_id=uid,
                    module=module_map.get(module, module),
                    action='permanent_delete',
                    entity_id=entity_id_int,
                    details=f'bulk_deleted_from_trash module={module}'
                ))
            count += 1
        except Exception:
            continue
            
    try:
        db.session.commit()
        flash(f'Đã xóa vĩnh viễn thành công {count} bản ghi.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi xóa vĩnh viễn: {str(e)}', 'error')
        
    return redirect(url_for('trash', module=module))

@app.route('/trash/permanent-delete', methods=['POST'])
@manager_required
def trash_permanent_delete():
    """Xóa vĩnh viễn bản ghi"""
    module = request.form.get('module') or request.args.get('module')
    id_str = request.form.get('id') or request.args.get('id')
    try:
        entity_id = int(id_str)
    except Exception:
        flash('Yêu cầu không hợp lệ.', 'error')
        return redirect(url_for('trash', module=module or 'all'))
    model_map = {
        'asset': Asset,
        'asset_type': AssetType,
        'user': User,
        'maintenance': MaintenanceRecord
    }
    model = model_map.get(module)
    if not model:
        flash('Phân hệ không hợp lệ.', 'error')
        return redirect(url_for('trash', module='all'))
    obj = model.query.get(entity_id)
    if not obj:
        flash('Không tìm thấy bản ghi.', 'error')
        return redirect(url_for('trash', module=module))
    try:
        if module == 'asset':
            for rec in obj.maintenance_records:
                db.session.delete(rec)
            if obj.invoice_file_path:
                try:
                    clean_filename = obj.invoice_file_path.replace('uploads/', '')
                    file_path = os.path.join(upload_folder, clean_filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception:
                    pass
        elif module == 'asset_type':
            # Kiểm tra xem có Asset nào đang sử dụng AssetType này không
            related_assets = Asset.query.filter(Asset.asset_type_id == entity_id).all()
            if related_assets:
                # Tìm một AssetType khác để gán (loại đầu tiên còn lại, không phải loại đang xóa)
                alternative_type = AssetType.query.filter(
                    AssetType.id != entity_id,
                    AssetType.deleted_at.is_(None)
                ).first()
                
                if not alternative_type:
                    flash('Không thể xóa loại tài sản này vì không còn loại tài sản nào khác để gán cho các tài sản đang sử dụng loại này.', 'error')
                    return redirect(url_for('trash', module=module))
                
                # Gán tất cả Asset sang loại thay thế
                for asset in related_assets:
                    asset.asset_type_id = alternative_type.id
                db.session.commit()
                flash(f'Đã gán {len(related_assets)} tài sản sang loại "{alternative_type.name}" trước khi xóa loại tài sản này.', 'info')
        
        db.session.delete(obj)
        db.session.commit()

        # Ghi nhật ký hoạt động
        module_map = {
            'asset': 'assets',
            'asset_type': 'asset_types',
            'user': 'users',
            'maintenance': 'maintenance'
        }
        try:
            uid = session.get('user_id')
            if uid:
                db.session.add(AuditLog(
                    user_id=uid,
                    module=module_map.get(module, module),
                    action='permanent_delete',
                    entity_id=entity_id,
                    details=f'deleted_from_trash module={module}'
                ))
                db.session.commit()
        except Exception:
            db.session.rollback()

        flash('Đã xóa vĩnh viễn.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi xóa vĩnh viễn: {str(e)}', 'error')
    return redirect(url_for('trash', module=module))

# Old index route - keep for backward compatibility
@app.route('/old')
def index_old():
    import traceback
    try:
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        assets = Asset.query.filter(Asset.deleted_at.is_(None)).all()
        asset_types = AssetType.query.filter(AssetType.deleted_at.is_(None)).all()
        users = User.query.filter(User.deleted_at.is_(None)).all()
    except Exception as e:
        error_msg = traceback.format_exc()
        app.logger.error(f"Error in index() - initial queries: {str(e)}")
        app.logger.error(error_msg)
        print(f"\n{'='*60}")
        print("INDEX ROUTE ERROR - Initial Queries:")
        print(f"{'='*60}")
        print(error_msg)
        print(f"{'='*60}\n")
        # Continue with empty data instead of failing
        assets = []
        asset_types = []
        users = []
    
    # Hàm mapping icon theo tên loại thiết bị
    def get_asset_type_icon(type_name):
        """Trả về icon phù hợp với loại thiết bị"""
        if not type_name:
            return 'fa-box'
        type_name_lower = type_name.lower().strip()
        
        # Mapping icon - sắp xếp theo độ dài giảm dần để ưu tiên từ khóa dài hơn, chính xác hơn
        icon_map = [
            # Các từ khóa dài và cụ thể trước
            ('thiết bị văn phòng', 'fa-print'),
            ('thiết bị điện tử', 'fa-microchip'),
            ('thiết bị mạng', 'fa-network-wired'),
            ('thiết bị điện', 'fa-plug'),
            ('thiết bị an ninh', 'fa-shield-alt'),
            ('cây máy tính', 'fa-desktop'),
            ('bàn ghế', 'fa-couch'),
            ('air conditioner', 'fa-snowflake'),
            ('cơ sở dữ liệu', 'fa-database'),
            ('máy chủ', 'fa-server'),
            ('sao lưu', 'fa-hdd'),
            
            # Các từ khóa ngắn hơn
            ('máy tính', 'fa-desktop'),
            ('computer', 'fa-desktop'),
            ('pc', 'fa-desktop'),
            ('laptop', 'fa-laptop'),
            ('office', 'fa-print'),
            ('máy in', 'fa-print'),
            ('printer', 'fa-print'),
            ('nội thất', 'fa-couch'),
            ('furniture', 'fa-couch'),
            ('bàn', 'fa-table'),
            ('ghế', 'fa-chair'),
            ('tủ', 'fa-archive'),
            ('kệ', 'fa-archive'),
            ('network', 'fa-network-wired'),
            ('router', 'fa-network-wired'),
            ('switch', 'fa-network-wired'),
            ('wifi', 'fa-wifi'),
            ('điện', 'fa-plug'),
            ('electrical', 'fa-plug'),
            ('điện tử', 'fa-microchip'),
            ('electronic', 'fa-microchip'),
            ('điện thoại', 'fa-mobile-alt'),
            ('phone', 'fa-mobile-alt'),
            ('smartphone', 'fa-mobile-alt'),
            ('phần mềm', 'fa-code'),
            ('software', 'fa-code'),
            ('app', 'fa-code'),
            ('security', 'fa-shield-alt'),
            ('camera', 'fa-video'),
            ('dụng cụ', 'fa-tools'),
            ('tool', 'fa-tools'),
            ('tools', 'fa-tools'),
            ('máy chiếu', 'fa-video'),
            ('projector', 'fa-video'),
            ('màn hình', 'fa-tv'),
            ('monitor', 'fa-tv'),
            ('screen', 'fa-tv'),
            ('máy lạnh', 'fa-snowflake'),
            ('ac', 'fa-snowflake'),
            ('quạt', 'fa-wind'),
            ('fan', 'fa-wind'),
            ('server', 'fa-server'),
            ('database', 'fa-database'),
            ('backup', 'fa-hdd'),
            ('khác', 'fa-box'),
            ('other', 'fa-box'),
        ]
        
        # Tìm icon phù hợp - kiểm tra từ khóa dài trước
        for key, icon in icon_map:
            if key in type_name_lower:
                return icon
        
        # Mặc định
        return 'fa-box'
    
    # Thống kê số lượng thiết bị theo từng loại
    asset_type_stats = []
    for asset_type in asset_types:
        if not asset_type or not asset_type.name:
            continue
        try:
            count = Asset.query.filter(
                Asset.asset_type_id == asset_type.id,
                Asset.deleted_at.is_(None)
            ).count()
            active_count = Asset.query.filter(
                Asset.asset_type_id == asset_type.id,
                Asset.status == 'active',
                Asset.deleted_at.is_(None)
            ).count()
            asset_type_stats.append({
                'type_id': asset_type.id,
                'type_name': asset_type.name or 'Không có tên',
                'total_count': count,
                'active_count': active_count,
                'icon': get_asset_type_icon(asset_type.name or '')
            })
        except Exception as ex:
            app.logger.warning(f"Error processing asset_type {asset_type.id}: {ex}")
            continue
    # Sắp xếp theo số lượng giảm dần
    asset_type_stats.sort(key=lambda x: x['total_count'], reverse=True)
    
    stats = {
        'total_assets': len(assets),
        'total_asset_types': len(asset_types),
        'total_users': len(users),
        'active_assets': len([a for a in assets if a.status == 'active']),
        'asset_type_stats': asset_type_stats
    }
    
    # Auto schedule yearly maintenance and show due soon list
    from datetime import timedelta
    today = today_vn()

    # Ensure each asset has a next scheduled maintenance (yearly)
    # Skip auto-creation to avoid errors - can be enabled later if needed
    # This feature can cause issues if database is locked or has constraints
    try:
        # Simplified: Skip maintenance auto-creation for now to ensure page loads
        pass
    except Exception as ex:
        app.logger.warning(f"Error in maintenance scheduling: {ex}")
        pass

    # Due soon/overdue notifications and list (30 days window)
    due_window = today + timedelta(days=30)
    due_records = []
    overdue = 0
    due_soon = 0
    try:
        # Query all records first, then filter in Python to avoid type mismatch
        all_due_records = MaintenanceRecord.query\
            .filter(
                MaintenanceRecord.deleted_at.is_(None),
                MaintenanceRecord.next_due_date.isnot(None))\
            .all()
        
        # Filter in Python to handle both date and datetime types
        filtered_records = []
        for r in all_due_records:
            if r.next_due_date:
                try:
                    # Convert to date for comparison
                    r_date = r.next_due_date.date() if isinstance(r.next_due_date, datetime) else r.next_due_date
                    if r_date and r_date <= due_window:
                        filtered_records.append(r)
                except Exception:
                    continue
        
        # Sort by date
        try:
            filtered_records.sort(key=lambda x: x.next_due_date.date() if isinstance(x.next_due_date, datetime) else x.next_due_date)
        except Exception:
            pass  # If sort fails, use unsorted list
        
        due_records = filtered_records[:10]
        
        # Calculate overdue and due soon counts
        for r in due_records:
            if r.next_due_date:
                try:
                    r_date = r.next_due_date.date() if isinstance(r.next_due_date, datetime) else r.next_due_date
                    if r_date:
                        if r_date < today:
                            overdue += 1
                        else:
                            due_soon += 1
                except Exception:
                    pass
    except Exception as ex:
        app.logger.warning(f"Error querying due records: {ex}")
        due_records = []  # Ensure it's always a list
        overdue = 0
        due_soon = 0
    try:
        if overdue:
            flash(f'{overdue} thiết bị quá hạn bảo trì!', 'warning')
        elif due_soon:
            flash(f'{due_soon} thiết bị sắp đến hạn bảo trì trong 30 ngày.', 'info')
    except Exception:
        pass  # Ignore flash errors

    try:
        return render_template('index.html', assets=assets, stats=stats, asset_types=asset_types, due_records=due_records, today=today)
    except Exception as e:
        app.logger.error(f"Error rendering index template: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        app.logger.error(error_trace)
        print(f"\n{'='*60}")
        print("TEMPLATE RENDERING ERROR:")
        print(f"{'='*60}")
        print(error_trace)
        print(f"{'='*60}\n")
        # In DEBUG mode, show detailed error
        if app.config.get('DEBUG', False):
            return f'<pre style="white-space: pre-wrap; font-family: monospace;">Lỗi render template:\n\n{error_trace}</pre>', 500
        # Return simple error page instead of raising
        return f'<h1>Lỗi 500</h1><p>Đã xảy ra lỗi khi tải trang. Vui lòng thử lại sau.</p><p>Chi tiết: {str(e)}</p>', 500

@app.route('/assets')
@login_required
def assets():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    type_id = request.args.get('type_id', type=int)
    status = request.args.get('status', type=str)
    user_id = request.args.get('user_id', type=int)

    query = Asset.query.filter(Asset.deleted_at.is_(None))
    # Nếu là user thường thì chỉ được xem tài sản của chính mình
    role = session.get('role')
    current_user_id = session.get('user_id')
    if role == 'user' and current_user_id:
        query = query.filter(Asset.user_id == current_user_id)
        # Bỏ filter theo user_id trên URL để tránh xem tài sản của người khác
        user_id = None
    if search:
        # Use case-insensitive search compatible with both SQLite and PostgreSQL
        search_lower = f'%{search.lower()}%'
        query = query.filter(db.func.lower(Asset.name).like(search_lower))
    if type_id:
        query = query.filter(Asset.asset_type_id == type_id)
    if status:
        # Map "other" thành "disposed" để hiển thị tài sản đã thanh lý
        if status == 'other':
            query = query.filter(Asset.status == 'disposed')
        else:
            query = query.filter(Asset.status == status)
    if user_id:
        query = query.filter(Asset.user_id == user_id)

    # Mới tạo/cập nhật sẽ hiển thị trước tiên (sắp xếp theo thời gian tạo giảm dần)
    query = query.order_by(Asset.created_at.desc())
    assets = query.paginate(page=page, per_page=10, error_out=False)
    asset_types = AssetType.query.filter(AssetType.deleted_at.is_(None)).all()
    return render_template('assets/list.html', assets=assets, asset_types=asset_types, search=search, type_id=type_id, status=status, user_id=user_id)


@app.route('/assets/value-detail')
@login_required
def assets_value_detail():
    """Hiển thị danh sách loại tài sản với tổng giá trị của mỗi loại"""
    asset_types = AssetType.query.filter(AssetType.deleted_at.is_(None)).all()
    
    # Tính tổng giá trị cho mỗi loại tài sản
    type_stats = []
    for asset_type in asset_types:
        assets = Asset.query.filter(
            Asset.asset_type_id == asset_type.id,
            Asset.deleted_at.is_(None),
            Asset.status != 'disposed'  # Loại bỏ tài sản đã thanh lý
        ).all()
        
        total_value = 0
        total_count = 0
        for asset in assets:
            if asset.price:
                total_value += asset.price * (asset.quantity or 1)
            total_count += asset.quantity or 1
        
        type_stats.append({
            'type': asset_type,
            'total_value': total_value,
            'total_count': total_count
        })
    
    # Sắp xếp theo tổng giá trị giảm dần
    type_stats.sort(key=lambda x: x['total_value'], reverse=True)
    
    return render_template('assets/value_detail.html', type_stats=type_stats)


@app.route('/assets/suggest')
@login_required
def assets_suggest():
    """
    Trả về danh sách gợi ý tài sản theo tên (tìm kiếm tương đối, không phân biệt hoa thường).
    Dùng cho autocomplete ở ô tìm kiếm danh sách tài sản.
    """
    term = request.args.get('term', '', type=str) or ''
    term = term.strip()
    if len(term) < 2:
        return jsonify([])

    search_lower = f"%{term.lower()}%"
    query = Asset.query.filter(
        Asset.deleted_at.is_(None),
        db.func.lower(Asset.name).like(search_lower)
    ).order_by(Asset.created_at.desc()).limit(10)

    results = []
    for a in query:
        label = a.name
        if a.device_code:
            label = f"{a.name} ({a.device_code})"
        results.append({
            "id": a.id,
            "label": label,
            "name": a.name,
            "device_code": a.device_code or ""
        })
    return jsonify(results)

@app.route('/assets/export/<string:fmt>')
@manager_required
def export_assets(fmt: str):
    fmt = (fmt or '').lower()
    # Common, normalized dataset
    assets = Asset.query.filter(Asset.deleted_at.is_(None)).order_by(Asset.id.asc()).all()
    rows = []
    for a in assets:
        rows.append({
            'id': a.id,
            'name': a.name,
            'asset_type': a.asset_type.name if a.asset_type else '',
            'price': float(a.price or 0),
            'quantity': int(a.quantity or 0),
            'purchase_date': a.purchase_date.strftime('%d/%m/%Y') if a.purchase_date else '',
            'device_code': a.device_code or '',
            'user': a.user.username if a.user else '',
            'condition': a.condition_label or '',
            'status': a.status or '',
            'notes': a.notes or ''
        })
    headers_vi = {
        'id': 'ID',
        'name': 'Tên tài sản',
        'asset_type': 'Loại',
        'price': 'Giá',
        'quantity': 'Số lượng',
        'purchase_date': 'Ngày mua',
        'device_code': 'Mã thiết bị',
        'user': 'Người sử dụng',
        'condition': 'Tình trạng',
        'status': 'Trạng thái',
        'notes': 'Ghi chú'
    }
    ordered_fields = list(headers_vi.keys())

    # Ghi nhật ký hoạt động cho thao tác xuất dữ liệu tài sản
    try:
        uid = session.get('user_id')
        if uid:
            db.session.add(AuditLog(
                user_id=uid,
                module='assets',
                action=f'export_{fmt}',
                entity_id=None,
                details=f'format={fmt}, total_rows={len(rows)}'
            ))
            db.session.commit()
    except Exception:
        db.session.rollback()

    def _save_and_response(data_bytes: bytes, filename: str, content_type: str):
        # Persist a copy to EXPORT_DIR
        try:
            export_dir = app.config.get('EXPORT_DIR', 'instance/exports')
            # Normalize to absolute path relative to app.root_path if needed
            if not os.path.isabs(export_dir):
                export_dir = os.path.join(app.root_path, export_dir)
            os.makedirs(export_dir, exist_ok=True)
            ts = now_vn().strftime('%Y%m%d_%H%M%S')
            base, ext = os.path.splitext(filename)
            server_filename = f"{base}_{ts}{ext}"
            out_path = os.path.join(export_dir, server_filename)
            with open(out_path, 'wb') as f:
                f.write(data_bytes)
        except Exception:
            # Non-fatal: logging to console; still return download
            print('[Export] Failed to persist exported file to disk.')
        response = make_response(data_bytes)
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        response.headers['Content-Type'] = content_type
        return response

    if fmt == 'csv':
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([headers_vi[f] for f in ordered_fields])
        for r in rows:
            writer.writerow([r[f] for f in ordered_fields])
        csv_data = output.getvalue().encode('utf-8-sig')
        return _save_and_response(csv_data, 'tai_san.csv', 'text/csv; charset=utf-8')
    elif fmt in ('xlsx', 'excel'):
        # Use pandas/openpyxl
        import pandas as pd  # type: ignore
        from io import BytesIO
        df = pd.DataFrame(rows, columns=ordered_fields)
        df.columns = [headers_vi[f] for f in ordered_fields]
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='TaiSan')
        buf.seek(0)
        data = buf.read()
        return _save_and_response(data, 'tai_san.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    elif fmt == 'json':
        import json
        data = json.dumps(rows, ensure_ascii=False).encode('utf-8')
        return _save_and_response(data, 'tai_san.json', 'application/json; charset=utf-8')
    elif fmt == 'docx':
        # Use utils.exporters for Word
        from types import SimpleNamespace
        from utils.exporters import export_docx
        ns_rows = [SimpleNamespace(**r) for r in rows]
        buf = export_docx(ns_rows, ordered_fields, title='Danh sách tài sản', header_map=headers_vi)
        return _save_and_response(buf.getvalue(), 'tai_san.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    elif fmt == 'pdf':
        # Use utils.exporters for PDF
        from types import SimpleNamespace
        from utils.exporters import export_pdf
        ns_rows = [SimpleNamespace(**r) for r in rows]
        buf = export_pdf(ns_rows, ordered_fields, title='Danh sách tài sản', header_map=headers_vi)
        return _save_and_response(buf.getvalue(), 'tai_san.pdf', 'application/pdf')
    else:
        flash('Định dạng không được hỗ trợ. Hỗ trợ: csv, xlsx, json, docx, pdf.', 'warning')
        return redirect(url_for('assets'))

@app.route('/assets/invoice/<path:filename>')
@login_required
def download_invoice(filename):
    """Download/hiển thị file hóa đơn/phiếu giao hàng"""
    try:
        # Security: chỉ cho phép xử lý file trong thư mục uploads
        if '..' in filename or filename.startswith('/'):
            flash('Đường dẫn file không hợp lệ.', 'error')
            return redirect(url_for('assets'))
        
        # Remove 'uploads/' prefix if present
        clean_filename = filename.replace('uploads/', '') if filename.startswith('uploads/') else filename
        file_path = os.path.join(upload_folder, clean_filename)
        
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            flash('File không tồn tại.', 'error')
            return redirect(url_for('assets'))
        
        # Check if file is in upload folder (security)
        if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
            flash('Đường dẫn file không hợp lệ.', 'error')
            return redirect(url_for('assets'))
        
        inline_requested = request.args.get('inline') == '1'
        inline_allowed = inline_requested and is_image_file(clean_filename)
        guessed_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        response = send_from_directory(
            upload_folder,
            clean_filename,
            as_attachment=not inline_allowed,
            mimetype=guessed_type if inline_allowed else None
        )
        if inline_allowed:
            response.headers['Content-Disposition'] = f'inline; filename="{clean_filename}"'
        return response
    except Exception as e:
        flash(f'Lỗi khi tải file: {str(e)}', 'error')
        return redirect(url_for('assets'))

# Maintenance module
@app.route('/maintenance')
@login_required
def maintenance_list():
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '', type=str)
        asset_id = request.args.get('asset_id', type=int)
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        overdue_flag = request.args.get('overdue', type=int)
        due30_flag = request.args.get('due_30', type=int)

        query = MaintenanceRecord.query.filter(MaintenanceRecord.deleted_at.is_(None))
        if asset_id:
            query = query.filter(MaintenanceRecord.asset_id == asset_id)
        if search:
            # Use case-insensitive search compatible with both SQLite and PostgreSQL
            search_lower = f'%{search.lower()}%'
            query = query.filter(
                (db.func.lower(MaintenanceRecord.description).like(search_lower)) |
                (db.func.lower(MaintenanceRecord.vendor).like(search_lower)) |
                (db.func.lower(MaintenanceRecord.person_in_charge).like(search_lower))
            )
        if month:
            query = query.filter(db.extract('month', MaintenanceRecord.maintenance_date) == month)
        if year:
            query = query.filter(db.extract('year', MaintenanceRecord.maintenance_date) == year)
        # Additional filters for next due date
        if overdue_flag:
            today = today_vn()
            query = query.filter(MaintenanceRecord.next_due_date != None, MaintenanceRecord.next_due_date < today)
        if due30_flag:
            from datetime import timedelta
            today = today_vn()
            query = query.filter(
                MaintenanceRecord.next_due_date != None,
                MaintenanceRecord.next_due_date.between(today, today + timedelta(days=30))
            )
        
        # Filter for records with cost (chi phí > 0)
        has_cost = request.args.get('has_cost')
        if has_cost:
            query = query.filter(MaintenanceRecord.cost > 0)
        
        # Giới hạn quyền xem cho tài khoản user: chỉ thấy bảo trì của tài sản thuộc về mình
        role = session.get('role')
        current_user_id = session.get('user_id')
        if role == 'user' and current_user_id:
            query = query.join(Asset, MaintenanceRecord.asset_id == Asset.id, isouter=False) \
                         .filter(Asset.user_id == current_user_id)

        # Get filter values from request
        asset_type_id = request.args.get('asset_type_id', type=int)
        vendor = request.args.get('vendor', type=str)
        status = request.args.get('status', type=str)
        date_from = request.args.get('date_from', type=str)
        
        # Apply additional filters
        if asset_type_id:
            query = query.join(Asset, MaintenanceRecord.asset_id == Asset.id, isouter=False).filter(Asset.asset_type_id == asset_type_id)
        if vendor:
            query = query.filter(MaintenanceRecord.vendor.contains(vendor))
        if status:
            query = query.filter(MaintenanceRecord.status == status)
        if date_from:
            try:
                from datetime import datetime
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(MaintenanceRecord.maintenance_date >= date_from_obj)
            except (ValueError, TypeError):
                pass  # Ignore invalid date format

        try:
            records = query.order_by(MaintenanceRecord.maintenance_date.desc()).paginate(page=page, per_page=10, error_out=False)
        except Exception as e:
            app.logger.error(f"Error querying maintenance records: {str(e)}")
            import traceback
            app.logger.error(traceback.format_exc())
            db.session.rollback()  # Rollback transaction khi có lỗi
            records = MaintenanceRecord.query.filter(MaintenanceRecord.deleted_at.is_(None)).order_by(MaintenanceRecord.maintenance_date.desc()).paginate(page=1, per_page=10, error_out=False)
        
        try:
            assets_query = Asset.query.filter(Asset.deleted_at.is_(None))
            if role == 'user' and current_user_id:
                assets_query = assets_query.filter(Asset.user_id == current_user_id)
            assets = assets_query.all()
        except Exception as e:
            app.logger.error(f"Error querying assets: {str(e)}")
            db.session.rollback()  # Rollback transaction khi có lỗi
            assets = []
        
        # Get asset types for filter
        try:
            asset_types = AssetType.query.filter(AssetType.deleted_at.is_(None)).all()
        except Exception as e:
            app.logger.error(f"Error querying asset types: {str(e)}")
            db.session.rollback()  # Rollback transaction khi có lỗi
            asset_types = []
        
        # Get unique vendors for filter
        try:
            vendors_query = db.session.query(MaintenanceRecord.vendor).filter(
                MaintenanceRecord.deleted_at.is_(None),
                MaintenanceRecord.vendor.isnot(None),
                MaintenanceRecord.vendor != ''
            ).distinct().all()
            vendors = [v[0] for v in vendors_query if v[0]]
        except Exception as e:
            app.logger.error(f"Error querying vendors: {str(e)}")
            db.session.rollback()  # Rollback transaction khi có lỗi
            vendors = []
        
        return render_template(
            'maintenance/list.html',
            records=records,
            assets=assets,
            asset_types=asset_types,
            vendors=vendors,
            search=search,
            asset_id=asset_id,
            asset_type_id=asset_type_id,
            vendor=vendor,
            status=status,
            date_from=date_from,
            month=month,
            year=year,
            overdue=overdue_flag,
            due_30=due30_flag
        )
    except Exception as e:
        app.logger.error(f"Error in maintenance_list: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        db.session.rollback()  # Rollback transaction khi có lỗi
        flash(f'Lỗi khi tải trang bảo trì: {str(e)}', 'error')
        # Return a minimal working page
        try:
            records = MaintenanceRecord.query.filter(MaintenanceRecord.deleted_at.is_(None)).order_by(MaintenanceRecord.maintenance_date.desc()).paginate(page=1, per_page=10, error_out=False)
            return render_template(
                'maintenance/list.html',
                records=records,
                assets=[],
                asset_types=[],
                vendors=[],
                search='',
                asset_id=None,
                asset_type_id=None,
                vendor=None,
                status=None,
                date_from=None,
                month=None,
                year=None,
                overdue=None,
                due_30=None
            )
        except Exception as e2:
            app.logger.error(f"Error in maintenance_list fallback: {str(e2)}")
            db.session.rollback()  # Rollback transaction khi có lỗi
            return f"Lỗi máy chủ (500). Vui lòng thử lại, hoặc truy cập /dev/diag để chẩn đoán nhanh. Chi tiết: {str(e)}", 500


@app.route('/maintenance/suggest')
@login_required
def maintenance_suggest():
    """
    Gợi ý nhanh các bản ghi bảo trì theo mô tả / đơn vị bảo trì / người phụ trách.
    Dùng cho autocomplete ở ô tìm kiếm danh sách bảo trì.
    """
    term = request.args.get('term', '', type=str) or ''
    term = term.strip()
    if len(term) < 2:
        return jsonify([])

    search_lower = f"%{term.lower()}%"
    query = MaintenanceRecord.query.filter(
        MaintenanceRecord.deleted_at.is_(None),
        (
            db.func.lower(MaintenanceRecord.description).like(search_lower) |
            db.func.lower(MaintenanceRecord.vendor).like(search_lower) |
            db.func.lower(MaintenanceRecord.person_in_charge).like(search_lower)
        )
    ).order_by(MaintenanceRecord.maintenance_date.desc()).limit(10)

    results = []
    for rec in query:
        asset_name = rec.asset.name if rec.asset else "Không rõ tài sản"
        vendor = rec.vendor or ""
        desc = rec.description or ""
        pieces = [asset_name]
        if vendor:
            pieces.append(vendor)
        if desc:
            pieces.append(desc[:60])
        label = " - ".join(pieces)
        results.append({
            "id": rec.id,
            "label": label
        })
    return jsonify(results)
@app.route('/maintenance/add', methods=['GET','POST'])
@login_required
def maintenance_add():
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    if request.method == 'POST':
        try:
            asset_id = int(request.form['asset_id'])
            asset = Asset.query.get_or_404(asset_id)

            if current_role == 'user' and asset.user_id != current_user_id:
                flash('Bạn chỉ có thể tạo yêu cầu bảo trì cho tài sản của mình.', 'error')
                return redirect(url_for('maintenance_add'))

            request_date = request.form.get('request_date') or today_vn().isoformat()
            requested_by_id = request.form.get('requested_by_id', type=int) or None
            maintenance_reason = request.form.get('maintenance_reason') or None
            condition_before = request.form.get('condition_before') or None
            damage_level = request.form.get('damage_level') or None
            mtype = request.form.get('type', 'maintenance')
            description = request.form.get('description', '')
            
            vendor = request.form.get('vendor', '')
            person = request.form.get('person_in_charge', '')
            vendor_phone = request.form.get('vendor_phone', '')
            estimated_cost = float(request.form.get('estimated_cost', 0) or 0)
            
            maintenance_date = request.form.get('maintenance_date') or request_date
            completed_date = request.form.get('completed_date') or None
            cost = float(request.form.get('cost', 0) or 0)
            replaced_parts = request.form.get('replaced_parts', '')
            result_status = request.form.get('result_status') or None
            result_notes = request.form.get('result_notes', '')
            
            status_val = request.form.get('status', 'pending')
            next_due_date = request.form.get('next_due_date') or None

            rec = MaintenanceRecord(
                asset_id=asset_id,
                request_date=parse_iso_date(request_date),
                requested_by_id=requested_by_id,
                maintenance_reason=maintenance_reason,
                condition_before=condition_before,
                damage_level=damage_level,
                type=mtype,
                description=description,
                vendor=vendor,
                person_in_charge=person,
                vendor_phone=vendor_phone,
                estimated_cost=estimated_cost,
                maintenance_date=parse_iso_date(maintenance_date),
                completed_date=parse_iso_date(completed_date),
                cost=cost,
                replaced_parts=replaced_parts,
                result_status=result_status,
                result_notes=result_notes,
                next_due_date=parse_iso_date(next_due_date),
                status=status_val
            )
            
            db.session.add(rec)
            db.session.flush()  # Get ID before committing
            
            # Handle file uploads
            if 'invoice_file' in request.files:
                file = request.files['invoice_file']
                if file and file.filename:
                    filename = save_uploaded_file(file, f'maintenance_{rec.id}')
                    if filename:
                        rec.invoice_file = filename
            
            if 'acceptance_file' in request.files:
                file = request.files['acceptance_file']
                if file and file.filename:
                    filename = save_uploaded_file(file, f'maintenance_{rec.id}')
                    if filename:
                        rec.acceptance_file = filename
            
            if 'before_image' in request.files:
                file = request.files['before_image']
                if file and file.filename:
                    filename = save_uploaded_file(file, f'maintenance_{rec.id}')
                    if filename:
                        rec.before_image = filename
            
            if 'after_image' in request.files:
                file = request.files['after_image']
                if file and file.filename:
                    filename = save_uploaded_file(file, f'maintenance_{rec.id}')
                    if filename:
                        rec.after_image = filename
            
            db.session.commit()
            flash('Đã tạo yêu cầu bảo trì thành công.', 'success')
            return redirect(url_for('maintenance_list'))
        except Exception as e:
            app.logger.error(f"Error creating maintenance record: {str(e)}")
            import traceback
            app.logger.error(traceback.format_exc())
            db.session.rollback()
            flash(f'Lỗi khi tạo yêu cầu bảo trì: {str(e)}', 'error')
    
    if current_role == 'user':
        assets = Asset.query.filter(
            Asset.deleted_at.is_(None),
            Asset.user_id == current_user_id
        ).all()
    else:
        assets = Asset.query.filter(Asset.deleted_at.is_(None)).all()
    users = User.query.filter(User.deleted_at.is_(None), User.is_active == True).all()
    today = today_vn()
    return render_template('maintenance/add.html', assets=assets, users=users, today=today)

@app.route('/maintenance/edit/<int:id>', methods=['GET','POST'])
@login_required
def maintenance_edit(id):
    rec = MaintenanceRecord.query.get_or_404(id)
    if request.method == 'POST':
        rec.asset_id = int(request.form['asset_id'])
        maintenance_date = request.form.get('maintenance_date') or today_vn().isoformat()
        rec.maintenance_date = datetime.fromisoformat(maintenance_date).date()
        rec.type = request.form.get('type','maintenance')
        rec.description = request.form.get('description','')
        rec.vendor = request.form.get('vendor','')
        rec.person_in_charge = request.form.get('person_in_charge','')
        rec.cost = float(request.form.get('cost', 0) or 0)
        next_due_date = request.form.get('next_due_date') or None
        rec.next_due_date = datetime.fromisoformat(next_due_date).date() if next_due_date else None
        rec.status = request.form.get('status','completed')
        db.session.commit()
        flash('Đã cập nhật bản ghi bảo trì.', 'success')
        return redirect(url_for('maintenance_list'))
    assets = Asset.query.filter(Asset.deleted_at.is_(None)).all()
    return render_template('maintenance/edit.html', rec=rec, assets=assets)

@app.route('/maintenance/view/<int:id>')
@login_required
def maintenance_view(id):
    rec = MaintenanceRecord.query.get_or_404(id)
    return render_template('maintenance/view.html', rec=rec)

@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    """Serve uploaded files for maintenance and other modules"""
    try:
        # Security: chỉ cho phép xử lý file trong thư mục uploads
        if '..' in filename or filename.startswith('/'):
            return "File not found", 404
        
        # Remove 'uploads/' prefix if present
        clean_filename = filename.replace('uploads/', '') if filename.startswith('uploads/') else filename
        file_path = os.path.join(upload_folder, clean_filename)
        
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return "File not found", 404
        
        # Check if file is in upload folder (security)
        if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
            return "File not found", 404
        
        inline_requested = request.args.get('inline') == '1'
        inline_allowed = inline_requested and is_image_file(clean_filename)
        
        return send_from_directory(
            upload_folder,
            clean_filename,
            as_attachment=not inline_allowed
        )
    except Exception as e:
        app.logger.error(f"Error serving file {filename}: {str(e)}")
        return "File not found", 404

@app.route('/maintenance/delete/<int:id>', methods=['POST'])
@login_required
def maintenance_delete(id):
    rec = MaintenanceRecord.query.get_or_404(id)
    if rec.deleted_at:
        flash('Bản ghi đã nằm trong thùng rác.', 'info')
        return redirect(url_for('maintenance_list'))
    rec.soft_delete()
    db.session.commit()
    flash('Đã chuyển bản ghi bảo trì vào thùng rác.', 'success')
    return redirect(url_for('maintenance_list'))

@app.route('/maintenance/export')
@manager_required
def maintenance_export():
    """Export maintenance records to Excel"""
    try:
        from utils.exporters import export_maintenance_to_excel
        from flask import Response
        
        # Get filter parameters
        search = request.args.get('search', '', type=str)
        asset_id = request.args.get('asset_id', type=int)
        asset_type_id = request.args.get('asset_type_id', type=int)
        vendor = request.args.get('vendor', type=str)
        status = request.args.get('status', type=str)
        date_from = request.args.get('date_from', type=str)
        date_to = request.args.get('date_to', type=str)
        
        # Build query
        query = MaintenanceRecord.query.filter(MaintenanceRecord.deleted_at.is_(None))
        
        if asset_id:
            query = query.filter(MaintenanceRecord.asset_id == asset_id)
        if asset_type_id:
            query = query.join(Asset).filter(Asset.asset_type_id == asset_type_id)
        if vendor:
            query = query.filter(MaintenanceRecord.vendor.contains(vendor))
        if status:
            query = query.filter(MaintenanceRecord.status == status)
        if search:
            search_lower = f'%{search.lower()}%'
            query = query.filter(
                (db.func.lower(MaintenanceRecord.description).like(search_lower)) |
                (db.func.lower(MaintenanceRecord.vendor).like(search_lower)) |
                (db.func.lower(MaintenanceRecord.person_in_charge).like(search_lower))
            )
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(MaintenanceRecord.request_date >= date_from_obj)
            except ValueError:
                pass
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(MaintenanceRecord.request_date <= date_to_obj)
            except ValueError:
                pass
        
        records = query.order_by(MaintenanceRecord.request_date.desc()).all()
        
        # Ghi nhật ký hoạt động cho thao tác xuất Excel bảo trì
        try:
            uid = session.get('user_id')
            if uid:
                db.session.add(AuditLog(
                    user_id=uid,
                    module='maintenance',
                    action='export_excel',
                    entity_id=None,
                    details=f'total_records={len(records)}'
                ))
                db.session.commit()
        except Exception:
            db.session.rollback()
        
        # Export to Excel
        from utils.exporters import export_maintenance_to_excel
        output = export_maintenance_to_excel(records)
        
        timestamp = now_vn().strftime('%Y%m%d_%H%M%S')
        filename = f'bao_tri_{timestamp}.xlsx'
        
        response = make_response(output)
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return response
    except Exception as e:
        app.logger.error(f"Error exporting maintenance: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        flash(f'Lỗi khi xuất Excel: {str(e)}', 'error')
        return redirect(url_for('maintenance_list'))

@app.route('/reports/dashboard')
@login_required
@manager_required
def reports_dashboard():
    """Reports dashboard - show all available reports"""
    return render_template('reports/index.html')


@app.route('/reports/inventory-doc')
@login_required
def inventory_business_doc():
    """
    Tài liệu nghiệp vụ kiểm kê tài sản (hiển thị trên giao diện QLTS chính).
    """
    return render_template('reports/inventory_business_doc.html')

@app.route('/reports/catalog')
@login_required
def reports_catalog():
    """Reports catalog page with filters"""
    # Get filter parameters
    year = request.args.get('year', type=int) or today_vn().year
    asset_type_id = request.args.get('asset_type_id', type=int)
    unit_id = request.args.get('unit_id', type=int)  # user_id
    
    # Get dropdown data
    asset_types = AssetType.query.filter(AssetType.deleted_at.is_(None)).all()
    users = User.query.filter(User.deleted_at.is_(None), User.is_active == True).all()
    
    return render_template('reports/catalog.html',
                         year=year,
                         asset_type_id=asset_type_id,
                         unit_id=unit_id,
                         asset_types=asset_types,
                         units=users)

# ========== BÁO CÁO THEO THÔNG TƯ ==========

@app.route('/reports/tt144-tt23')
@login_required
@manager_required
def report_tt144_tt23():
    """Báo cáo công khai, kê khai TSNN theo TT 144/2017 và TT 23/2023"""
    current_year = today_vn().year
    year = request.args.get('year', type=int) or current_year
    quarter = request.args.get('quarter', type=str)
    asset_type_id = request.args.get('asset_type_id', type=int)
    
    # Query assets
    query = Asset.query.filter(Asset.deleted_at.is_(None))
    
    if asset_type_id:
        query = query.filter(Asset.asset_type_id == asset_type_id)
    
    if quarter:
        # Filter by quarter if needed
        quarter_num = int(quarter)
        start_month = (quarter_num - 1) * 3 + 1
        end_month = quarter_num * 3
        from sqlalchemy import extract
        query = query.filter(
            extract('month', Asset.created_at).between(start_month, end_month)
        )
    
    assets = query.order_by(Asset.created_at.desc()).all()
    asset_types = AssetType.query.filter(AssetType.deleted_at.is_(None)).all()
    
    return render_template('reports/tt144_tt23.html',
                         assets=assets,
                         asset_types=asset_types,
                         current_year=current_year,
                         year=year,
                         quarter=quarter)

@app.route('/reports/tt144-tt23/export')
@login_required
@manager_required
def report_tt144_tt23_export():
    """Export báo cáo TT 144/2017, TT 23/2023 ra Excel"""
    from utils.exporters import export_excel
    from io import BytesIO
    
    year = request.args.get('year', type=int) or today_vn().year
    quarter = request.args.get('quarter', type=str)
    asset_type_id = request.args.get('asset_type_id', type=int)
    
    query = Asset.query.filter(Asset.deleted_at.is_(None))
    
    if asset_type_id:
        query = query.filter(Asset.asset_type_id == asset_type_id)
    
    if quarter:
        quarter_num = int(quarter)
        start_month = (quarter_num - 1) * 3 + 1
        end_month = quarter_num * 3
        from sqlalchemy import extract
        query = query.filter(
            extract('month', Asset.created_at).between(start_month, end_month)
        )
    
    assets = query.order_by(Asset.created_at.desc()).all()
    
    # Prepare data for export
    fields = ['device_code', 'name', 'asset_type', 'price', 'purchase_date', 'user', 'condition_label', 'status']
    header_map = {
        'device_code': 'Mã tài sản',
        'name': 'Tên tài sản',
        'asset_type': 'Loại tài sản',
        'price': 'Giá trị (VNĐ)',
        'purchase_date': 'Ngày mua',
        'user': 'Người quản lý',
        'condition_label': 'Tình trạng',
        'status': 'Trạng thái'
    }
    
    # Convert assets to exportable format
    export_data = []
    for idx, asset in enumerate(assets, 1):
        export_data.append({
            'device_code': asset.device_code or f"TS{asset.id:05d}",
            'name': asset.name or '',
            'asset_type': asset.asset_type.name if asset.asset_type else '',
            'price': asset.price or 0,
            'purchase_date': asset.purchase_date.strftime('%d/%m/%Y') if asset.purchase_date else '',
            'user': asset.user.username if asset.user else asset.user_text or '',
            'condition_label': asset.condition_label or '',
            'status': status_vi(asset.status) if asset.status else ''
        })
    
    # Create DataFrame and export
    import pandas as pd
    df = pd.DataFrame(export_data)
    df.columns = [header_map.get(col, col) for col in df.columns]
    
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=f'Báo cáo TSNN {year}', index=False)
    buf.seek(0)
    
    filename = f'Bao_cao_TSNN_TT144_TT23_{year}.xlsx'
    return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=filename)

@app.route('/reports/tt24')
@login_required
@manager_required
def report_tt24():
    """Báo cáo tài sản, công cụ dụng cụ theo TT 24/2024"""
    current_year = today_vn().year
    year = request.args.get('year', type=int) or current_year
    report_type = request.args.get('report_type', 'all')
    status = request.args.get('status', '')
    
    query = Asset.query.filter(Asset.deleted_at.is_(None))
    
    if status:
        query = query.filter(Asset.status == status)
    
    assets = query.order_by(Asset.created_at.desc()).all()
    
    return render_template('reports/tt24.html',
                         assets=assets,
                         current_year=current_year,
                         year=year,
                         report_type=report_type,
                         status=status)

@app.route('/reports/tt24/export')
@login_required
@manager_required
def report_tt24_export():
    """Export báo cáo TT 24/2024 ra Excel"""
    from io import BytesIO
    import pandas as pd
    
    year = request.args.get('year', type=int) or today_vn().year
    report_type = request.args.get('report_type', 'all')
    status = request.args.get('status', '')
    
    query = Asset.query.filter(Asset.deleted_at.is_(None))
    
    if status:
        query = query.filter(Asset.status == status)
    
    assets = query.order_by(Asset.created_at.desc()).all()
    
    export_data = []
    for idx, asset in enumerate(assets, 1):
        export_data.append({
            'STT': idx,
            'Mã tài sản': asset.device_code or f"TS{asset.id:05d}",
            'Tên tài sản/Công cụ': asset.name or '',
            'Loại': asset.asset_type.name if asset.asset_type else '',
            'Nguyên giá (VNĐ)': asset.price or 0,
            'Khấu hao (VNĐ)': 0,  # TODO: Tính khấu hao
            'Giá trị còn lại (VNĐ)': asset.price or 0,  # TODO: Tính giá trị còn lại
            'Ngày mua': asset.purchase_date.strftime('%d/%m/%Y') if asset.purchase_date else '',
            'Người sử dụng': asset.user.username if asset.user else asset.user_text or '',
            'Tình trạng': asset.condition_label or ''
        })
    
    df = pd.DataFrame(export_data)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=f'Báo cáo TT24_{year}', index=False)
    buf.seek(0)
    
    filename = f'Bao_cao_Tai_san_CCDC_TT24_{year}.xlsx'
    return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=filename)

@app.route('/reports/tt35')
@login_required
@manager_required
def report_tt35():
    """Báo cáo tài sản hạ tầng đường bộ theo TT 35/2022"""
    current_year = today_vn().year
    year = request.args.get('year', type=int) or current_year
    infrastructure_type = request.args.get('infrastructure_type', '')
    location = request.args.get('location', '')
    
    query = Asset.query.filter(Asset.deleted_at.is_(None))
    
    if location:
        query = query.filter(Asset.user_text.contains(location))
    
    assets = query.order_by(Asset.created_at.desc()).all()
    
    return render_template('reports/tt35.html',
                         assets=assets,
                         current_year=current_year,
                         year=year,
                         infrastructure_type=infrastructure_type,
                         location=location)

@app.route('/reports/tt35/export')
@login_required
@manager_required
def report_tt35_export():
    """Export báo cáo TT 35/2022 ra Excel"""
    from io import BytesIO
    import pandas as pd
    
    year = request.args.get('year', type=int) or today_vn().year
    infrastructure_type = request.args.get('infrastructure_type', '')
    location = request.args.get('location', '')
    
    query = Asset.query.filter(Asset.deleted_at.is_(None))
    
    if location:
        query = query.filter(Asset.user_text.contains(location))
    
    assets = query.order_by(Asset.created_at.desc()).all()
    
    export_data = []
    for idx, asset in enumerate(assets, 1):
        export_data.append({
            'STT': idx,
            'Mã tài sản': asset.device_code or f"TS{asset.id:05d}",
            'Tên tài sản': asset.name or '',
            'Loại hạ tầng': asset.asset_type.name if asset.asset_type else '',
            'Vị trí': asset.user_text or '',
            'Giá trị (VNĐ)': asset.price or 0,
            'Ngày đưa vào sử dụng': asset.purchase_date.strftime('%d/%m/%Y') if asset.purchase_date else '',
            'Tình trạng': asset.condition_label or '',
            'Ghi chú': (asset.notes or '')[:200] if asset.notes else ''
        })
    
    df = pd.DataFrame(export_data)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=f'Báo cáo hạ tầng {year}', index=False)
    buf.seek(0)
    
    filename = f'Bao_cao_Ha_tang_Duong_bo_TT35_{year}.xlsx'
    return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=filename)

@app.route('/reports/special')
@login_required
@manager_required
def report_special():
    """Báo cáo thiết bị y tế, tài sản vô hình, đặc thù"""
    current_year = today_vn().year
    year = request.args.get('year', type=int) or current_year
    report_type = request.args.get('report_type', 'all')
    status = request.args.get('status', '')
    
    query = Asset.query.filter(Asset.deleted_at.is_(None))
    
    if status:
        query = query.filter(Asset.status == status)
    
    # Filter by report type (có thể filter theo asset_type hoặc keyword trong name)
    from sqlalchemy import or_
    if report_type == 'medical':
        query = query.filter(
            or_(
                Asset.name.contains('y tế'),
                Asset.name.contains('thiết bị y tế'),
                Asset.name.contains('medical'),
                Asset.asset_type.has(AssetType.name.contains('y tế'))
            )
        )
    elif report_type == 'intangible':
        query = query.filter(
            or_(
                Asset.name.contains('vô hình'),
                Asset.name.contains('bản quyền'),
                Asset.name.contains('thương hiệu'),
                Asset.asset_type.has(AssetType.name.contains('vô hình'))
            )
        )
    
    assets = query.order_by(Asset.created_at.desc()).all()
    
    return render_template('reports/special.html',
                         assets=assets,
                         current_year=current_year,
                         year=year,
                         report_type=report_type,
                         status=status)

@app.route('/reports/special/export')
@login_required
@manager_required
def report_special_export():
    """Export báo cáo đặc thù ra Excel"""
    from io import BytesIO
    import pandas as pd
    
    year = request.args.get('year', type=int) or today_vn().year
    report_type = request.args.get('report_type', 'all')
    status = request.args.get('status', '')
    
    query = Asset.query.filter(Asset.deleted_at.is_(None))
    
    if status:
        query = query.filter(Asset.status == status)
    
    from sqlalchemy import or_
    if report_type == 'medical':
        query = query.filter(
            or_(
                Asset.name.contains('y tế'),
                Asset.name.contains('thiết bị y tế'),
                Asset.name.contains('medical'),
                Asset.asset_type.has(AssetType.name.contains('y tế'))
            )
        )
    elif report_type == 'intangible':
        query = query.filter(
            or_(
                Asset.name.contains('vô hình'),
                Asset.name.contains('bản quyền'),
                Asset.name.contains('thương hiệu'),
                Asset.asset_type.has(AssetType.name.contains('vô hình'))
            )
        )
    
    assets = query.order_by(Asset.created_at.desc()).all()
    
    export_data = []
    for idx, asset in enumerate(assets, 1):
        export_data.append({
            'STT': idx,
            'Mã tài sản': asset.device_code or f"TS{asset.id:05d}",
            'Tên tài sản': asset.name or '',
            'Loại': asset.asset_type.name if asset.asset_type else '',
            'Giá trị (VNĐ)': asset.price or 0,
            'Ngày mua': asset.purchase_date.strftime('%d/%m/%Y') if asset.purchase_date else '',
            'Người sử dụng': asset.user.username if asset.user else asset.user_text or '',
            'Tình trạng': asset.condition_label or '',
            'Ghi chú': (asset.notes or '')[:200] if asset.notes else ''
        })
    
    df = pd.DataFrame(export_data)
    buf = BytesIO()
    sheet_name = {
        'medical': 'Thiết bị y tế',
        'intangible': 'Tài sản vô hình',
        'other': 'Tài sản đặc thù',
        'all': 'Tất cả'
    }.get(report_type, 'Báo cáo')
    
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    buf.seek(0)
    
    filename = f'Bao_cao_Dac_thu_{report_type}_{year}.xlsx'
    return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=filename)

@app.route('/maintenance/report')
@login_required  # Tất cả user đều có thể xem báo cáo bảo trì
def maintenance_report():
    # Simple aggregation by month/year
    year = request.args.get('year', type=int)
    if not year:
        year = today_vn().year
    rows = db.session.query(
        db.extract('month', MaintenanceRecord.maintenance_date).label('month'),
        db.func.sum(MaintenanceRecord.cost).label('total')
    ).filter(
        MaintenanceRecord.deleted_at.is_(None),
        db.extract('year', MaintenanceRecord.maintenance_date) == year
    )
    rows = rows.group_by('month').order_by('month').all()
    data = [{'month': int(r.month), 'total': float(r.total or 0)} for r in rows]
    total_year = sum(d['total'] for d in data)
    return render_template('maintenance/report.html', year=year, data=data, total_year=total_year)

@app.route('/maintenance/dashboard')
@login_required
def maintenance_dashboard():
    from datetime import timedelta, date
    today = today_vn()
    year = today.year
    month = today.month
    active_record_filter = MaintenanceRecord.deleted_at.is_(None)
    # KPIs (avoid db.extract for SQLite compatibility)
    start_year = date(year, 1, 1)
    end_year = date(year, 12, 31)
    total_records_year = MaintenanceRecord.query \
        .filter(
            active_record_filter,
            MaintenanceRecord.maintenance_date >= start_year,
            MaintenanceRecord.maintenance_date <= end_year
        ).count()
    total_cost_year = db.session.query(db.func.sum(MaintenanceRecord.cost)) \
        .filter(
            active_record_filter,
            MaintenanceRecord.maintenance_date >= start_year,
            MaintenanceRecord.maintenance_date <= end_year
        ).scalar() or 0
    # Detailed year stats
    year_records = MaintenanceRecord.query \
        .filter(
            active_record_filter,
            MaintenanceRecord.maintenance_date >= start_year,
            MaintenanceRecord.maintenance_date <= end_year
        ).all()
    completed_year = sum(1 for r in year_records if (r.status or '').lower() == 'completed')
    scheduled_year = sum(1 for r in year_records if (r.status or '').lower() == 'scheduled')
    in_progress_year = sum(1 for r in year_records if (r.status or '').lower() == 'in_progress')
    cancelled_year = sum(1 for r in year_records if (r.status or '').lower() == 'cancelled')
    records_with_cost_year = sum(1 for r in year_records if (r.cost or 0) > 0)
    costs_year = [float(r.cost or 0) for r in year_records if (r.cost or 0) > 0]
    max_cost_year = max(costs_year) if costs_year else 0
    min_cost_year = min(costs_year) if costs_year else 0
    completion_rate = round((completed_year / total_records_year) * 100, 1) if total_records_year else 0
    avg_cost_per_record = round(total_cost_year / total_records_year) if total_records_year else 0
    # Month stats (current month)
    start_month = date(year, month, 1)
    # Compute end of month safely
    if month == 12:
        start_next_month = date(year + 1, 1, 1)
    else:
        start_next_month = date(year, month + 1, 1)
    end_month = start_next_month - timedelta(days=1)
    month_records = MaintenanceRecord.query \
        .filter(
            active_record_filter,
            MaintenanceRecord.maintenance_date >= start_month,
            MaintenanceRecord.maintenance_date <= end_month
        ).all()
    total_records_month = len(month_records)
    total_cost_month = sum(float(r.cost or 0) for r in month_records)
    records_with_cost_month = sum(1 for r in month_records if (r.cost or 0) > 0)
    costs_month = [float(r.cost or 0) for r in month_records if (r.cost or 0) > 0]
    max_cost_month = max(costs_month) if costs_month else 0
    min_cost_month = min(costs_month) if costs_month else 0
    completed_month = sum(1 for r in month_records if (r.status or '').lower() == 'completed')
    in_progress_month = sum(1 for r in month_records if (r.status or '').lower() == 'in_progress')
    # Overdue lists and counts
    overdue = MaintenanceRecord.query\
        .filter(
            active_record_filter,
            MaintenanceRecord.next_due_date != None,
            MaintenanceRecord.next_due_date < today
        ).count()
    overdue_records = MaintenanceRecord.query\
        .filter(
            active_record_filter,
            MaintenanceRecord.next_due_date != None,
            MaintenanceRecord.next_due_date < today)\
        .order_by(MaintenanceRecord.next_due_date.asc()).limit(10).all()
    due_30 = MaintenanceRecord.query\
        .filter(
            active_record_filter,
            MaintenanceRecord.next_due_date != None,
            MaintenanceRecord.next_due_date.between(today, today + timedelta(days=30))
        ).count()

    # Recent / upcoming
    recent = MaintenanceRecord.query \
        .filter(active_record_filter) \
        .order_by(MaintenanceRecord.maintenance_date.desc()).limit(8).all()
    upcoming = MaintenanceRecord.query \
        .filter(
            active_record_filter,
            MaintenanceRecord.next_due_date != None,
            MaintenanceRecord.next_due_date.between(today, today + timedelta(days=30))
        ) \
        .order_by(MaintenanceRecord.next_due_date.asc()).all()

    return render_template('maintenance/dashboard.html',
                           today=today,
                           year=year,
                           month=month,
                           total_records_year=total_records_year,
                           total_cost_year=total_cost_year,
                           completed_year=completed_year,
                           scheduled_year=scheduled_year,
                           in_progress_year=in_progress_year,
                           cancelled_year=cancelled_year,
                           records_with_cost_year=records_with_cost_year,
                           max_cost_year=max_cost_year,
                           min_cost_year=min_cost_year,
                           completion_rate=completion_rate,
                           avg_cost_per_record=avg_cost_per_record,
                           total_records_month=total_records_month,
                           total_cost_month=total_cost_month,
                           records_with_cost_month=records_with_cost_month,
                           max_cost_month=max_cost_month,
                           min_cost_month=min_cost_month,
                           completed_month=completed_month,
                           in_progress_month=in_progress_month,
                           overdue=overdue,
                           due_30=due_30,
                           overdue_records=overdue_records,
                           recent=recent,
                           upcoming=upcoming)

@app.route('/assets/add', methods=['GET', 'POST'])
@manager_required
def add_asset():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        # Danh sách tên nếu muốn thêm nhiều tài sản cùng lúc
        raw_name_list = (request.form.get('name_list') or '').strip()
        name_list = []
        if raw_name_list:
            name_list = [n.strip() for n in raw_name_list.splitlines() if n.strip()]
        # Ngày mua, mã thiết bị, tình trạng
        purchase_date_str = (request.form.get('purchase_date') or '').strip()
        purchase_date = None
        if purchase_date_str:
            try:
                # input type="date" -> yyyy-mm-dd
                purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
                from datetime import date
                if purchase_date > date.today():
                    flash('Ngày mua không được lớn hơn ngày hiện tại.', 'error')
                    return redirect(url_for('add_asset'))
            except Exception:
                flash('Ngày mua không hợp lệ.', 'error')
                return redirect(url_for('add_asset'))
        device_code = (request.form.get('device_code') or '').strip() or None
        condition_label = (request.form.get('condition_label') or '').strip() or None
        try:
            price = float(request.form['price'])
        except Exception:
            price = 0.0
        try:
            quantity = int(request.form['quantity'])
        except Exception:
            quantity = 0
        asset_type_id = request.form['asset_type_id']
        user_id = request.form.get('user_id') or None
        user_text = request.form.get('user_text', '')
        notes = request.form.get('notes', '')
        usage_months = request.form.get('usage_months')
        condition_percent = request.form.get('condition_percent')
        status = request.form['status']
        # Validate basic constraints
        if not name and not name_list:
            flash('Vui lòng nhập Tên tài sản hoặc danh sách tài sản.', 'error')
            return redirect(url_for('add_asset'))
        if price <= 0:
            flash('Giá phải lớn hơn 0.', 'error')
            return redirect(url_for('add_asset'))
        if quantity < 1:
            flash('Số lượng phải >= 1.', 'error')
            return redirect(url_for('add_asset'))
        # Chuẩn hóa danh sách tên để dùng chung logic
        if name_list:
            all_names = name_list
        else:
            all_names = [name]

        # Kiểm tra trùng tên
        for n in all_names:
            if Asset.query.filter_by(name=n).first():
                flash(f'Tên tài sản &quot;{n}&quot; đã tồn tại, vui lòng chọn tên khác.', 'error')
                return redirect(url_for('add_asset'))
        
        # Append usage/condition into notes if provided
        prefix_parts = []
        try:
            if usage_months is not None and usage_months != '':
                um = int(usage_months)
                if um < 0:
                    flash('Thời gian sử dụng không hợp lệ.', 'error')
                    return redirect(url_for('add_asset'))
                prefix_parts.append(f"Thời gian sử dụng: {um} tháng")
        except Exception:
            flash('Thời gian sử dụng không hợp lệ.', 'error')
            return redirect(url_for('add_asset'))
        try:
            if condition_percent is not None and condition_percent != '':
                cp = int(condition_percent)
                if cp < 0 or cp > 100:
                    flash('Độ mới phải trong khoảng 0-100%.', 'error')
                    return redirect(url_for('add_asset'))
                prefix_parts.append(f"Độ mới: {cp}%")
        except Exception:
            flash('Độ mới không hợp lệ.', 'error')
            return redirect(url_for('add_asset'))
        if prefix_parts:
            notes = ("; ".join(prefix_parts) + ".\n") + (notes or '')
        
        # Xử lý thông tin bảo hành
        warranty_start_date = None
        warranty_end_date = None
        warranty_period_months = None
        
        warranty_start_str = request.form.get('warranty_start_date', '').strip()
        warranty_period_str = request.form.get('warranty_period_months', '').strip()
        
        if warranty_start_str:
            try:
                # Hỗ trợ cả định dạng dd/mm/yyyy và yyyy-mm-dd
                if '/' in warranty_start_str:
                    warranty_start_date = datetime.strptime(warranty_start_str, '%d/%m/%Y').date()
                else:
                    warranty_start_date = datetime.strptime(warranty_start_str, '%Y-%m-%d').date()
                if warranty_period_str:
                    warranty_period_months = int(warranty_period_str)
                    # Tính ngày kết thúc bảo hành (xấp xỉ 30 ngày/tháng)
                    warranty_end_date = warranty_start_date + timedelta(days=warranty_period_months * 30)
            except Exception:
                pass
        
        # Xử lý số điện thoại bảo hành - chỉ cho phép số
        raw_phone = request.form.get('warranty_contact_phone', '').strip()
        phone_digits = ''.join(ch for ch in raw_phone if ch.isdigit())
        if raw_phone and not phone_digits:
            flash('Số điện thoại chỉ được phép chứa số.', 'error')
            return redirect(url_for('add_asset'))

        created_count = 0
        last_asset_id = None
        created_asset_ids = []

        voucher_action = request.form.get('voucher_action') or 'none'  # none, increase, decrease
        voucher_description = request.form.get('voucher_description', '').strip() or None

        # Xử lý upload file (nếu có), dùng chung cho tất cả tài sản được tạo
        invoice_file_path = None
        invoice_file = request.files.get('invoice_file')
        if invoice_file and invoice_file.filename:
            # Tạm lưu file, sau đó gán cho từng asset
            # File sẽ được lưu theo asset đầu tiên, các asset sau cùng trỏ chung đường dẫn này
            pass  # sẽ lưu sau khi có asset đầu tiên

        for idx, asset_name in enumerate(all_names):
            asset = Asset(
                name=asset_name,
                price=price,
                quantity=quantity,
                asset_type_id=asset_type_id,
                user_id=user_id,
                user_text=user_text,
                notes=notes,
                status=status,
                purchase_date=purchase_date,
                device_code=device_code,
                condition_label=condition_label,
                warranty_contact_name=request.form.get('warranty_contact_name', '').strip() or None,
                warranty_contact_phone=phone_digits or None,
                warranty_contact_email=request.form.get('warranty_contact_email', '').strip() or None,
                warranty_website=request.form.get('warranty_website', '').strip() or None,
                warranty_start_date=warranty_start_date,
                warranty_end_date=warranty_end_date,
                warranty_period_months=warranty_period_months
            )
            
            db.session.add(asset)
            db.session.flush()  # Lấy ID mà chưa commit

            # Lưu file hóa đơn một lần cho asset đầu tiên
            if idx == 0 and invoice_file and invoice_file.filename:
                saved_path = save_uploaded_file(invoice_file, asset.id)
                if saved_path:
                    invoice_file_path = saved_path
                    asset.invoice_file_path = saved_path
            elif invoice_file_path:
                # Các asset sau dùng chung đường dẫn
                asset.invoice_file_path = invoice_file_path

            created_count += 1
            last_asset_id = asset.id
            created_asset_ids.append(asset.id)

            # Ghi audit log cho từng tài sản
            try:
                uid = session.get('user_id')
                if uid:
                    db.session.add(AuditLog(
                        user_id=uid,
                        module='assets',
                        action='create',
                        entity_id=asset.id,
                        details=f"name={asset_name}"
                    ))
            except Exception:
                db.session.rollback()

        # Tạo chứng từ ghi tăng/ghi giảm nếu được chọn
        if voucher_action in ['increase', 'decrease'] and created_asset_ids:
            from utils.voucher import generate_voucher_code
            voucher_code = generate_voucher_code(db.session, AssetVoucher)
            voucher = AssetVoucher(
                voucher_code=voucher_code,
                voucher_type=voucher_action,
                voucher_date=today_vn(),
                description=voucher_description,
                created_by_id=session.get('user_id')
            )
            db.session.add(voucher)
            db.session.flush()

            for asset_id in created_asset_ids:
                db.session.add(AssetVoucherItem(
                    voucher_id=voucher.id,
                    asset_id=asset_id,
                    old_value=(price if voucher_action == 'decrease' else None),
                    new_value=(0 if voucher_action == 'decrease' else price),
                    quantity=quantity,
                    reason=voucher_description,
                    notes=voucher_description
                ))

        db.session.commit()

        # Thông báo kết quả
        if created_count == 1:
            flash('Tài sản đã được thêm thành công!', 'success')
        else:
            flash(f'Đã thêm thành công {created_count} tài sản!', 'success')

        return redirect(url_for('assets'))
    
    asset_types = AssetType.query.filter(AssetType.deleted_at.is_(None)).all()
    users = User.query.filter(User.deleted_at.is_(None)).all()
    today = today_vn()
    # Lấy danh sách tên tài sản hiện có (distinct, sắp xếp theo tên)
    existing_asset_names = [
        row[0] for row in db.session.query(Asset.name)
        .filter(Asset.deleted_at.is_(None))
        .distinct()
        .order_by(Asset.name.asc())
        .all()
    ]
    return render_template(
        'assets/add.html',
        asset_types=asset_types,
        users=users,
        today_iso=today.isoformat(),
        existing_asset_names=existing_asset_names
    )

@app.route('/assets/import', methods=['GET', 'POST'])
@login_required
def import_assets():
    if request.method == 'POST':
        if 'excel_file' not in request.files:
            flash('Vui lòng chọn file Excel để import.', 'error')
            return redirect(url_for('import_assets'))
        
        file = request.files['excel_file']
        if file.filename == '':
            flash('Vui lòng chọn file Excel để import.', 'error')
            return redirect(url_for('import_assets'))
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            flash('File phải có định dạng Excel (.xlsx hoặc .xls).', 'error')
            return redirect(url_for('import_assets'))
        
        try:
            # Đọc file Excel
            df = pd.read_excel(file)
            
            # Kiểm tra các cột bắt buộc
            required_columns = ['Tên tài sản', 'Giá tiền', 'Số lượng', 'Loại tài sản']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                flash(f'File Excel thiếu các cột bắt buộc: {", ".join(missing_columns)}', 'error')
                return redirect(url_for('import_assets'))
            
            # Lấy danh sách asset types và users để mapping
            asset_types = {at.name: at.id for at in AssetType.query.filter(AssetType.deleted_at.is_(None)).all()}
            users = {u.username: u.id for u in User.query.filter(User.deleted_at.is_(None)).all()}
            users_by_email = {u.email: u.id for u in User.query.filter(User.deleted_at.is_(None)).all()}
            
            # Mapping trạng thái linh hoạt hơn
            status_map = {
                'đang sử dụng': 'active',
                'bảo trì': 'maintenance',
                'đã thanh lý': 'disposed',
                'active': 'active',
                'maintenance': 'maintenance',
                'disposed': 'disposed',
                'sẵn sàng': 'active',
                'đang dùng': 'active'
            }
            
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Lấy dữ liệu từ Excel
                    name = str(row['Tên tài sản']).strip()
                    if not name or name == 'nan':
                        errors.append(f"Dòng {index + 2}: Tên tài sản không được để trống")
                        error_count += 1
                        continue
                    
                    # Kiểm tra trùng tên
                    if Asset.query.filter(Asset.name == name, Asset.deleted_at.is_(None)).first():
                        errors.append(f"Dòng {index + 2}: Tên tài sản '{name}' đã tồn tại")
                        error_count += 1
                        continue
                    
                    # Giá tiền
                    try:
                        price = float(row['Giá tiền'])
                        if price < 0:
                            errors.append(f"Dòng {index + 2}: Giá tiền không được nhỏ hơn 0")
                            error_count += 1
                            continue
                    except (ValueError, TypeError):
                        errors.append(f"Dòng {index + 2}: Giá tiền không hợp lệ")
                        error_count += 1
                        continue
                    
                    # Số lượng
                    try:
                        quantity = int(row['Số lượng'])
                        if quantity < 1:
                            errors.append(f"Dòng {index + 2}: Số lượng phải >= 1")
                            error_count += 1
                            continue
                    except (ValueError, TypeError):
                        errors.append(f"Dòng {index + 2}: Số lượng không hợp lệ")
                        error_count += 1
                        continue
                    
                    # Loại tài sản (Tự động tạo nếu chưa có)
                    asset_type_name = str(row['Loại tài sản']).strip()
                    if not asset_type_name or asset_type_name == 'nan':
                        errors.append(f"Dòng {index + 2}: Loại tài sản không được để trống")
                        error_count += 1
                        continue
                        
                    if asset_type_name not in asset_types:
                        try:
                            new_type = AssetType(name=asset_type_name, description=f"Tạo tự động từ file import")
                            db.session.add(new_type)
                            db.session.flush()
                            asset_types[asset_type_name] = new_type.id
                            print(f"Auto-created asset type: {asset_type_name}")
                        except Exception as e:
                            errors.append(f"Dòng {index + 2}: Không thể tạo loại tài sản '{asset_type_name}'")
                            error_count += 1
                            continue
                    asset_type_id = asset_types[asset_type_name]
                    
                    # Trạng thái (tùy chọn)
                    status = 'active'
                    if 'Trạng thái' in df.columns:
                        status_str = str(row['Trạng thái']).strip().lower()
                        status = status_map.get(status_str, 'active')
                    
                    # Người sử dụng (Tự động tạo nếu chưa có)
                    user_id = None
                    if 'Người sử dụng' in df.columns:
                        user_value = str(row['Người sử dụng']).strip()
                        if user_value and user_value != 'nan':
                            if user_value in users:
                                user_id = users[user_value]
                            elif user_value in users_by_email:
                                user_id = users_by_email[user_value]
                            else:
                                # Tự động tạo user mới nếu chưa tồn tại
                                try:
                                    # Lấy role mặc định là 'user'
                                    user_role = Role.query.filter_by(name='user').first()
                                    if not user_role:
                                        user_role = Role(name='user', description='Người dùng thông thường')
                                        db.session.add(user_role)
                                        db.session.commit()
                                    
                                    new_user = User(
                                        username=user_value,
                                        email=f"{user_value}@hethong.local", # Email tạm thời
                                        role_id=user_role.id,
                                        is_active=True
                                    )
                                    new_user.set_password("123456") # Mật khẩu mặc định
                                    db.session.add(new_user)
                                    db.session.flush()
                                    users[user_value] = new_user.id
                                    user_id = new_user.id
                                    print(f"Auto-created user: {user_value}")
                                except Exception as e:
                                    # Nếu lỗi tạo user thì để trống user_id, vẫn tiếp tục import asset
                                    print(f"Failed to auto-create user {user_value}: {e}")
                                    pass
                    
                    # Ngày mua (tùy chọn)
                    purchase_date = None
                    if 'Ngày mua' in df.columns:
                        purchase_date_str = str(row['Ngày mua']).strip()
                        if purchase_date_str and purchase_date_str != 'nan':
                            try:
                                # Thử parse nhiều định dạng
                                if isinstance(row['Ngày mua'], pd.Timestamp):
                                    purchase_date = row['Ngày mua'].date()
                                else:
                                    # Thử các định dạng phổ biến
                                    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']:
                                        try:
                                            purchase_date = datetime.strptime(purchase_date_str, fmt).date()
                                            break
                                        except:
                                            continue
                                if purchase_date and purchase_date > date.today():
                                    purchase_date = None  # Bỏ qua nếu là ngày tương lai
                            except:
                                pass
                    
                    # Mã thiết bị (tùy chọn)
                    device_code = None
                    if 'Mã thiết bị' in df.columns:
                        device_code_str = str(row['Mã thiết bị']).strip()
                        if device_code_str and device_code_str != 'nan':
                            device_code = device_code_str
                    
                    # Tình trạng (tùy chọn)
                    condition_label = None
                    if 'Tình trạng' in df.columns:
                        condition_str = str(row['Tình trạng']).strip()
                        if condition_str and condition_str != 'nan':
                            condition_label = condition_str
                    
                    # Ghi chú (tùy chọn)
                    notes = None
                    if 'Ghi chú' in df.columns:
                        notes_str = str(row['Ghi chú']).strip()
                        if notes_str and notes_str != 'nan':
                            notes = notes_str
                    
                    # Tạo asset mới
                    asset = Asset(
                        name=name,
                        price=price,
                        quantity=quantity,
                        asset_type_id=asset_type_id,
                        user_id=user_id,
                        notes=notes,
                        status=status,
                        purchase_date=purchase_date,
                        device_code=device_code,
                        condition_label=condition_label
                    )
                    
                    db.session.add(asset)
                    db.session.flush()
                    
                    # Ghi audit log
                    try:
                        uid = session.get('user_id')
                        if uid:
                            db.session.add(AuditLog(user_id=uid, module='assets', action='create', entity_id=asset.id, details=f"name={name} (imported)"))
                    except Exception:
                        pass
                    
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Dòng {index + 2}: Lỗi không xác định - {str(e)}")
                    error_count += 1
                    continue
            
            # Commit tất cả
            try:
                db.session.commit()
                if success_count > 0:
                    flash(f'Import thành công {success_count} tài sản!', 'success')
                if error_count > 0:
                    error_msg = f'Có {error_count} dòng bị lỗi. '
                    if len(errors) <= 10:
                        error_msg += 'Chi tiết: ' + '; '.join(errors)
                    else:
                        error_msg += f'Chi tiết 10 lỗi đầu: ' + '; '.join(errors[:10])
                    flash(error_msg, 'warning')
                if success_count == 0 and error_count == 0:
                    flash('Không có dữ liệu nào được import.', 'warning')
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi khi lưu dữ liệu: {str(e)}', 'error')
            
            return redirect(url_for('assets'))
        
        except Exception as e:
            flash(f'Lỗi khi đọc file Excel: {str(e)}', 'error')
            return redirect(url_for('import_assets'))
    
    # GET request - hiển thị form import
    return render_template('assets/import.html')

@app.route('/assets/edit/<int:id>', methods=['GET', 'POST'])
@manager_required
def edit_asset(id):
    asset = Asset.query.get_or_404(id)
    
    if request.method == 'POST':
        asset.name = request.form['name'].strip()
        # Ngày mua, mã thiết bị, tình trạng
        purchase_date_str = (request.form.get('purchase_date') or '').strip()
        if purchase_date_str:
            try:
                from datetime import date
                new_purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
                if new_purchase_date > date.today():
                    flash('Ngày mua không được lớn hơn ngày hiện tại.', 'error')
                    return redirect(url_for('edit_asset', id=id))
                asset.purchase_date = new_purchase_date
            except Exception:
                flash('Ngày mua không hợp lệ.', 'error')
                return redirect(url_for('edit_asset', id=id))
        else:
            asset.purchase_date = None
        asset.device_code = (request.form.get('device_code') or '').strip() or None
        asset.condition_label = (request.form.get('condition_label') or '').strip() or None
        try:
            asset.price = float(request.form['price'])
        except Exception:
            asset.price = 0.0
        try:
            asset.quantity = int(request.form['quantity'])
        except Exception:
            asset.quantity = 0
        asset.asset_type_id = request.form['asset_type_id']
        asset.user_id = request.form.get('user_id') or None
        asset.user_text = request.form.get('user_text', '')
        notes = request.form.get('notes', '')
        usage_months = request.form.get('usage_months')
        condition_percent = request.form.get('condition_percent')
        prefix_parts = []
        try:
            if usage_months is not None and usage_months != '':
                um = int(usage_months)
                if um < 0:
                    flash('Thời gian sử dụng không hợp lệ.', 'error')
                    return redirect(url_for('edit_asset', id=id))
                prefix_parts.append(f"Thời gian sử dụng: {um} tháng")
        except Exception:
            flash('Thời gian sử dụng không hợp lệ.', 'error')
            return redirect(url_for('edit_asset', id=id))
        try:
            if condition_percent is not None and condition_percent != '':
                cp = int(condition_percent)
                if cp < 0 or cp > 100:
                    flash('Độ mới phải trong khoảng 0-100%.', 'error')
                    return redirect(url_for('edit_asset', id=id))
                prefix_parts.append(f"Độ mới: {cp}%")
        except Exception:
            flash('Độ mới không hợp lệ.', 'error')
            return redirect(url_for('edit_asset', id=id))
        if prefix_parts:
            notes = ("; ".join(prefix_parts) + ".\n") + (notes or '')
        asset.notes = notes
        new_status = request.form.get('status', '').strip()
        if new_status:
            asset.status = new_status
        
        # Xử lý khi status = 'disposed': đảm bảo deleted_at = None (disposed không phải soft delete)
        # Tài sản đã thanh lý vẫn hiển thị trong danh sách, chỉ khác status
        if asset.status == 'disposed':
            asset.deleted_at = None
            app.logger.info(f"Asset {asset.id} ({asset.name}) status updated to 'disposed', deleted_at set to None")
        # Nếu chuyển từ disposed sang status khác, đảm bảo deleted_at = None
        elif asset.status != 'disposed' and asset.deleted_at is not None:
            # Nếu đang restore từ soft delete, giữ nguyên deleted_at = None
            pass
        
        # Cập nhật thông tin bảo hành
        warranty_start_str = request.form.get('warranty_start_date', '').strip()
        warranty_period_str = request.form.get('warranty_period_months', '').strip()
        
        if warranty_start_str:
            try:
                # Hỗ trợ cả định dạng dd/mm/yyyy và yyyy-mm-dd
                if '/' in warranty_start_str:
                    asset.warranty_start_date = datetime.strptime(warranty_start_str, '%d/%m/%Y').date()
                else:
                    asset.warranty_start_date = datetime.strptime(warranty_start_str, '%Y-%m-%d').date()
                if warranty_period_str:
                    asset.warranty_period_months = int(warranty_period_str)
                    asset.warranty_end_date = asset.warranty_start_date + timedelta(days=asset.warranty_period_months * 30)
                else:
                    # Nếu có ngày bắt đầu nhưng không có thời gian, giữ nguyên ngày kết thúc
                    pass
            except Exception:
                pass
        else:
            asset.warranty_start_date = None
            asset.warranty_end_date = None
            asset.warranty_period_months = None
        
        asset.warranty_contact_name = request.form.get('warranty_contact_name', '').strip() or None
        # Số điện thoại bảo hành - chỉ cho phép số
        raw_phone = request.form.get('warranty_contact_phone', '').strip()
        phone_digits = ''.join(ch for ch in raw_phone if ch.isdigit())
        if raw_phone and not phone_digits:
            flash('Số điện thoại chỉ được phép chứa số.', 'error')
            return redirect(url_for('edit_asset', id=id))
        asset.warranty_contact_phone = phone_digits or None
        asset.warranty_contact_email = request.form.get('warranty_contact_email', '').strip() or None
        asset.warranty_website = request.form.get('warranty_website', '').strip() or None
        
        # Xử lý upload file hóa đơn mới
        if 'invoice_file' in request.files:
            invoice_file = request.files['invoice_file']
            if invoice_file and invoice_file.filename:
                invoice_file_path = save_uploaded_file(invoice_file, asset.id)
                if invoice_file_path:
                    asset.invoice_file_path = invoice_file_path
        
        # Validate
        if not asset.name:
            flash('Tên tài sản không được để trống.', 'error')
            return redirect(url_for('edit_asset', id=id))
        if asset.price <= 0:
            flash('Giá phải lớn hơn 0.', 'error')
            return redirect(url_for('edit_asset', id=id))
        if asset.quantity < 1:
            flash('Số lượng phải >= 1.', 'error')
            return redirect(url_for('edit_asset', id=id))
        dup = Asset.query.filter(Asset.name == asset.name, Asset.id != id).first()
        if dup:
            flash('Tên tài sản đã tồn tại, vui lòng chọn tên khác.', 'error')
            return redirect(url_for('edit_asset', id=id))
        
        try:
            db.session.commit()
            app.logger.info(f"Asset {asset.id} ({asset.name}) updated successfully, status: {asset.status}")
            try:
                uid = session.get('user_id')
                if uid:
                    db.session.add(AuditLog(user_id=uid, module='assets', action='update', entity_id=id, details=f"name={asset.name}, status={asset.status}"))
                    db.session.commit()
            except Exception as e:
                app.logger.error(f"Error logging audit for asset update: {str(e)}")
                db.session.rollback()
            flash('Tài sản đã được cập nhật thành công!', 'success')
            return redirect(url_for('assets'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating asset {id}: {str(e)}")
            flash(f'Lỗi khi cập nhật tài sản: {str(e)}', 'error')
            return redirect(url_for('edit_asset', id=id))
    
    asset_types = AssetType.query.filter(AssetType.deleted_at.is_(None)).all()
    users = User.query.filter(User.deleted_at.is_(None)).all()
    today = today_vn()
    return render_template(
        'assets/edit.html',
        asset=asset,
        asset_types=asset_types,
        users=users,
        today_iso=today.isoformat()
    )

@app.route('/assets/delete/<int:id>', methods=['POST'])
@manager_required
def delete_asset(id):
    asset = Asset.query.get_or_404(id)
    try:
        if asset.deleted_at:
            flash('Tài sản đã nằm trong thùng rác.', 'info')
            return redirect(url_for('assets'))

        # Chuyển tài sản vào thùng rác
        asset.soft_delete()

        # Ẩn các bản ghi bảo trì liên quan (nếu có)
        for rec in asset.maintenance_records:
            if hasattr(rec, 'soft_delete') and rec.deleted_at is None:
                rec.soft_delete()

        db.session.commit()
        flash('Tài sản đã được xóa thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi xóa tài sản: {str(e)}', 'error')
        # Kiểm tra return_url nếu có
        return_url = request.args.get('return_url')
        if return_url:
            return redirect(return_url)
        return redirect(url_for('assets'))
    try:
        uid = session.get('user_id')
        if uid:
            db.session.add(AuditLog(user_id=uid, module='assets', action='delete', entity_id=id, details=f"name={asset.name}"))
            db.session.commit()
    except Exception:
        db.session.rollback()
    
    # Kiểm tra return_url nếu có
    return_url = request.args.get('return_url')
    if return_url:
        return redirect(return_url)
    return redirect(url_for('assets'))

# ========== CÁC TÍNH NĂNG TÀI SẢN THEO MISA QLTS ==========

@app.route('/assets/standardize')
@login_required
@manager_required
def asset_standardize():
    """Chuẩn hóa dữ liệu tài sản - Rà soát và phát hiện lỗi"""
    # Phát hiện các lỗi dữ liệu
    errors = []
    
    # 1. Trùng mã tài sản
    from collections import Counter
    device_codes = [a.device_code for a in Asset.query.filter(
        Asset.deleted_at.is_(None),
        Asset.device_code.isnot(None)
    ).all() if a.device_code]
    duplicate_codes = [code for code, count in Counter(device_codes).items() if count > 1]
    for code in duplicate_codes:
        assets = Asset.query.filter(Asset.device_code == code, Asset.deleted_at.is_(None)).all()
        errors.append({
            'type': 'duplicate_code',
            'severity': 'error',
            'message': f'Mã tài sản "{code}" bị trùng lặp',
            'count': len(assets),
            'assets': [{'id': a.id, 'name': a.name} for a in assets]
        })
    
    # 2. Thiếu thông tin bắt buộc
    missing_name = Asset.query.filter(
        Asset.deleted_at.is_(None),
        db.or_(Asset.name.is_(None), Asset.name == '')
    ).count()
    if missing_name > 0:
        errors.append({
            'type': 'missing_name',
            'severity': 'error',
            'message': f'Có {missing_name} tài sản thiếu tên',
            'count': missing_name
        })
    
    missing_code = Asset.query.filter(
        Asset.deleted_at.is_(None),
        db.or_(Asset.device_code.is_(None), Asset.device_code == '')
    ).count()
    if missing_code > 0:
        errors.append({
            'type': 'missing_code',
            'severity': 'warning',
            'message': f'Có {missing_code} tài sản thiếu mã số',
            'count': missing_code
        })
    
    missing_price = Asset.query.filter(
        Asset.deleted_at.is_(None),
        db.or_(Asset.price.is_(None), Asset.price <= 0)
    ).count()
    if missing_price > 0:
        errors.append({
            'type': 'missing_price',
            'severity': 'error',
            'message': f'Có {missing_price} tài sản thiếu hoặc giá trị = 0',
            'count': missing_price
        })
    
    # 3. Sai định dạng ngày
    # (Có thể kiểm tra thêm nếu cần)
    
    return render_template('assets/standardize.html', errors=errors)

@app.route('/assets/increase', methods=['GET', 'POST'])
@login_required
@manager_required
def asset_increase():
    """Ghi tăng tài sản - Tạo chứng từ và lưu tài sản"""
    from utils.voucher import generate_voucher_code
    from datetime import datetime
    
    if request.method == 'POST':
        try:
            # Tạo chứng từ
            voucher_code = generate_voucher_code('increase', db.session, AssetVoucher)
            voucher = AssetVoucher(
                voucher_code=voucher_code,
                voucher_type='increase',
                voucher_date=datetime.fromisoformat(request.form.get('voucher_date', today_vn().isoformat())).date(),
                description=request.form.get('description', ''),
                created_by_id=session.get('user_id')
            )
            db.session.add(voucher)
            db.session.flush()
            
            # Tạo tài sản
            asset = Asset(
                name=request.form.get('name'),
                device_code=request.form.get('device_code'),
                asset_type_id=int(request.form.get('asset_type_id')),
                price=float(request.form.get('price', 0)),
                quantity=int(request.form.get('quantity', 1)),
                purchase_date=datetime.fromisoformat(request.form.get('purchase_date')).date() if request.form.get('purchase_date') else None,
                user_text=request.form.get('department', ''),
                notes=request.form.get('notes', ''),
                status='active'
            )
            db.session.add(asset)
            db.session.flush()
            
            # Tạo chi tiết chứng từ
            voucher_item = AssetVoucherItem(
                voucher_id=voucher.id,
                asset_id=asset.id,
                new_value=asset.price,
                quantity=asset.quantity,
                reason=request.form.get('source', ''),
                notes=request.form.get('notes', '')
            )
            db.session.add(voucher_item)
            db.session.commit()
            
            flash(f'Đã ghi tăng tài sản thành công. Mã chứng từ: {voucher_code}', 'success')
            return redirect(url_for('asset_increase'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error in asset_increase: {str(e)}")
            flash(f'Lỗi khi ghi tăng tài sản: {str(e)}', 'error')
    
    asset_types = AssetType.query.filter(AssetType.deleted_at.is_(None)).all()
    today = today_vn()
    return render_template('assets/increase.html', asset_types=asset_types, today=today)

@app.route('/assets/change-info', methods=['GET', 'POST'])
@login_required
@manager_required
def asset_change_info():
    """Thay đổi thông tin tài sản - KHÔNG thay đổi giá trị"""
    if request.method == 'POST':
        try:
            asset_id = int(request.form.get('asset_id'))
            asset = Asset.query.get_or_404(asset_id)
            
            # Chỉ cập nhật thông tin không ảnh hưởng giá trị
            asset.name = request.form.get('name', asset.name)
            asset.user_text = request.form.get('department', asset.user_text)
            user_id = request.form.get('user_id')
            if user_id:
                asset.user_id = int(user_id) if user_id else None
            asset.notes = request.form.get('notes', asset.notes)
            asset.condition_label = request.form.get('condition', asset.condition_label)
            
            db.session.commit()
            flash('Đã cập nhật thông tin tài sản thành công.', 'success')
            return redirect(url_for('asset_change_info'))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi cập nhật: {str(e)}', 'error')
    
    assets = Asset.query.filter(Asset.deleted_at.is_(None)).all()
    users = User.query.filter(User.deleted_at.is_(None), User.is_active == True).all()
    return render_template('assets/change_info.html', assets=assets, users=users)

@app.route('/assets/reevaluate', methods=['GET', 'POST'])
@login_required
@manager_required
def asset_reevaluate():
    """Đánh giá lại tài sản - Tạo chứng từ đánh giá lại"""
    from utils.voucher import generate_voucher_code
    from datetime import datetime
    
    if request.method == 'POST':
        try:
            asset_id = int(request.form.get('asset_id'))
            old_value = float(request.form.get('old_value', 0))
            new_value = float(request.form.get('new_value', 0))
            reason = request.form.get('reason', '')
            
            asset = Asset.query.get_or_404(asset_id)
            
            # Tạo chứng từ
            voucher_code = generate_voucher_code('reevaluate', db.session, AssetVoucher)
            voucher = AssetVoucher(
                voucher_code=voucher_code,
                voucher_type='reevaluate',
                voucher_date=datetime.fromisoformat(request.form.get('voucher_date', today_vn().isoformat())).date(),
                description=f'Đánh giá lại tài sản {asset.name}',
                created_by_id=session.get('user_id')
            )
            db.session.add(voucher)
            db.session.flush()
            
            # Tạo chi tiết chứng từ
            voucher_item = AssetVoucherItem(
                voucher_id=voucher.id,
                asset_id=asset.id,
                old_value=old_value,
                new_value=new_value,
                reason=reason
            )
            db.session.add(voucher_item)
            
            # Cập nhật giá trị tài sản
            asset.price = new_value
            asset.notes = (asset.notes or '') + f'\n[Đánh giá lại {today_vn().strftime("%d/%m/%Y")}] {old_value} → {new_value}. Lý do: {reason}'
            
            db.session.commit()
            flash(f'Đã đánh giá lại tài sản thành công. Mã chứng từ: {voucher_code}', 'success')
            return redirect(url_for('asset_reevaluate'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error in asset_reevaluate: {str(e)}")
            flash(f'Lỗi khi đánh giá lại: {str(e)}', 'error')
    
    assets = Asset.query.filter(Asset.deleted_at.is_(None)).all()
    today = today_vn()
    return render_template('assets/reevaluate.html', assets=assets, today=today)

@app.route('/assets/transfer-menu', methods=['GET', 'POST'])
@login_required
@manager_required
def asset_transfer_menu():
    """Điều chuyển tài sản - Lưu lịch sử điều chuyển"""
    from datetime import datetime
    
    if request.method == 'POST':
        try:
            asset_id = int(request.form.get('asset_id'))
            from_department = request.form.get('from_department', '')
            to_department = request.form.get('to_department', '')
            from_user_id = int(request.form.get('from_user_id')) if request.form.get('from_user_id') else None
            to_user_id = int(request.form.get('to_user_id')) if request.form.get('to_user_id') else None
            transfer_date = datetime.fromisoformat(request.form.get('transfer_date', today_vn().isoformat())).date()
            reason = request.form.get('reason', '')
            transfer_code = request.form.get('transfer_code', '')
            
            asset = Asset.query.get_or_404(asset_id)
            
            # Lưu lịch sử điều chuyển
            transfer_history = AssetTransferHistory(
                asset_id=asset_id,
                from_department=from_department,
                to_department=to_department,
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                transfer_date=transfer_date,
                reason=reason,
                transfer_code=transfer_code,
                created_by_id=session.get('user_id')
            )
            db.session.add(transfer_history)
            
            # Cập nhật tài sản
            asset.user_id = to_user_id
            asset.user_text = to_department
            asset.notes = (asset.notes or '') + f'\n[Điều chuyển {transfer_date.strftime("%d/%m/%Y")}] {from_department} → {to_department}. {reason}'
            
            db.session.commit()
            flash('Đã điều chuyển tài sản thành công.', 'success')
            return redirect(url_for('asset_transfer_menu'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error in asset_transfer_menu: {str(e)}")
            flash(f'Lỗi khi điều chuyển: {str(e)}', 'error')
    
    assets = Asset.query.filter(Asset.deleted_at.is_(None)).all()
    users = User.query.filter(User.deleted_at.is_(None), User.is_active == True).all()
    transfer_history = AssetTransferHistory.query.order_by(AssetTransferHistory.created_at.desc()).limit(50).all()
    today = today_vn()
    return render_template('assets/transfer_menu.html', 
                         assets=assets, 
                         users=users,
                         transfer_history=transfer_history,
                         today=today)

@app.route('/assets/process-request', methods=['GET', 'POST'])
@login_required
@manager_required
def asset_process_request():
    """Đề nghị xử lý tài sản - Workflow: Draft → Submitted → (Verifying) → Approved"""
    from utils.voucher import generate_process_request_code
    
    if request.method == 'POST':
        try:
            asset_id = int(request.form.get('asset_id'))
            request_type = request.form.get('request_type')
            unit_name = request.form.get('unit_name')
            current_status = request.form.get('current_status')
            quantity = int(request.form.get('quantity', 1))
            reason = request.form.get('reason')
            notes = request.form.get('notes')
            status = request.form.get('status', 'draft')  # draft hoặc submitted
            
            asset = Asset.query.get_or_404(asset_id)
            original_price = asset.price
            
            # Tính giá trị còn lại (nếu có module khấu hao thì lấy từ đó, k thì lấy mặc định)
            remaining_value = float(request.form.get('remaining_value', original_price))
            
            # Xử lý file đính kèm
            attachment_path = None
            if 'attachment' in request.files:
                file = request.files['attachment']
                if file and file.filename:
                    filename = secure_filename(f"process_{now_vn().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                    target_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'process_requests')
                    os.makedirs(target_dir, exist_ok=True)
                    file.save(os.path.join(target_dir, filename))
                    attachment_path = f"process_requests/{filename}"

            request_code = generate_process_request_code(db.session, AssetProcessRequest)
            process_request = AssetProcessRequest(
                request_code=request_code,
                request_date=today_vn(),
                asset_id=asset_id,
                unit_name=unit_name,
                current_status=current_status,
                quantity=quantity,
                original_price=original_price,
                remaining_value=remaining_value,
                request_type=request_type,
                reason=reason,
                notes=notes,
                attachment_path=attachment_path,
                status=status,
                created_by_id=session.get('user_id')
            )
            
            if status == 'submitted':
                process_request.submitted_at = now_vn()
            
            db.session.add(process_request)
            db.session.commit()
            
            flash(f'Đã tạo đề nghị xử lý thành công. Mã đề nghị: {request_code}', 'success')
            return redirect(url_for('asset_process_request'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error in asset_process_request: {str(e)}")
            flash(f'Lỗi khi tạo đề nghị: {str(e)}', 'error')
    
    # Hiển thị danh sách đề nghị
    requests = AssetProcessRequest.query.order_by(AssetProcessRequest.created_at.desc()).limit(50).all()
    assets = Asset.query.filter(Asset.deleted_at.is_(None)).all()
    return render_template('assets/process_request.html', assets=assets, requests=requests)

@app.route('/assets/process-request/<int:id>/approve', methods=['POST'])
@login_required
@admin_required
def asset_process_request_approve(id):
    """Duyệt/Thẩm định đề nghị xử lý"""
    process_request = AssetProcessRequest.query.get_or_404(id)
    
    action = request.form.get('action')  # verify, approve, reject
    
    if action == 'verify':
        if process_request.status != 'submitted':
            flash('Chỉ có thể thẩm định đề nghị ở trạng thái "Đã gửi".', 'error')
        else:
            process_request.status = 'verifying'
            process_request.verifier_id = session.get('user_id')
            process_request.verified_at = now_vn()
            process_request.verification_notes = request.form.get('verification_notes', '')
            db.session.commit()
            flash('Đã ghi nhận kết quả thẩm định. Chờ phê duyệt.', 'success')
            
    elif action == 'approve':
        if process_request.status not in ['submitted', 'verifying']:
            flash('Trạng thái không hợp lệ để phê duyệt.', 'error')
            return redirect(url_for('asset_process_request'))
            
        process_request.status = 'approved'
        process_request.approved_at = now_vn()
        process_request.approved_by_id = session.get('user_id')
        
        # Thực hiện xử lý tài sản dựa trên request_type
        asset = process_request.asset
        rtype = process_request.request_type
        
        if rtype in ['dispose', 'destroy']:
            asset.soft_delete() # Đánh dấu disposed và deleted_at
        elif rtype == 'sell':
            asset.status = 'disposed'
            asset.notes = (asset.notes or '') + f'\n[Đã bán {today_vn().strftime("%d/%m/%Y")}] {process_request.reason}'
        elif rtype == 'transfer':
            asset.status = 'active'
            asset.notes = (asset.notes or '') + f'\n[Yêu cầu điều chuyển {today_vn().strftime("%d/%m/%Y")}] {process_request.reason}'
            # Note: Thực tế điều chuyển có thể cần cập nhật location/user, nhưng ở đây là "Request" xử lý chung
        elif rtype == 'recall':
            asset.user_id = None
            asset.status = 'stock' # Thu hồi về kho
            asset.notes = (asset.notes or '') + f'\n[Thu hồi {today_vn().strftime("%d/%m/%Y")}] {process_request.reason}'
        
        db.session.commit()
        flash('Đã phê duyệt đề nghị xử lý.', 'success')
        
    elif action == 'reject':
        process_request.status = 'rejected'
        process_request.rejected_at = now_vn()
        process_request.rejected_reason = request.form.get('rejected_reason', '')
        db.session.commit()
        flash('Đã từ chối đề nghị xử lý.', 'success')
    
    return redirect(url_for('asset_process_request'))

@app.route('/assets/decrease', methods=['GET', 'POST'])
@login_required
@manager_required
def asset_decrease():
    """Ghi giảm tài sản - Tạo chứng từ ghi giảm"""
    from utils.voucher import generate_voucher_code
    from datetime import datetime
    
    if request.method == 'POST':
        try:
            asset_id = int(request.form.get('asset_id'))
            reason = request.form.get('reason')
            notes = request.form.get('notes')
            voucher_date = datetime.fromisoformat(request.form.get('voucher_date', today_vn().isoformat())).date()
            
            asset = Asset.query.get_or_404(asset_id)
            
            # Tạo chứng từ
            voucher_code = generate_voucher_code('decrease', db.session, AssetVoucher)
            voucher = AssetVoucher(
                voucher_code=voucher_code,
                voucher_type='decrease',
                voucher_date=voucher_date,
                description=f'Ghi giảm tài sản {asset.name}',
                created_by_id=session.get('user_id')
            )
            db.session.add(voucher)
            db.session.flush()
            
            # Tạo chi tiết chứng từ
            voucher_item = AssetVoucherItem(
                voucher_id=voucher.id,
                asset_id=asset.id,
                old_value=asset.price,
                new_value=0,
                reason=reason,
                notes=notes
            )
            db.session.add(voucher_item)
            
            # Ghi giảm tài sản
            asset.soft_delete()
            asset.price = 0  # Giảm nguyên giá về 0
            asset.notes = (asset.notes or '') + f'\n[Ghi giảm {voucher_date.strftime("%d/%m/%Y")}] Lý do: {reason}. {notes}'
            
            db.session.commit()
            flash(f'Đã ghi giảm tài sản thành công. Mã chứng từ: {voucher_code}', 'success')
            return redirect(url_for('asset_decrease'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error in asset_decrease: {str(e)}")
            flash(f'Lỗi khi ghi giảm: {str(e)}', 'error')
    
    assets = Asset.query.filter(Asset.deleted_at.is_(None)).all()
    today = today_vn()
    return render_template('assets/decrease.html', assets=assets, today=today)

@app.route('/assets/depreciation', methods=['GET', 'POST'])
@login_required
@manager_required
def asset_depreciation():
    """Tính khấu hao/hao mòn tài sản"""
    if request.method == 'POST':
        try:
            period_year = int(request.form.get('year'))
            period_month = int(request.form.get('month')) if request.form.get('month') else None
            method = request.form.get('method', 'straight_line')
            asset_ids = request.form.getlist('asset_ids')
            
            if not asset_ids:
                flash('Vui lòng chọn ít nhất một tài sản.', 'error')
                return redirect(url_for('asset_depreciation'))
            
            # Tính khấu hao cho từng tài sản
            calculated_count = 0
            skipped_assets = []  # Danh sách tài sản chưa đủ kỳ tính khấu hao
            for asset_id in asset_ids:
                asset = Asset.query.get(asset_id)
                if not asset or asset.deleted_at:
                    continue
                
                original_value = asset.price or 0
                if original_value <= 0:
                    continue
                
                # Kiểm tra điều kiện tính khấu hao: giá trị tài sản phải >= 30 triệu VNĐ
                if original_value < 30000000:
                    skipped_assets.append(asset.name)
                    continue  # Giá trị < 30 triệu, không tính khấu hao
                
                # Kiểm tra điều kiện tính khấu hao: phải đủ 12 tháng từ ngày mua
                if asset.purchase_date:
                    # Tính số tháng từ ngày mua đến cuối năm tính khấu hao (31/12/period_year)
                    purchase_year = asset.purchase_date.year
                    purchase_month = asset.purchase_date.month
                    
                    # Tính số tháng từ tháng mua đến cuối năm period_year
                    if purchase_year < period_year:
                        # Năm mua < năm tính: 
                        # - Từ tháng mua đến cuối năm mua: (12 - purchase_month + 1) tháng
                        # - Các năm ở giữa: (period_year - purchase_year - 1) * 12 tháng
                        # - Năm tính: 12 tháng
                        # Ví dụ: mua 02/2024, tính năm 2025 -> (12-2+1) + 0*12 + 12 = 11 + 12 = 23 tháng
                        months_from_purchase = (12 - purchase_month + 1) + (period_year - purchase_year - 1) * 12 + 12
                    elif purchase_year == period_year:
                        # Cùng năm: tính từ tháng mua đến cuối năm
                        # Ví dụ: mua 09/2025, tính năm 2025 -> từ 09/2025 đến 12/2025 = 4 tháng
                        months_from_purchase = 12 - purchase_month + 1
                    else:
                        # Năm mua > năm tính (không hợp lý), bỏ qua
                        continue
                    
                    # Chỉ tính khấu hao nếu đã đủ 12 tháng từ ngày mua
                    if months_from_purchase < 12:
                        skipped_assets.append(asset.name)
                        continue  # Chưa đủ 12 tháng, bỏ qua tài sản này
                
                # Tính lũy kế khấu hao trước kỳ này
                prev_query = AssetDepreciation.query.filter(
                    AssetDepreciation.asset_id == asset_id
                )
                
                # Lọc theo năm và tháng
                if period_month:
                    # Tính lũy kế đến trước tháng này trong cùng năm
                    prev_query = prev_query.filter(
                        db.or_(
                            AssetDepreciation.period_year < period_year,
                            db.and_(
                                AssetDepreciation.period_year == period_year,
                                AssetDepreciation.period_month < period_month
                            )
                        )
                    )
                else:
                    # Tính lũy kế đến trước năm này
                    prev_query = prev_query.filter(
                        AssetDepreciation.period_year < period_year
                    )
                
                prev_depreciations = prev_query.all()
                prev_accumulated = sum(d.accumulated_depreciation or 0 for d in prev_depreciations)
                
                # Khấu hao theo năm (đường thẳng) và tùy chọn số dư giảm dần
                useful_life_years = getattr(asset, 'useful_life_years', None) or 5
                depreciation_rate = 1.0 / useful_life_years  # Tỷ lệ khấu hao năm (dạng thập phân)
                
                if method == 'straight_line':
                    # Công thức: Mức trích khấu hao hàng năm = Nguyên giá / Thời gian trích khấu hao
                    annual_depreciation = original_value / useful_life_years
                    
                    if period_month:
                        # Tính khấu hao hàng tháng = Khấu hao hàng năm / 12
                        monthly_depreciation = annual_depreciation / 12
                        
                        # Nếu có ngày mua trong tháng đó, tính theo số ngày sử dụng thực tế
                        if asset.purchase_date:
                            # Lấy số ngày trong tháng tính khấu hao
                            days_in_month = monthrange(period_year, period_month)[1]
                            
                            # Kiểm tra nếu ngày mua trong tháng này
                            if (asset.purchase_date.year == period_year and 
                                asset.purchase_date.month == period_month):
                                # Số ngày sử dụng = Tổng số ngày của tháng - Ngày bắt đầu sử dụng + 1
                                days_used = days_in_month - asset.purchase_date.day + 1
                                # Mức trích khấu hao theo tháng phát sinh = (Khấu hao hàng tháng / Tổng số ngày của tháng) x Số ngày sử dụng
                                depreciation_amount = (monthly_depreciation / days_in_month) * days_used
                            else:
                                # Nếu không phải tháng mua, tính đủ tháng
                                depreciation_amount = monthly_depreciation
                        else:
                            # Không có ngày mua, tính đủ tháng
                            depreciation_amount = monthly_depreciation
                    else:
                        # Tính theo năm
                        depreciation_amount = annual_depreciation
                else:
                    # Số dư giảm dần: áp dụng hệ số 2 trên giá trị còn lại
                    remaining_value_before = original_value - prev_accumulated
                    annual_depreciation = remaining_value_before * depreciation_rate * 2
                    
                    if period_month:
                        monthly_depreciation = annual_depreciation / 12
                        
                        # Nếu có ngày mua trong tháng đó, tính theo số ngày sử dụng thực tế
                        if asset.purchase_date:
                            days_in_month = monthrange(period_year, period_month)[1]
                            
                            if (asset.purchase_date.year == period_year and 
                                asset.purchase_date.month == period_month):
                                days_used = days_in_month - asset.purchase_date.day + 1
                                depreciation_amount = (monthly_depreciation / days_in_month) * days_used
                            else:
                                depreciation_amount = monthly_depreciation
                        else:
                            depreciation_amount = monthly_depreciation
                    else:
                        depreciation_amount = annual_depreciation
                
                # Đảm bảo không vượt quá nguyên giá
                depreciation_amount = min(depreciation_amount, original_value - prev_accumulated)
                if depreciation_amount < 0:
                    depreciation_amount = 0
                
                accumulated = prev_accumulated + depreciation_amount
                remaining_value = original_value - accumulated
                
                # Kiểm tra đã tính chưa
                existing = AssetDepreciation.query.filter(
                    AssetDepreciation.asset_id == asset_id,
                    AssetDepreciation.period_year == period_year
                )
                if period_month:
                    existing = existing.filter(AssetDepreciation.period_month == period_month)
                else:
                    existing = existing.filter(AssetDepreciation.period_month.is_(None))
                existing = existing.first()
                
                if existing:
                    existing.depreciation_amount = depreciation_amount
                    existing.accumulated_depreciation = accumulated
                    existing.remaining_value = remaining_value
                    existing.method = method
                    existing.depreciation_rate = depreciation_rate * 100
                else:
                    depreciation = AssetDepreciation(
                        asset_id=asset_id,
                        period_year=period_year,
                        period_month=period_month,
                        original_value=original_value,
                        depreciation_amount=depreciation_amount,
                        accumulated_depreciation=accumulated,
                        remaining_value=remaining_value,
                        method=method,
                        depreciation_rate=depreciation_rate * 100
                    )
                    db.session.add(depreciation)
                
                calculated_count += 1
            
            db.session.commit()
            
            # Hiển thị thông báo kết quả
            if calculated_count > 0:
                flash(f'Đã tính khấu hao/hao mòn thành công cho {calculated_count} tài sản.', 'success')
            
            if skipped_assets:
                asset_names = ', '.join(skipped_assets[:5])  # Hiển thị tối đa 5 tài sản
                if len(skipped_assets) > 5:
                    asset_names += f' và {len(skipped_assets) - 5} tài sản khác'
                flash(f'Tài sản không đủ điều kiện tính khấu hao (chưa đủ 12 tháng hoặc giá trị < 30 triệu): {asset_names}', 'warning')
            
            redirect_url = url_for('asset_depreciation', year=period_year, method=method)
            if period_month:
                redirect_url += f'&month={period_month}'
            return redirect(redirect_url)
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error in asset_depreciation: {str(e)}")
            flash(f'Lỗi khi tính khấu hao/hao mòn: {str(e)}', 'error')
    
    year = request.args.get('year', type=int) or today_vn().year
    month = request.args.get('month', type=int)
    page = request.args.get('page', 1, type=int)
    asset_page = request.args.get('asset_page', 1, type=int)
    
    # Phân trang cho danh sách tài sản: tối đa 20 bản ghi mỗi trang
    assets_query = Asset.query.filter(Asset.deleted_at.is_(None))
    assets_paginate = assets_query.order_by(Asset.id.desc()).paginate(
        page=asset_page, per_page=20, error_out=False
    )
    
    # Lấy tất cả khấu hao của năm được chọn để hiển thị trong bảng
    depreciations_query = AssetDepreciation.query.filter(
        AssetDepreciation.period_year == year
    )
    if month:
        depreciations_query = depreciations_query.filter(AssetDepreciation.period_month == month)
    
    all_depreciations = depreciations_query.all()
    # Tạo dict để dễ tìm khấu hao theo asset_id
    depreciations_dict = {dep.asset_id: dep for dep in all_depreciations}
    
    # Tính số kỳ đã khấu hao cho mỗi asset
    asset_periods_count = {}
    for asset in assets_paginate.items:
        # Đếm số bản ghi khấu hao của asset này
        periods = AssetDepreciation.query.filter(
            AssetDepreciation.asset_id == asset.id
        ).count()
        asset_periods_count[asset.id] = periods
    
    # Hiển thị tất cả khấu hao đã tính (không phân trang)
    all_depreciations_list = depreciations_query.order_by(AssetDepreciation.created_at.desc()).all()
    
    # Tạo paginate object giả để tương thích với template (nhưng không dùng phân trang)
    class FakePaginate:
        def __init__(self, items):
            self.items = items
            self.page = 1
            self.pages = 1
            self.per_page = len(items) if items else 1
            self.total = len(items)
    
    depreciations_paginate = FakePaginate(all_depreciations_list)
    
    current_year = today_vn().year
    return render_template('assets/depreciation.html', 
                         assets_paginate=assets_paginate,
                         assets=assets_paginate.items,  # Giữ để tương thích với template cũ
                         depreciations_paginate=depreciations_paginate,
                         depreciations=depreciations_paginate.items,  # Giữ để tương thích với template cũ
                         depreciations_dict=depreciations_dict,  # Dict để tìm nhanh khấu hao theo asset_id
                         asset_periods_count=asset_periods_count,  # Số kỳ đã khấu hao của mỗi asset
                         current_year=current_year,
                         year=year,
                         month=month)

@app.route('/assets/depreciation/add/<int:asset_id>', methods=['GET', 'POST'])
@login_required
@manager_required
def add_depreciation(asset_id):
    """Thêm khấu hao/hao mòn mới cho tài sản"""
    asset = Asset.query.get_or_404(asset_id)
    
    if request.method == 'POST':
        try:
            period_year = int(request.form.get('period_year', today_vn().year))
            period_month = int(request.form.get('period_month')) if request.form.get('period_month') else None
            original_value = float(request.form.get('original_value', asset.price or 0))
            depreciation_amount = float(request.form.get('depreciation_amount', 0))
            accumulated_depreciation = float(request.form.get('accumulated_depreciation', 0))
            remaining_value = float(request.form.get('remaining_value', original_value))
            method = request.form.get('method', 'straight_line')
            depreciation_rate = float(request.form.get('depreciation_rate', 0))
            
            # Kiểm tra đã tồn tại chưa
            existing = AssetDepreciation.query.filter(
                AssetDepreciation.asset_id == asset_id,
                AssetDepreciation.period_year == period_year
            )
            if period_month:
                existing = existing.filter(AssetDepreciation.period_month == period_month)
            else:
                existing = existing.filter(AssetDepreciation.period_month.is_(None))
            existing = existing.first()
            
            if existing:
                flash('Khấu hao/hao mòn cho kỳ này đã tồn tại. Vui lòng sửa thay vì thêm mới.', 'error')
                return redirect(url_for('asset_depreciation', year=period_year, month=period_month))
            
            depreciation = AssetDepreciation(
                asset_id=asset_id,
                period_year=period_year,
                period_month=period_month,
                original_value=original_value,
                depreciation_amount=depreciation_amount,
                accumulated_depreciation=accumulated_depreciation,
                remaining_value=remaining_value,
                method=method,
                depreciation_rate=depreciation_rate
            )
            db.session.add(depreciation)
            db.session.commit()
            flash('Đã thêm khấu hao/hao mòn thành công!', 'success')
            return redirect(url_for('asset_depreciation', year=period_year, month=period_month))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error adding depreciation: {str(e)}")
            flash(f'Lỗi khi thêm khấu hao/hao mòn: {str(e)}', 'error')
    
    # GET: hiển thị form thêm mới
    year = request.args.get('year', type=int) or today_vn().year
    month = request.args.get('month', type=int)
    return render_template('assets/depreciation_add.html', asset=asset, year=year, month=month)

@app.route('/assets/depreciation/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@manager_required
def edit_depreciation(id):
    """Sửa khấu hao/hao mòn tài sản"""
    depreciation = AssetDepreciation.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            depreciation.depreciation_amount = float(request.form.get('depreciation_amount', 0))
            depreciation.accumulated_depreciation = float(request.form.get('accumulated_depreciation', 0))
            depreciation.remaining_value = float(request.form.get('remaining_value', 0))
            depreciation.method = request.form.get('method', depreciation.method)
            depreciation.depreciation_rate = float(request.form.get('depreciation_rate', 0))
            
            db.session.commit()
            flash('Đã cập nhật khấu hao/hao mòn thành công!', 'success')
            return redirect(url_for('asset_depreciation', year=depreciation.period_year, month=depreciation.period_month))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error editing depreciation: {str(e)}")
            flash(f'Lỗi khi cập nhật khấu hao/hao mòn: {str(e)}', 'error')
    
    return render_template('assets/depreciation_edit.html', depreciation=depreciation)

@app.route('/assets/depreciation/delete/<int:id>', methods=['POST'])
@login_required
@manager_required
def delete_depreciation(id):
    """Xóa khấu hao/hao mòn tài sản"""
    depreciation = AssetDepreciation.query.get_or_404(id)
    year = depreciation.period_year
    month = depreciation.period_month
    
    try:
        db.session.delete(depreciation)
        db.session.commit()
        flash('Đã xóa khấu hao/hao mòn thành công!', 'success')
        
        # Giữ lại các tham số từ request hiện tại
        redirect_url = url_for('asset_depreciation', year=year)
        if month:
            redirect_url += f'&month={month}'
        
        # Giữ lại tham số pagination nếu có
        asset_page = request.args.get('asset_page', type=int)
        page = request.args.get('page', type=int)
        method = request.args.get('method')
        
        if asset_page:
            redirect_url += f'&asset_page={asset_page}'
        if page:
            redirect_url += f'&page={page}'
        if method:
            redirect_url += f'&method={method}'
            
        return redirect(redirect_url)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting depreciation: {str(e)}")
        flash(f'Lỗi khi xóa khấu hao/hao mòn: {str(e)}', 'error')
        
        # Giữ lại các tham số từ request hiện tại
        redirect_url = url_for('asset_depreciation', year=year)
        if month:
            redirect_url += f'&month={month}'
        
        # Giữ lại tham số pagination nếu có
        asset_page = request.args.get('asset_page', type=int)
        page = request.args.get('page', type=int)
        method = request.args.get('method')
        
        if asset_page:
            redirect_url += f'&asset_page={asset_page}'
        if page:
            redirect_url += f'&page={page}'
        if method:
            redirect_url += f'&method={method}'
            
        return redirect(redirect_url)
    
    return redirect(url_for('asset_depreciation', year=year, month=month if month else None))


# ---------------------- INVENTORY MODULE (API) ---------------------- #

def require_role_api(*roles):
    """Simple role guard for API routes."""
    role = session.get('role')
    return role in roles or role == 'admin'


def user_role():
    return session.get('role')


def can_edit_inventory(inv):
    """Kiểm tra user hiện tại có được nhập/sửa đợt kiểm kê này không."""
    role = user_role()
    if inv.status not in ['draft', 'in_progress']:
        return False
    return role in ['admin', 'manager', 'accountant', 'inventory_leader', 'inventory_member']


def log_inventory_action(inventory_id, action, actor_id, from_status=None, to_status=None, reason=None, payload=None):
    try:
        entry = InventoryLog(
            inventory_id=inventory_id,
            action=action,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            payload=json.dumps(payload) if payload is not None else None,
            actor_id=actor_id
        )
        db.session.add(entry)
    except Exception:
        db.session.rollback()
        raise


@app.route('/api/inventories', methods=['POST'])
@login_required
def api_inventory_create():
    """Tạo đợt kiểm kê mới (Draft)."""
    data = request.get_json() or {}
    role = session.get('role')
    if role not in ['admin', 'manager', 'accountant']:
        return jsonify({'success': False, 'message': 'Không có quyền'}), 403

    try:
        name = data.get('name')
        inventory_time = data.get('inventory_time')
        if not name or not inventory_time:
            return jsonify({'success': False, 'message': 'Thiếu tên đợt hoặc thời điểm kiểm kê'}), 400

        scope_type = data.get('scope_type')
        scope_locations = data.get('scope_locations') or []
        scope_asset_groups = data.get('scope_asset_groups') or []

        # Ràng buộc: không trùng thời điểm + phạm vi
        duplicate = Inventory.query.filter(
            Inventory.inventory_time == datetime.fromisoformat(inventory_time),
            Inventory.scope_type == scope_type
        ).first()
        if duplicate:
            return jsonify({'success': False, 'message': 'Đã tồn tại đợt kiểm kê cùng thời điểm và phạm vi'}), 400

        from utils.voucher import generate_inventory_code
        code = generate_inventory_code(db.session, Inventory)

        inv = Inventory(
            inventory_code=code,
            inventory_name=name,
            inventory_time=datetime.fromisoformat(inventory_time),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            inventory_type=data.get('inventory_type'),
            scope_type=scope_type,
            scope=data.get('scope_text'),
            scope_locations=json.dumps(scope_locations),
            scope_asset_groups=json.dumps(scope_asset_groups),
            decision_number=data.get('decision_number'),
            decision_date=data.get('decision_date'),
            decision_file_path=data.get('decision_file_path'),
            status='draft',
            created_by_id=session.get('user_id')
        )
        db.session.add(inv)
        db.session.flush()  # đảm bảo có id trước khi ghi log
        log_inventory_action(inv.id, 'create_batch', session.get('user_id'))
        db.session.commit()
        return jsonify({'success': True, 'data': {'id': inv.id, 'code': inv.inventory_code}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/inventories/<int:inventory_id>/generate-lines', methods=['POST'])
@login_required
def api_inventory_generate_lines(inventory_id):
    """Sinh danh mục tài sản theo sổ tại thời điểm kiểm kê."""
    inv = Inventory.query.get_or_404(inventory_id)
    if not require_role_api('manager', 'accountant'):
        return jsonify({'success': False, 'message': 'Không có quyền'}), 403
    if inv.status not in ['draft', 'in_progress']:
        return jsonify({'success': False, 'message': 'Trạng thái không cho phép tạo danh mục'}), 400

    try:
        # Lọc phạm vi
        scope_locations = json.loads(inv.scope_locations) if inv.scope_locations else []
        scope_asset_groups = json.loads(inv.scope_asset_groups) if inv.scope_asset_groups else []

        asset_query = Asset.query.filter(Asset.deleted_at.is_(None))
        # Chỉ lấy active/idle/paused
        asset_query = asset_query.filter(Asset.status.in_(['active', 'idle', 'paused']))

        if inv.scope_type == 'by_location' and scope_locations:
            if hasattr(Asset, 'location_id'):
                asset_query = asset_query.filter(Asset.location_id.in_(scope_locations))
        if inv.scope_type == 'by_asset_group' and scope_asset_groups:
            if hasattr(Asset, 'asset_type_id'):
                asset_query = asset_query.filter(Asset.asset_type_id.in_(scope_asset_groups))

        assets = asset_query.all()

        created = 0
        for asset in assets:
            exists = InventoryResult.query.filter_by(inventory_id=inventory_id, asset_id=asset.id).first()
            if exists:
                continue
            line = InventoryResult(
                inventory_id=inventory_id,
                asset_id=asset.id,
                book_quantity=getattr(asset, 'quantity', 1) or 1,
                book_value=asset.price or 0,
                book_location_id=getattr(asset, 'location_id', None),
                book_asset_type_id=getattr(asset, 'asset_type_id', None),
                book_status=getattr(asset, 'status', None)
            )
            db.session.add(line)
            created += 1
        inv.status = 'in_progress'
        log_inventory_action(inv.id, 'generate_book_lines', session.get('user_id'))
        db.session.commit()
        return jsonify({'success': True, 'created': created})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/inventories/<int:inventory_id>/result', methods=['POST'])
@login_required
def api_inventory_save_result(inventory_id):
    """Nhập kết quả thực tế cho 1 tài sản."""
    inv = Inventory.query.get_or_404(inventory_id)
    if not can_edit_inventory(inv):
        return jsonify({'success': False, 'message': 'Đợt đã bị khóa/gửi duyệt hoặc bạn không có quyền'}), 400

    data = request.get_json() or {}
    asset_id = data.get('asset_id')
    if not asset_id:
        return jsonify({'success': False, 'message': 'Thiếu asset_id'}), 400

    try:
        line = InventoryResult.query.filter_by(inventory_id=inventory_id, asset_id=asset_id).first()
        if not line:
            return jsonify({'success': False, 'message': 'Tài sản không thuộc đợt này'}), 404

        line.actual_quantity = data.get('actual_quantity')
        line.actual_condition = data.get('actual_condition')
        line.actual_status = data.get('actual_condition')
        line.actual_value = data.get('actual_value')
        line.actual_location_id = data.get('actual_location_id')
        line.actual_serial_plate = data.get('actual_serial_plate')
        line.notes = data.get('notes')

        # difference simple
        if line.actual_value is not None:
            line.difference = (line.actual_value or 0) - (line.book_value or 0)

        line.checked_by_id = session.get('user_id')
        line.checked_at = now_vn()

        db.session.add(line)
        log_inventory_action(inv.id, 'input_result', session.get('user_id'), payload={'asset_id': asset_id})
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/inventories/<int:inventory_id>/surplus', methods=['POST'])
@login_required
def api_inventory_surplus(inventory_id):
    """Thêm tài sản thừa."""
    inv = Inventory.query.get_or_404(inventory_id)
    if not can_edit_inventory(inv):
        return jsonify({'success': False, 'message': 'Đợt đã bị khóa/gửi duyệt hoặc bạn không có quyền'}), 400

    data = request.get_json() or {}
    required = ['name', 'quantity']
    if any(not data.get(k) for k in required):
        return jsonify({'success': False, 'message': 'Thiếu thông tin tài sản thừa'}), 400
    try:
        surplus = InventorySurplusAsset(
            inventory_id=inventory_id,
            team_id=data.get('team_id'),
            name=data.get('name'),
            asset_type_id=data.get('asset_type_id'),
            location_id=data.get('location_id'),
            quantity=data.get('quantity'),
            estimated_start_year=data.get('estimated_start_year'),
            origin=data.get('origin'),
            notes=data.get('notes'),
            created_by_id=session.get('user_id')
        )
        db.session.add(surplus)
        log_inventory_action(inv.id, 'add_surplus', session.get('user_id'), payload={'surplus_name': surplus.name})
        db.session.commit()
        return jsonify({'success': True, 'data': {'id': surplus.id}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/inventories/<int:inventory_id>/submit', methods=['POST'])
@login_required
def api_inventory_submit(inventory_id):
    """Kế toán submit đợt kiểm kê."""
    inv = Inventory.query.get_or_404(inventory_id)
    if not require_role_api('manager', 'accountant'):
        return jsonify({'success': False, 'message': 'Không có quyền'}), 403
    if inv.status not in ['draft', 'in_progress']:
        return jsonify({'success': False, 'message': 'Đợt không ở trạng thái cho phép submit'}), 400
    try:
        from_status = inv.status
        inv.status = 'submitted'
        log_inventory_action(inv.id, 'submit', session.get('user_id'), from_status=from_status, to_status='submitted')
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/inventories/<int:inventory_id>/approve-lock', methods=['POST'])
@login_required
def api_inventory_approve_lock(inventory_id):
    """Lãnh đạo duyệt & khóa đợt kiểm kê."""
    if session.get('role') not in ['admin', 'manager']:
        return jsonify({'success': False, 'message': 'Không có quyền'}), 403
    inv = Inventory.query.get_or_404(inventory_id)
    if inv.status != 'submitted':
        return jsonify({'success': False, 'message': 'Chỉ duyệt được khi đã submit'}), 400
    try:
        from_status = inv.status
        inv.status = 'approved_locked'
        inv.locked_at = now_vn()
        inv.locked_by_id = session.get('user_id')
        log_inventory_action(inv.id, 'approve_lock', session.get('user_id'), from_status=from_status, to_status='approved_locked')
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/inventories/<int:inventory_id>/unlock', methods=['POST'])
@login_required
def api_inventory_unlock(inventory_id):
    """Super admin mở khóa đợt đã khóa."""
    if session.get('role') != 'super_admin':
        return jsonify({'success': False, 'message': 'Chỉ Super Admin mới được mở khóa'}), 403
    inv = Inventory.query.get_or_404(inventory_id)
    if inv.status != 'approved_locked':
        return jsonify({'success': False, 'message': 'Chỉ mở khóa trạng thái locked'}), 400
    data = request.get_json() or {}
    reason = data.get('reason')
    if not reason:
        return jsonify({'success': False, 'message': 'Cần lý do mở khóa'}), 400
    try:
        from_status = inv.status
        inv.status = 'in_progress'
        inv.locked_at = None
        inv.locked_by_id = None
        log_inventory_action(inv.id, 'unlock', session.get('user_id'), from_status=from_status, to_status='in_progress', reason=reason)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/inventories/<int:inventory_id>/close', methods=['POST'])
@login_required
def api_inventory_close(inventory_id):
    """Đóng đợt kiểm kê (sau khi xử lý xong)."""
    if session.get('role') not in ['admin', 'manager']:
        return jsonify({'success': False, 'message': 'Không có quyền'}), 403
    inv = Inventory.query.get_or_404(inventory_id)
    if inv.status != 'approved_locked':
        return jsonify({'success': False, 'message': 'Chỉ đóng khi đã khóa'}), 400
    try:
        inv.status = 'closed'
        inv.closed_at = now_vn()
        inv.closed_by_id = session.get('user_id')
        log_inventory_action(inv.id, 'close', session.get('user_id'), from_status='approved_locked', to_status='closed')
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/assets/inventory', methods=['GET', 'POST'])
@login_required
def asset_inventory():
    """Kiểm kê tài sản"""
    from utils.voucher import generate_inventory_code as gen_inv_code
    from datetime import datetime
    import json as _json

    allowed_manage_roles = ['admin', 'manager', 'accountant']
    allowed_input_roles = ['admin', 'manager', 'accountant', 'inventory_leader', 'inventory_member']

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create_inventory':
            if session.get('role') not in allowed_manage_roles:
                flash('Bạn không có quyền tạo đợt kiểm kê.', 'error')
                return redirect(url_for('asset_inventory'))
            # Tạo đợt kiểm kê mới
            try:
                name = request.form.get('inventory_name', '').strip()
                if not name:
                    flash('Vui lòng nhập tên đợt kiểm kê.', 'error')
                    return redirect(url_for('asset_inventory'))

                # Thời điểm kiểm kê (ngày) – lấy từ start_date nếu không nhập riêng
                inventory_time_str = request.form.get('inventory_time') or request.form.get('start_date')
                if not inventory_time_str:
                    flash('Vui lòng chọn thời điểm kiểm kê.', 'error')
                    return redirect(url_for('asset_inventory'))

                inventory_time = parse_iso_datetime(inventory_time_str)
                if not inventory_time:
                    flash('Định dạng thời điểm kiểm kê không hợp lệ.', 'error')
                    return redirect(url_for('asset_inventory'))

                inventory = Inventory(
                    inventory_code=inventory_code,
                    inventory_name=name,
                    inventory_time=inventory_time,
                    start_date=parse_iso_date(request.form.get('start_date')),
                    end_date=parse_iso_date(request.form.get('end_date')),
                    inventory_type=request.form.get('inventory_type') or 'periodic',
                    scope_type=scope_type,
                    scope=scope_text,
                    scope_locations=json.dumps(scope_locations) if scope_locations else None,
                    scope_asset_groups=json.dumps(scope_asset_groups) if scope_asset_groups else None,
                    decision_number=request.form.get('decision_number') or None,
                    decision_date=parse_iso_date(request.form.get('decision_date')),
                    decision_file_path=decision_file_path,
                    status='draft',
                    created_by_id=session.get('user_id')
                )
                db.session.add(inventory)
                db.session.flush()  # cần flush để có inventory.id cho log
                log_inventory_action(inventory.id, 'create_batch', session.get('user_id'))
                db.session.commit()
                flash(f'Đã tạo đợt kiểm kê: {inventory_code}', 'success')
                return redirect(url_for('asset_inventory', inventory_id=inventory.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi khi tạo đợt kiểm kê: {str(e)}', 'error')
        
        elif action == 'create_team':
            if session.get('role') not in allowed_manage_roles:
                flash('Bạn không có quyền tạo tổ.', 'error')
                return redirect(url_for('asset_inventory', inventory_id=request.form.get('inventory_id')))
            try:
                inventory_id = int(request.form.get('inventory_id'))
                inventory = Inventory.query.get_or_404(inventory_id)
                if inventory.status not in ['draft', 'in_progress']:
                    flash('Chỉ tạo tổ khi đợt đang mở.', 'error')
                    return redirect(url_for('asset_inventory', inventory_id=inventory_id))
                team_name = request.form.get('team_name', '').strip()
                leader_id = request.form.get('leader_id', type=int)
                if not team_name or not leader_id:
                    flash('Vui lòng nhập tên tổ và chọn trưởng tổ.', 'error')
                    return redirect(url_for('asset_inventory', inventory_id=inventory_id))
                team = InventoryTeam(inventory_id=inventory_id, name=team_name, leader_id=leader_id)
                db.session.add(team)
                db.session.flush()
                log_inventory_action(inventory_id, 'assign_team', session.get('user_id'),
                                     payload=_json.dumps({'team_id': team.id, 'name': team_name, 'leader_id': leader_id}))
                db.session.commit()
                flash('Đã tạo tổ kiểm kê.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi khi tạo tổ: {str(e)}', 'error')
            return redirect(url_for('asset_inventory', inventory_id=inventory_id))

        elif action == 'add_member':
            if session.get('role') not in allowed_manage_roles:
                flash('Bạn không có quyền chỉnh sửa tổ.', 'error')
                return redirect(url_for('asset_inventory', inventory_id=request.form.get('inventory_id')))
            try:
                inventory_id = int(request.form.get('inventory_id'))
                team_id = int(request.form.get('team_id'))
                user_id = int(request.form.get('member_id'))
                member_role = request.form.get('member_role') or 'member'
                team = InventoryTeam.query.get_or_404(team_id)
                if team.inventory_id != inventory_id:
                    flash('Tổ không thuộc đợt này.', 'error')
                    return redirect(url_for('asset_inventory', inventory_id=inventory_id))
                if team.inventory.status not in ['draft', 'in_progress']:
                    flash('Đợt đã khóa, không thể sửa thành viên.', 'error')
                    return redirect(url_for('asset_inventory', inventory_id=inventory_id))
                exists = InventoryTeamMember.query.filter_by(team_id=team_id, user_id=user_id).first()
                if exists:
                    flash('Thành viên đã có trong tổ.', 'warning')
                    return redirect(url_for('asset_inventory', inventory_id=inventory_id))
                m = InventoryTeamMember(team_id=team_id, user_id=user_id, role=member_role)
                db.session.add(m)
                db.session.flush()
                log_inventory_action(inventory_id, 'assign_team', session.get('user_id'),
                                     payload=_json.dumps({'team_id': team_id, 'member_id': user_id, 'role': member_role}))
                db.session.commit()
                flash('Đã thêm thành viên vào tổ.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi khi thêm thành viên: {str(e)}', 'error')
            return redirect(url_for('asset_inventory', inventory_id=request.form.get('inventory_id')))

        elif action == 'remove_member':
            if session.get('role') not in allowed_manage_roles:
                flash('Bạn không có quyền chỉnh sửa tổ.', 'error')
                return redirect(url_for('asset_inventory', inventory_id=request.form.get('inventory_id')))
            try:
                inventory_id = int(request.form.get('inventory_id'))
                team_id = int(request.form.get('team_id'))
                member_id = int(request.form.get('member_id'))
                team = InventoryTeam.query.get_or_404(team_id)
                if team.inventory_id != inventory_id or team.inventory.status not in ['draft', 'in_progress']:
                    flash('Không được phép xóa thành viên.', 'error')
                    return redirect(url_for('asset_inventory', inventory_id=inventory_id))
                InventoryTeamMember.query.filter_by(team_id=team_id, user_id=member_id).delete()
                log_inventory_action(inventory_id, 'assign_team', session.get('user_id'),
                                     payload=_json.dumps({'team_id': team_id, 'remove_member_id': member_id}))
                db.session.commit()
                flash('Đã xóa thành viên.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi khi xóa thành viên: {str(e)}', 'error')
            return redirect(url_for('asset_inventory', inventory_id=request.form.get('inventory_id')))

        elif action == 'delete_team':
            if session.get('role') not in allowed_manage_roles:
                flash('Bạn không có quyền xóa tổ.', 'error')
                return redirect(url_for('asset_inventory', inventory_id=request.form.get('inventory_id')))
            try:
                inventory_id = int(request.form.get('inventory_id'))
                team_id = int(request.form.get('team_id'))
                team = InventoryTeam.query.get_or_404(team_id)
                if team.inventory_id != inventory_id or team.inventory.status not in ['draft', 'in_progress']:
                    flash('Không được phép xóa tổ.', 'error')
                    return redirect(url_for('asset_inventory', inventory_id=inventory_id))
                db.session.delete(team)
                db.session.flush()
                log_inventory_action(inventory_id, 'assign_team', session.get('user_id'),
                                     payload=_json.dumps({'delete_team_id': team_id}))
                db.session.commit()
                flash('Đã xóa tổ kiểm kê.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi khi xóa tổ: {str(e)}', 'error')
            return redirect(url_for('asset_inventory', inventory_id=request.form.get('inventory_id')))

        elif action == 'save_results':
            if session.get('role') not in allowed_input_roles:
                flash('Bạn không có quyền nhập kết quả kiểm kê.', 'error')
                return redirect(url_for('asset_inventory', inventory_id=request.form.get('inventory_id')))
            # Lưu kết quả kiểm kê
            try:
                inventory_id = int(request.form.get('inventory_id'))
                inventory = Inventory.query.get_or_404(inventory_id)
                
                asset_ids = request.form.getlist('asset_ids')
                for asset_id in asset_ids:
                    asset = Asset.query.get(asset_id)
                    if not asset:
                        continue
                    
                    actual_condition = request.form.get(f'condition_{asset_id}')
                    actual_quantity = request.form.get(f'quantity_{asset_id}', type=int)
                    actual_value = request.form.get(f'value_{asset_id}', type=float)
                    notes = request.form.get(f'notes_{asset_id}', '')
                    actual_serial = request.form.get(f'serial_{asset_id}', '').strip()
                    
                    # Tính chênh lệch
                    book_value = asset.price or 0
                    difference = (actual_value or book_value) - book_value
                    
                    # Kiểm tra đã có kết quả chưa
                    existing = InventoryResult.query.filter(
                        InventoryResult.inventory_id == inventory_id,
                        InventoryResult.asset_id == asset_id
                    ).first()
                    
                    if existing:
                        existing.actual_condition = actual_condition
                        existing.actual_status = actual_condition
                        existing.actual_quantity = actual_quantity
                        existing.actual_value = actual_value
                        existing.difference = difference
                        existing.notes = notes
                        existing.actual_serial_plate = actual_serial if actual_serial else None
                        existing.checked_by_id = session.get('user_id')
                        existing.checked_at = now_vn()
                    else:
                        result = InventoryResult(
                            inventory_id=inventory_id,
                            asset_id=asset_id,
                            book_quantity=getattr(asset, 'quantity', 1) or 1,
                            book_value=book_value,
                            actual_condition=actual_condition,
                            actual_status=actual_condition,
                            actual_quantity=actual_quantity,
                            actual_value=actual_value,
                            difference=difference,
                            notes=notes,
                            actual_serial_plate=actual_serial if actual_serial else None,
                            checked_by_id=session.get('user_id'),
                            checked_at=now_vn()
                        )
                        db.session.add(result)
                        existing = result
                    
                    # Lưu ảnh minh chứng nếu có
                    photo_files = request.files.getlist(f'photos_{asset_id}')
                    if photo_files:
                        upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'inventory_photos')
                        os.makedirs(upload_dir, exist_ok=True)
                        for pf in photo_files:
                            if not pf or not pf.filename:
                                continue
                            fname = secure_filename(pf.filename)
                            save_path = os.path.join(upload_dir, fname)
                            pf.save(save_path)
                            rel_path = os.path.relpath(save_path, app.root_path).replace('\\', '/')
                            db.session.add(InventoryLinePhoto(inventory_result_id=existing.id, file_path=rel_path, uploaded_by_id=session.get('user_id')))
                
                if inventory.status == 'draft':
                    inventory.status = 'in_progress'
                db.session.commit()
                flash('Đã lưu kết quả kiểm kê.', 'success')
                return redirect(url_for('asset_inventory', inventory_id=inventory_id))
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi khi lưu kết quả: {str(e)}', 'error')
    
    inventory_id = request.args.get('inventory_id', type=int)
    inventories = Inventory.query.order_by(Inventory.created_at.desc()).limit(10).all()
    
    if inventory_id:
        inventory = Inventory.query.get_or_404(inventory_id)
        page = request.args.get('page', 1, type=int)
        per_page = 10
        assets_paginate = Asset.query.filter(Asset.deleted_at.is_(None)).order_by(Asset.id).paginate(
            page=page, per_page=per_page, error_out=False
        )
        assets = assets_paginate.items
        results = InventoryResult.query.filter_by(inventory_id=inventory_id).all()
        teams = InventoryTeam.query.filter_by(inventory_id=inventory_id).all()
        users = User.query.filter(User.deleted_at.is_(None)).all()
        return render_template('assets/inventory.html', 
                             inventory=inventory,
                             inventories=inventories,
                             results=results,
                             assets=assets,
                             assets_paginate=assets_paginate,
                             teams=teams,
                             users=users)
    
    assets = Asset.query.filter(Asset.deleted_at.is_(None)).all()
    return render_template('assets/inventory.html', 
                         inventories=inventories,
                         assets=assets)

@app.route('/asset-types')
@login_required
def asset_types():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = AssetType.query.filter(AssetType.deleted_at.is_(None))
    
    if search:
        # Use case-insensitive search compatible with both SQLite and PostgreSQL
        search_lower = f'%{search.lower()}%'
        query = query.filter(db.func.lower(AssetType.name).like(search_lower))
    
    asset_types = query.paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('asset_types/list.html', 
                         asset_types=asset_types, 
                         search=search)


@app.route('/asset-types/suggest')
@login_required
def asset_types_suggest():
    """
    Gợi ý nhanh tên loại tài sản (autocomplete cho ô tìm kiếm loại tài sản).
    """
    term = request.args.get('term', '', type=str) or ''
    term = term.strip()
    if len(term) < 2:
        return jsonify([])

    search_lower = f"%{term.lower()}%"
    query = AssetType.query.filter(
        AssetType.deleted_at.is_(None),
        db.func.lower(AssetType.name).like(search_lower)
    ).order_by(AssetType.created_at.desc()).limit(10)

    results = [{
        "id": t.id,
        "label": t.name,
        "name": t.name
    } for t in query]
    return jsonify(results)

@app.route('/asset-types/add', methods=['POST'])
@manager_required
def add_asset_type():
    try:
        name = request.form['name']
        description = request.form.get('description', '')
        
        # Kiểm tra tên đã tồn tại
        existing = AssetType.query.filter(AssetType.name == name, AssetType.deleted_at.is_(None)).first()
        if existing:
            return jsonify({'success': False, 'message': 'Tên loại tài sản đã tồn tại!'})
        
        asset_type = AssetType(name=name, description=description)
        db.session.add(asset_type)
        db.session.commit()
        try:
            uid = session.get('user_id')
            if uid:
                db.session.add(AuditLog(user_id=uid, module='asset_types', action='create', entity_id=asset_type.id, details=f"name={name}"))
                db.session.commit()
        except Exception:
            db.session.rollback()
        
        return jsonify({
            'success': True, 
            'message': 'Loại tài sản đã được thêm thành công!',
            'data': {
                'id': asset_type.id,
                'name': asset_type.name,
                'description': asset_type.description,
                'created_at': asset_type.created_at.strftime('%d/%m/%Y %H:%M')
            }
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/asset-types/edit/<int:id>', methods=['GET', 'POST'])
@manager_required
def edit_asset_type(id):
    asset_type = AssetType.query.get_or_404(id)
    if request.method == 'GET':
        return render_template('asset_types/edit.html', asset_type=asset_type)
    try:
        name = request.form['name']
        description = request.form.get('description', '')
        # Kiểm tra tên đã tồn tại (trừ chính nó)
        existing = AssetType.query.filter(
            AssetType.name == name,
            AssetType.id != id,
            AssetType.deleted_at.is_(None)
        ).first()
        if existing:
            flash('Tên loại tài sản đã tồn tại!', 'error')
            return render_template('asset_types/edit.html', asset_type=asset_type)
        asset_type.name = name
        asset_type.description = description
        db.session.commit()
        try:
            uid = session.get('user_id')
            if uid:
                db.session.add(AuditLog(user_id=uid, module='asset_types', action='update', entity_id=id, details=f"name={asset_type.name}"))
                db.session.commit()
        except Exception:
            db.session.rollback()
        flash('Loại tài sản đã được cập nhật thành công!', 'success')
        return redirect(url_for('asset_types'))
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi: {str(e)}', 'error')
        return render_template('asset_types/edit.html', asset_type=asset_type)

@app.route('/asset-types/delete/<int:id>', methods=['POST'])
@manager_required
def delete_asset_type(id):
    try:
        asset_type = AssetType.query.get_or_404(id)
        
        # Kiểm tra có tài sản nào đang sử dụng loại này không
        active_assets = Asset.query.filter(
            Asset.asset_type_id == asset_type.id,
            Asset.deleted_at.is_(None)
        ).count()
        if active_assets:
            return jsonify({'success': False, 'message': 'Không thể xóa loại tài sản đang được sử dụng!'})
        
        if asset_type.deleted_at:
            return jsonify({'success': False, 'message': 'Loại tài sản đã nằm trong thùng rác!'})
        asset_type.soft_delete()
        db.session.commit()
        try:
            uid = session.get('user_id')
            if uid:
                db.session.add(AuditLog(user_id=uid, module='asset_types', action='delete', entity_id=id, details=f"name={asset_type.name}"))
                db.session.commit()
        except Exception:
            db.session.rollback()
        
        return jsonify({'success': True, 'message': 'Loại tài sản đã được xóa thành công!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/users')
@manager_required
def users():
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '', type=str)
        role_id = request.args.get('role_id', type=int)

        query = User.query.filter(User.deleted_at.is_(None))
        if search:
            search_lower = f'%{search.lower()}%'
            query = query.filter(
                (db.func.lower(User.username).like(search_lower)) |
                (db.func.lower(User.email).like(search_lower))
            )
        if role_id:
            query = query.filter(User.role_id == role_id)

        query = query.order_by(db.func.lower(User.username))
        users_pagination = query.paginate(page=page, per_page=10, error_out=False)
        roles = Role.query.all()

        # Đếm số tài sản đang gán cho từng user
        asset_counts = {}
        try:
            from models import asset_user
            asset_counts_query = db.session.query(
                asset_user.c.user_id,
                db.func.count(asset_user.c.asset_id)
            ).join(
                Asset, Asset.id == asset_user.c.asset_id
            ).filter(
                Asset.deleted_at.is_(None)
            ).group_by(asset_user.c.user_id).all()
            asset_counts = {user_id: count for user_id, count in asset_counts_query}
        except Exception as e:
            app.logger.warning(f"Could not count assets for users: {e}")

        for user in users_pagination.items:
            # Set virtual attribute safely
            user.assigned_asset_count = asset_counts.get(user.id, 0)

        return render_template(
            'users/list.html',
            users=users_pagination,
            roles=roles,
            search=search,
            role_id=role_id,
            asset_counts=asset_counts
        )
    except Exception as e:
        app.logger.error(f"Error in users route: {str(e)}")
        flash(f"Lỗi hệ thống khi tải danh sách người dùng: {str(e)}", "error")
        return redirect(url_for('index'))


@app.route('/users/suggest')
@login_required
def users_suggest():
    """
    Gợi ý nhanh người dùng theo username / email / tên (autocomplete).
    Dùng cho ô tìm kiếm người dùng và chọn người nhận bàn giao.
    """
    term = request.args.get('term', '', type=str) or ''
    term = term.strip()
    if len(term) < 2:
        return jsonify([])

    search_lower = f"%{term.lower()}%"
    query = User.query.filter(
        User.deleted_at.is_(None),
        (
            db.func.lower(User.username).like(search_lower) |
            db.func.lower(User.email).like(search_lower) |
            db.func.lower(User.name).like(search_lower)
        )
    ).limit(10)

    results = []
    for u in query:
        label = u.username
        if u.email:
            label += f" ({u.email})"
        if u.name:
            label += f" - {u.name}"
            
        results.append({
            "id": u.id,
            "label": label,
            "username": u.username,
            "email": u.email or "",
            "name": u.name or ""
        })
    return jsonify(results)

@app.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@manager_required
def edit_user(id):
    user = User.query.get_or_404(id)
    def ensure_default_roles():
        role_defs = [
            ('super_admin', 'Super Admin'),
            ('admin', 'Quản trị viên hệ thống'),
            ('manager', 'Quản lý tài sản'),
            ('accountant', 'Kế toán tài sản'),
            ('inventory_leader', 'Tổ trưởng kiểm kê'),
            ('inventory_member', 'Thành viên kiểm kê'),
            ('user', 'Người dùng thông thường'),
        ]
        existing = {r.name for r in Role.query.all()}
        for name, desc in role_defs:
            if name not in existing:
                db.session.add(Role(name=name, description=desc))
        db.session.commit()
    
    ensure_default_roles()
    
    from models import Permission, UserPermission
    from collections import defaultdict
    from sqlalchemy import inspect
    
    roles = Role.query.all()
    permissions_by_category = defaultdict(lambda: defaultdict(dict))
    permission_categories = []
    user_permissions = {}
    
    try:
        inspector = inspect(db.engine)
        if 'permission' not in inspector.get_table_names():
            db.create_all()
        
        try:
            permissions = Permission.query.order_by(Permission.category, Permission.module, Permission.action).all()
        except Exception:
            db.create_all()
            permissions = Permission.query.order_by(Permission.category, Permission.module, Permission.action).all()
            
        for perm in permissions:
            category = perm.category or 'Khác'
            module = perm.module or 'other'
            action = perm.action or 'view'
            permissions_by_category[category][module][action] = perm
        
        permission_categories = sorted(permissions_by_category.keys())
        user_permissions = {up.permission_id: up.granted for up in UserPermission.query.filter_by(user_id=user.id).all()}
    except Exception as e:
        app.logger.error(f"Error loading permissions: {str(e)}")

    if request.method == 'GET':
        return render_template('users/edit.html', user=user, roles=roles, permissions_by_category=permissions_by_category, permission_categories=permission_categories, user_permissions=user_permissions)
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        role_id_raw = request.form.get('role_id', '')
        asset_quota_raw = request.form.get('asset_quota', str(user.asset_quota or 0)).strip()
        name = request.form.get('name', '').strip()
        password = request.form.get('password')
        is_active = True if request.form.get('is_active') == 'on' else False

        # Check existing username
        if User.query.filter(User.username == username, User.id != id).first():
            flash('Tên đăng nhập đã tồn tại!', 'error')
            return redirect(url_for('edit_user', id=id))

        # Check existing email
        if User.query.filter(User.email == email, User.id != id).first():
            flash('Email đã tồn tại!', 'error')
            return redirect(url_for('edit_user', id=id))

        # Validate Email
        import re
        email_regex = r'^([\w\.-]+)@([\w\.-]+)\.([a-zA-Z]{2,})$'
        if not email or not re.match(email_regex, email):
            flash('Email không hợp lệ!', 'error')
            return redirect(url_for('edit_user', id=id))
        
        try:
            role_id = int(role_id_raw)
        except:
            flash('Vai trò không hợp lệ.', 'error')
            return redirect(url_for('edit_user', id=id))

        try:
            asset_quota = int(asset_quota_raw or 0)
            if asset_quota < 0: raise ValueError
        except ValueError:
            flash('Số tài sản phải là số nguyên không âm.', 'error')
            return redirect(url_for('edit_user', id=id))

        try:
            name = request.form.get('name', '').strip()
            user.username = username
            user.email = email
            user.name = name if name else None
            user.role_id = role_id
            user.is_active = is_active
            user.asset_quota = asset_quota
            
            # Cập nhật phân quyền (chỉ cho user không phải admin)
            from models import Permission, UserPermission
            if user.role.name != 'admin':
                # Xóa tất cả permissions cũ
                UserPermission.query.filter_by(user_id=user.id).delete()
                # Thêm permissions mới
                for key, value in request.form.items():
                    if key.startswith('permission_') and value == '1':
                        try:
                            perm_id = int(key.replace('permission_', ''))
                            user_perm = UserPermission(user_id=user.id, permission_id=perm_id, granted=True)
                            db.session.add(user_perm)
                        except (ValueError, TypeError):
                            continue
            if password:
                user.set_password(password)

            db.session.commit()
            try:
                uid = session.get('user_id')
                if uid:
                    db.session.add(AuditLog(user_id=uid, module='users', action='update', entity_id=id, details=f"username={user.username}"))
                    db.session.commit()
            except Exception:
                db.session.rollback()
            flash('Người dùng đã được cập nhật!', 'success')
            return redirect(url_for('users'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error editing user: {str(e)}")
            flash(f'Lỗi hệ thống: {str(e)}', 'error')
            return redirect(url_for('edit_user', id=id))


@app.route('/users/view/<int:id>')
@manager_required
def view_user(id):
    """Trang chi tiết người dùng"""
    user = User.query.get_or_404(id)
    assets = Asset.query.filter(
        Asset.deleted_at.is_(None),
        Asset.user_id == user.id
    ).order_by(Asset.name.asc()).all()

    transfer_history = AssetTransfer.query.filter(
        (AssetTransfer.from_user_id == user.id) | (AssetTransfer.to_user_id == user.id)
    ).order_by(AssetTransfer.created_at.desc()).limit(10).all()

    return render_template(
        'users/view.html',
        user=user,
        assets=assets,
        transfer_history=transfer_history
    )

@app.route('/users/delete/<int:id>', methods=['POST'])
@manager_required
def delete_user(id):
    try:
        user = User.query.get_or_404(id)
        if user.assets:
            flash('Không thể xóa người dùng đang sở hữu tài sản!', 'error')
            return redirect(url_for('users'))
        if user.deleted_at:
            flash('Người dùng đã nằm trong thùng rác.', 'info')
            return redirect(url_for('users'))
        user.soft_delete()
        db.session.commit()
        try:
            uid = session.get('user_id')
            if uid:
                db.session.add(AuditLog(user_id=uid, module='users', action='delete', entity_id=id, details=f"username={user.username}"))
                db.session.commit()
        except Exception:
            db.session.rollback()
        flash('Đã xóa người dùng!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi: {str(e)}', 'error')
    return redirect(url_for('users'))

@app.route('/api/permissions/list')
@manager_required
def api_permissions_list():
    """API: Lấy danh sách tất cả permissions nhóm theo category"""
    from collections import defaultdict
    from sqlalchemy import inspect
    
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'permission' not in tables:
            db.create_all()
        
        permissions = Permission.query.order_by(Permission.category, Permission.module, Permission.action).all()
        
        if not permissions:
            default_perms = Permission.get_default_permissions()
            for perm_data in default_perms:
                try:
                    existing = Permission.query.filter_by(
                        module=perm_data['module'],
                        action=perm_data['action']
                    ).first()
                    if not existing:
                        perm = Permission(
                            module=perm_data['module'],
                            action=perm_data['action'],
                            name=perm_data['name'],
                            category=perm_data['category']
                        )
                        db.session.add(perm)
                except Exception:
                    continue
            try:
                db.session.commit()
                permissions = Permission.query.order_by(Permission.category, Permission.module, Permission.action).all()
            except Exception:
                db.session.rollback()
                permissions = []
        
        # Nhóm permissions theo category và module
        permissions_by_category = defaultdict(lambda: defaultdict(dict))
        for perm in permissions:
            category = perm.category or 'Khác'
            module = perm.module or 'other'
            action = perm.action or 'view'
            permissions_by_category[category][module][action] = {
                'id': perm.id,
                'name': perm.name,
                'module': perm.module,
                'action': perm.action
            }
        
        return jsonify({
            'success': True,
            'categories': dict(permissions_by_category)
        })
    except Exception as e:
        app.logger.error(f"Error loading permissions: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/permissions/user/<int:user_id>', methods=['GET', 'POST'])
@manager_required
def api_user_permissions(user_id):
    """API: Lấy hoặc cập nhật permissions của user"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'GET':
        # Lấy permissions của user
        try:
            user_perms = UserPermission.query.filter_by(user_id=user.id, granted=True).all()
            permission_ids = [up.permission_id for up in user_perms]
            return jsonify({
                'success': True,
                'permissions': permission_ids
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        # Cập nhật permissions của user
        try:
            if user.role.name == 'admin':
                return jsonify({'success': False, 'message': 'Admin luôn có toàn quyền, không thể chỉnh sửa!'}), 400
            
            data = request.get_json()
            permission_ids = data.get('permissions', [])
            
            # Xóa tất cả permissions cũ
            UserPermission.query.filter_by(user_id=user.id).delete()
            
            # Thêm permissions mới
            for perm_id in permission_ids:
                try:
                    perm_id = int(perm_id)
                    user_perm = UserPermission(user_id=user.id, permission_id=perm_id, granted=True)
                    db.session.add(user_perm)
                except (ValueError, TypeError):
                    continue
            
            db.session.commit()
            
            # Ghi audit log
            try:
                uid = session.get('user_id')
                if uid:
                    db.session.add(AuditLog(
                        user_id=uid,
                        module='users',
                        action='update',
                        entity_id=user.id,
                        details=f"Updated permissions for user: {user.username}"
                    ))
                    db.session.commit()
            except Exception:
                db.session.rollback()
            
            return jsonify({
                'success': True,
                'message': 'Đã cập nhật phân quyền thành công!'
            })
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating permissions: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/audit-logs')
@manager_required
def audit_logs():
    page = request.args.get('page', 1, type=int)
    search_user = request.args.get('user_id', type=int)
    module = request.args.get('module', '', type=str)
    date_from = request.args.get('date_from', '', type=str)
    date_to = request.args.get('date_to', '', type=str)

    query = AuditLog.query.order_by(AuditLog.created_at.desc())
    if search_user:
        query = query.filter(AuditLog.user_id == search_user)
    if module:
        query = query.filter(AuditLog.module == module)
    try:
        if date_from:
            start = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(AuditLog.created_at >= start)
        if date_to:
            end = datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            query = query.filter(AuditLog.created_at <= end)
    except Exception:
        pass

    logs = query.paginate(page=page, per_page=10, error_out=False)
    users = User.query.filter(User.deleted_at.is_(None)).all()
    modules = ['assets', 'asset_types', 'users']
    return render_template('audit_logs/list.html', logs=logs, users=users, modules=modules,
                           search_user=search_user, module=module, date_from=date_from, date_to=date_to)

@app.route('/test-session')
@login_required
def test_session():
    return jsonify({
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'role': session.get('role')
    })

@app.route('/admin/permissions', methods=['GET', 'POST'])
@manager_required
def admin_permissions():
    """Trang quản lý phân quyền cho tất cả users"""
    from collections import defaultdict
    from sqlalchemy import inspect
    
    if request.method == 'POST':
        # Xử lý cập nhật permissions cho một user
        try:
            user_id = request.form.get('user_id')
            if not user_id:
                flash('Vui lòng chọn người dùng!', 'error')
                return redirect(url_for('admin_permissions'))
            
            user_id = int(user_id)
            user = User.query.get_or_404(user_id)
            
            # Kiểm tra nếu là admin
            if user.role.name == 'admin':
                flash('Admin luôn có toàn quyền, không thể chỉnh sửa!', 'warning')
                return redirect(url_for('admin_permissions'))
            
            # Lấy tất cả permission IDs được chọn
            permission_ids = []
            for key, value in request.form.items():
                if key.startswith('permission_') and value == '1':
                    try:
                        perm_id = int(key.replace('permission_', ''))
                        permission_ids.append(perm_id)
                    except (ValueError, TypeError):
                        continue
            
            # Xóa tất cả permissions cũ của user
            UserPermission.query.filter_by(user_id=user.id).delete()
            
            # Thêm permissions mới
            for perm_id in permission_ids:
                user_perm = UserPermission(user_id=user.id, permission_id=perm_id, granted=True)
                db.session.add(user_perm)
            
            db.session.commit()
            
            # Ghi audit log
            try:
                uid = session.get('user_id')
                if uid:
                    db.session.add(AuditLog(
                        user_id=uid,
                        module='users',
                        action='update',
                        entity_id=user.id,
                        details=f"Updated permissions for user: {user.username}"
                    ))
                    db.session.commit()
            except Exception:
                db.session.rollback()
            
            flash(f'Đã cập nhật phân quyền cho {user.username}!', 'success')
            return redirect(url_for('admin_permissions'))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi cập nhật phân quyền: {str(e)}', 'error')
            return redirect(url_for('admin_permissions'))
    
    # GET: Hiển thị bảng phân quyền
    try:
        # Kiểm tra bảng permission có tồn tại không
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'permission' not in tables:
            db.create_all()
        
        # Lấy tất cả users (trừ deleted)
        users = User.query.filter(User.deleted_at.is_(None)).order_by(User.username).all()
        
        # Lấy tất cả permissions, nhóm theo category
        try:
            permissions = Permission.query.order_by(Permission.category, Permission.module, Permission.action).all()
        except Exception:
            db.create_all()
            permissions = Permission.query.order_by(Permission.category, Permission.module, Permission.action).all()
        
        # Nếu chưa có permissions, khởi tạo
        if not permissions:
            default_perms = Permission.get_default_permissions()
            for perm_data in default_perms:
                try:
                    existing = Permission.query.filter_by(
                        module=perm_data['module'],
                        action=perm_data['action']
                    ).first()
                    if not existing:
                        perm = Permission(
                            module=perm_data['module'],
                            action=perm_data['action'],
                            name=perm_data['name'],
                            category=perm_data['category']
                        )
                        db.session.add(perm)
                except Exception:
                    continue
            try:
                db.session.commit()
                permissions = Permission.query.order_by(Permission.category, Permission.module, Permission.action).all()
            except Exception:
                db.session.rollback()
                permissions = []
        
        # Nhóm permissions theo category và module
        permissions_by_category = defaultdict(lambda: defaultdict(dict))
        for perm in permissions:
            category = perm.category or 'Khác'
            module = perm.module or 'other'
            action = perm.action or 'view'
            permissions_by_category[category][module][action] = perm
        
        # Lấy user permissions
        user_permissions_map = {}
        try:
            all_user_perms = UserPermission.query.all()
            for up in all_user_perms:
                if up.user_id not in user_permissions_map:
                    user_permissions_map[up.user_id] = set()
                if up.granted:
                    user_permissions_map[up.user_id].add(up.permission_id)
        except Exception:
            user_permissions_map = {}
        
        return render_template(
            'permissions/list.html',
            users=users,
            permissions=permissions,
            permissions_by_category=dict(permissions_by_category),
            user_permissions_map=user_permissions_map
        )
    except Exception as e:
        app.logger.error(f"Error loading permissions page: {str(e)}")
        flash(f'Lỗi khi tải trang phân quyền: {str(e)}', 'error')
        return redirect(url_for('users'))

@app.route('/users/add', methods=['GET', 'POST'])
@manager_required
def add_user():
    # đảm bảo các role mặc định luôn tồn tại để hiển thị đầy đủ lựa chọn
    def ensure_default_roles():
        role_defs = [
            ('super_admin', 'Super Admin'),
            ('admin', 'Quản trị viên hệ thống'),
            ('manager', 'Quản lý tài sản'),
            ('accountant', 'Kế toán tài sản'),
            ('inventory_leader', 'Tổ trưởng kiểm kê'),
            ('inventory_member', 'Thành viên kiểm kê'),
            ('user', 'Người dùng thông thường'),
        ]
        existing = {r.name for r in Role.query.all()}
        created = False
        for name, desc in role_defs:
            if name not in existing:
                db.session.add(Role(name=name, description=desc))
                created = True
        if created:
            db.session.commit()
    ensure_default_roles()

    from models import Permission
    from collections import defaultdict
    from sqlalchemy import inspect
    
    roles = Role.query.all()
    permissions_by_category = defaultdict(lambda: defaultdict(dict))
    permission_categories = []
    
    try:
        # Kiểm tra xem bảng permission có tồn tại không
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'permission' not in tables:
            # Tạo bảng nếu chưa có
            db.create_all()
        
        # Query permissions
        try:
            permissions = Permission.query.order_by(Permission.category, Permission.module, Permission.action).all()
        except Exception:
            # Nếu query lỗi, thử tạo lại bảng
            db.create_all()
            permissions = Permission.query.order_by(Permission.category, Permission.module, Permission.action).all()
        
        # Nếu chưa có permissions, khởi tạo
        if not permissions:
            default_perms = Permission.get_default_permissions()
            for perm_data in default_perms:
                try:
                    perm = Permission(
                        module=perm_data['module'],
                        action=perm_data['action'],
                        name=perm_data['name'],
                        category=perm_data['category']
                    )
                    db.session.add(perm)
                except Exception:
                    continue
            try:
                db.session.commit()
                permissions = Permission.query.order_by(Permission.category, Permission.module, Permission.action).all()
            except Exception:
                db.session.rollback()
                permissions = []
        
        # Nhóm permissions theo category và module
        for perm in permissions:
            if not perm:
                continue
            category = perm.category or 'Khác'
            module = perm.module or 'other'
            action = perm.action or 'view'
            permissions_by_category[category][module][action] = perm
        
        permission_categories = sorted(permissions_by_category.keys())
    except Exception as e:
        # Nếu có lỗi, vẫn cho phép tạo user nhưng không có phân quyền
        app.logger.error(f"Error loading permissions: {str(e)}")
        permissions_by_category = defaultdict(lambda: defaultdict(dict))
        permission_categories = []

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        name = request.form.get('name', '').strip()
        role_id_raw = request.form.get('role_id', '')
        asset_quota_raw = request.form.get('asset_quota', '0').strip()

        # Input storage for returning to template on error
        form_data = request.form

        # Ensure password
        if not password:
            password = 'mh123#@!'

        try:
            asset_quota = int(asset_quota_raw or 0)
            if asset_quota < 0: raise ValueError
        except ValueError:
            flash('Số tài sản phải là số nguyên không âm.', 'error')
            return render_template('users/add.html', roles=roles, permissions_by_category=permissions_by_category, permission_categories=permission_categories, form_data=form_data)

        # Validate username
        if not username:
            flash('Tên đăng nhập không được để trống.', 'error')
            return render_template('users/add.html', roles=roles, permissions_by_category=permissions_by_category, permission_categories=permission_categories, form_data=form_data)

        # Check existing username (including soft-deleted ones)
        existing_user = User.query.filter(User.username == username).first()
        if existing_user:
            if existing_user.deleted_at:
                flash(f'Tên đăng nhập "{username}" đã tồn tại trong thùng rác. Vui lòng khôi phục hoặc dùng tên khác.', 'error')
            else:
                flash(f'Tên đăng nhập "{username}" đã tồn tại.', 'error')
            return render_template('users/add.html', roles=roles, permissions_by_category=permissions_by_category, permission_categories=permission_categories, form_data=form_data)

        # Validate Email
        import re
        email_regex = r'^([\w\.-]+)@([\w\.-]+)\.([a-zA-Z]{2,})$'
        if not email or not re.match(email_regex, email):
            flash('Email không hợp lệ.', 'error')
            return render_template('users/add.html', roles=roles, permissions_by_category=permissions_by_category, permission_categories=permission_categories, form_data=form_data)

        # Check existing email
        if User.query.filter(User.email == email).first():
            flash(f'Email "{email}" đã tồn tại.', 'error')
            return render_template('users/add.html', roles=roles, permissions_by_category=permissions_by_category, permission_categories=permission_categories, form_data=form_data)

        # Validate and convert role_id
        if not role_id_raw:
            flash('Vui lòng chọn vai trò.', 'error')
            return render_template('users/add.html', roles=roles, permissions_by_category=permissions_by_category, permission_categories=permission_categories, form_data=form_data)
        
        try:
            role_id = int(role_id_raw)
        except (ValueError, TypeError):
            flash('Vai trò không hợp lệ.', 'error')
            return render_template('users/add.html', roles=roles, permissions_by_category=permissions_by_category, permission_categories=permission_categories, form_data=form_data)

        try:
            user = User(
                username=username,
                email=email,
                name=name if name else None,
                role_id=role_id,
                asset_quota=asset_quota
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            # Save permissions
            from models import Permission, UserPermission
            for key, value in request.form.items():
                if key.startswith('permission_') and value == '1':
                    try:
                        perm_id = int(key.replace('permission_', ''))
                        user_perm = UserPermission(user_id=user.id, permission_id=perm_id, granted=True)
                        db.session.add(user_perm)
                    except: continue

            db.session.commit()

            # Audit Log
            try:
                uid = session.get('user_id')
                if uid:
                    db.session.add(AuditLog(user_id=uid, module='users', action='create', entity_id=user.id, details=f"username={username}"))
                    db.session.commit()
            except: db.session.rollback()

            flash('Người dùng đã được thêm thành công!', 'success')
            return redirect(url_for('users'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating user: {str(e)}")
            flash(f'Lỗi hệ thống: {str(e)}', 'error')
            return render_template('users/add.html', roles=roles, permissions_by_category=permissions_by_category, permission_categories=permission_categories, form_data=form_data)
    
    return render_template('users/add.html', roles=roles, permissions_by_category=permissions_by_category, permission_categories=permission_categories)
@app.route('/dev/seed-sample')
@login_required
def seed_sample():
    # Optional: restrict to admin
    if session.get('role') != 'admin':
        flash('Chỉ admin mới được phép thực hiện.', 'error')
        return redirect(url_for('index'))

    # Ensure base roles
    if Role.query.count() == 0:
        roles = [
            Role(name='admin', description='Quản trị'),
            Role(name='manager', description='Quản lý'),
            Role(name='user', description='Nhân viên'),
        ]
        db.session.add_all(roles)
        db.session.commit()

    # Seed users up to at least 25
    base_users = [
        ('user', 'user', 'user{}@example.com', 3),
        ('manager', 'manager', 'manager{}@example.com', 2)
    ]
    current_users = User.query.count()
    idx = 1
    while current_users < 25 and idx <= 30:
        for prefix, pwd, email_tpl, role_id in base_users:
            if current_users >= 25:
                break
            username = f"{prefix}{idx}"
            if not User.query.filter_by(username=username).first():
                u = User(username=username, email=email_tpl.format(idx), role_id=role_id, is_active=True)
                u.set_password('mh123#@!')
                db.session.add(u)
                current_users += 1
        idx += 1
    db.session.commit()

    # Seed asset types up to at least 12
    default_types = [
        'Máy tính', 'Thiết bị văn phòng', 'Nội thất', 'Thiết bị mạng', 'Điện thoại',
        'Thiết bị điện', 'Phần mềm', 'Thiết bị an ninh', 'Dụng cụ', 'Khác'
    ]
    for name in default_types:
        if not AssetType.query.filter_by(name=name).first():
            db.session.add(AssetType(name=name, description=f'{name} - mẫu'))
    db.session.commit()

    # Seed assets up to at least 60
    import random
    types = AssetType.query.all()
    users = User.query.all()
    current_assets = Asset.query.count()
    while current_assets < 60:
        t = random.choice(types)
        owner = random.choice(users) if users else None
        a = Asset(
            name=f"TS-{current_assets+1:03d}",
            price=random.randint(500_000, 50_000_000),
            quantity=random.randint(1, 10),
            asset_type_id=t.id,
            user_id=owner.id if owner else None,
            status=random.choice(['active', 'maintenance', 'disposed'])
        )
        db.session.add(a)
        current_assets += 1
    db.session.commit()

    flash('Đã thêm dữ liệu mẫu cho phân trang.', 'success')
    return redirect(url_for('index'))

# Thông tin cá nhân
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Trang thông tin cá nhân - cho phép user xem và chỉnh sửa thông tin của chính mình"""
    user = User.query.get_or_404(session.get('user_id'))
    
    if request.method == 'POST':
        try:
            # Chỉ cho phép cập nhật email, không cho đổi username
            new_email = request.form.get('email', '').strip()
            
            # Validate email
            import re
            email_regex = r'^([\w\.-]+)@([\w\.-]+)\.([a-zA-Z]{2,})$'
            if not re.match(email_regex, new_email):
                flash('Email không hợp lệ!', 'error')
                return render_template('profile/view.html', user=user)
            
            # Kiểm tra email đã tồn tại chưa (trừ chính user này)
            existing_user = User.query.filter(
                User.email == new_email,
                User.id != user.id,
                User.deleted_at.is_(None)
            ).first()
            if existing_user:
                flash('Email đã được sử dụng bởi người dùng khác!', 'error')
                return render_template('profile/view.html', user=user)
            
            # Cập nhật email
            user.email = new_email
            db.session.commit()
            
            try:
                uid = session.get('user_id')
                if uid:
                    db.session.add(AuditLog(user_id=uid, module='profile', action='update', entity_id=user.id, details=f"email={new_email}"))
                    db.session.commit()
            except Exception:
                db.session.rollback()
            
            flash('Đã cập nhật thông tin cá nhân thành công!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi: {str(e)}', 'error')
    
    # Lấy danh sách tài sản của user (bao gồm cả tài sản được gán qua assigned_users)
    # 1. Tài sản có user_id == user.id (người sở hữu) - không bao gồm disposed
    assets_owned = Asset.query.filter(
        Asset.user_id == user.id,
        Asset.deleted_at.is_(None),
        Asset.status != 'disposed'  # Loại bỏ tài sản đã thanh lý
    ).all()
    
    # 2. Tài sản được gán qua bảng asset_user (assigned_users) - không bao gồm disposed
    assets_assigned = Asset.query.join(
        asset_user, Asset.id == asset_user.c.asset_id
    ).filter(
        asset_user.c.user_id == user.id,
        Asset.deleted_at.is_(None),
        Asset.status != 'disposed'  # Loại bỏ tài sản đã thanh lý
    ).all()
    
    # Gộp và loại bỏ trùng lặp (dùng set với id)
    all_asset_ids = set()
    all_assets = []
    for asset in assets_owned + assets_assigned:
        if asset.id not in all_asset_ids:
            all_asset_ids.add(asset.id)
            all_assets.append(asset)
    
    # Sắp xếp theo tên
    assets = sorted(all_assets, key=lambda x: (x.name or '').lower())
    asset_count = len(assets)

    # Phân trang tài sản cá nhân
    per_page = 10
    requested_page = request.args.get('page', 1, type=int)
    total_pages = (asset_count + per_page - 1) // per_page if asset_count else 0
    asset_page = max(1, min(requested_page, total_pages or 1))
    start_idx = (asset_page - 1) * per_page
    end_idx = start_idx + per_page
    assets_paginated = assets[start_idx:end_idx]
    display_start = start_idx + 1 if asset_count else 0
    display_end = end_idx if end_idx < asset_count else asset_count
    
    # Tính số lượng bảo trì cho tất cả tài sản của user
    if all_asset_ids:
        maintenance_count = MaintenanceRecord.query.join(Asset).filter(
            Asset.id.in_(list(all_asset_ids)),
            Asset.deleted_at.is_(None),
            MaintenanceRecord.deleted_at.is_(None)
        ).count()
    else:
        maintenance_count = 0
    
    return render_template(
        'profile/view.html',
        user=user,
        assets=assets_paginated,
        asset_count=asset_count,
        maintenance_count=maintenance_count,
        asset_page=asset_page,
        asset_total_pages=total_pages,
        asset_per_page=per_page,
        asset_display_start=display_start,
        asset_display_end=display_end
    )

# Cài đặt
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Trang cài đặt - đổi mật khẩu, ngôn ngữ, theme"""
    user = User.query.get_or_404(session.get('user_id'))
    
    if request.method == 'POST':
        action = request.form.get('action', '')
        
        if action == 'change_password':
            # Đổi mật khẩu
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Validate
            if not current_password or not new_password or not confirm_password:
                flash('Vui lòng điền đầy đủ thông tin!', 'error')
                return redirect(url_for('settings'))
            
            if not user.check_password(current_password):
                flash('Mật khẩu hiện tại không đúng!', 'error')
                return redirect(url_for('settings'))
            
            if len(new_password) < 6:
                flash('Mật khẩu mới phải có ít nhất 6 ký tự!', 'error')
                return redirect(url_for('settings'))
            
            if new_password != confirm_password:
                flash('Mật khẩu mới và xác nhận không khớp!', 'error')
                return redirect(url_for('settings'))
            
            # Cập nhật mật khẩu
            user.set_password(new_password)
            db.session.commit()
            
            try:
                uid = session.get('user_id')
                if uid:
                    db.session.add(AuditLog(user_id=uid, module='settings', action='change_password', entity_id=user.id, details='Password changed'))
                    db.session.commit()
            except Exception:
                db.session.rollback()
            
            flash('Đã đổi mật khẩu thành công!', 'success')
            return redirect(url_for('settings'))
        
        elif action == 'change_language':
            # Đổi ngôn ngữ
            lang = request.form.get('language', 'vi')
            if lang in ['vi', 'en']:
                session['lang'] = lang
                flash('Đã thay đổi ngôn ngữ!', 'success')
            return redirect(url_for('settings'))
        
    
    # Lấy ngôn ngữ hiện tại
    current_lang = session.get('lang', 'vi')
    
    return render_template('settings/view.html', user=user, current_lang=current_lang)

@app.route('/settings/system-config', methods=['GET', 'POST'])
@login_required
@manager_required
def system_config():
    """Cấu hình hệ thống - thương hiệu, logo, tiêu đề"""
    if request.method == 'POST':
        try:
            # Lấy dữ liệu từ form
            org_name = request.form.get('org_name', '').strip()
            browser_title = request.form.get('browser_title', '').strip()
            
            # Lưu cấu hình
            SystemSetting.set_setting('org_name', org_name, 'Tên đơn vị / Tổ chức')
            SystemSetting.set_setting('browser_title', browser_title, 'Tiêu đề trình duyệt')
            
            # Xử lý upload logo
            if 'logo' in request.files:
                logo_file = request.files['logo']
                if logo_file and logo_file.filename:
                    # Kiểm tra định dạng file
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'svg', 'gif'}
                    filename = secure_filename(logo_file.filename)
                    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                    
                    if file_ext not in allowed_extensions:
                        flash('Chỉ chấp nhận file PNG, JPG, SVG, GIF!', 'error')
                        return redirect(url_for('system_config'))
                    
                    # Kiểm tra kích thước (2MB)
                    logo_file.seek(0, os.SEEK_END)
                    file_size = logo_file.tell()
                    logo_file.seek(0)
                    
                    if file_size > 2 * 1024 * 1024:  # 2MB
                        flash('File logo không được vượt quá 2MB!', 'error')
                        return redirect(url_for('system_config'))
                    
                    # Lưu file
                    logo_filename = f'logo_{int(now_vn().timestamp())}.{file_ext}'
                    logo_path = os.path.join(app.config['UPLOAD_FOLDER'], 'logos')
                    os.makedirs(logo_path, exist_ok=True)
                    
                    filepath = os.path.join(logo_path, logo_filename)
                    logo_file.save(filepath)
                    
                    # Lưu đường dẫn logo (relative to uploads folder)
                    logo_url = f'logos/{logo_filename}'
                    SystemSetting.set_setting('logo_path', logo_url, 'Đường dẫn logo hệ thống')
            
            flash('Đã lưu cấu hình hệ thống thành công!', 'success')
            return redirect(url_for('system_config'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error saving system config: {str(e)}")
            flash(f'Lỗi khi lưu cấu hình: {str(e)}', 'error')
    
    # GET: Hiển thị form
    org_name = SystemSetting.get_setting('org_name', '')
    browser_title = SystemSetting.get_setting('browser_title', 'Quản lý tài sản công')
    logo_path_setting = SystemSetting.get_setting('logo_path', '')
    
    if logo_path_setting:
        logo_path = url_for('uploaded_file', filename=logo_path_setting)
    else:
        logo_path = url_for('static', filename='img/logo.png')
    
    return render_template('settings/system_config.html', 
                         org_name=org_name,
                         browser_title=browser_title,
                         logo_path=logo_path)

@app.route('/dev/seed-maintenance')
@login_required
def seed_maintenance():
    if session.get('role') != 'admin':
        flash('Chỉ admin mới được phép thực hiện.', 'error')
        return redirect(url_for('maintenance_list'))
    import random
    from datetime import timedelta
    assets = Asset.query.limit(20).all()
    if not assets:
        flash('Chưa có tài sản để tạo bảo trì mẫu.', 'error')
        return redirect(url_for('maintenance_list'))
    created = 0
    today = today_vn()
    for i in range(10):
        a = random.choice(assets)
        days_ago = random.randint(0, 180)
        mdate = today - timedelta(days=days_ago)
        next_due = mdate + timedelta(days=random.choice([30,60,90]))
        rec = MaintenanceRecord(
            asset_id=a.id,
            maintenance_date=mdate,
            type=random.choice(['maintenance','repair','inspection']),
            description=f'Bảo trì mẫu #{i+1} cho {a.name}',
            vendor=random.choice(['FPT Services','Viettel','NCC A','NCC B']),
            person_in_charge=random.choice(['Admin','Kỹ thuật 1','Kỹ thuật 2']),
            cost=random.randint(100_000, 5_000_000),
            next_due_date=next_due,
            status='completed'
        )
        db.session.add(rec)
        created += 1
    db.session.commit()
    flash(f'Đã tạo {created} bản ghi bảo trì mẫu.', 'success')
    return redirect(url_for('maintenance_list'))

# ==================== ASSET TRANSFER (BÀN GIAO TÀI SẢN) ====================

def generate_transfer_token():
    """Tạo token ngẫu nhiên cho xác nhận bàn giao"""
    return secrets.token_urlsafe(32)

def generate_transfer_code(seq_number: int) -> str:
    """Tạo mã bàn giao tăng dần, bắt đầu từ 1.

    Format đơn giản: BG + số thứ tự (không padding),
    ví dụ: BG1, BG2, BG3...
    """
    return f"BG{seq_number}"

def send_transfer_email(transfer):
    """Gửi email xác nhận bàn giao nếu cấu hình cho phép."""
    if not app.config.get('EMAIL_ENABLED'):
        message = 'Chức năng email chưa được bật trong cấu hình.'
        app.logger.info(f"{message} Bỏ qua gửi email cho {transfer.transfer_code}.")
        return False, message
    
    if not transfer.to_user or not transfer.to_user.email:
        message = 'Không tìm thấy email hợp lệ của người nhận.'
        app.logger.warning(f"{message} transfer_id={transfer.id}")
        return False, message
    
    # Tạo link xác nhận tuyệt đối
    try:
        confirm_url = url_for('transfer_confirm', token=transfer.confirmation_token, _external=True)
    except RuntimeError:
        base_url = app.config.get('APP_URL', '').rstrip('/')
        confirm_path = f"/transfer/confirm/{transfer.confirmation_token}"
        confirm_url = f"{base_url}{confirm_path}" if base_url else confirm_path
    
    subject = f"[QLTS] Xác nhận bàn giao {transfer.transfer_code}"
    body_text = (
        f"Xin chào {transfer.to_user.username},\n\n"
        f"Bạn có một bàn giao tài sản cần xác nhận:\n"
        f"- Mã bàn giao: {transfer.transfer_code}\n"
        f"- Tài sản: {transfer.asset.name if transfer.asset else 'N/A'}\n"
        f"- Số lượng: {transfer.expected_quantity}\n"
        f"- Người bàn giao: {transfer.from_user.username if transfer.from_user else 'N/A'}\n\n"
        f"Vui lòng xác nhận tại: {confirm_url}\n\n"
        "Trân trọng,\nHệ thống Quản lý tài sản"
    )
    body_html = (
        f"<p>Xin chào <strong>{transfer.to_user.username}</strong>,</p>"
        f"<p>Bạn có một bàn giao tài sản cần xác nhận:</p>"
        f"<ul>"
        f"<li><strong>Mã bàn giao:</strong> {transfer.transfer_code}</li>"
        f"<li><strong>Tài sản:</strong> {transfer.asset.name if transfer.asset else 'N/A'}</li>"
        f"<li><strong>Số lượng:</strong> {transfer.expected_quantity}</li>"
        f"<li><strong>Người bàn giao:</strong> {transfer.from_user.username if transfer.from_user else 'N/A'}</li>"
        f"</ul>"
        f"<p>Vui lòng nhấn vào liên kết sau để xác nhận: "
        f"<a href=\"{confirm_url}\">{confirm_url}</a></p>"
        f"<p>Trân trọng,<br>Hệ thống Quản lý tài sản</p>"
    )
    
    success, message = send_email_from_config(
        to_emails=[transfer.to_user.email],
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        config=app.config
    )
    
    if success:
        app.logger.info(f"Đã gửi email xác nhận bàn giao {transfer.transfer_code} tới {transfer.to_user.email}.")
    else:
        app.logger.error(f"Gửi email bàn giao {transfer.transfer_code} thất bại: {message}")
    return success, message

@app.route('/transfer/create', methods=['GET', 'POST'])
@login_required
def transfer_create():
    """Tạo yêu cầu bàn giao tài sản"""
    if request.method == 'POST':
        try:
            asset_id = int(request.form.get('asset_id'))
            to_user_id = int(request.form.get('to_user_id'))
            quantity = int(request.form.get('quantity', 1))
            notes = request.form.get('notes', '')
            send_email_requested = request.form.get('send_email') == '1'
            
            # Validate
            asset = Asset.query.get_or_404(asset_id)
            to_user = User.query.get_or_404(to_user_id)
            from_user = User.query.get(session.get('user_id'))
            
            if not from_user:
                flash('Không tìm thấy thông tin người bàn giao!', 'error')
                return redirect(url_for('transfer_create'))
            
            # Kiểm tra phân quyền: User chỉ có thể bàn giao cho admin, không thể bàn giao cho user khác
            # Lấy role thực tế của from_user từ database để đảm bảo chính xác (không dựa vào session)
            from_user_role = Role.query.get(from_user.role_id)
            to_user_role = Role.query.get(to_user.role_id)
            admin_role = Role.query.filter_by(name='admin').first()
            
            # Debug logging
            app.logger.info(f"Transfer validation: from_user={from_user.username}, from_user_role_id={from_user.role_id}, from_user_role_name={from_user_role.name if from_user_role else None}, to_user={to_user.username}, to_user_role_id={to_user.role_id}, to_user_role_name={to_user_role.name if to_user_role else None}")
            
            # Kiểm tra: Nếu người bàn giao là user, chỉ có thể bàn giao cho admin
            if from_user_role and from_user_role.name.lower() == 'user':
                # User chỉ có thể bàn giao cho admin
                if not admin_role:
                    app.logger.error("Admin role not found in database!")
                    flash('Lỗi hệ thống: Không tìm thấy role Admin.', 'error')
                    db.session.rollback()
                    return redirect(url_for('transfer_create'))
                
                # Kiểm tra người nhận có phải admin không
                if to_user.role_id != admin_role.id:
                    # Nếu người nhận là user khác (không phải admin)
                    app.logger.warning(f"BLOCKED: User {from_user.username} (role: {from_user_role.name}) attempted to transfer to {to_user.username} (role: {to_user_role.name if to_user_role else 'unknown'})")
                    flash('Bạn không có quyền bàn giao tài sản. User chỉ có thể bàn giao cho Admin.', 'error')
                    db.session.rollback()
                    return redirect(url_for('transfer_create'))
                
                # Nếu đến đây, người nhận là admin - cho phép
                app.logger.info(f"ALLOWED: User {from_user.username} transferring to admin {to_user.username}")
            
            if quantity <= 0:
                flash('Số lượng phải lớn hơn 0!', 'error')
                return redirect(url_for('transfer_create'))
            
            if quantity > asset.quantity:
                flash(f'Số lượng bàn giao ({quantity}) không được vượt quá số lượng hiện có ({asset.quantity})!', 'error')
                return redirect(url_for('transfer_create'))
            
            # Tạo bàn giao (mã bàn giao tăng dần theo ID)
            token = generate_transfer_token()
            token_expires = now_vn() + timedelta(days=7)
            
            transfer = AssetTransfer(
                transfer_code='',  # sẽ cập nhật sau khi có ID
                from_user_id=from_user.id,
                to_user_id=to_user_id,
                asset_id=asset_id,
                quantity=quantity,
                expected_quantity=quantity,
                notes=notes,
                confirmation_token=token,
                token_expires_at=token_expires
            )
            
            db.session.add(transfer)
            # Flush để lấy ID tự tăng, sau đó sinh mã bàn giao dạng BG<ID>
            db.session.flush()
            transfer.transfer_code = generate_transfer_code(transfer.id)
            transfer_code = transfer.transfer_code
            db.session.commit()
            
            email_success = False
            email_message = ''
            if send_email_requested:
                email_success, email_message = send_transfer_email(transfer)
            
            success_message = (
                f'✅ Đã tạo yêu cầu bàn giao {transfer_code}. Sao chép link xác nhận trong danh sách bàn giao và gửi cho {to_user.username}.'
            )
            if send_email_requested and email_success:
                success_message += f' Email xác nhận đã được gửi tới {to_user.email}.'
            flash(success_message, 'success')
            
            if send_email_requested and not email_success:
                flash(f'Không thể gửi email tự động: {email_message}', 'warning')
            
            app.logger.info(f"Bàn giao {transfer_code} tạo thành công. Email tự động: {'đã gửi' if email_success else 'không gửi'}.")
            
            # Ghi audit log
            try:
                uid = session.get('user_id')
                if uid:
                    db.session.add(AuditLog(user_id=uid, module='transfer', action='create', entity_id=transfer.id, details=f"transfer_code={transfer_code}"))
                    db.session.commit()
            except Exception:
                db.session.rollback()
            
            return redirect(url_for('transfer_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi: {str(e)}', 'error')
            return redirect(url_for('transfer_create'))
    
    # GET request
    current_user_id = session.get('user_id')
    current_role = session.get('role')
    
    # Phân quyền: User chỉ thấy tài sản mà họ đang sở hữu, Admin/Manager thấy tất cả
    if current_role == 'user':
        # User chỉ thấy tài sản mà họ đang sở hữu
        assets = Asset.query.filter(
            Asset.deleted_at.is_(None),
            Asset.status == 'active',
            Asset.user_id == current_user_id
        ).all()
    else:
        # Admin và Manager thấy tất cả tài sản
        assets = Asset.query.filter(Asset.deleted_at.is_(None), Asset.status == 'active').all()
    
    # Phân quyền: User chỉ có thể bàn giao cho admin, Admin có thể bàn giao cho tất cả
    if current_role == 'user':
        # User chỉ có thể chọn admin
        admin_role = Role.query.filter_by(name='admin').first()
        if admin_role:
            users = User.query.filter(
                User.deleted_at.is_(None), 
                User.is_active == True,
                User.role_id == admin_role.id
            ).all()
        else:
            users = []
    else:
        # Admin và Manager có thể chọn tất cả user
        users = User.query.filter(User.deleted_at.is_(None), User.is_active == True).all()
    
    return render_template('transfer/create.html', assets=assets, users=users)

@app.route('/transfer')
@login_required
def transfer_list():
    """Danh sách bàn giao tài sản"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', type=str)
    user_id = session.get('user_id')
    
    query = AssetTransfer.query
    
    # Lọc theo status
    if status:
        query = query.filter(AssetTransfer.status == status)
    
    # User chỉ thấy bàn giao của mình (bàn giao mà họ là người gửi hoặc người nhận)
    # Admin và Manager có thể xem tất cả bàn giao
    current_role = session.get('role')
    if current_role == 'user':
        # User chỉ thấy bàn giao mà họ gửi hoặc nhận
        query = query.filter(
            (AssetTransfer.from_user_id == user_id) | (AssetTransfer.to_user_id == user_id)
        )
    
    # Sắp xếp từ mới nhất đến cũ nhất theo ID (tương ứng mã BG<ID>)
    transfers = query.order_by(AssetTransfer.id.desc()).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('transfer/list.html', transfers=transfers, status=status)

@app.route('/transfer/clear-all', methods=['POST'])
@manager_required
def transfer_clear_all():
    """Xóa tất cả bản ghi bàn giao tài sản (chỉ dành cho admin/manager)"""
    try:
        count = AssetTransfer.query.count()
        if count > 0:
            AssetTransfer.query.delete()
            db.session.commit()
            
            # Ghi nhật ký
            try:
                uid = session.get('user_id')
                if uid:
                    db.session.add(AuditLog(
                        user_id=uid,
                        module='transfer',
                        action='clear_all',
                        entity_id=None,
                        details=f'cleared_all_transfers count={count}'
                    ))
                    db.session.commit()
            except Exception:
                db.session.rollback()
            
            flash(f'Đã xóa {count} bản ghi bàn giao tài sản.', 'success')
        else:
            flash('Không có bản ghi nào để xóa.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi xóa: {str(e)}', 'error')
    
    return redirect(url_for('transfer_list'))

@app.route('/transfer/send-email', methods=['GET', 'POST'])
@login_required
def transfer_send_email():
    """Chọn email từ hệ thống và gửi email xác nhận"""
    flash('Tính năng gửi email đã bị vô hiệu hóa. Vui lòng sao chép link xác nhận từ danh sách bàn giao và gửi thủ công.', 'info')
    return redirect(url_for('transfer_list'))

@app.route('/transfer/resend-email/<int:transfer_id>', methods=['POST'])
@login_required
def transfer_resend_email(transfer_id):
    """Gửi lại email xác nhận cho bàn giao tài sản"""
    flash('Chức năng gửi lại email đã bị vô hiệu hóa. Hãy chia sẻ liên kết xác nhận thủ công.', 'info')
    return redirect(url_for('transfer_list'))

@app.route('/transfer/confirm/<token>', methods=['GET', 'POST'])
def transfer_confirm(token):
    """Xác nhận bàn giao tài sản qua email link"""
    transfer = AssetTransfer.query.filter_by(confirmation_token=token).first_or_404()
    
    # Kiểm tra token hết hạn
    if not transfer.is_token_valid():
        return render_template('transfer/expired.html', transfer=transfer), 400
    
    # Kiểm tra đã xác nhận chưa
    if transfer.status == 'confirmed':
        return render_template('transfer/already_confirmed.html', transfer=transfer)
    
    if request.method == 'POST':
        try:
            confirmed_quantity = int(request.form.get('confirmed_quantity', 0))
            
            if confirmed_quantity < 0:
                flash('Số lượng không hợp lệ!', 'error')
                return render_template('transfer/confirm.html', transfer=transfer)
            
            # Cập nhật số lượng xác nhận (cộng dồn nếu đã xác nhận trước đó)
            if confirmed_quantity > transfer.confirmed_quantity:
                transfer.confirmed_quantity = confirmed_quantity
            
            # Kiểm tra xác nhận đầy đủ
            if transfer.is_fully_confirmed() and transfer.status != 'confirmed':
                transfer.status = 'confirmed'
                transfer.confirmed_at = now_vn()
                
                app.logger.info(f"Bắt đầu cập nhật tài sản cho bàn giao {transfer.transfer_code}")
                
                # Cập nhật tài sản: chuyển quyền sở hữu
                asset = transfer.asset
                if asset.quantity >= transfer.expected_quantity:
                    # Giảm số lượng từ người gửi
                    old_quantity = asset.quantity
                    asset.quantity -= transfer.expected_quantity
                    app.logger.info(f"Giảm số lượng tài sản {asset.name} từ {old_quantity} xuống {asset.quantity}")
                    
                    # Nếu số lượng còn lại = 0, có thể đánh dấu là disposed hoặc giữ nguyên
                    if asset.quantity == 0:
                        asset.status = 'disposed'
                        app.logger.info(f"Tài sản {asset.name} đã hết số lượng, đánh dấu là disposed")
                    
                    # Tìm tài sản tương tự của người nhận
                    existing_asset = Asset.query.filter(
                        Asset.name == asset.name,
                        Asset.user_id == transfer.to_user_id,
                        Asset.asset_type_id == asset.asset_type_id,
                        Asset.deleted_at.is_(None)
                    ).first()
                    
                    if existing_asset:
                        # Cập nhật số lượng nếu đã có tài sản tương tự
                        old_existing_quantity = existing_asset.quantity
                        existing_asset.quantity += transfer.expected_quantity
                        if existing_asset.notes:
                            existing_asset.notes += f"\nBàn giao từ {transfer.from_user.username} - Mã: {transfer.transfer_code} ({transfer.confirmed_at.strftime('%d/%m/%Y')})"
                        else:
                            existing_asset.notes = f"Bàn giao từ {transfer.from_user.username} - Mã: {transfer.transfer_code} ({transfer.confirmed_at.strftime('%d/%m/%Y')})"
                        app.logger.info(f"Cập nhật tài sản hiện có {existing_asset.name} từ {old_existing_quantity} lên {existing_asset.quantity}")
                    else:
                        # Tạo tài sản mới cho người nhận
                        new_asset = Asset(
                            name=asset.name,
                            price=asset.price,
                            quantity=transfer.expected_quantity,
                            asset_type_id=asset.asset_type_id,
                            user_id=transfer.to_user_id,
                            status='active',
                            purchase_date=asset.purchase_date,
                            device_code=None,  # Có thể cập nhật sau
                            notes=f"Bàn giao từ {transfer.from_user.username} - Mã: {transfer.transfer_code} ({transfer.confirmed_at.strftime('%d/%m/%Y')})"
                        )
                        db.session.add(new_asset)
                        app.logger.info(f"Tạo tài sản mới {new_asset.name} cho người nhận {transfer.to_user.username}")
                
                app.logger.info(f"✅ Đã cập nhật tài sản thành công cho bàn giao {transfer.transfer_code}")
                flash('✅ Đã xác nhận bàn giao thành công! Tài sản đã được tự động cập nhật trong hệ thống.', 'success')
            elif transfer.confirmed_quantity < transfer.expected_quantity:
                transfer.status = 'pending'
                flash(f'Đã xác nhận {transfer.confirmed_quantity}/{transfer.expected_quantity} thiết bị. Vui lòng xác nhận đầy đủ để hoàn tất bàn giao.', 'warning')
            
            db.session.commit()
            
            # Ghi audit log
            try:
                db.session.add(AuditLog(
                    user_id=transfer.to_user_id,
                    module='transfer',
                    action='confirm',
                    entity_id=transfer.id,
                    details=f"confirmed_quantity={confirmed_quantity}"
                ))
                db.session.commit()
            except Exception:
                db.session.rollback()
            
            # Nếu user đã đăng nhập, redirect về trang chính
            if session.get('user_id'):
                flash('✅ Đã xác nhận bàn giao thành công! Tài sản đã được tự động cập nhật trong hệ thống.', 'success')
                return redirect(url_for('index'))
            
            return render_template('transfer/confirmed.html', transfer=transfer)
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi: {str(e)}', 'error')
            return render_template('transfer/confirm.html', transfer=transfer)
    
    # GET request - hiển thị form xác nhận
    return render_template('transfer/confirm.html', transfer=transfer)

# Register AI Chat Route
try:
    from ai_chat_route import ai_chat
    # Register with endpoint='ai_chat' to match url_for('ai_chat')
    app.add_url_rule('/api/ai_chat', endpoint='ai_chat', view_func=login_required(ai_chat), methods=['POST'])
except ImportError as e:
    print(f"Warning: Could not import ai_chat: {e}")

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Warning: db.create_all failed: {e}")
    import os
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5000'))
    print(f"Starting server at http://{host}:{port}")
    app.run(debug=app.config.get('DEBUG', False), host=host, port=port)
