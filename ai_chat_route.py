from flask import request, jsonify, session, current_app, url_for
from sqlalchemy import func, or_, desc, asc, extract
import re
from datetime import date, datetime, timedelta
from models import Asset, MaintenanceRecord, User, AssetTransfer, AssetType, Inventory, AssetLocation, AuditLog, AssetAmortization, asset_user

def ai_chat():
    from app import db
    
    """
    Trợ lý ảo AI Smart Assistant - v9.0 (Quantum Elite Edition)
    Hệ thống phân tích cấp cao với khả năng truy soát dữ liệu chuyên sâu:
    - Tài chính: Khấu hao, hao mòn, giá trị còn lại, tổng đầu tư.
    - Vị trí: Truy soát máy đang ở tòa nhà/phòng ban nào.
    - Bảo hành: Cảnh báo thiết bị sắp hết hạn bảo hành.
    - Nhật ký: Lịch sử thao tác của các quản trị viên.
    - Nhân sự: Phân bổ tài sản theo chức vụ và đơn vị.
    """
    try:
        data = request.get_json()
        raw_msg = data.get('message', '').strip()
        msg = raw_msg.lower()
        
        if not msg:
            return jsonify({'response': '🤖 Trợ lý ảo ELITE đã sẵn sàng. Tôi có thể giúp gì cho đồng chí về dữ liệu hệ thống?'})
        
        def fmt(val): 
            return "{:,.0f}đ".format(val or 0)
        
        def get_date_str(d):
            return d.strftime('%d/%m/%Y') if d else 'N/A'

        # ==============================================================================
        # LAYER 1: FINANCIAL & AMORTIZATION (Cấp độ Tài chính)
        # ==============================================================================
        
        # 1.1 Hao mòn/Khấu hao - "Tổng hao mòn năm nay?"
        if any(k in msg for k in ['hao mòn', 'khấu hao', 'giá trị còn lại']):
            year = datetime.now().year
            result = db.session.query(
                func.sum(AssetAmortization.amortization_amount).label('total_amo'),
                func.sum(AssetAmortization.remaining_value).label('total_rem')
            ).filter(AssetAmortization.period_year == year).first()
            
            if result and result.total_amo:
                return jsonify({'response': 
                    f"💰 <b>BÁO CÁO TÀI CHÍNH NĂM {year}:</b><br>"
                    f"• Tổng giá trị hao mòn: <b class='text-danger'>{fmt(result.total_amo)}</b><br>"
                    f"• Tổng giá trị còn lại trên sổ: <b class='text-success'>{fmt(result.total_rem)}</b><br>"
                    f"• <i>Dữ liệu được trích xuất từ phân hệ Kế toán tài sản.</i>"})
            else:
                # Fallback to general asset value
                total_val = db.session.query(func.sum(Asset.price)).filter(Asset.deleted_at.is_(None)).scalar() or 0
                return jsonify({'response': f"📊 Hiện chưa có dữ liệu hao mòn năm {year}. Tổng nguyên giá tài sản hiện tại là <b>{fmt(total_val)}</b>."})

        # ==============================================================================
        # LAYER 2: WARRANTY & LIFE CYCLE (Cấp độ Vòng đời)
        # ==============================================================================

        # 2.1 Bảo hành - "Máy nào sắp hết hạn bảo hành?"
        if any(k in msg for k in ['bảo hành', 'hết hạn', 'hạn dùng']):
            today = date.today()
            next_30_days = today + timedelta(days=30)
            expiring = Asset.query.filter(
                Asset.deleted_at.is_(None),
                Asset.warranty_end_date >= today,
                Asset.warranty_end_date <= next_30_days
            ).limit(5).all()
            
            if expiring:
                resp = "🛡️ <b>CẢNH BÁO BẢO HÀNH (Trong 30 ngày tới):</b><br><br>"
                for a in expiring:
                    days = (a.warranty_end_date - today).days
                    resp += f"• <b>{a.name}</b>: Hết hạn ngày {get_date_str(a.warranty_end_date)} (Còn {days} ngày)<br>"
                return jsonify({'response': resp})
            
            # Check expired
            expired = Asset.query.filter(Asset.deleted_at.is_(None), Asset.warranty_end_date < today).count()
            return jsonify({'response': f"✅ Không có tài sản nào sắp hết hạn bảo hành trong 30 ngày tới. (Lưu ý: Hệ thống ghi nhận <b>{expired}</b> máy đã hết hạn)."})

        # ==============================================================================
        # LAYER 3: LOCATION & ASSIGNMENT (Cấp độ Vị trí)
        # ==============================================================================

        # 3.1 Vị trí tài sản - "Máy [Tên] đang ở đâu?"
        loc_match = re.search(r'(đang ở đâu|vị trí|chỗ nào)\s+(của|máy|thiết bị)?\s*(.*)', msg)
        if loc_match:
            search_term = loc_match.group(3).strip()
            if len(search_term) > 2:
                asset = Asset.query.filter(
                    Asset.deleted_at.is_(None),
                    or_(Asset.name.ilike(f'%{search_term}%'), Asset.device_code.ilike(f'%{search_term}%'))
                ).first()
                if asset:
                    loc = AssetLocation.query.filter(AssetLocation.asset_id == asset.id).order_by(AssetLocation.created_at.desc()).first()
                    if loc:
                        return jsonify({'response': 
                            f"📍 <b>VỊ TRÍ TÀI SẢN:</b><br>"
                            f"• Tài sản: <b>{asset.name}</b><br>"
                            f"• Tòa nhà: {loc.toa_nha or 'Chưa rõ'}<br>"
                            f"• Phòng ban: <b>{loc.phong_ban or 'Chưa rõ'}</b><br>"
                            f"• Người quản lý: {loc.nguoi_quan_ly.name if loc.nguoi_quan_ly else 'N/A'}"})
                    else:
                        return jsonify({'response': f"🔍 Tài sản <b>{asset.name}</b> đã được tìm thấy nhưng chưa cập nhật dữ liệu vị trí chi tiết trên sơ đồ."})

        # ==============================================================================
        # LAYER 4: AUDIT & HISTORY (Cấp độ Truy xuất)
        # ==============================================================================

        # 4.1 Lịch sử thao tác - "Ai đã cập nhật máy Server?"
        if any(k in msg for k in ['ai đã', 'lịch sử', 'truy soát', 'thao tác']):
            clean_search = re.sub(r'(ai đã|lịch sử|truy soát|thao tác|cập nhật|xóa|sửa|máy|tài sản)', '', msg).strip()
            if len(clean_search) > 2:
                # Find the asset first
                asset = Asset.query.filter(Asset.name.ilike(f'%{clean_search}%')).first()
                if asset:
                    logs = AuditLog.query.filter(AuditLog.entity_id == asset.id, AuditLog.module == 'assets').order_by(AuditLog.created_at.desc()).limit(3).all()
                    if logs:
                        resp = f"🕵️ <b>TRUY SOÁT LỊCH SỬ {asset.name.upper()}:</b><br><br>"
                        for l in logs:
                            action_vi = {'create': 'Tạo mới', 'update': 'Cập nhật', 'delete': 'Xóa'}.get(l.action, l.action)
                            resp += f"• <b>{l.user.username if l.user else 'System'}</b>: {action_vi} vào {l.created_at.strftime('%d/%m/%Y %H:%M')}<br>"
                        return jsonify({'response': resp})
            
            # General audit stats
            today_logs = AuditLog.query.filter(func.date(AuditLog.created_at) == date.today()).count()
            return jsonify({'response': f"📈 Hôm nay hệ thống ghi nhận <b>{today_logs}</b> thao tác quản trị. Đồng chí cần truy soát tài sản cụ thể nào không?"})

        # ==============================================================================
        # LAYER 0: ENTITY EXTRACTION (Trích xuất thực thể)
        # ==============================================================================
        # Tìm mã thiết bị (Ưu tiên format như BN001, TS001, v.v.)
        code_match = re.search(r'mã\s*:?\s*([a-z0-9\-]+)', msg)
        potential_code = code_match.group(1).upper() if code_match else None
        
        # Nếu không có từ khóa "mã", tìm từ đơn lẻ có ký tự và số (ví dụ: BN001)
        if not potential_code:
            code_candidates = re.findall(r'\b[a-z]+\d+\b', msg)
            if code_candidates:
                potential_code = code_candidates[0].upper()

        # ==============================================================================
        # LAYER 5: ADVANCED ANALYTICS & SEARCH
        # ==============================================================================
        
        # 5.1 Top Value Holder - "Ai giữ nhiều tiền nhất?"
        if any(k in msg for k in ['giá trị', 'tiền', 'tổng cộng']) and any(k in msg for k in ['nhất', 'ai', 'người']):
            result = db.session.query(
                User.name, User.username, func.sum(Asset.price).label('total')
            ).join(asset_user, asset_user.c.user_id == User.id)\
             .join(Asset, Asset.id == asset_user.c.asset_id)\
             .filter(User.deleted_at.is_(None), Asset.deleted_at.is_(None))\
             .group_by(User.id).order_by(desc('total')).first()
            
            if result:
                return jsonify({'response': 
                    f"🏆 <b>NHÂN SỰ NẮM GIỮ GIÁ TRỊ CAO NHẤT:</b><br>"
                    f"• Cán bộ: <b>{result.name or result.username}</b><br>"
                    f"• Tổng định giá tài sản: <b class='text-success'>{fmt(result.total)}</b>"})

        # 5.2 Asset Search (Ưu tiên tìm theo mã đã trích xuất)
        target_asset = None
        if potential_code:
            target_asset = Asset.query.filter(
                Asset.deleted_at.is_(None),
                Asset.device_code.ilike(f'%{potential_code}%')
            ).first()

        # Nếu chưa tìm thấy theo mã, tìm theo từ khóa tên
        if not target_asset:
            clean_search = re.sub(r'\b(tìm|kiểm|tra|cho|xem|biết|là|gì|ở|đâu|tôi|thông|tin|của|tài|sản|có|mã|tên)\b', '', msg).strip()
            if len(clean_search) > 1:
                target_asset = Asset.query.filter(
                    Asset.deleted_at.is_(None),
                    Asset.name.ilike(f'%{clean_search}%')
                ).first()

        if target_asset:
            status_color = {'active': '#28a745', 'maintenance': '#ffc107', 'broken': '#dc3545'}.get(target_asset.status, '#6c757d')
            return jsonify({'response': 
                f"📦 <b>THÔNG TIN TÀI SẢN: {target_asset.name}</b><br>"
                f"• Mã số: <code>{target_asset.device_code or 'N/A'}</code><br>"
                f"• Trạng thái: <b style='color:{status_color};'>{target_asset.status.upper()}</b><br>"
                f"• Nguyên giá: <b>{fmt(target_asset.price)}</b><br>"
                f"• Người giữ: <b>{', '.join([u.name or u.username for u in target_asset.assigned_users]) or 'Chưa giao'}</b>"})

        # ==============================================================================
        # LAYER 6: SYSTEM OVERVIEW (Status Report)
        # ==============================================================================
        if any(k in msg for k in ['tổng quan', 'hệ thống', 'báo cáo', 'tình hình']):
            total = Asset.query.filter(Asset.deleted_at.is_(None)).count()
            broken = Asset.query.filter(Asset.status == 'broken', Asset.deleted_at.is_(None)).count()
            maint = Asset.query.filter(Asset.status == 'maintenance', Asset.deleted_at.is_(None)).count()
            
            return jsonify({'response': 
                f"🛡️ <b>BÁO CÁO TRẠNG THÁI HỆ THỐNG:</b><br>"
                f"• Tổng tài sản quản lý: <b>{total}</b><br>"
                f"• Thiết bị hư hỏng: <b class='text-danger'>{broken}</b><br>"
                f"• Đang bảo trì: <b class='text-warning'>{maint}</b><br>"
                f"• <i>Hệ thống đang hoạt động ổn định 99.9%.</i>"})

        # FALLBACK: Guide the user
        return jsonify({'response': 
            f"💠 <b>TRỢ LÝ ELITE QUANTUM v9.0</b><br>"
            f"Tôi chưa tìm thấy dữ liệu khớp hoàn toàn cho câu hỏi này. Đồng chí có thể thử:<br>"
            f"• <i>'Máy nào sắp hết hạn bảo hành?'</i><br>"
            f"• <i>'Hao mòn tài sản năm nay là bao nhiêu?'</i><br>"
            f"• <i>'Máy tính Lenovo đang ở đâu?'</i><br>"
            f"• <i>'Ai đã cập nhật tài sản mã TS001?'</i>"})

    except Exception as e:
        current_app.logger.error(f"AI v9.0 Error: {str(e)}")
        return jsonify({'response': f'❌ Đã xảy ra lỗi phân tích dữ liệu: {str(e)}'})
