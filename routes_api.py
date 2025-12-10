"""
RESTful API Routes cho Quản lý Tài sản
Hỗ trợ JWT Authentication và Swagger Documentation
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from flask_restx import Api, Resource, fields, Namespace
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, get_jwt, create_refresh_token
)
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from models import (
    db,
    User,
    Asset,
    AssetType,
    MaintenanceRecord,
    Role,
    LegalDocument,
    AssetSource,
    AssetLocation,
    AssetLocationHistory,
    AssetUsageStatusLog,
    InventoryBatch,
    InventoryItem,
    DisposalRequest,
    AssetChangeLog,
    AssetTransfer,
)
from utils.timezone import now_vn, today_vn
from data_integrity_improvements import (
    validate_asset_data, validate_user_data, validate_maintenance_data,
    safe_db_operation, validate_status, validate_maintenance_type, validate_maintenance_status
)
import os
import pandas as pd
from io import BytesIO

# Tạo Blueprint cho API
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Tạo API object với Swagger
api = Api(
    api_bp,
    version='1.0',
    title='Quản lý Tài sản API',
    description='RESTful API cho hệ thống quản lý tài sản công ty',
    doc='/docs/'  # Swagger UI sẽ ở /api/v1/docs/
)

# JWT Manager sẽ được khởi tạo trong app.py
jwt = JWTManager()

# ========== JWT Configuration ==========
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    """Kiểm tra token có bị revoke không"""
    # Có thể implement blacklist nếu cần
    return False

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'message': 'Token đã hết hạn',
        'error': 'token_expired'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'message': 'Token không hợp lệ',
        'error': 'invalid_token'
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'message': 'Thiếu token xác thực',
        'error': 'authorization_required'
    }), 401

# ========== Namespaces ==========
auth_ns = Namespace('auth', description='Authentication operations')
assets_ns = Namespace('assets', description='Asset operations')
users_ns = Namespace('users', description='User operations')
maintenance_ns = Namespace('maintenance', description='Maintenance operations')
asset_types_ns = Namespace('asset-types', description='Asset Type operations')
legal_ns = Namespace('legal-docs', description='Hồ sơ pháp lý tài sản')
sources_ns = Namespace('asset-sources', description='Nguồn hình thành tài sản')
locations_ns = Namespace('asset-locations', description='Vị trí sử dụng tài sản')
usage_ns = Namespace('asset-usage', description='Tình trạng sử dụng tài sản')
inventory_ns = Namespace('inventory', description='Kiểm kê tài sản')
disposal_ns = Namespace('disposals', description='Thanh lý tài sản')
changelog_ns = Namespace('asset-changes', description='Lịch sử biến động tài sản')

api.add_namespace(auth_ns)
api.add_namespace(assets_ns)
api.add_namespace(users_ns)
api.add_namespace(maintenance_ns)
api.add_namespace(asset_types_ns)
api.add_namespace(legal_ns)
api.add_namespace(sources_ns)
api.add_namespace(locations_ns)
api.add_namespace(usage_ns)
api.add_namespace(inventory_ns)
api.add_namespace(disposal_ns)
api.add_namespace(changelog_ns)

# ========== Helper Functions ==========
def admin_required(f):
    """Decorator yêu cầu quyền admin"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or not user.is_active:
            return {'message': 'Người dùng không hợp lệ'}, 403
        if user.role.name != 'admin':
            return {'message': 'Yêu cầu quyền quản trị'}, 403
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Lấy user hiện tại từ JWT token"""
    user_id = get_jwt_identity()
    return User.query.get(user_id)

# ========== API Models (Schemas) ==========

# Auth Models
login_model = api.model('Login', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password')
})

token_model = api.model('Token', {
    'access_token': fields.String(description='Access token'),
    'refresh_token': fields.String(description='Refresh token'),
    'token_type': fields.String(description='Token type'),
    'expires_in': fields.Integer(description='Token expiration time in seconds')
})

# User Models
user_model = api.model('User', {
    'id': fields.Integer(description='User ID'),
    'username': fields.String(required=True, description='Username'),
    'email': fields.String(required=True, description='Email'),
    'role_id': fields.Integer(required=True, description='Role ID'),
    'is_active': fields.Boolean(description='Is active'),
    'asset_quota': fields.Integer(description='Asset quota'),
    'created_at': fields.DateTime(description='Created at'),
    'updated_at': fields.DateTime(description='Updated at')
})

user_create_model = api.model('UserCreate', {
    'username': fields.String(required=True, description='Username'),
    'email': fields.String(required=True, description='Email'),
    'password': fields.String(required=True, description='Password'),
    'role_id': fields.Integer(required=True, description='Role ID'),
    'is_active': fields.Boolean(default=True, description='Is active'),
    'asset_quota': fields.Integer(default=0, description='Asset quota')
})

user_update_model = api.model('UserUpdate', {
    'email': fields.String(description='Email'),
    'role_id': fields.Integer(description='Role ID'),
    'is_active': fields.Boolean(description='Is active'),
    'asset_quota': fields.Integer(description='Asset quota')
})

# Asset Type Models
asset_type_model = api.model('AssetType', {
    'id': fields.Integer(description='Asset Type ID'),
    'name': fields.String(required=True, description='Name'),
    'description': fields.String(description='Description'),
    'created_at': fields.DateTime(description='Created at'),
    'updated_at': fields.DateTime(description='Updated at')
})

asset_type_create_model = api.model('AssetTypeCreate', {
    'name': fields.String(required=True, description='Name'),
    'description': fields.String(description='Description')
})

# Asset Models
asset_model = api.model('Asset', {
    'id': fields.Integer(description='Asset ID'),
    'name': fields.String(required=True, description='Asset name'),
    'price': fields.Float(required=True, description='Price'),
    'quantity': fields.Integer(description='Quantity'),
    'status': fields.String(description='Status (active, maintenance, disposed)'),
    'purchase_date': fields.Date(description='Purchase date'),
    'device_code': fields.String(description='Device code'),
    'tinh_trang_danh_gia': fields.String(description='Tình trạng đánh giá'),
    'usage_status': fields.String(description='Tình trạng sử dụng'),
    'asset_type_id': fields.Integer(required=True, description='Asset Type ID'),
    'user_id': fields.Integer(description='User ID'),
    'user_text': fields.String(description='User text'),
    'notes': fields.String(description='Notes'),
    'warranty_start_date': fields.Date(description='Warranty start date'),
    'warranty_end_date': fields.Date(description='Warranty end date'),
    'warranty_period_months': fields.Integer(description='Warranty period (months)'),
    'created_at': fields.DateTime(description='Created at'),
    'updated_at': fields.DateTime(description='Updated at')
})

asset_create_model = api.model('AssetCreate', {
    'name': fields.String(required=True, description='Asset name'),
    'price': fields.Float(required=True, description='Price'),
    'quantity': fields.Integer(default=1, description='Quantity'),
    'status': fields.String(default='active', description='Status'),
    'purchase_date': fields.String(description='Purchase date (YYYY-MM-DD)'),
    'device_code': fields.String(description='Device code'),
    'tinh_trang_danh_gia': fields.String(description='Tình trạng đánh giá'),
    'usage_status': fields.String(description='Tình trạng sử dụng'),
    'asset_type_id': fields.Integer(required=True, description='Asset Type ID'),
    'user_id': fields.Integer(description='User ID'),
    'user_text': fields.String(description='User text'),
    'notes': fields.String(description='Notes'),
    'warranty_start_date': fields.String(description='Warranty start date (YYYY-MM-DD)'),
    'warranty_end_date': fields.String(description='Warranty end date (YYYY-MM-DD)'),
    'warranty_period_months': fields.Integer(description='Warranty period (months)')
})

asset_update_model = api.model('AssetUpdate', {
    'name': fields.String(description='Asset name'),
    'price': fields.Float(description='Price'),
    'quantity': fields.Integer(description='Quantity'),
    'status': fields.String(description='Status'),
    'purchase_date': fields.String(description='Purchase date (YYYY-MM-DD)'),
    'device_code': fields.String(description='Device code'),
    'tinh_trang_danh_gia': fields.String(description='Tình trạng đánh giá'),
    'usage_status': fields.String(description='Tình trạng sử dụng'),
    'asset_type_id': fields.Integer(description='Asset Type ID'),
    'user_id': fields.Integer(description='User ID'),
    'user_text': fields.String(description='User text'),
    'notes': fields.String(description='Notes'),
    'warranty_start_date': fields.String(description='Warranty start date (YYYY-MM-DD)'),
    'warranty_end_date': fields.String(description='Warranty end date (YYYY-MM-DD)'),
    'warranty_period_months': fields.Integer(description='Warranty period (months)')
})

# Legal document
legal_doc_model = api.model('LegalDocument', {
    'id': fields.Integer(description='ID'),
    'asset_id': fields.Integer(required=True, description='Asset ID'),
    'so_quyet_dinh': fields.String(description='Số quyết định'),
    'ngay_ban_hanh': fields.Date(description='Ngày ban hành'),
    'loai_van_ban': fields.String(description='Loại văn bản'),
    'co_quan_ban_hanh': fields.String(description='Cơ quan ban hành'),
    'noi_dung': fields.String(description='Nội dung'),
    'file_dinh_kem': fields.String(description='File đính kèm')
})

# Asset source
asset_source_model = api.model('AssetSource', {
    'id': fields.Integer(description='ID'),
    'asset_id': fields.Integer(required=True, description='Asset ID'),
    'nguon': fields.String(required=True, description='Nguồn hình thành'),
    'nha_cung_cap': fields.String(description='Nhà cung cấp'),
    'so_hop_dong': fields.String(description='Số hợp đồng'),
    'so_hoa_don': fields.String(description='Số hóa đơn'),
    'gia_tri': fields.Float(description='Giá trị'),
    'ghi_chu': fields.String(description='Ghi chú')
})

# Asset location
asset_location_model = api.model('AssetLocation', {
    'id': fields.Integer(description='ID'),
    'asset_id': fields.Integer(required=True, description='Asset ID'),
    'toa_nha': fields.String(description='Tòa nhà'),
    'phong_ban': fields.String(description='Phòng ban'),
    'nguoi_quan_ly_id': fields.Integer(description='Người quản lý'),
    'hieu_luc_tu': fields.Date(description='Hiệu lực từ'),
    'hieu_luc_den': fields.Date(description='Hiệu lực đến')
})

# Usage status log
usage_status_model = api.model('AssetUsageStatus', {
    'id': fields.Integer(description='ID'),
    'asset_id': fields.Integer(required=True, description='Asset ID'),
    'trang_thai': fields.String(required=True, description='Tình trạng sử dụng'),
    'ghi_chu': fields.String(description='Ghi chú')
})

# Inventory
inventory_batch_model = api.model('InventoryBatch', {
    'id': fields.Integer(description='ID'),
    'ma_dot': fields.String(required=True, description='Mã đợt'),
    'ten_dot': fields.String(required=True, description='Tên đợt'),
    'loai_kiem_ke': fields.String(description='Loại kiểm kê'),
    'pham_vi': fields.String(description='Phạm vi'),
    'so_quyet_dinh': fields.String(description='Số quyết định'),
    'trang_thai': fields.String(description='Trạng thái'),
})

inventory_item_model = api.model('InventoryItem', {
    'id': fields.Integer(description='ID'),
    'batch_id': fields.Integer(required=True, description='Inventory batch ID'),
    'asset_id': fields.Integer(required=True, description='Asset ID'),
    'so_thuc_te': fields.Integer(description='Số thực tế'),
    'so_he_thong': fields.Integer(description='Số hệ thống'),
    'chenhlech': fields.Integer(description='Chênh lệch'),
    'ghi_chu': fields.String(description='Ghi chú')
})

# Disposal
disposal_model = api.model('DisposalRequest', {
    'id': fields.Integer(description='ID'),
    'asset_id': fields.Integer(required=True, description='Asset ID'),
    'de_nghi_thanh_ly': fields.String(description='Đề nghị thanh lý'),
    'phe_duyet': fields.String(description='Phê duyệt'),
    'so_quyet_dinh': fields.String(description='Số quyết định'),
    'gia_tri_con_lai': fields.Float(description='Giá trị còn lại'),
    'gia_tri_ban': fields.Float(description='Giá trị bán'),
    'file_dinh_kem': fields.String(description='File đính kèm'),
    'trang_thai': fields.String(description='Trạng thái')
})

# Asset change log
change_log_model = api.model('AssetChangeLog', {
    'id': fields.Integer(description='ID'),
    'asset_id': fields.Integer(required=True, description='Asset ID'),
    'loai_bien_dong': fields.String(required=True, description='Loại biến động'),
    'truoc': fields.String(description='Giá trị trước'),
    'sau': fields.String(description='Giá trị sau')
})

# Maintenance Record Models
maintenance_model = api.model('MaintenanceRecord', {
    'id': fields.Integer(description='Maintenance Record ID'),
    'asset_id': fields.Integer(required=True, description='Asset ID'),
    'asset_name': fields.String(description='Asset name'),
    'asset_code': fields.String(description='Asset device code'),
    'asset_type_name': fields.String(description='Asset type name'),
    'asset_user': fields.String(description='Asset user/unit'),
    'asset_status': fields.String(description='Asset current status'),
    'request_date': fields.Date(description='Request date'),
    'requested_by_id': fields.Integer(description='Requested by user ID'),
    'requested_by_name': fields.String(description='Requested by username'),
    'maintenance_reason': fields.String(description='Maintenance reason (broken, periodic, calibration, other)'),
    'condition_before': fields.String(description='Condition before maintenance'),
    'damage_level': fields.String(description='Damage level (light, medium, heavy)'),
    'maintenance_date': fields.Date(description='Maintenance date'),
    'type': fields.String(description='Type (maintenance, repair, inspection)'),
    'description': fields.String(description='Description'),
    'vendor': fields.String(description='Vendor/Unit name'),
    'person_in_charge': fields.String(description='Person in charge'),
    'vendor_phone': fields.String(description='Vendor phone'),
    'estimated_cost': fields.Float(description='Estimated cost'),
    'cost': fields.Float(description='Actual cost'),
    'completed_date': fields.Date(description='Completed date'),
    'replaced_parts': fields.String(description='Replaced parts'),
    'result_status': fields.String(description='Result status (passed, failed, need_retry)'),
    'result_notes': fields.String(description='Result notes'),
    'invoice_file': fields.String(description='Invoice file path'),
    'acceptance_file': fields.String(description='Acceptance file path'),
    'before_image': fields.String(description='Before image path'),
    'after_image': fields.String(description='After image path'),
    'next_due_date': fields.Date(description='Next due date'),
    'status': fields.String(description='Status (pending, in_progress, completed, failed, cancelled)'),
    'created_at': fields.DateTime(description='Created at'),
    'updated_at': fields.DateTime(description='Updated at')
})

maintenance_create_model = api.model('MaintenanceCreate', {
    'asset_id': fields.Integer(required=True, description='Asset ID'),
    'request_date': fields.String(description='Request date (YYYY-MM-DD)'),
    'requested_by_id': fields.Integer(description='Requested by user ID'),
    'maintenance_reason': fields.String(description='Maintenance reason (broken, periodic, calibration, other)'),
    'condition_before': fields.String(description='Condition before maintenance'),
    'damage_level': fields.String(description='Damage level (light, medium, heavy)'),
    'maintenance_date': fields.String(description='Maintenance date (YYYY-MM-DD)'),
    'type': fields.String(default='maintenance', description='Type (maintenance, repair, inspection)'),
    'description': fields.String(description='Description'),
    'vendor': fields.String(description='Vendor/Unit name'),
    'person_in_charge': fields.String(description='Person in charge'),
    'vendor_phone': fields.String(description='Vendor phone'),
    'estimated_cost': fields.Float(default=0.0, description='Estimated cost'),
    'cost': fields.Float(default=0.0, description='Actual cost'),
    'completed_date': fields.String(description='Completed date (YYYY-MM-DD)'),
    'replaced_parts': fields.String(description='Replaced parts'),
    'result_status': fields.String(description='Result status (passed, failed, need_retry)'),
    'result_notes': fields.String(description='Result notes'),
    'next_due_date': fields.String(description='Next due date (YYYY-MM-DD)'),
    'status': fields.String(default='pending', description='Status')
})

maintenance_update_model = api.model('MaintenanceUpdate', {
    'asset_id': fields.Integer(description='Asset ID'),
    'request_date': fields.String(description='Request date (YYYY-MM-DD)'),
    'requested_by_id': fields.Integer(description='Requested by user ID'),
    'maintenance_reason': fields.String(description='Maintenance reason'),
    'condition_before': fields.String(description='Condition before maintenance'),
    'damage_level': fields.String(description='Damage level'),
    'maintenance_date': fields.String(description='Maintenance date (YYYY-MM-DD)'),
    'type': fields.String(description='Type'),
    'description': fields.String(description='Description'),
    'vendor': fields.String(description='Vendor'),
    'person_in_charge': fields.String(description='Person in charge'),
    'vendor_phone': fields.String(description='Vendor phone'),
    'estimated_cost': fields.Float(description='Estimated cost'),
    'cost': fields.Float(description='Actual cost'),
    'completed_date': fields.String(description='Completed date (YYYY-MM-DD)'),
    'replaced_parts': fields.String(description='Replaced parts'),
    'result_status': fields.String(description='Result status'),
    'result_notes': fields.String(description='Result notes'),
    'next_due_date': fields.String(description='Next due date (YYYY-MM-DD)'),
    'status': fields.String(description='Status')
})

# Pagination model
pagination_model = api.model('Pagination', {
    'page': fields.Integer(description='Current page'),
    'per_page': fields.Integer(description='Items per page'),
    'total': fields.Integer(description='Total items'),
    'pages': fields.Integer(description='Total pages')
})

# ========== Auth Endpoints ==========

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.doc('login')
    @auth_ns.expect(login_model)
    @auth_ns.marshal_with(token_model)
    def post(self):
        """Đăng nhập và nhận JWT token"""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return {'message': 'Username và password là bắt buộc'}, 400
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return {'message': 'Username hoặc password không đúng'}, 401
        
        if not user.is_active or user.deleted_at:
            return {'message': 'Tài khoản đã bị vô hiệu hóa'}, 403
        
        # Tạo JWT token
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24)
        )
        refresh_token = create_refresh_token(identity=user.id)
        
        # Cập nhật last_login
        user.last_login = now_vn()
        db.session.commit()
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 86400  # 24 hours
        }, 200

@auth_ns.route('/refresh')
class Refresh(Resource):
    @jwt_required(refresh=True)
    @auth_ns.doc('refresh_token')
    @auth_ns.marshal_with(token_model)
    def post(self):
        """Làm mới access token"""
        current_user_id = get_jwt_identity()
        access_token = create_access_token(
            identity=current_user_id,
            expires_delta=timedelta(hours=24)
        )
        return {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 86400
        }, 200

# ========== Hồ sơ pháp lý ==========
@legal_ns.route('')
class LegalDocList(Resource):
    @jwt_required()
    @legal_ns.marshal_list_with(legal_doc_model)
    def get(self):
        asset_id = request.args.get('asset_id', type=int)
        query = LegalDocument.query
        if asset_id:
            query = query.filter_by(asset_id=asset_id)
        return query.order_by(LegalDocument.created_at.desc()).all(), 200

    @jwt_required()
    @legal_ns.expect(legal_doc_model)
    @legal_ns.marshal_with(legal_doc_model)
    def post(self):
        data = request.get_json()
        doc = LegalDocument(
            asset_id=data['asset_id'],
            so_quyet_dinh=data.get('so_quyet_dinh'),
            ngay_ban_hanh=datetime.strptime(data['ngay_ban_hanh'], '%Y-%m-%d').date() if data.get('ngay_ban_hanh') else None,
            loai_van_ban=data.get('loai_van_ban'),
            co_quan_ban_hanh=data.get('co_quan_ban_hanh'),
            noi_dung=data.get('noi_dung'),
            file_dinh_kem=data.get('file_dinh_kem'),
        )
        db.session.add(doc)
        db.session.commit()
        return doc, 201

@legal_ns.route('/<int:id>')
class LegalDocDetail(Resource):
    @jwt_required()
    @legal_ns.expect(legal_doc_model)
    @legal_ns.marshal_with(legal_doc_model)
    def put(self, id):
        doc = LegalDocument.query.get_or_404(id)
        data = request.get_json()
        for field in ['asset_id', 'so_quyet_dinh', 'loai_van_ban', 'co_quan_ban_hanh', 'noi_dung', 'file_dinh_kem']:
            if field in data:
                setattr(doc, field, data.get(field))
        if 'ngay_ban_hanh' in data:
            doc.ngay_ban_hanh = datetime.strptime(data['ngay_ban_hanh'], '%Y-%m-%d').date() if data['ngay_ban_hanh'] else None
        db.session.commit()
        return doc, 200

    @jwt_required()
    def delete(self, id):
        doc = LegalDocument.query.get_or_404(id)
        db.session.delete(doc)
        db.session.commit()
        return {'message': 'Deleted'}, 200

# ========== Nguồn hình thành ==========
@sources_ns.route('')
class AssetSourceList(Resource):
    @jwt_required()
    @sources_ns.marshal_list_with(asset_source_model)
    def get(self):
        asset_id = request.args.get('asset_id', type=int)
        query = AssetSource.query
        if asset_id:
            query = query.filter_by(asset_id=asset_id)
        return query.order_by(AssetSource.created_at.desc()).all(), 200

    @jwt_required()
    @sources_ns.expect(asset_source_model)
    @sources_ns.marshal_with(asset_source_model)
    def post(self):
        data = request.get_json()
        src = AssetSource(
            asset_id=data['asset_id'],
            nguon=data['nguon'],
            nha_cung_cap=data.get('nha_cung_cap'),
            so_hop_dong=data.get('so_hop_dong'),
            so_hoa_don=data.get('so_hoa_don'),
            gia_tri=data.get('gia_tri', 0),
            ghi_chu=data.get('ghi_chu'),
        )
        db.session.add(src)
        db.session.commit()
        return src, 201

@sources_ns.route('/<int:id>')
class AssetSourceDetail(Resource):
    @jwt_required()
    @sources_ns.expect(asset_source_model)
    @sources_ns.marshal_with(asset_source_model)
    def put(self, id):
        src = AssetSource.query.get_or_404(id)
        data = request.get_json()
        for field in ['nguon', 'nha_cung_cap', 'so_hop_dong', 'so_hoa_don', 'gia_tri', 'ghi_chu']:
            if field in data:
                setattr(src, field, data.get(field))
        if 'asset_id' in data:
            src.asset_id = data.get('asset_id')
        db.session.commit()
        return src, 200

    @jwt_required()
    def delete(self, id):
        src = AssetSource.query.get_or_404(id)
        db.session.delete(src)
        db.session.commit()
        return {'message': 'Deleted'}, 200

# ========== Vị trí sử dụng ==========
@locations_ns.route('')
class AssetLocationList(Resource):
    @jwt_required()
    @locations_ns.marshal_list_with(asset_location_model)
    def get(self):
        asset_id = request.args.get('asset_id', type=int)
        query = AssetLocation.query
        if asset_id:
            query = query.filter_by(asset_id=asset_id)
        return query.order_by(AssetLocation.created_at.desc()).all(), 200

    @jwt_required()
    @locations_ns.expect(asset_location_model)
    @locations_ns.marshal_with(asset_location_model)
    def post(self):
        data = request.get_json()
        loc = AssetLocation(
            asset_id=data['asset_id'],
            toa_nha=data.get('toa_nha'),
            phong_ban=data.get('phong_ban'),
            nguoi_quan_ly_id=data.get('nguoi_quan_ly_id'),
            hieu_luc_tu=datetime.strptime(data['hieu_luc_tu'], '%Y-%m-%d').date() if data.get('hieu_luc_tu') else None,
            hieu_luc_den=datetime.strptime(data['hieu_luc_den'], '%Y-%m-%d').date() if data.get('hieu_luc_den') else None,
        )
        db.session.add(loc)
        db.session.commit()
        return loc, 201

@locations_ns.route('/<int:id>')
class AssetLocationDetail(Resource):
    @jwt_required()
    @locations_ns.expect(asset_location_model)
    @locations_ns.marshal_with(asset_location_model)
    def put(self, id):
        loc = AssetLocation.query.get_or_404(id)
        data = request.get_json()
        for field in ['asset_id', 'toa_nha', 'phong_ban', 'nguoi_quan_ly_id']:
            if field in data:
                setattr(loc, field, data.get(field))
        if 'hieu_luc_tu' in data:
            loc.hieu_luc_tu = datetime.strptime(data['hieu_luc_tu'], '%Y-%m-%d').date() if data['hieu_luc_tu'] else None
        if 'hieu_luc_den' in data:
            loc.hieu_luc_den = datetime.strptime(data['hieu_luc_den'], '%Y-%m-%d').date() if data['hieu_luc_den'] else None
        db.session.commit()
        return loc, 200

    @jwt_required()
    def delete(self, id):
        loc = AssetLocation.query.get_or_404(id)
        db.session.delete(loc)
        db.session.commit()
        return {'message': 'Deleted'}, 200

# ========== Tình trạng sử dụng ==========
@usage_ns.route('')
class UsageStatusList(Resource):
    @jwt_required()
    @usage_ns.marshal_list_with(usage_status_model)
    def get(self):
        asset_id = request.args.get('asset_id', type=int)
        query = AssetUsageStatusLog.query
        if asset_id:
            query = query.filter_by(asset_id=asset_id)
        return query.order_by(AssetUsageStatusLog.changed_at.desc()).all(), 200

    @jwt_required()
    @usage_ns.expect(usage_status_model)
    @usage_ns.marshal_with(usage_status_model)
    def post(self):
        data = request.get_json()
        log = AssetUsageStatusLog(
            asset_id=data['asset_id'],
            trang_thai=data['trang_thai'],
            ghi_chu=data.get('ghi_chu'),
            user_id=get_jwt_identity()
        )
        # update asset usage_status
        asset = Asset.query.get(log.asset_id)
        if asset:
            asset.usage_status = log.trang_thai
        db.session.add(log)
        db.session.commit()
        return log, 201

# ========== Kiểm kê ==========
@inventory_ns.route('/batches')
class InventoryBatchList(Resource):
    @jwt_required()
    @inventory_ns.marshal_list_with(inventory_batch_model)
    def get(self):
        return InventoryBatch.query.order_by(InventoryBatch.created_at.desc()).all(), 200

    @jwt_required()
    @inventory_ns.expect(inventory_batch_model)
    @inventory_ns.marshal_with(inventory_batch_model)
    def post(self):
        data = request.get_json()
        batch = InventoryBatch(
            ma_dot=data['ma_dot'],
            ten_dot=data['ten_dot'],
            loai_kiem_ke=data.get('loai_kiem_ke'),
            pham_vi=data.get('pham_vi'),
            so_quyet_dinh=data.get('so_quyet_dinh'),
            trang_thai='draft',
            created_by_id=get_jwt_identity(),
        )
        db.session.add(batch)
        db.session.commit()
        return batch, 201

@inventory_ns.route('/batches/<int:id>/approve')
class InventoryBatchApprove(Resource):
    @jwt_required()
    def post(self, id):
        batch = InventoryBatch.query.get_or_404(id)
        batch.trang_thai = 'approved'
        batch.approved_by_id = get_jwt_identity()
        batch.approved_at = now_vn()
        db.session.commit()
        return {'message': 'Approved'}, 200

@inventory_ns.route('/items')
class InventoryItemList(Resource):
    @jwt_required()
    @inventory_ns.marshal_list_with(inventory_item_model)
    def get(self):
        batch_id = request.args.get('batch_id', type=int)
        query = InventoryItem.query
        if batch_id:
            query = query.filter_by(batch_id=batch_id)
        return query.order_by(InventoryItem.created_at.desc()).all(), 200

    @jwt_required()
    @inventory_ns.expect(inventory_item_model)
    @inventory_ns.marshal_with(inventory_item_model)
    def post(self):
        data = request.get_json()
        item = InventoryItem(
            batch_id=data['batch_id'],
            asset_id=data['asset_id'],
            so_thuc_te=data.get('so_thuc_te', 0),
            so_he_thong=data.get('so_he_thong', 0),
            chenhlech=data.get('chenhlech', 0),
            ghi_chu=data.get('ghi_chu'),
        )
        db.session.add(item)
        db.session.commit()
        return item, 201

@inventory_ns.route('/items/<int:id>')
class InventoryItemDetail(Resource):
    @jwt_required()
    @inventory_ns.expect(inventory_item_model)
    @inventory_ns.marshal_with(inventory_item_model)
    def put(self, id):
        item = InventoryItem.query.get_or_404(id)
        data = request.get_json()
        for field in ['so_thuc_te', 'so_he_thong', 'chenhlech', 'ghi_chu']:
            if field in data:
                setattr(item, field, data.get(field))
        db.session.commit()
        return item, 200

    @jwt_required()
    def delete(self, id):
        item = InventoryItem.query.get_or_404(id)
        db.session.delete(item)
        db.session.commit()
        return {'message': 'Deleted'}, 200

# ========== Thanh lý ==========
@disposal_ns.route('')
class DisposalList(Resource):
    @jwt_required()
    @disposal_ns.marshal_list_with(disposal_model)
    def get(self):
        return DisposalRequest.query.order_by(DisposalRequest.created_at.desc()).all(), 200

    @jwt_required()
    @disposal_ns.expect(disposal_model)
    @disposal_ns.marshal_with(disposal_model)
    def post(self):
        data = request.get_json()
        req = DisposalRequest(
            asset_id=data['asset_id'],
            de_nghi_thanh_ly=data.get('de_nghi_thanh_ly'),
            phe_duyet=data.get('phe_duyet'),
            so_quyet_dinh=data.get('so_quyet_dinh'),
            gia_tri_con_lai=data.get('gia_tri_con_lai', 0),
            gia_tri_ban=data.get('gia_tri_ban', 0),
            file_dinh_kem=data.get('file_dinh_kem'),
            trang_thai=data.get('trang_thai', 'draft'),
        )
        db.session.add(req)
        db.session.commit()
        return req, 201

@disposal_ns.route('/<int:id>/approve')
class DisposalApprove(Resource):
    @jwt_required()
    def post(self, id):
        req = DisposalRequest.query.get_or_404(id)
        req.trang_thai = 'approved'
        req.approved_at = now_vn()
        # cập nhật trạng thái asset
        if req.asset:
            req.asset.status = 'disposed'
        db.session.commit()
        return {'message': 'Approved & asset disposed'}, 200

# ========== Biến động tài sản ==========
@changelog_ns.route('')
class ChangeLogList(Resource):
    @jwt_required()
    @changelog_ns.marshal_list_with(change_log_model)
    def get(self):
        asset_id = request.args.get('asset_id', type=int)
        query = AssetChangeLog.query
        if asset_id:
            query = query.filter_by(asset_id=asset_id)
        return query.order_by(AssetChangeLog.created_at.desc()).all(), 200

@auth_ns.route('/me')
class CurrentUser(Resource):
    @jwt_required()
    @auth_ns.doc('get_current_user')
    @auth_ns.marshal_with(user_model)
    def get(self):
        """Lấy thông tin user hiện tại"""
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or not user.is_active:
            return {'message': 'Người dùng không hợp lệ'}, 404
        return user, 200

# ========== Asset Type Endpoints ==========

@asset_types_ns.route('')
class AssetTypeList(Resource):
    @jwt_required()
    @asset_types_ns.doc('list_asset_types')
    @asset_types_ns.marshal_list_with(asset_type_model)
    def get(self):
        """Lấy danh sách tất cả asset types"""
        asset_types = AssetType.query.filter(AssetType.deleted_at.is_(None)).all()
        return asset_types, 200
    
    @jwt_required()
    @admin_required
    @asset_types_ns.doc('create_asset_type')
    @asset_types_ns.expect(asset_type_create_model)
    @asset_types_ns.marshal_with(asset_type_model)
    def post(self):
        """Tạo asset type mới (Admin only)"""
        data = request.get_json()
        
        # Kiểm tra tên đã tồn tại chưa
        existing = AssetType.query.filter_by(name=data.get('name')).filter(AssetType.deleted_at.is_(None)).first()
        if existing:
            return {'message': 'Tên loại tài sản đã tồn tại'}, 400
        
        asset_type = AssetType(
            name=data.get('name'),
            description=data.get('description')
        )
        
        db.session.add(asset_type)
        db.session.commit()
        
        return asset_type, 201

@asset_types_ns.route('/<int:id>')
class AssetTypeDetail(Resource):
    @jwt_required()
    @asset_types_ns.doc('get_asset_type')
    @asset_types_ns.marshal_with(asset_type_model)
    def get(self, id):
        """Lấy thông tin asset type theo ID"""
        asset_type = AssetType.query.filter_by(id=id, deleted_at=None).first_or_404()
        return asset_type, 200
    
    @jwt_required()
    @admin_required
    @asset_types_ns.doc('update_asset_type')
    @asset_types_ns.expect(asset_type_create_model)
    @asset_types_ns.marshal_with(asset_type_model)
    def put(self, id):
        """Cập nhật asset type (Admin only)"""
        asset_type = AssetType.query.filter_by(id=id, deleted_at=None).first_or_404()
        data = request.get_json()
        
        # Kiểm tra tên trùng (nếu có thay đổi)
        if 'name' in data and data['name'] != asset_type.name:
            existing = AssetType.query.filter_by(name=data['name']).filter(AssetType.deleted_at.is_(None)).first()
            if existing:
                return {'message': 'Tên loại tài sản đã tồn tại'}, 400
        
        if 'name' in data:
            asset_type.name = data['name']
        if 'description' in data:
            asset_type.description = data.get('description')
        
        db.session.commit()
        return asset_type, 200
    
    @jwt_required()
    @admin_required
    @asset_types_ns.doc('delete_asset_type')
    def delete(self, id):
        """Xóa asset type (soft delete, Admin only)"""
        asset_type = AssetType.query.filter_by(id=id, deleted_at=None).first_or_404()
        
        # Kiểm tra có asset nào đang sử dụng không
        if Asset.query.filter_by(asset_type_id=id, deleted_at=None).count() > 0:
            return {'message': 'Không thể xóa loại tài sản đang được sử dụng'}, 400
        
        asset_type.soft_delete()
        db.session.commit()
        return {'message': 'Đã xóa loại tài sản thành công'}, 200

# ========== Asset Endpoints ==========

def asset_to_dict(asset):
    """Chuyển Asset object thành dictionary"""
    return {
        'id': asset.id,
        'name': asset.name,
        'price': float(asset.price),
        'quantity': asset.quantity,
        'status': asset.status,
        'purchase_date': asset.purchase_date.isoformat() if asset.purchase_date else None,
        'device_code': asset.device_code,
        'tinh_trang_danh_gia': asset.tinh_trang_danh_gia,
        'usage_status': asset.usage_status,
        'asset_type_id': asset.asset_type_id,
        'asset_type_name': asset.asset_type.name if asset.asset_type else None,
        'user_id': asset.user_id,
        'user_text': asset.user_text,
        'notes': asset.notes,
        'warranty_start_date': asset.warranty_start_date.isoformat() if asset.warranty_start_date else None,
        'warranty_end_date': asset.warranty_end_date.isoformat() if asset.warranty_end_date else None,
        'warranty_period_months': asset.warranty_period_months,
        'created_at': asset.created_at.isoformat() if asset.created_at else None,
        'updated_at': asset.updated_at.isoformat() if asset.updated_at else None
    }

@assets_ns.route('')
class AssetList(Resource):
    @jwt_required()
    @assets_ns.doc('list_assets')
    @assets_ns.param('page', 'Page number', type='integer', default=1)
    @assets_ns.param('per_page', 'Items per page', type='integer', default=20)
    @assets_ns.param('status', 'Filter by status')
    @assets_ns.param('asset_type_id', 'Filter by asset type ID')
    @assets_ns.param('search', 'Search by name or device_code')
    def get(self):
        """Lấy danh sách assets với phân trang và filter"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        asset_type_id = request.args.get('asset_type_id', type=int)
        search = request.args.get('search')
        
        query = Asset.query.filter(Asset.deleted_at.is_(None))
        
        # Filters
        if status:
            query = query.filter(Asset.status == status)
        if asset_type_id:
            query = query.filter(Asset.asset_type_id == asset_type_id)
        if search:
            query = query.filter(or_(
                Asset.name.contains(search),
                Asset.device_code.contains(search)
            ))
        
        # Pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'items': [asset_to_dict(asset) for asset in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }, 200
    
    @jwt_required()
    @assets_ns.doc('create_asset')
    @assets_ns.expect(asset_create_model)
    def post(self):
        """Tạo asset mới"""
        data = request.get_json()
        
        # Comprehensive validation
        validation_errors = validate_asset_data(data, is_update=False)
        if validation_errors:
            return {'message': 'Dữ liệu không hợp lệ', 'errors': validation_errors}, 400
        
        # Parse dates
        purchase_date = None
        if data.get('purchase_date'):
            try:
                purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
            except ValueError:
                return {'message': 'Ngày mua không đúng định dạng (YYYY-MM-DD)'}, 400
        
        warranty_start_date = None
        if data.get('warranty_start_date'):
            try:
                warranty_start_date = datetime.strptime(data['warranty_start_date'], '%Y-%m-%d').date()
            except ValueError:
                return {'message': 'Ngày bắt đầu bảo hành không đúng định dạng (YYYY-MM-DD)'}, 400
        
        warranty_end_date = None
        if data.get('warranty_end_date'):
            try:
                warranty_end_date = datetime.strptime(data['warranty_end_date'], '%Y-%m-%d').date()
            except ValueError:
                return {'message': 'Ngày kết thúc bảo hành không đúng định dạng (YYYY-MM-DD)'}, 400
        
        # Create asset with transaction safety
        def create_asset():
            asset = Asset(
                name=data.get('name'),
                price=data.get('price'),
                quantity=data.get('quantity', 1),
                status=data.get('status', 'active'),
                purchase_date=purchase_date,
                device_code=data.get('device_code'),
                tinh_trang_danh_gia=data.get('tinh_trang_danh_gia') or data.get('condition_label'),
                usage_status=data.get('usage_status', 'dang_su_dung'),
                asset_type_id=data.get('asset_type_id'),
                user_id=data.get('user_id'),
                user_text=data.get('user_text'),
                notes=data.get('notes'),
                warranty_start_date=warranty_start_date,
                warranty_end_date=warranty_end_date,
                warranty_period_months=data.get('warranty_period_months')
            )
            db.session.add(asset)
            db.session.flush()  # Get ID without committing
            return asset
        
        result, error = safe_db_operation(create_asset)
        if error:
            return error, 400
        
        return asset_to_dict(result), 201

