from flask import request, jsonify, session, current_app, url_for
from sqlalchemy import func, or_
import re
from models import Asset, MaintenanceRecord, User, AssetTransfer, AssetType, Inventory, AssetLocation

def ai_chat():
    from app import db
    from sqlalchemy import or_, func, desc, asc, extract
    from datetime import date, datetime, timedelta
    from models import asset_user, Role
    
    """
    Trợ lý ảo AI Smart Assistant - v8.0 (Omniscient Phoenix)
    Hệ thống phân tích đa chiều với khả năng trả lời mọi câu hỏi về:
    - Tài chính: Xếp hạng giá trị, tổng tài sản, phân bổ ngân sách
    - Nhân sự: Ai giữ gì, ai có nhiều nhất, phân công vị trí  
    - Bảo trì: Lịch sử sửa chữa, thiết bị hay hỏng, chi phí
    - Thời gian: Nhập mua theo năm/tháng, tài sản cũ/mới
    - Trạng thái: Đang dùng, hỏng, kho, thanh lý
    """
    try:
        data = request.get_json()
        raw_msg = data.get('message', '').strip()
        msg = raw_msg.lower()
        
        if not msg:
            return jsonify({'response': '🤖 Tôi sẵn sàng giúp bạn! Hãy hỏi tôi bất cứ điều gì về hệ thống.'})
        
        def fmt(val): 
            """Format currency"""
            return "{:,.0f}đ".format(val or 0)
        
        # ==============================================================================
        # LAYER 1: HIGH-LEVEL ANALYTICS (Leaderboards & Comparisons)
        # ==============================================================================
        
        # 1.1 Top Value Holder - "Nhân viên nào giữ tài sản giá trị nhất?"
        if any(k in msg for k in ['giá trị', 'tiền', 'đắt']) and any(k in msg for k in ['nhất', 'cao', 'nhiều']):
            if any(k in msg for k in ['nhân viên', 'người', 'ai']):
                # Query: Find user with highest total asset value
                result = db.session.query(
                    User.id,
                    User.username,
                    User.name,
                    func.sum(Asset.price).label('total_value')
                ).join(asset_user, asset_user.c.user_id == User.id)\
                 .join(Asset, Asset.id == asset_user.c.asset_id)\
                 .filter(User.deleted_at.is_(None), Asset.deleted_at.is_(None))\
                 .group_by(User.id, User.username, User.name)\
                 .order_by(desc('total_value'))\
                 .first()
                
                if result:
                    uid, username, name, total_val = result
                    # Get count
                    count = db.session.query(func.count(asset_user.c.asset_id))\
                        .filter(asset_user.c.user_id == uid).scalar()
                    
                    return jsonify({'response': 
                        f"🏆 <b>Nhân viên giữ tài sản giá trị cao nhất:</b><br>"
                        f"• Tên: <b>{name or username}</b><br>"
                        f"• Số lượng: {count} tài sản<br>"
                        f"• Tổng giá trị: <b style='color:#28a745;'>{fmt(total_val)}</b>"})
                else:
                    return jsonify({'response': '📊 Hiện chưa có dữ liệu phân bổ tài sản cho nhân viên.'})
        
        # 1.2 Top Quantity Holder - "Ai đang giữ nhiều máy nhất?"
        if 'nhiều' in msg and any(k in msg for k in ['ai', 'nhân viên', 'người']) and 'giá' not in msg:
            result = db.session.query(
                User.id,
                User.username, 
                User.name,
                func.count(asset_user.c.asset_id).label('total_count')
            ).join(asset_user, asset_user.c.user_id == User.id)\
             .filter(User.deleted_at.is_(None))\
             .group_by(User.id, User.username, User.name)\
             .order_by(desc('total_count'))\
             .first()
            
            if result:
                uid, username, name, cnt = result
                return jsonify({'response': 
                    f"📊 <b>Nhân viên quản lý nhiều tài sản nhất:</b><br>"
                    f"• <b>{name or username}</b> đang nắm giữ <b>{cnt}</b> thiết bị."})
        
        # 1.3 Most Expensive Asset - "Tài sản đắt nhất?"
        if 'đắt' in msg and 'nhất' in msg and 'ai' not in msg:
            asset = Asset.query.filter(Asset.deleted_at.is_(None))\
                .order_by(desc(Asset.price)).first()
            if asset:
                return jsonify({'response': 
                    f"💎 Tài sản có giá trị cao nhất: <b>{asset.name}</b> "
                    f"({asset.device_code}) - <b>{fmt(asset.price)}</b>"})
        
        # ==============================================================================
        # LAYER 2: MAINTENANCE & RELIABILITY
        # ==============================================================================
        
        # 2.1 Most Problematic Type - "Loại máy nào hay hỏng?"
        if 'loại' in msg and any(k in msg for k in ['hỏng', 'sửa', 'bảo trì']):
            result = db.session.query(
                AssetType.name,
                func.count(MaintenanceRecord.id).label('maintenance_count')
            ).join(Asset, Asset.asset_type_id == AssetType.id)\
             .join(MaintenanceRecord, MaintenanceRecord.asset_id == Asset.id)\
             .group_by(AssetType.id, AssetType.name)\
             .order_by(desc('maintenance_count'))\
             .first()
            
            if result:
                type_name, m_count = result
                return jsonify({'response': 
                    f"⚠️ Loại tài sản <b>{type_name}</b> có tần suất bảo trì cao nhất "
                    f"({m_count} lần). Nên chú ý khi mua loại này."})
        
        # 2.2 Pending Maintenance - "Còn bao nhiêu máy đang sửa?"
        if 'đang' in msg and any(k in msg for k in ['sửa', 'bảo trì']):
            pending = MaintenanceRecord.query.filter(
                MaintenanceRecord.status.in_(['pending', 'in_progress'])
            ).count()
            return jsonify({'response': 
                f"🔧 Hiện có <b>{pending}</b> lượt bảo trì đang được thực hiện."})
        
        # ==============================================================================
        # LAYER 3: TEMPORAL & TIME-BASED
        # ==============================================================================
        
        # 3.1 New This Month - "Tháng này nhập bao nhiêu máy?"
        if 'tháng này' in msg or 'tháng nay' in msg:
            now = datetime.now()
            count = Asset.query.filter(
                Asset.deleted_at.is_(None),
                extract('month', Asset.created_at) == now.month,
                extract('year', Asset.created_at) == now.year
            ).count()
            return jsonify({'response': 
                f"📅 Tháng {now.month}/{now.year} đã tiếp nhận <b>{count}</b> tài sản mới."})
        
        # 3.2 Newest Asset - "Tài sản mới nhất?"
        if 'mới nhất' in msg or 'vừa nhập' in msg:
            latest = Asset.query.filter(Asset.deleted_at.is_(None))\
                .order_by(desc(Asset.created_at)).first()
            if latest:
                return jsonify({'response': 
                    f"🆕 Tài sản mới nhất: <b>{latest.name}</b> ({latest.device_code}) "
                    f"nhập ngày {latest.created_at.strftime('%d/%m/%Y')}."})
        
        # ==============================================================================
        # LAYER 4: STATUS & FILTERING  
        # ==============================================================================
        
        # 4.1 Status Count - "Có bao nhiêu máy đang hỏng?"
        status_keywords = {
            'hỏng': 'broken',
            'hư': 'broken',
            'bảo trì': 'maintenance',
            'kho': 'stock',
            'thanh lý': 'liquidation',
            'đang dùng': 'active'
        }
        
        for keyword, db_status in status_keywords.items():
            if keyword in msg:
                count = Asset.query.filter(
                    Asset.deleted_at.is_(None),
                    Asset.status == db_status
                ).count()
                return jsonify({'response': 
                    f"📊 Có <b>{count}</b> tài sản đang ở trạng thái <b>{db_status.upper()}</b>."})
        
        # ==============================================================================
        # LAYER 5: INDIVIDUAL LOOKUP (Precision Search)
        # ==============================================================================
        
        # ==============================================================================
        # LAYER 5: INDIVIDUAL LOOKUP (Precision Search)
        # ==============================================================================
        
        # Clean keyword extraction - expanded stopwords
        stop_words = r'\b(tìm|xem|cho|biết|là|gì|ai|của|máy|thiết|bị|tài|sản|nó|tôi|thông|tin|hiện|có|danh|sách|liệt|kê|hihi|haha|với|tại|trong)\b'
        clean = re.sub(stop_words, '', msg).strip()
        # Remove extra spaces
        clean = re.sub(r'\s+', ' ', clean).strip()

        # 5.1 General User List - "Liệt kê người dùng", "Danh sách nhân viên"
        if any(k in msg for k in ['người dùng', 'nhân viên', 'tài khoản']) and any(k in msg for k in ['danh sách', 'liệt kê', 'tất cả']):
            users_list = User.query.filter(User.deleted_at.is_(None)).limit(10).all()
            if users_list:
                resp = "👥 <b>Danh sách nhân viên (tối đa 10):</b><br>"
                for u in users_list:
                    asset_count = db.session.query(func.count(asset_user.c.asset_id)).filter(asset_user.c.user_id == u.id).scalar()
                    resp += f"• <b>{u.name or u.username}</b>: {asset_count} tài sản<br>"
                return jsonify({'response': resp})

        # 5.2 Asset Search by Code/Name
        if len(clean) > 1:
            asset = Asset.query.filter(
                Asset.deleted_at.is_(None),
                or_(
                    Asset.device_code.ilike(f'%{clean}%'),
                    Asset.name.ilike(f'%{clean}%')
                )
            ).order_by(Asset.created_at.desc()).first()
            
            if asset:
                session['ai_last_asset_id'] = asset.id
                # Get all users assigned to this asset
                assigned_users = [u.username for u in asset.assigned_users]
                owner = ", ".join(assigned_users) if assigned_users else "Chưa phân công"
                
                return jsonify({'response': 
                    f"📌 <b>Tìm thấy tài sản: {asset.name}</b> ({asset.device_code or 'Không mã'})<br>"
                    f"• Giá trị: <b>{fmt(asset.price)}</b><br>"
                    f"• Loại: {asset.asset_type.name if asset.asset_type else 'N/A'}<br>"
                    f"• Trạng thái: <b>{asset.status.upper()}</b><br>"
                    f"• Người giữ: <b>{owner}</b><br>"
                    f"• Ghi chú: {asset.notes or 'Không có'}"})
        
        # 5.3 User Search by Name/Username
        if len(clean) > 1 and any(k in msg for k in ['nhân viên', 'người dùng', 'của', 'giữ', 'nắm']):
            user = User.query.filter(
                User.deleted_at.is_(None),
                or_(
                    User.username.ilike(f'%{clean}%'),
                    User.name.ilike(f'%{clean}%')
                )
            ).first()
            
            if user:
                assets = user.assigned_assets
                total_val = sum(a.price for a in assets if a.price)
                
                asset_list = ""
                if assets:
                    # Sort active ones first
                    assets_sorted = sorted(assets, key=lambda x: x.price or 0, reverse=True)
                    asset_list = "<br><b>Các tài sản đang giữ:</b><br>• " + "<br>• ".join([f"{a.name} ({fmt(a.price)})" for a in assets_sorted[:5]])
                    if len(assets) > 5:
                        asset_list += f"<br>• <i>...và {len(assets)-5} tài sản khác</i>"
                
                return jsonify({'response': 
                    f"👤 <b>Nhân viên: {user.name or user.username}</b><br>"
                    f"• Đang quản lý: <b>{len(assets)}</b> tài sản<br>"
                    f"• Tổng giá trị: <b style='color:#28a745;'>{fmt(total_val)}</b><br>"
                    f"{asset_list}"})

        # Extra: If they ask for 'thông tin người dùng/nhân viên'
        if any(k in msg for k in ['thông tin người dùng', 'thông tin nhân viên', 'danh sách nhân viên', 'danh sách người dùng']):
            # Fetch users and their asset counts (both direct and many-to-many)
            all_users = User.query.filter(User.deleted_at.is_(None)).limit(15).all()
            
            if not all_users:
                return jsonify({'response': "👥 Hệ thống hiện chưa có thông tin nhân viên nào."})
                
            resp = "👥 <b>DANH SÁCH NHÂN VIÊN HỆ THỐNG:</b><br><br>"
            for u in all_users:
                # Count assets from direct user_id
                direct_count = Asset.query.filter(Asset.user_id == u.id, Asset.deleted_at.is_(None)).count()
                # Count assets from many-to-many
                secondary_count = len(u.assigned_assets)
                total_assets = direct_count + secondary_count
                
                status_icon = "🟢" if u.is_active else "🔴"
                resp += f"{status_icon} <b>{u.name or u.username}</b> ({u.username}) - Đang giữ: <b>{total_assets}</b> tài sản<br>"
            
            if len(all_users) >= 15:
                resp += "<br><i>... và một số nhân viên khác. Bạn có thể gõ tên cụ thể để xem chi tiết.</i>"
            
            return jsonify({'response': resp})

        # ==============================================================================
        # LAYER 6: SYSTEM OVERVIEW (General Stats)
        # ==============================================================================
        
        # ==============================================================================
        # LAYER 6: SYSTEM OVERVIEW (General Stats)
        # ==============================================================================
        
        if any(k in msg for k in ['tổng', 'hệ thống', 'tất cả', 'báo cáo', 'tổng quan']):
            total = Asset.query.filter(Asset.deleted_at.is_(None)).count()
            total_val = db.session.query(func.sum(Asset.price))\
                .filter(Asset.deleted_at.is_(None)).scalar() or 0
            
            # Status breakdown
            stats = db.session.query(Asset.status, func.count(Asset.id))\
                .filter(Asset.deleted_at.is_(None))\
                .group_by(Asset.status).all()
            
            # Accurate active user count (checks both Asset.user_id and many-to-many table)
            users_with_assets_primary = db.session.query(Asset.user_id).filter(Asset.user_id.isnot(None), Asset.deleted_at.is_(None))
            users_with_assets_secondary = db.session.query(asset_user.c.user_id)
            active_users_count = db.session.query(func.count(func.distinct(users_with_assets_primary.union(users_with_assets_secondary).subquery().c.user_id))).scalar() or 0

            status_map_vi = {
                'active': 'Đang sử dụng',
                'maintenance': 'Bảo trì',
                'broken': 'Hỏng',
                'disposed': 'Đã thanh lý',
                'stock': 'Trong kho'
            }
            
            status_str = "<br>".join([f"• {status_map_vi.get(s, s.upper())}: <b>{c}</b>" for s, c in stats])
            
            return jsonify({'response': 
                f"📊 <b>BÁO CÁO TỔNG QUAN HỆ THỐNG</b><br>"
                f"• Tổng tài sản: <b>{total}</b><br>"
                f"• Tổng giá trị: <b style='color:#28a745;'>{fmt(total_val)}</b><br>"
                f"• Số nhân viên đang giữ máy: <b>{active_users_count}</b><br><br>"
                f"<b>📍 Phân bổ theo trạng thái:</b><br>{status_str}"})
        
        # ==============================================================================
        # FALLBACK: Intelligent Suggestion
        # ==============================================================================
        
        total_assets = Asset.query.filter(Asset.deleted_at.is_(None)).count()
        total_users = User.query.filter(User.deleted_at.is_(None)).count()
        
        return jsonify({'response': 
            f"🤔 Xin lỗi, tôi chưa hiểu rõ câu hỏi của bạn.<br><br>"
            f"<b>Hệ thống hiện có:</b><br>"
            f"• <b>{total_assets}</b> tài sản<br>"
            f"• <b>{total_users}</b> người dùng<br><br>"
            f"<b>Gợi ý cho bạn:</b><br>"
            f"• <i>'Nhân viên giữ tài sản giá trị nhất?'</i><br>"
            f"• <i>'Thông tin người dùng manager1'</i><br>"
            f"• <i>'Hệ thống có bao nhiêu máy đang hỏng?'</i><br>"
            f"• <i>'Tìm máy Server'</i>"})
    
    except Exception as e:
        current_app.logger.error(f"AI v8.0 Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'response': f'❌ Lỗi hệ thống: {str(e)}<br>Vui lòng thử lại với câu hỏi đơn giản hơn.'})
