"""API endpoints cho MISA QLTS"""
from flask import Blueprint, request, jsonify, session
from models import (
    db, Asset, AssetVoucher, AssetVoucherItem, AssetTransferHistory,
    AssetProcessRequest, AssetDepreciation, AssetAmortization, Inventory, InventoryResult
)
from utils.voucher import generate_voucher_code, generate_inventory_code, generate_process_request_code
from utils.timezone import now_vn, today_vn
from datetime import datetime

api_misa_bp = Blueprint('api_misa', __name__, url_prefix='/api/misa')

def login_required_api(f):
    """Decorator kiểm tra đăng nhập cho API"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Chưa đăng nhập'}), 401
        return f(*args, **kwargs)
    return decorated_function

@api_misa_bp.route('/assets/increase', methods=['POST'])
@login_required_api
def api_asset_increase():
    """API ghi tăng tài sản"""
    try:
        data = request.get_json()
        voucher_code = generate_voucher_code('increase', db.session, AssetVoucher)
        
        voucher = AssetVoucher(
            voucher_code=voucher_code,
            voucher_type='increase',
            voucher_date=datetime.fromisoformat(data.get('voucher_date', today_vn().isoformat())).date(),
            description=data.get('description', ''),
            created_by_id=session.get('user_id')
        )
        db.session.add(voucher)
        db.session.flush()
        
        asset = Asset(
            name=data.get('name'),
            device_code=data.get('device_code'),
            asset_type_id=int(data.get('asset_type_id')),
            price=float(data.get('price', 0)),
            quantity=int(data.get('quantity', 1)),
            purchase_date=datetime.fromisoformat(data.get('purchase_date')).date() if data.get('purchase_date') else None,
            user_text=data.get('department', ''),
            notes=data.get('notes', ''),
            status='active'
        )
        db.session.add(asset)
        db.session.flush()
        
        voucher_item = AssetVoucherItem(
            voucher_id=voucher.id,
            asset_id=asset.id,
            new_value=asset.price,
            quantity=asset.quantity,
            reason=data.get('source', ''),
            notes=data.get('notes', '')
        )
        db.session.add(voucher_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Đã ghi tăng tài sản thành công',
            'data': {
                'voucher_code': voucher_code,
                'asset_id': asset.id
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@api_misa_bp.route('/assets/change-info/<int:asset_id>', methods=['PUT'])
@login_required_api
def api_asset_change_info(asset_id):
    """API thay đổi thông tin tài sản (không thay đổi giá trị)"""
    try:
        asset = Asset.query.get_or_404(asset_id)
        data = request.get_json()
        
        # Chỉ cập nhật thông tin không ảnh hưởng giá trị
        if 'name' in data:
            asset.name = data['name']
        if 'department' in data:
            asset.user_text = data['department']
        if 'user_id' in data:
            asset.user_id = int(data['user_id']) if data['user_id'] else None
        if 'notes' in data:
            asset.notes = data['notes']
        if 'condition' in data:
            asset.condition_label = data['condition']
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Đã cập nhật thông tin thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@api_misa_bp.route('/assets/reevaluate', methods=['POST'])
@login_required_api
def api_asset_reevaluate():
    """API đánh giá lại tài sản"""
    try:
        data = request.get_json()
        asset_id = int(data.get('asset_id'))
        old_value = float(data.get('old_value', 0))
        new_value = float(data.get('new_value', 0))
        reason = data.get('reason', '')
        
        asset = Asset.query.get_or_404(asset_id)
        voucher_code = generate_voucher_code('reevaluate', db.session, AssetVoucher)
        
        voucher = AssetVoucher(
            voucher_code=voucher_code,
            voucher_type='reevaluate',
            voucher_date=datetime.fromisoformat(data.get('voucher_date', today_vn().isoformat())).date(),
            description=f'Đánh giá lại tài sản {asset.name}',
            created_by_id=session.get('user_id')
        )
        db.session.add(voucher)
        db.session.flush()
        
        voucher_item = AssetVoucherItem(
            voucher_id=voucher.id,
            asset_id=asset.id,
            old_value=old_value,
            new_value=new_value,
            reason=reason
        )
        db.session.add(voucher_item)
        
        asset.price = new_value
        asset.notes = (asset.notes or '') + f'\n[Đánh giá lại {today_vn().strftime("%d/%m/%Y")}] {old_value} → {new_value}. Lý do: {reason}'
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Đã đánh giá lại thành công',
            'data': {'voucher_code': voucher_code}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@api_misa_bp.route('/assets/transfer', methods=['POST'])
@login_required_api
def api_asset_transfer():
    """API điều chuyển tài sản"""
    try:
        data = request.get_json()
        asset_id = int(data.get('asset_id'))
        
        asset = Asset.query.get_or_404(asset_id)
        
        transfer_history = AssetTransferHistory(
            asset_id=asset_id,
            from_department=data.get('from_department', ''),
            to_department=data.get('to_department', ''),
            from_user_id=int(data.get('from_user_id')) if data.get('from_user_id') else None,
            to_user_id=int(data.get('to_user_id')) if data.get('to_user_id') else None,
            transfer_date=datetime.fromisoformat(data.get('transfer_date', today_vn().isoformat())).date(),
            reason=data.get('reason', ''),
            transfer_code=data.get('transfer_code', ''),
            created_by_id=session.get('user_id')
        )
        db.session.add(transfer_history)
        
        asset.user_id = transfer_history.to_user_id
        asset.user_text = transfer_history.to_department
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Đã điều chuyển thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@api_misa_bp.route('/assets/process-request', methods=['POST'])
@login_required_api
def api_asset_process_request():
    """API tạo đề nghị xử lý"""
    try:
        data = request.get_json()
        request_code = generate_process_request_code(db.session, AssetProcessRequest)
        
        process_request = AssetProcessRequest(
            request_code=request_code,
            asset_id=int(data.get('asset_id')),
            request_type=data.get('request_type'),
            reason=data.get('reason', ''),
            notes=data.get('notes', ''),
            status=data.get('status', 'draft'),
            created_by_id=session.get('user_id')
        )
        
        if process_request.status == 'submitted':
            process_request.submitted_at = now_vn()
        
        db.session.add(process_request)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Đã tạo đề nghị thành công',
            'data': {'request_code': request_code}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@api_misa_bp.route('/assets/process-request/<int:id>/approve', methods=['PUT'])
@login_required_api
def api_asset_process_request_approve(id):
    """API duyệt/không duyệt đề nghị"""
    try:
        process_request = AssetProcessRequest.query.get_or_404(id)
        data = request.get_json()
        action = data.get('action')  # approve hoặc reject
        
        if process_request.status != 'submitted':
            return jsonify({'success': False, 'message': 'Chỉ có thể duyệt đề nghị đã được gửi'}), 400
        
        if action == 'approve':
            process_request.status = 'approved'
            process_request.approved_at = now_vn()
            process_request.approved_by_id = session.get('user_id')
            
            asset = process_request.asset
            if process_request.request_type in ['dispose', 'destroy']:
                asset.soft_delete()
            elif process_request.request_type == 'sell':
                asset.status = 'disposed'
        elif action == 'reject':
            process_request.status = 'rejected'
            process_request.rejected_at = now_vn()
            process_request.rejected_reason = data.get('rejected_reason', '')
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'Đã {action} đề nghị thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@api_misa_bp.route('/assets/decrease', methods=['POST'])
@login_required_api
def api_asset_decrease():
    """API ghi giảm tài sản"""
    try:
        data = request.get_json()
        asset_id = int(data.get('asset_id'))
        asset = Asset.query.get_or_404(asset_id)
        
        voucher_code = generate_voucher_code('decrease', db.session, AssetVoucher)
        voucher = AssetVoucher(
            voucher_code=voucher_code,
            voucher_type='decrease',
            voucher_date=datetime.fromisoformat(data.get('voucher_date', today_vn().isoformat())).date(),
            description=f'Ghi giảm tài sản {asset.name}',
            created_by_id=session.get('user_id')
        )
        db.session.add(voucher)
        db.session.flush()
        
        voucher_item = AssetVoucherItem(
            voucher_id=voucher.id,
            asset_id=asset.id,
            old_value=asset.price,
            new_value=0,
            reason=data.get('reason', ''),
            notes=data.get('notes', '')
        )
        db.session.add(voucher_item)
        
        asset.soft_delete()
        asset.price = 0
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Đã ghi giảm thành công',
            'data': {'voucher_code': voucher_code}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@api_misa_bp.route('/assets/depreciation/calculate', methods=['POST'])
@login_required_api
def api_asset_depreciation_calculate():
    """API tính khấu hao"""
    try:
        data = request.get_json()
        period_year = int(data.get('year'))
        period_month = int(data.get('month')) if data.get('month') else None
        method = data.get('method', 'straight_line')
        asset_ids = data.get('asset_ids', [])
        
        results = []
        for asset_id in asset_ids:
            asset = Asset.query.get(asset_id)
            if not asset or asset.deleted_at:
                continue
            
            original_value = asset.price or 0
            if original_value <= 0:
                continue
            
            # Thời gian sử dụng chuẩn (năm) mặc định 5 nếu không có dữ liệu khác
            useful_life_years = getattr(asset, 'useful_life_years', None) or 5
            depreciation_rate = 1.0 / useful_life_years  # Tỷ lệ khấu hao năm (dạng thập phân)
            
            # Tìm lũy kế trước kỳ tính
            prev_query = AssetDepreciation.query.filter(AssetDepreciation.asset_id == asset_id)
            if period_month:
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
                prev_query = prev_query.filter(AssetDepreciation.period_year < period_year)
            prev_deps = prev_query.all()
            prev_accumulated = sum(d.depreciation_amount or 0 for d in prev_deps)
            
            # Công thức đường thẳng: khấu hao năm = Nguyên giá / Thời gian sử dụng; tháng = năm / 12
            if method == 'straight_line':
                annual_amount = original_value / useful_life_years
                depreciation_amount = annual_amount / 12 if period_month else annual_amount
            else:
                # Số dư giảm dần: áp dụng hệ số 2 trên giá trị còn lại
                remaining_value_before = original_value - prev_accumulated
                annual_amount = remaining_value_before * depreciation_rate * 2
                depreciation_amount = annual_amount / 12 if period_month else annual_amount
            
            accumulated = prev_accumulated + depreciation_amount
            remaining_value = original_value - accumulated
            
            existing = AssetDepreciation.query.filter(
                AssetDepreciation.asset_id == asset_id,
                AssetDepreciation.period_year == period_year,
                AssetDepreciation.period_month == period_month
            ).first()
            
            if existing:
                existing.depreciation_amount = depreciation_amount
                existing.accumulated_depreciation = accumulated
                existing.remaining_value = remaining_value
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
            
            results.append({
                'asset_id': asset_id,
                'depreciation_amount': depreciation_amount,
                'accumulated': accumulated,
                'remaining_value': remaining_value
            })
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Đã tính khấu hao thành công', 'data': results})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@api_misa_bp.route('/assets/amortization/calculate', methods=['POST'])
@login_required_api
def api_asset_amortization_calculate():
    """API tính hao mòn"""
    try:
        data = request.get_json()
        period_year = int(data.get('year'))
        asset_data = data.get('assets', [])  # [{asset_id, usage_years, condition_score}]
        
        results = []
        for item in asset_data:
            asset_id = item.get('asset_id')
            asset = Asset.query.get(asset_id)
            if not asset or asset.deleted_at:
                continue
            
            original_value = asset.price or 0
            if original_value <= 0:
                continue
            
            usage_years = int(item.get('usage_years') or 0)
            if usage_years <= 0:
                usage_years = getattr(asset, 'useful_life_years', None) or 5
            
            # Hao mòn đường thẳng theo năm: giá trị hao mòn năm = Nguyên giá / Số năm sử dụng
            annual_amort = original_value / usage_years
            
            # Lũy kế trước năm tính
            prev_amort = AssetAmortization.query.filter(
                AssetAmortization.asset_id == asset_id,
                AssetAmortization.period_year < period_year
            ).order_by(AssetAmortization.period_year.desc()).first()
            prev_remaining = prev_amort.remaining_value if prev_amort else original_value
            
            amortization_amount = annual_amort
            remaining_value = prev_remaining - amortization_amount
            
            amortization_rate = (1.0 / usage_years) * 100
            
            existing = AssetAmortization.query.filter(
                AssetAmortization.asset_id == asset_id,
                AssetAmortization.period_year == period_year
            ).first()
            
            if existing:
                existing.amortization_rate = amortization_rate
                existing.amortization_amount = amortization_amount
                existing.remaining_value = remaining_value
                existing.usage_years = usage_years
                existing.condition_score = item.get('condition_score')
            else:
                amortization = AssetAmortization(
                    asset_id=asset_id,
                    period_year=period_year,
                    original_value=original_value,
                    amortization_rate=amortization_rate,
                    amortization_amount=amortization_amount,
                    remaining_value=remaining_value,
                    usage_years=usage_years,
                    condition_score=item.get('condition_score')
                )
                db.session.add(amortization)
            
            results.append({
                'asset_id': asset_id,
                'amortization_amount': amortization_amount,
                'remaining_value': remaining_value
            })
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Đã tính hao mòn thành công', 'data': results})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@api_misa_bp.route('/inventory', methods=['POST'])
@login_required_api
def api_inventory_create():
    """API tạo đợt kiểm kê"""
    try:
        data = request.get_json()
        inventory_code = generate_inventory_code(db.session, Inventory)
        
        inventory = Inventory(
            inventory_code=inventory_code,
            inventory_name=data.get('inventory_name', ''),
            start_date=datetime.fromisoformat(data.get('start_date')).date(),
            end_date=datetime.fromisoformat(data.get('end_date')).date() if data.get('end_date') else None,
            scope=data.get('scope', ''),
            status='draft',
            created_by_id=session.get('user_id')
        )
        db.session.add(inventory)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Đã tạo đợt kiểm kê thành công',
            'data': {'inventory_code': inventory_code, 'inventory_id': inventory.id}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@api_misa_bp.route('/inventory/<int:inventory_id>/results', methods=['POST'])
@login_required_api
def api_inventory_results(inventory_id):
    """API nhập kết quả kiểm kê"""
    try:
        inventory = Inventory.query.get_or_404(inventory_id)
        data = request.get_json()
        results_data = data.get('results', [])  # [{asset_id, actual_status, actual_value, notes}]
        
        for item in results_data:
            asset_id = item.get('asset_id')
            asset = Asset.query.get(asset_id)
            if not asset:
                continue
            
            book_value = asset.price or 0
            actual_status = item.get('actual_status')
            actual_value = float(item.get('actual_value', book_value))
            difference = actual_value - book_value
            notes = item.get('notes', '')
            
            existing = InventoryResult.query.filter(
                InventoryResult.inventory_id == inventory_id,
                InventoryResult.asset_id == asset_id
            ).first()
            
            if existing:
                existing.actual_status = actual_status
                existing.actual_value = actual_value
                existing.difference = difference
                existing.notes = notes
                existing.checked_by_id = session.get('user_id')
                existing.checked_at = now_vn()
            else:
                result = InventoryResult(
                    inventory_id=inventory_id,
                    asset_id=asset_id,
                    book_value=book_value,
                    actual_status=actual_status,
                    actual_value=actual_value,
                    difference=difference,
                    notes=notes,
                    checked_by_id=session.get('user_id'),
                    checked_at=now_vn()
                )
                db.session.add(result)
        
        inventory.status = 'in_progress'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Đã lưu kết quả kiểm kê thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

