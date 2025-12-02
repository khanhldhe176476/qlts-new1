#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script tạo dữ liệu mẫu đa dạng và realistic cho hệ thống quản lý tài sản
Tạo assets, maintenance records, transfers với dữ liệu theo thời gian
"""

import sys
import io
import random
from datetime import datetime, date, timedelta

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app import app
from models import db, Role, User, AssetType, Asset, MaintenanceRecord, AssetTransfer, AuditLog
from utils.timezone import now_vn, today_vn

# Danh sách tên tài sản realistic
ASSET_NAMES = {
    'Máy tính': [
        'Laptop Dell Latitude 5520', 'Laptop HP EliteBook 840', 'Laptop Lenovo ThinkPad X1',
        'Laptop MacBook Pro 14"', 'Laptop Asus ZenBook', 'Máy tính để bàn Dell OptiPlex',
        'Máy tính để bàn HP ProDesk', 'Máy tính để bàn Lenovo ThinkCentre',
        'Máy tính để bàn Acer Veriton', 'Laptop Dell Inspiron 15', 'Laptop HP Pavilion',
        'Laptop Lenovo IdeaPad', 'Máy tính để bàn Intel NUC', 'Laptop MSI Modern',
        'Máy tính để bàn ASUS VivoMini'
    ],
    'Thiết bị văn phòng': [
        'Máy in HP LaserJet Pro', 'Máy in Canon PIXMA', 'Máy in Brother HL',
        'Máy photocopy Canon IR', 'Máy photocopy Ricoh', 'Máy scan HP ScanJet',
        'Máy fax Panasonic', 'Máy hủy giấy Fellowes', 'Máy đóng sách',
        'Máy in đa chức năng HP', 'Máy in đa chức năng Canon', 'Máy in màu Epson'
    ],
    'Thiết bị mạng': [
        'Router Cisco Catalyst', 'Router TP-Link Archer', 'Switch Cisco 24 port',
        'Switch TP-Link 16 port', 'Access Point Ubiquiti', 'Modem ADSL',
        'Modem Fiber', 'Firewall Fortinet', 'Router WiFi 6 ASUS',
        'Switch managed Netgear', 'Access Point TP-Link', 'Router MikroTik'
    ],
    'Thiết bị điện tử': [
        'iPhone 14 Pro', 'Samsung Galaxy S23', 'iPad Pro 12.9"', 'iPad Air',
        'Máy ảnh Canon EOS', 'Máy ảnh Nikon D850', 'Loa JBL Charge',
        'Loa Sony SRS', 'Tai nghe AirPods Pro', 'Tai nghe Sony WH',
        'Màn hình Dell 27"', 'Màn hình LG UltraWide', 'Màn hình Samsung 32"',
        'Webcam Logitech C920', 'Microphone Blue Yeti'
    ],
    'Nội thất': [
        'Bàn làm việc gỗ 120cm', 'Bàn làm việc gỗ 160cm', 'Bàn họp gỗ lớn',
        'Ghế văn phòng ergonomic', 'Ghế xoay văn phòng', 'Ghế họp',
        'Tủ tài liệu 2 ngăn', 'Tủ tài liệu 4 ngăn', 'Kệ sách 5 tầng',
        'Kệ tài liệu di động', 'Bàn tròn họp', 'Ghế khách',
        'Sofa văn phòng', 'Bàn coffee', 'Tủ locker'
    ],
    'Thiết bị điện': [
        'Quạt điều hòa', 'Máy lạnh Daikin 1HP', 'Máy lạnh LG 1.5HP',
        'Máy lạnh Samsung 2HP', 'Quạt trần', 'Quạt đứng',
        'Đèn bàn LED', 'Đèn chiếu sáng văn phòng', 'Ổ cắm đa năng',
        'Bộ lưu điện UPS', 'Bộ lưu điện APC', 'Máy phát điện'
    ]
}

# Giá tiền mẫu theo loại (VNĐ)
PRICE_RANGES = {
    'Máy tính': (8000000, 35000000),
    'Thiết bị văn phòng': (2000000, 15000000),
    'Thiết bị mạng': (500000, 12000000),
    'Thiết bị điện tử': (3000000, 40000000),
    'Nội thất': (500000, 8000000),
    'Thiết bị điện': (1000000, 25000000)
}

# Trạng thái và tỷ lệ
STATUS_WEIGHTS = {
    'active': 0.75,      # 75% đang sử dụng
    'maintenance': 0.15, # 15% bảo trì
    'disposed': 0.10     # 10% thanh lý
}

def random_date(start_year=2020, end_year=2025):
    """Tạo ngày ngẫu nhiên trong khoảng"""
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    days_between = (end - start).days
    random_days = random.randint(0, days_between)
    return start + timedelta(days=random_days)

def generate_assets(num_assets=200):
    """Tạo assets đa dạng"""
    print(f"\n📦 Đang tạo {num_assets} tài sản...")
    
    asset_types = AssetType.query.filter(AssetType.deleted_at.is_(None)).all()
    users = User.query.filter(User.deleted_at.is_(None), User.is_active == True).all()
    
    if not asset_types:
        print("❌ Chưa có loại tài sản. Vui lòng tạo loại tài sản trước.")
        return 0
    
    if not users:
        print("❌ Chưa có người dùng. Vui lòng tạo người dùng trước.")
        return 0
    
    created = 0
    today = today_vn()
    
    for i in range(num_assets):
        try:
            # Chọn ngẫu nhiên loại tài sản
            asset_type = random.choice(asset_types)
            type_name = asset_type.name
            
            # Chọn tên từ danh sách hoặc tạo tên mới
            if type_name in ASSET_NAMES:
                asset_name = random.choice(ASSET_NAMES[type_name])
                # Thêm số serial để tránh trùng
                if random.random() < 0.3:  # 30% có số serial
                    asset_name += f" - SN{random.randint(1000, 9999)}"
            else:
                asset_name = f"{type_name} {i+1}"
            
            # Chọn giá tiền
            if type_name in PRICE_RANGES:
                min_price, max_price = PRICE_RANGES[type_name]
                price = random.randint(min_price, max_price)
            else:
                price = random.randint(1000000, 20000000)
            
            # Số lượng (phần lớn là 1, một số có nhiều)
            if random.random() < 0.15:  # 15% có số lượng > 1
                quantity = random.randint(2, 10)
            else:
                quantity = 1
            
            # Trạng thái theo tỷ lệ
            status = random.choices(
                list(STATUS_WEIGHTS.keys()),
                weights=list(STATUS_WEIGHTS.values())
            )[0]
            
            # Ngày mua (trong 5 năm qua)
            purchase_date = random_date(2020, 2025)
            
            # Ngày tạo (có thể khác ngày mua)
            created_date = purchase_date + timedelta(days=random.randint(0, 30))
            if created_date > today:
                created_date = today - timedelta(days=random.randint(1, 90))
            
            # Chọn người dùng ngẫu nhiên
            user = random.choice(users)
            
            # Mã thiết bị
            device_code = f"{type_name[:2].upper()}{random.randint(100, 999)}"
            
            # Condition label
            conditions = ['Mới', 'Còn tốt', 'Cần kiểm tra', 'Đã cũ']
            condition = random.choice(conditions)
            
            # Tạo asset
            asset = Asset(
                name=asset_name,
                price=price,
                quantity=quantity,
                status=status,
                asset_type_id=asset_type.id,
                user_id=user.id,
                purchase_date=purchase_date,
                device_code=device_code,
                condition_label=condition,
                user_text=f"Tài sản được cấp cho {user.username}",
                notes=f"Tài sản được mua vào {purchase_date.strftime('%d/%m/%Y')}",
                created_at=datetime.combine(created_date, datetime.min.time())
            )
            
            db.session.add(asset)
            created += 1
            
            if (i + 1) % 50 == 0:
                print(f"  Đã tạo {i + 1}/{num_assets} tài sản...")
                db.session.commit()
        
        except Exception as e:
            print(f"  Lỗi khi tạo tài sản {i+1}: {str(e)}")
            db.session.rollback()
            continue
    
    db.session.commit()
    print(f"✅ Đã tạo {created} tài sản")
    return created

def generate_maintenance_records(num_records=150):
    """Tạo maintenance records theo thời gian"""
    print(f"\n🔧 Đang tạo {num_records} bản ghi bảo trì...")
    
    assets = Asset.query.filter(Asset.deleted_at.is_(None)).all()
    if not assets:
        print("❌ Chưa có tài sản. Vui lòng tạo tài sản trước.")
        return 0
    
    maintenance_types = ['maintenance', 'repair', 'inspection', 'upgrade']
    maintenance_statuses = ['completed', 'scheduled', 'in_progress', 'cancelled']
    vendors = ['Công ty ABC', 'Dịch vụ XYZ', 'Nhà cung cấp DEF', 'Trung tâm bảo hành', None]
    persons = ['Nguyễn Văn A', 'Trần Thị B', 'Lê Văn C', 'Phạm Thị D', 'System']
    
    created = 0
    today = today_vn()
    
    for i in range(num_records):
        try:
            asset = random.choice(assets)
            
            # Ngày bảo trì (trong 2 năm qua)
            maintenance_date = random_date(2023, 2025)
            if maintenance_date > today:
                maintenance_date = today - timedelta(days=random.randint(1, 180))
            
            # Loại bảo trì
            mtype = random.choice(maintenance_types)
            
            # Mô tả
            descriptions = {
                'maintenance': 'Bảo trì định kỳ',
                'repair': 'Sửa chữa',
                'inspection': 'Kiểm tra định kỳ',
                'upgrade': 'Nâng cấp phần mềm'
            }
            description = descriptions.get(mtype, 'Bảo trì')
            
            # Chi phí
            max_cost = int(asset.price // 10) if asset.price > 0 else 0
            cost = float(random.randint(0, max_cost)) if max_cost > 0 else 0.0
            
            # Trạng thái
            status = random.choice(maintenance_statuses)
            
            # Ngày bảo trì tiếp theo (nếu completed)
            next_due_date = None
            if status == 'completed' and random.random() < 0.7:
                next_due_date = maintenance_date + timedelta(days=random.randint(180, 365))
            
            maintenance = MaintenanceRecord(
                asset_id=asset.id,
                maintenance_date=maintenance_date,
                type=mtype,
                description=description,
                vendor=random.choice(vendors),
                person_in_charge=random.choice(persons),
                cost=cost,
                next_due_date=next_due_date,
                status=status
            )
            
            db.session.add(maintenance)
            created += 1
            
            if (i + 1) % 50 == 0:
                print(f"  Đã tạo {i + 1}/{num_records} bản ghi bảo trì...")
                db.session.commit()
        
        except Exception as e:
            print(f"  Lỗi khi tạo bản ghi bảo trì {i+1}: {str(e)}")
            db.session.rollback()
            continue
    
    db.session.commit()
    print(f"✅ Đã tạo {created} bản ghi bảo trì")
    return created

def generate_transfers(num_transfers=50):
    """Tạo asset transfers"""
    print(f"\n🔄 Đang tạo {num_transfers} bàn giao tài sản...")
    
    assets = Asset.query.filter(
        Asset.deleted_at.is_(None),
        Asset.status == 'active',
        Asset.quantity > 0
    ).all()
    
    users = User.query.filter(User.deleted_at.is_(None), User.is_active == True).all()
    
    if len(assets) < 2 or len(users) < 2:
        print("❌ Cần ít nhất 2 tài sản và 2 người dùng để tạo bàn giao.")
        return 0
    
    created = 0
    today = today_vn()
    
    for i in range(num_transfers):
        try:
            asset = random.choice(assets)
            from_user = asset.user
            if not from_user:
                from_user = random.choice(users)
            
            # Chọn người nhận khác người gửi
            to_users = [u for u in users if u.id != from_user.id]
            if not to_users:
                continue
            to_user = random.choice(to_users)
            
            # Số lượng bàn giao (không vượt quá số lượng hiện có)
            max_qty = min(asset.quantity, 5)
            expected_quantity = random.randint(1, max_qty)
            
            # Ngày tạo (trong 1 năm qua)
            created_date = random_date(2024, 2025)
            if created_date > today:
                created_date = today - timedelta(days=random.randint(1, 90))
            
            # Trạng thái
            statuses = ['pending', 'confirmed', 'cancelled']
            weights = [0.3, 0.6, 0.1]  # 30% pending, 60% confirmed, 10% cancelled
            status = random.choices(statuses, weights=weights)[0]
            
            # Tạo mã bàn giao
            transfer_code = f"BG{random.randint(1000, 9999)}"
            
            # Tạo token xác nhận
            import secrets
            confirmation_token = secrets.token_urlsafe(32)
            token_expires_at = created_date + timedelta(days=7)
            
            transfer = AssetTransfer(
                asset_id=asset.id,
                from_user_id=from_user.id,
                to_user_id=to_user.id,
                expected_quantity=expected_quantity,
                confirmed_quantity=expected_quantity if status == 'confirmed' else 0,
                status=status,
                transfer_code=transfer_code,
                confirmation_token=confirmation_token,
                token_expires_at=datetime.combine(token_expires_at, datetime.min.time()),
                notes=f"Bàn giao tài sản từ {from_user.username} sang {to_user.username}",
                created_at=datetime.combine(created_date, datetime.min.time())
            )
            
            if status == 'confirmed':
                transfer.confirmed_at = datetime.combine(created_date + timedelta(days=random.randint(1, 7)), datetime.min.time())
            
            db.session.add(transfer)
            created += 1
            
            if (i + 1) % 20 == 0:
                print(f"  Đã tạo {i + 1}/{num_transfers} bàn giao...")
                db.session.commit()
        
        except Exception as e:
            print(f"  Lỗi khi tạo bàn giao {i+1}: {str(e)}")
            db.session.rollback()
            continue
    
    db.session.commit()
    print(f"✅ Đã tạo {created} bàn giao tài sản")
    return created

def generate_audit_logs(num_logs=300):
    """Tạo audit logs"""
    print(f"\n📝 Đang tạo {num_logs} nhật ký audit...")
    
    users = User.query.filter(User.deleted_at.is_(None), User.is_active == True).all()
    assets = Asset.query.filter(Asset.deleted_at.is_(None)).limit(100).all()
    
    if not users:
        print("❌ Chưa có người dùng.")
        return 0
    
    modules = ['assets', 'users', 'asset_types', 'maintenance', 'transfer']
    actions = ['create', 'update', 'delete', 'view', 'export', 'import']
    
    created = 0
    today = today_vn()
    
    for i in range(num_logs):
        try:
            user = random.choice(users)
            module = random.choice(modules)
            action = random.choice(actions)
            
            # Entity ID (nếu có)
            entity_id = None
            if module == 'assets' and assets:
                entity_id = random.choice(assets).id
            
            # Ngày tạo (trong 1 năm qua)
            log_date = random_date(2024, 2025)
            if log_date > today:
                log_date = today - timedelta(days=random.randint(1, 90))
            
            # Chi tiết
            details = f"{action} {module}"
            if entity_id:
                details += f" (ID: {entity_id})"
            
            audit_log = AuditLog(
                user_id=user.id,
                module=module,
                action=action,
                entity_id=entity_id,
                details=details,
                created_at=datetime.combine(log_date, datetime.min.time())
            )
            
            db.session.add(audit_log)
            created += 1
            
            if (i + 1) % 100 == 0:
                print(f"  Đã tạo {i + 1}/{num_logs} nhật ký...")
                db.session.commit()
        
        except Exception as e:
            print(f"  Lỗi khi tạo nhật ký {i+1}: {str(e)}")
            db.session.rollback()
            continue
    
    db.session.commit()
    print(f"✅ Đã tạo {created} nhật ký audit")
    return created

def main():
    """Hàm chính"""
    print("=" * 60)
    print("TAO DU LIEU MAU CHO HE THONG QUAN LY TAI SAN")
    print("=" * 60)
    
    with app.app_context():
        # Kiểm tra dữ liệu hiện có
        existing_assets = Asset.query.filter(Asset.deleted_at.is_(None)).count()
        existing_maintenance = MaintenanceRecord.query.filter(MaintenanceRecord.deleted_at.is_(None)).count()
        existing_transfers = AssetTransfer.query.count()
        existing_logs = AuditLog.query.count()
        
        print(f"\n📊 Dữ liệu hiện có:")
        print(f"   - Tài sản: {existing_assets}")
        print(f"   - Bảo trì: {existing_maintenance}")
        print(f"   - Bàn giao: {existing_transfers}")
        print(f"   - Nhật ký: {existing_logs}")
        
        # Tính số lượng cần tạo (để có tổng cộng ~200 assets, 150 maintenance, etc.)
        num_assets = max(0, 200 - existing_assets)
        num_maintenance = max(0, 150 - existing_maintenance)
        num_transfers = max(0, 50 - existing_transfers)
        num_logs = max(0, 300 - existing_logs)
        
        if num_assets == 0 and num_maintenance == 0 and num_transfers == 0 and num_logs == 0:
            print("\n✅ Đã có đủ dữ liệu trong hệ thống!")
            return
        
        print(f"\n🎯 Sẽ tạo thêm:")
        print(f"   - {num_assets} tài sản")
        print(f"   - {num_maintenance} bản ghi bảo trì")
        print(f"   - {num_transfers} bàn giao")
        print(f"   - {num_logs} nhật ký")
        
        total_created = 0
        
        if num_assets > 0:
            total_created += generate_assets(num_assets)
        
        if num_maintenance > 0:
            total_created += generate_maintenance_records(num_maintenance)
        
        if num_transfers > 0:
            total_created += generate_transfers(num_transfers)
        
        if num_logs > 0:
            total_created += generate_audit_logs(num_logs)
        
        print(f"\n{'='*60}")
        print("✅ HOAN TAT TAO DU LIEU MAU")
        print(f"{'='*60}")
        print(f"\n📊 Tổng kết:")
        
        final_assets = Asset.query.filter(Asset.deleted_at.is_(None)).count()
        final_maintenance = MaintenanceRecord.query.filter(MaintenanceRecord.deleted_at.is_(None)).count()
        final_transfers = AssetTransfer.query.count()
        final_logs = AuditLog.query.count()
        
        print(f"   - Tài sản: {final_assets}")
        print(f"   - Bảo trì: {final_maintenance}")
        print(f"   - Bàn giao: {final_transfers}")
        print(f"   - Nhật ký: {final_logs}")
        print(f"\n🎉 Hệ thống đã có đủ dữ liệu để test!")

if __name__ == "__main__":
    main()

