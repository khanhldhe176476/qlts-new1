#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để xóa tất cả tài sản hiện có và tạo dữ liệu mẫu mới theo các loại tài sản
"""
import sys
import io
from datetime import datetime, date, timedelta
import random

# Configure UTF-8 encoding for stdout/stderr on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app import app, db
from models import Asset, AssetType, User
from utils.timezone import now_vn, today_vn

# Dữ liệu mẫu theo từng loại tài sản
SAMPLE_ASSETS = {
    'Tài sản cơ quan': [
        {'name': 'Máy tính Dell OptiPlex 7090', 'price': 15000000, 'quantity': 5, 'device_code': 'PC001-PC005'},
        {'name': 'Laptop HP EliteBook 840', 'price': 25000000, 'quantity': 3, 'device_code': 'LT001-LT003'},
        {'name': 'Máy in Canon PIXMA G3010', 'price': 3500000, 'quantity': 2, 'device_code': 'IN001-IN002'},
        {'name': 'Máy photocopy Ricoh MP 4054', 'price': 45000000, 'quantity': 1, 'device_code': 'CP001'},
        {'name': 'Bàn làm việc gỗ cao cấp', 'price': 2500000, 'quantity': 20, 'device_code': 'BN001-BN020'},
        {'name': 'Ghế văn phòng ergonomic', 'price': 3000000, 'quantity': 25, 'device_code': 'GH001-GH025'},
        {'name': 'Tủ hồ sơ 4 ngăn', 'price': 2000000, 'quantity': 10, 'device_code': 'TU001-TU010'},
        {'name': 'Điều hòa Daikin 2HP', 'price': 18000000, 'quantity': 8, 'device_code': 'AC001-AC008'},
        {'name': 'Camera an ninh Hikvision', 'price': 5000000, 'quantity': 12, 'device_code': 'CAM001-CAM012'},
        {'name': 'Máy fax Panasonic KX-FT982', 'price': 2500000, 'quantity': 2, 'device_code': 'FX001-FX002'},
    ],
    'Kết cấu hạ tầng': [
        {'name': 'Đường giao thông nội bộ', 'price': 500000000, 'quantity': 1, 'device_code': 'DT001'},
        {'name': 'Cầu bê tông cốt thép', 'price': 2000000000, 'quantity': 1, 'device_code': 'CAU001'},
        {'name': 'Hệ thống chiếu sáng đường phố', 'price': 150000000, 'quantity': 1, 'device_code': 'DEN001'},
        {'name': 'Công viên công cộng', 'price': 300000000, 'quantity': 1, 'device_code': 'CV001'},
        {'name': 'Trạm biến áp 110kV', 'price': 5000000000, 'quantity': 1, 'device_code': 'BA001'},
        {'name': 'Trường học tiểu học', 'price': 10000000000, 'quantity': 1, 'device_code': 'TH001'},
        {'name': 'Bệnh viện đa khoa', 'price': 50000000000, 'quantity': 1, 'device_code': 'BV001'},
        {'name': 'Hệ thống thoát nước', 'price': 800000000, 'quantity': 1, 'device_code': 'TN001'},
        {'name': 'Đường ống cấp nước', 'price': 600000000, 'quantity': 1, 'device_code': 'ON001'},
        {'name': 'Trạm xử lý nước thải', 'price': 2000000000, 'quantity': 1, 'device_code': 'XL001'},
    ],
    'Tài sản doanh nghiệp Nhà nước': [
        {'name': 'Nhà xưởng sản xuất', 'price': 50000000000, 'quantity': 1, 'device_code': 'NX001'},
        {'name': 'Máy móc sản xuất dây chuyền', 'price': 10000000000, 'quantity': 2, 'device_code': 'MM001-MM002'},
        {'name': 'Kho bãi lưu trữ', 'price': 20000000000, 'quantity': 1, 'device_code': 'KB001'},
        {'name': 'Xe tải vận chuyển hàng hóa', 'price': 800000000, 'quantity': 5, 'device_code': 'XT001-XT005'},
        {'name': 'Xe container', 'price': 1200000000, 'quantity': 3, 'device_code': 'CT001-CT003'},
        {'name': 'Trạm thu phí đường bộ', 'price': 3000000000, 'quantity': 1, 'device_code': 'TP001'},
        {'name': 'Hệ thống cân điện tử', 'price': 500000000, 'quantity': 2, 'device_code': 'CN001-CN002'},
        {'name': 'Cần cẩu xây dựng', 'price': 2000000000, 'quantity': 1, 'device_code': 'CC001'},
        {'name': 'Máy đào đất', 'price': 1500000000, 'quantity': 2, 'device_code': 'MD001-MD002'},
        {'name': 'Xe nâng hàng', 'price': 400000000, 'quantity': 4, 'device_code': 'XN001-XN004'},
    ],
    'Tài sản dự án': [
        {'name': 'Máy xúc đào dự án xây dựng', 'price': 3000000000, 'quantity': 1, 'device_code': 'DA001'},
        {'name': 'Công trình đang thi công - Tòa nhà A', 'price': 50000000000, 'quantity': 1, 'device_code': 'CT001'},
        {'name': 'Phần mềm quản lý dự án', 'price': 500000000, 'quantity': 1, 'device_code': 'PM001'},
        {'name': 'Vật tư dự phòng - Xi măng', 'price': 100000000, 'quantity': 50, 'device_code': 'VT001-VT050'},
        {'name': 'Vật tư dự phòng - Sắt thép', 'price': 200000000, 'quantity': 30, 'device_code': 'ST001-ST030'},
        {'name': 'Thiết bị đo đạc địa chất', 'price': 800000000, 'quantity': 1, 'device_code': 'DD001'},
        {'name': 'Máy trộn bê tông', 'price': 600000000, 'quantity': 2, 'device_code': 'MT001-MT002'},
        {'name': 'Giàn giáo xây dựng', 'price': 300000000, 'quantity': 10, 'device_code': 'GJ001-GJ010'},
        {'name': 'Máy cắt sắt', 'price': 15000000, 'quantity': 5, 'device_code': 'CS001-CS005'},
        {'name': 'Máy hàn điện', 'price': 5000000, 'quantity': 8, 'device_code': 'MH001-MH008'},
    ],
    'Sở hữu toàn dân': [
        {'name': 'Tài sản tịch thu - Xe ô tô', 'price': 500000000, 'quantity': 1, 'device_code': 'TC001'},
        {'name': 'Tài sản tịch thu - Đất đai', 'price': 2000000000, 'quantity': 1, 'device_code': 'TC002'},
        {'name': 'Tài sản vô chủ - Nhà ở', 'price': 3000000000, 'quantity': 1, 'device_code': 'VC001'},
        {'name': 'Tài sản hiến tặng - Thiết bị y tế', 'price': 1000000000, 'quantity': 1, 'device_code': 'HT001'},
        {'name': 'Hàng hóa tịch thu - Điện thoại', 'price': 50000000, 'quantity': 20, 'device_code': 'HH001-HH020'},
        {'name': 'Hàng hóa tịch thu - Laptop', 'price': 15000000, 'quantity': 10, 'device_code': 'HH021-HH030'},
        {'name': 'Tài sản tịch thu - Vàng', 'price': 1000000000, 'quantity': 1, 'device_code': 'TC003'},
        {'name': 'Tài sản vô chủ - Xe máy', 'price': 30000000, 'quantity': 5, 'device_code': 'VC002-VC006'},
        {'name': 'Tài sản hiến tặng - Sách', 'price': 5000000, 'quantity': 100, 'device_code': 'HT002-HT101'},
        {'name': 'Hàng hóa tịch thu - Đồng hồ', 'price': 20000000, 'quantity': 15, 'device_code': 'HH031-HH045'},
    ],
    'Tiền & quỹ Nhà nước': [
        {'name': 'Quỹ ngân sách Nhà nước', 'price': 1000000000000, 'quantity': 1, 'device_code': 'NS001'},
        {'name': 'Quỹ BHXH', 'price': 500000000000, 'quantity': 1, 'device_code': 'BH001'},
        {'name': 'Quỹ bảo trì đường bộ', 'price': 200000000000, 'quantity': 1, 'device_code': 'BT001'},
        {'name': 'Dự trữ ngoại hối', 'price': 2000000000000, 'quantity': 1, 'device_code': 'DT001'},
        {'name': 'Quỹ đầu tư phát triển', 'price': 300000000000, 'quantity': 1, 'device_code': 'DT002'},
        {'name': 'Quỹ dự phòng tài chính', 'price': 100000000000, 'quantity': 1, 'device_code': 'DP001'},
        {'name': 'Quỹ hỗ trợ phát triển', 'price': 150000000000, 'quantity': 1, 'device_code': 'HT001'},
        {'name': 'Quỹ bảo hiểm y tế', 'price': 400000000000, 'quantity': 1, 'device_code': 'YT001'},
        {'name': 'Quỹ hỗ trợ nông nghiệp', 'price': 250000000000, 'quantity': 1, 'device_code': 'NN001'},
        {'name': 'Quỹ phát triển giáo dục', 'price': 180000000000, 'quantity': 1, 'device_code': 'GD001'},
    ],
    'Tài nguyên quốc gia': [
        {'name': 'Đất đai công cộng', 'price': 50000000000, 'quantity': 1, 'device_code': 'DD001'},
        {'name': 'Rừng phòng hộ', 'price': 100000000000, 'quantity': 1, 'device_code': 'RF001'},
        {'name': 'Khoáng sản - Than đá', 'price': 50000000000, 'quantity': 1, 'device_code': 'KS001'},
        {'name': 'Nguồn nước mặt', 'price': 20000000000, 'quantity': 1, 'device_code': 'NM001'},
        {'name': 'Nguồn nước ngầm', 'price': 15000000000, 'quantity': 1, 'device_code': 'NN001'},
        {'name': 'Tài nguyên biển - Vùng đánh bắt', 'price': 30000000000, 'quantity': 1, 'device_code': 'TB001'},
        {'name': 'Tần số vô tuyến', 'price': 10000000000, 'quantity': 1, 'device_code': 'TS001'},
        {'name': 'Kho số viễn thông', 'price': 5000000000, 'quantity': 1, 'device_code': 'VT001'},
        {'name': 'Khoáng sản - Quặng sắt', 'price': 40000000000, 'quantity': 1, 'device_code': 'KS002'},
        {'name': 'Rừng đặc dụng', 'price': 80000000000, 'quantity': 1, 'device_code': 'RF002'},
    ]
}

def reset_and_create_assets():
    """Xóa tất cả tài sản và tạo dữ liệu mẫu mới"""
    with app.app_context():
        try:
            print("=" * 60)
            print("XOA TAT CA TAI SAN VA TAO DU LIEU MAU MOI")
            print("=" * 60)
            
            # Lấy tất cả loại tài sản
            asset_types = AssetType.query.filter(AssetType.deleted_at.is_(None)).all()
            asset_type_dict = {at.name: at for at in asset_types}
            
            print(f"\nTim thay {len(asset_types)} loai tai san:")
            for at in asset_types:
                print(f"  - {at.name}")
            
            # Đếm số tài sản hiện có
            existing_assets = Asset.query.filter(Asset.deleted_at.is_(None)).all()
            print(f"\nTim thay {len(existing_assets)} tai san hien co")
            
            # Xóa tất cả tài sản (soft delete)
            print("\nDang xoa tat ca tai san...")
            deleted_count = 0
            for asset in existing_assets:
                asset.soft_delete()
                deleted_count += 1
            
            db.session.commit()
            print(f"✓ Da xoa {deleted_count} tai san")
            
            # Lấy admin user để gán làm người tạo
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("⚠️  Khong tim thay admin user, se de user_id = None")
                admin_user_id = None
            else:
                admin_user_id = admin_user.id
            
            # Tạo dữ liệu mẫu mới
            print("\nDang tao du lieu mau moi...")
            total_created = 0
            
            for asset_type_name, assets_data in SAMPLE_ASSETS.items():
                asset_type = asset_type_dict.get(asset_type_name)
                if not asset_type:
                    print(f"⚠️  Khong tim thay loai tai san: {asset_type_name}")
                    continue
                
                print(f"\n  Loai: {asset_type_name}")
                created_count = 0
                
                for asset_data in assets_data:
                    # Xử lý device_code nếu có nhiều số lượng
                    device_codes = []
                    if 'device_code' in asset_data and '-' in asset_data['device_code']:
                        # Format: 'PC001-PC005' -> tạo nhiều asset
                        parts = asset_data['device_code'].split('-')
                        if len(parts) == 2:
                            prefix = parts[0][:-3]  # Lấy phần prefix (PC)
                            start_num = int(parts[0][-3:])  # Lấy số (001)
                            end_num = int(parts[1][-3:])  # Lấy số (005)
                            for num in range(start_num, end_num + 1):
                                device_codes.append(f"{prefix}{num:03d}")
                    else:
                        device_codes = [asset_data.get('device_code', '')]
                    
                    quantity = asset_data.get('quantity', 1)
                    
                    # Tạo asset cho mỗi device_code hoặc theo quantity
                    for i in range(quantity):
                        device_code = device_codes[i] if i < len(device_codes) else f"{asset_data.get('device_code', '')}{i+1:03d}" if asset_data.get('device_code') else ''
                        
                        # Tạo ngày mua ngẫu nhiên trong 2 năm qua
                        days_ago = random.randint(0, 730)
                        purchase_date = today_vn() - timedelta(days=days_ago)
                        
                        # Tình trạng ngẫu nhiên
                        conditions = ['Còn tốt', 'Mới', 'Cần kiểm tra', 'Đã sử dụng']
                        condition = random.choice(conditions)
                        
                        # Trạng thái ngẫu nhiên
                        statuses = ['active', 'active', 'active', 'maintenance']  # Chủ yếu là active
                        status = random.choice(statuses)
                        
                        asset = Asset(
                            name=asset_data['name'] if quantity == 1 else f"{asset_data['name']} ({i+1})",
                            price=asset_data['price'],
                            quantity=1,
                            asset_type_id=asset_type.id,
                            user_id=admin_user_id,
                            purchase_date=purchase_date,
                            device_code=device_code if device_code else None,
                            condition_label=condition,
                            status=status,
                            notes=f"Tài sản mẫu - Loại: {asset_type_name}"
                        )
                        
                        db.session.add(asset)
                        created_count += 1
                        total_created += 1
                
                print(f"    ✓ Da tao {created_count} tai san")
            
            db.session.commit()
            
            # Hiển thị kết quả
            print("\n" + "=" * 60)
            print("KET QUA")
            print("=" * 60)
            
            for asset_type in asset_types:
                asset_count = Asset.query.filter(
                    Asset.asset_type_id == asset_type.id,
                    Asset.deleted_at.is_(None)
                ).count()
                print(f"  {asset_type.name}: {asset_count} tai san")
            
            print(f"\n✓ Tong cong: {total_created} tai san da duoc tao")
            print("=" * 60)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ LOI: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    reset_and_create_assets()

