@assets_ns.route('/<int:id>')
class AssetDetail(Resource):
    @jwt_required()
    @assets_ns.doc('get_asset')
    def get(self, id):
        """Lấy thông tin asset theo ID"""
        asset = Asset.query.filter_by(id=id, deleted_at=None).first_or_404()
        return asset_to_dict(asset), 200
    
    @jwt_required()
    @assets_ns.doc('update_asset')
    @assets_ns.expect(asset_update_model)
    def put(self, id):
        """Cập nhật asset"""
        asset = Asset.query.filter_by(id=id, deleted_at=None).first_or_404()
        data = request.get_json()
        
        # Comprehensive validation
        validation_errors = validate_asset_data(data, is_update=True)
        if validation_errors:
            return {'message': 'Dữ liệu không hợp lệ', 'errors': validation_errors}, 400
        
        # Update fields with transaction safety
        def update_asset():
            if 'name' in data:
                asset.name = data['name']
            if 'price' in data:
                asset.price = data['price']
            if 'quantity' in data:
                asset.quantity = data['quantity']
            if 'status' in data:
                if not validate_status(data['status']):
                    raise ValueError(f'Trạng thái không hợp lệ: {data["status"]}')
                asset.status = data['status']
            if 'purchase_date' in data:
                if data['purchase_date']:
                    try:
                        asset.purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
                    except ValueError:
                        raise ValueError('Ngày mua không đúng định dạng (YYYY-MM-DD)')
                else:
                    asset.purchase_date = None
            if 'device_code' in data:
                asset.device_code = data.get('device_code')
            if 'tinh_trang_danh_gia' in data or 'condition_label' in data:
                asset.tinh_trang_danh_gia = data.get('tinh_trang_danh_gia') or data.get('condition_label')
            if 'usage_status' in data:
                asset.usage_status = data.get('usage_status')
            if 'asset_type_id' in data:
                asset_type = AssetType.query.filter_by(id=data['asset_type_id'], deleted_at=None).first()
                if not asset_type:
                    raise ValueError('Loại tài sản không tồn tại')
                asset.asset_type_id = data['asset_type_id']
            if 'user_id' in data:
                asset.user_id = data.get('user_id')
            if 'user_text' in data:
                asset.user_text = data.get('user_text')
            if 'notes' in data:
                asset.notes = data.get('notes')
            if 'warranty_start_date' in data:
                if data['warranty_start_date']:
                    try:
                        asset.warranty_start_date = datetime.strptime(data['warranty_start_date'], '%Y-%m-%d').date()
                    except ValueError:
                        raise ValueError('Ngày bắt đầu bảo hành không đúng định dạng (YYYY-MM-DD)')
                else:
                    asset.warranty_start_date = None
            if 'warranty_end_date' in data:
                if data['warranty_end_date']:
                    try:
                        asset.warranty_end_date = datetime.strptime(data['warranty_end_date'], '%Y-%m-%d').date()
                    except ValueError:
                        raise ValueError('Ngày kết thúc bảo hành không đúng định dạng (YYYY-MM-DD)')
                else:
                    asset.warranty_end_date = None
            if 'warranty_period_months' in data:
                asset.warranty_period_months = data.get('warranty_period_months')
            return asset
        
        result, error = safe_db_operation(update_asset)
        if error:
            return error, 400
        
        return asset_to_dict(result), 200
    
    @jwt_required()
    @assets_ns.doc('delete_asset')
    def delete(self, id):
        """Xóa asset (soft delete)"""
        asset = Asset.query.filter_by(id=id, deleted_at=None).first_or_404()
        
        def delete_asset():
            asset.soft_delete()
            return asset
        
        result, error = safe_db_operation(delete_asset)
        if error:
            return error, 400
        
        return {'message': 'Đã xóa tài sản thành công'}, 200

# ========== User Endpoints ==========

def user_to_dict(user):
    """Chuyển User object thành dictionary"""
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role_id': user.role_id,
        'role_name': user.role.name if user.role else None,
        'is_active': user.is_active,
        'asset_quota': user.asset_quota,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'updated_at': user.updated_at.isoformat() if user.updated_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None
    }

@users_ns.route('')
class UserList(Resource):
    @jwt_required()
    @admin_required
    @users_ns.doc('list_users')
    @users_ns.param('page', 'Page number', type='integer', default=1)
    @users_ns.param('per_page', 'Items per page', type='integer', default=20)
    @users_ns.param('role_id', 'Filter by role ID')
    @users_ns.param('is_active', 'Filter by active status')
    @users_ns.param('search', 'Search by username or email')
    def get(self):
        """Lấy danh sách users với phân trang và filter (Admin only)"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        role_id = request.args.get('role_id', type=int)
        is_active = request.args.get('is_active', type=bool)
        search = request.args.get('search')
        
        query = User.query.filter(User.deleted_at.is_(None))
        
        # Filters
        if role_id:
            query = query.filter(User.role_id == role_id)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if search:
            query = query.filter(or_(
                User.username.contains(search),
                User.email.contains(search)
            ))
        
        # Pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'items': [user_to_dict(user) for user in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }, 200
    
    @jwt_required()
    @admin_required
    @users_ns.doc('create_user')
    @users_ns.expect(user_create_model)
    def post(self):
        """Tạo user mới (Admin only)"""
        data = request.get_json()
        
        # Validate role_id
        role = Role.query.get(data.get('role_id'))
        if not role:
            return {'message': 'Role không tồn tại'}, 400
        
        # Kiểm tra username và email đã tồn tại chưa
        if User.query.filter_by(username=data.get('username'), deleted_at=None).first():
            return {'message': 'Username đã tồn tại'}, 400
        if User.query.filter_by(email=data.get('email'), deleted_at=None).first():
            return {'message': 'Email đã tồn tại'}, 400
        
        user = User(
            username=data.get('username'),
            email=data.get('email'),
            role_id=data.get('role_id'),
            is_active=data.get('is_active', True),
            asset_quota=data.get('asset_quota', 0)
        )
        user.set_password(data.get('password'))
        
        db.session.add(user)
        db.session.commit()
        
        return user_to_dict(user), 201

@users_ns.route('/<int:id>')
class UserDetail(Resource):
    @jwt_required()
    @users_ns.doc('get_user')
    def get(self, id):
        """Lấy thông tin user theo ID"""
        current_user = get_current_user()
        # User chỉ có thể xem thông tin của chính mình, admin có thể xem tất cả
        if current_user.id != id and current_user.role.name != 'admin':
            return {'message': 'Không có quyền truy cập'}, 403
        
        user = User.query.filter_by(id=id, deleted_at=None).first_or_404()
        return user_to_dict(user), 200
    
    @jwt_required()
    @users_ns.doc('update_user')
    @users_ns.expect(user_update_model)
    def put(self, id):
        """Cập nhật user"""
        current_user = get_current_user()
        user = User.query.filter_by(id=id, deleted_at=None).first_or_404()
        
        # User chỉ có thể cập nhật thông tin của chính mình (một số trường), admin có thể cập nhật tất cả
        if current_user.id != id and current_user.role.name != 'admin':
            return {'message': 'Không có quyền cập nhật'}, 403
        
        data = request.get_json()
        
        # Chỉ admin mới có thể thay đổi role và is_active
        if current_user.role.name != 'admin':
            if 'role_id' in data or 'is_active' in data:
                return {'message': 'Không có quyền thay đổi role hoặc trạng thái'}, 403
        
        if 'email' in data:
            # Kiểm tra email trùng
            existing = User.query.filter_by(email=data['email'], deleted_at=None).first()
            if existing and existing.id != id:
                return {'message': 'Email đã tồn tại'}, 400
            user.email = data['email']
        if 'role_id' in data:
            role = Role.query.get(data['role_id'])
            if not role:
                return {'message': 'Role không tồn tại'}, 400
            user.role_id = data['role_id']
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'asset_quota' in data:
            user.asset_quota = data['asset_quota']
        
        db.session.commit()
        return user_to_dict(user), 200
    
    @jwt_required()
    @admin_required
    @users_ns.doc('delete_user')
    def delete(self, id):
        """Xóa user (soft delete, Admin only)"""
        user = User.query.filter_by(id=id, deleted_at=None).first_or_404()
        
        # Không cho phép xóa chính mình
        current_user_id = get_jwt_identity()
        if user.id == current_user_id:
            return {'message': 'Không thể xóa chính mình'}, 400
        
        user.soft_delete()
        db.session.commit()
        return {'message': 'Đã xóa user thành công'}, 200

# ========== Maintenance Record Endpoints ==========

def maintenance_to_dict(record):
    """Chuyển MaintenanceRecord object thành dictionary"""
    asset = record.asset
    return {
        'id': record.id,
        'asset_id': record.asset_id,
        'asset_name': asset.name if asset else None,
        'asset_code': asset.device_code if asset else None,
        'asset_type_name': asset.asset_type.name if asset and asset.asset_type else None,
        'asset_user': asset.user.username if asset and asset.user else (asset.user_text if asset else None),
        'asset_status': asset.status if asset else None,
        'request_date': record.request_date.isoformat() if record.request_date else None,
        'requested_by_id': record.requested_by_id,
        'requested_by_name': record.requested_by.username if record.requested_by else None,
        'maintenance_reason': record.maintenance_reason,
        'condition_before': record.condition_before,
        'damage_level': record.damage_level,
        'maintenance_date': record.maintenance_date.isoformat() if record.maintenance_date else None,
        'type': record.type,
        'description': record.description,
        'vendor': record.vendor,
        'person_in_charge': record.person_in_charge,
        'vendor_phone': record.vendor_phone,
        'estimated_cost': float(record.estimated_cost) if record.estimated_cost else 0.0,
        'cost': float(record.cost) if record.cost else 0.0,
        'completed_date': record.completed_date.isoformat() if record.completed_date else None,
        'replaced_parts': record.replaced_parts,
        'result_status': record.result_status,
        'result_notes': record.result_notes,
        'invoice_file': record.invoice_file,
        'acceptance_file': record.acceptance_file,
        'before_image': record.before_image,
        'after_image': record.after_image,
        'next_due_date': record.next_due_date.isoformat() if record.next_due_date else None,
        'status': record.status,
        'created_at': record.created_at.isoformat() if record.created_at else None,
        'updated_at': record.updated_at.isoformat() if record.updated_at else None
    }

@maintenance_ns.route('')
class MaintenanceList(Resource):
    @jwt_required()
    @maintenance_ns.doc('list_maintenance')
    @maintenance_ns.param('page', 'Page number', type='integer', default=1)
    @maintenance_ns.param('per_page', 'Items per page', type='integer', default=20)
    @maintenance_ns.param('asset_id', 'Filter by asset ID')
    @maintenance_ns.param('asset_type_id', 'Filter by asset type ID')
    @maintenance_ns.param('status', 'Filter by status')
    @maintenance_ns.param('type', 'Filter by type')
    @maintenance_ns.param('vendor', 'Filter by vendor name')
    @maintenance_ns.param('date_from', 'Filter from date (YYYY-MM-DD)')
    @maintenance_ns.param('date_to', 'Filter to date (YYYY-MM-DD)')
    @maintenance_ns.param('search', 'Search by asset name or code')
    def get(self):
        """Lấy danh sách maintenance records với phân trang và filter"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        asset_id = request.args.get('asset_id', type=int)
        asset_type_id = request.args.get('asset_type_id', type=int)
        status = request.args.get('status')
        type_filter = request.args.get('type')
        vendor = request.args.get('vendor')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search = request.args.get('search')
        
        query = MaintenanceRecord.query.filter(MaintenanceRecord.deleted_at.is_(None))
        
        # Filters
        if asset_id:
            query = query.filter(MaintenanceRecord.asset_id == asset_id)
        if asset_type_id:
            query = query.join(Asset).filter(Asset.asset_type_id == asset_type_id)
        if status:
            query = query.filter(MaintenanceRecord.status == status)
        if type_filter:
            query = query.filter(MaintenanceRecord.type == type_filter)
        if vendor:
            query = query.filter(MaintenanceRecord.vendor.contains(vendor))
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(MaintenanceRecord.request_date >= date_from_obj)
            except ValueError:
                return {'message': 'Ngày bắt đầu không đúng định dạng (YYYY-MM-DD)'}, 400
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(MaintenanceRecord.request_date <= date_to_obj)
            except ValueError:
                return {'message': 'Ngày kết thúc không đúng định dạng (YYYY-MM-DD)'}, 400
        if search:
            query = query.join(Asset).filter(or_(
                Asset.name.contains(search),
                Asset.device_code.contains(search)
            ))
        
        # Pagination
        pagination = query.order_by(MaintenanceRecord.request_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {
            'items': [maintenance_to_dict(record) for record in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }, 200
    
    @jwt_required()
    @maintenance_ns.doc('create_maintenance')
    @maintenance_ns.expect(maintenance_create_model)
    def post(self):
        """Tạo maintenance record mới"""
        data = request.get_json()
        
        # Validate asset_id
        asset = Asset.query.filter_by(id=data.get('asset_id'), deleted_at=None).first()
        if not asset:
            return {'message': 'Tài sản không tồn tại'}, 400
        
        # Parse dates
        request_date = None
        if data.get('request_date'):
            try:
                request_date = datetime.strptime(data['request_date'], '%Y-%m-%d').date()
            except ValueError:
                return {'message': 'Ngày yêu cầu không đúng định dạng (YYYY-MM-DD)'}, 400
        
        maintenance_date = None
        if data.get('maintenance_date'):
            try:
                maintenance_date = datetime.strptime(data['maintenance_date'], '%Y-%m-%d').date()
            except ValueError:
                return {'message': 'Ngày bảo trì không đúng định dạng (YYYY-MM-DD)'}, 400
        
        completed_date = None
        if data.get('completed_date'):
            try:
                completed_date = datetime.strptime(data['completed_date'], '%Y-%m-%d').date()
            except ValueError:
                return {'message': 'Ngày hoàn thành không đúng định dạng (YYYY-MM-DD)'}, 400
        
        next_due_date = None
        if data.get('next_due_date'):
            try:
                next_due_date = datetime.strptime(data['next_due_date'], '%Y-%m-%d').date()
            except ValueError:
                return {'message': 'Ngày đến hạn tiếp theo không đúng định dạng (YYYY-MM-DD)'}, 400
        
        record = MaintenanceRecord(
            asset_id=data.get('asset_id'),
            request_date=request_date or today_vn(),
            requested_by_id=data.get('requested_by_id'),
            maintenance_reason=data.get('maintenance_reason'),
            condition_before=data.get('condition_before'),
            damage_level=data.get('damage_level'),
            maintenance_date=maintenance_date,
            type=data.get('type', 'maintenance'),
            description=data.get('description'),
            vendor=data.get('vendor'),
            person_in_charge=data.get('person_in_charge'),
            vendor_phone=data.get('vendor_phone'),
            estimated_cost=data.get('estimated_cost', 0.0),
            cost=data.get('cost', 0.0),
            completed_date=completed_date,
            replaced_parts=data.get('replaced_parts'),
            result_status=data.get('result_status'),
            result_notes=data.get('result_notes'),
            next_due_date=next_due_date,
            status=data.get('status', 'pending')
        )
        
        db.session.add(record)
        db.session.commit()
        
        return maintenance_to_dict(record), 201

@maintenance_ns.route('/<int:id>')
class MaintenanceDetail(Resource):
    @jwt_required()
    @maintenance_ns.doc('get_maintenance')
    def get(self, id):
        """Lấy thông tin maintenance record theo ID"""
        record = MaintenanceRecord.query.filter_by(id=id, deleted_at=None).first_or_404()
        return maintenance_to_dict(record), 200
    
    @jwt_required()
    @maintenance_ns.doc('update_maintenance')
    @maintenance_ns.expect(maintenance_update_model)
    def put(self, id):
        """Cập nhật maintenance record"""
        record = MaintenanceRecord.query.filter_by(id=id, deleted_at=None).first_or_404()
        data = request.get_json()
        
        # Update fields
        if 'asset_id' in data:
            asset = Asset.query.filter_by(id=data['asset_id'], deleted_at=None).first()
            if not asset:
                return {'message': 'Tài sản không tồn tại'}, 400
            record.asset_id = data['asset_id']
        if 'request_date' in data:
            if data['request_date']:
                try:
                    record.request_date = datetime.strptime(data['request_date'], '%Y-%m-%d').date()
                except ValueError:
                    return {'message': 'Ngày yêu cầu không đúng định dạng (YYYY-MM-DD)'}, 400
            else:
                record.request_date = today_vn()
        if 'requested_by_id' in data:
            record.requested_by_id = data.get('requested_by_id')
        if 'maintenance_reason' in data:
            record.maintenance_reason = data.get('maintenance_reason')
        if 'condition_before' in data:
            record.condition_before = data.get('condition_before')
        if 'damage_level' in data:
            record.damage_level = data.get('damage_level')
        if 'maintenance_date' in data:
            if data['maintenance_date']:
                try:
                    record.maintenance_date = datetime.strptime(data['maintenance_date'], '%Y-%m-%d').date()
                except ValueError:
                    return {'message': 'Ngày bảo trì không đúng định dạng (YYYY-MM-DD)'}, 400
            else:
                record.maintenance_date = None
        if 'type' in data:
            record.type = data['type']
        if 'description' in data:
            record.description = data.get('description')
        if 'vendor' in data:
            record.vendor = data.get('vendor')
        if 'person_in_charge' in data:
            record.person_in_charge = data.get('person_in_charge')
        if 'vendor_phone' in data:
            record.vendor_phone = data.get('vendor_phone')
        if 'estimated_cost' in data:
            record.estimated_cost = data.get('estimated_cost', 0.0)
        if 'cost' in data:
            record.cost = data.get('cost', 0.0)
        if 'completed_date' in data:
            if data['completed_date']:
                try:
                    record.completed_date = datetime.strptime(data['completed_date'], '%Y-%m-%d').date()
                except ValueError:
                    return {'message': 'Ngày hoàn thành không đúng định dạng (YYYY-MM-DD)'}, 400
            else:
                record.completed_date = None
        if 'replaced_parts' in data:
            record.replaced_parts = data.get('replaced_parts')
        if 'result_status' in data:
            record.result_status = data.get('result_status')
        if 'result_notes' in data:
            record.result_notes = data.get('result_notes')
        if 'next_due_date' in data:
            if data['next_due_date']:
                try:
                    record.next_due_date = datetime.strptime(data['next_due_date'], '%Y-%m-%d').date()
                except ValueError:
                    return {'message': 'Ngày đến hạn tiếp theo không đúng định dạng (YYYY-MM-DD)'}, 400
            else:
                record.next_due_date = None
        if 'status' in data:
            record.status = data['status']
        
        db.session.commit()
        return maintenance_to_dict(record), 200
    
    @jwt_required()
    @maintenance_ns.doc('delete_maintenance')
    def delete(self, id):
        """Xóa maintenance record (soft delete)"""
        record = MaintenanceRecord.query.filter_by(id=id, deleted_at=None).first_or_404()
        record.soft_delete()
        db.session.commit()
        return {'message': 'Đã xóa bản ghi bảo trì thành công'}, 200

@maintenance_ns.route('/<int:id>/upload')
class MaintenanceUpload(Resource):
    @jwt_required()
    @maintenance_ns.doc('upload_maintenance_file')
    def post(self, id):
        """Upload file đính kèm cho maintenance record"""
        record = MaintenanceRecord.query.filter_by(id=id, deleted_at=None).first_or_404()
        
        file_type = request.form.get('file_type')  # invoice_file, acceptance_file, before_image, after_image
        if not file_type or file_type not in ['invoice_file', 'acceptance_file', 'before_image', 'after_image']:
            return {'message': 'Loại file không hợp lệ'}, 400
        
        if file_type not in request.files:
            return {'message': 'Không có file được upload'}, 400
        
        file = request.files[file_type]
        if not file or file.filename == '':
            return {'message': 'File không hợp lệ'}, 400
        
        # Tạo thư mục maintenance nếu chưa có
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'instance/uploads')
        maintenance_folder = os.path.join(upload_folder, 'maintenance')
        os.makedirs(maintenance_folder, exist_ok=True)
        
        # Lưu file
        filename = secure_filename(file.filename)
        timestamp = now_vn().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        unique_filename = f"maintenance_{id}_{file_type}_{timestamp}{ext}"
        file_path = os.path.join(maintenance_folder, unique_filename)
        file.save(file_path)
        
        # Lưu đường dẫn vào DB
        relative_path = f"uploads/maintenance/{unique_filename}"
        setattr(record, file_type, relative_path)
        db.session.commit()
        
        return {'message': 'Upload file thành công', 'file_path': relative_path}, 200

@maintenance_ns.route('/export')
class MaintenanceExport(Resource):
    @jwt_required()
    @maintenance_ns.doc('export_maintenance')
    @maintenance_ns.param('asset_id', 'Filter by asset ID')
    @maintenance_ns.param('asset_type_id', 'Filter by asset type ID')
    @maintenance_ns.param('status', 'Filter by status')
    @maintenance_ns.param('vendor', 'Filter by vendor')
    @maintenance_ns.param('date_from', 'Filter from date (YYYY-MM-DD)')
    @maintenance_ns.param('date_to', 'Filter to date (YYYY-MM-DD)')
    def get(self):
        """Xuất Excel danh sách bảo trì"""
        asset_id = request.args.get('asset_id', type=int)
        asset_type_id = request.args.get('asset_type_id', type=int)
        status = request.args.get('status')
        vendor = request.args.get('vendor')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        query = MaintenanceRecord.query.filter(MaintenanceRecord.deleted_at.is_(None))
        
        # Apply filters (same as list endpoint)
        if asset_id:
            query = query.filter(MaintenanceRecord.asset_id == asset_id)
        if asset_type_id:
            query = query.join(Asset).filter(Asset.asset_type_id == asset_type_id)
        if status:
            query = query.filter(MaintenanceRecord.status == status)
        if vendor:
            query = query.filter(MaintenanceRecord.vendor.contains(vendor))
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(MaintenanceRecord.request_date >= date_from_obj)
            except ValueError:
                return {'message': 'Ngày bắt đầu không đúng định dạng'}, 400
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(MaintenanceRecord.request_date <= date_to_obj)
            except ValueError:
                return {'message': 'Ngày kết thúc không đúng định dạng'}, 400
        
        records = query.order_by(MaintenanceRecord.request_date.desc()).all()
        
        # Tạo DataFrame
        data = []
        for record in records:
            asset = record.asset
            data.append({
                'Mã tài sản': asset.device_code if asset else '',
                'Tên tài sản': asset.name if asset else '',
                'Loại tài sản': asset.asset_type.name if asset and asset.asset_type else '',
                'Đơn vị sử dụng': asset.user.username if asset and asset.user else (asset.user_text if asset else ''),
                'Trạng thái thiết bị': asset.status if asset else '',
                'Ngày yêu cầu': record.request_date.strftime('%d/%m/%Y') if record.request_date else '',
                'Người yêu cầu': record.requested_by.username if record.requested_by else '',
                'Nguyên nhân': {
                    'broken': 'Lỗi kỹ thuật',
                    'periodic': 'Bảo trì định kỳ',
                    'calibration': 'Hiệu chỉnh',
                    'other': 'Khác'
                }.get(record.maintenance_reason, record.maintenance_reason or ''),
                'Mô tả tình trạng': record.condition_before or '',
                'Mức độ hỏng': {
                    'light': 'Nhẹ',
                    'medium': 'Trung bình',
                    'heavy': 'Nặng'
                }.get(record.damage_level, record.damage_level or ''),
                'Đơn vị bảo trì': record.vendor or '',
                'Người thực hiện': record.person_in_charge or '',
                'Số điện thoại': record.vendor_phone or '',
                'Chi phí dự kiến': record.estimated_cost or 0,
                'Ngày hoàn thành': record.completed_date.strftime('%d/%m/%Y') if record.completed_date else '',
                'Phụ tùng thay thế': record.replaced_parts or '',
                'Chi phí thực tế': record.cost or 0,
                'Ghi chú': record.result_notes or '',
                'Trạng thái sau bảo trì': {
                    'passed': 'Đạt',
                    'failed': 'Không đạt',
                    'need_retry': 'Cần bảo trì lại'
                }.get(record.result_status, record.result_status or ''),
                'Trạng thái': {
                    'pending': 'Chờ xử lý',
                    'in_progress': 'Đang thực hiện',
                    'completed': 'Hoàn thành',
                    'failed': 'Không đạt',
                    'cancelled': 'Hủy'
                }.get(record.status, record.status)
            })
        
        df = pd.DataFrame(data)
        
        # Tạo file Excel trong memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Danh sách bảo trì', index=False)
        
        output.seek(0)
        timestamp = now_vn().strftime('%Y%m%d_%H%M%S')
        filename = f'bao_tri_{timestamp}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

