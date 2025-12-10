#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để xóa tất cả loại tài sản cũ và thêm các loại tài sản mới
"""
import sys
import io

# Configure UTF-8 encoding for stdout/stderr on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app import app, db
from models import AssetType, Asset
from utils.timezone import now_vn

# Danh sách loại tài sản mới
NEW_ASSET_TYPES = [
    {
        'name': 'Tài sản cơ quan',
        'description': 'Trụ sở làm việc, máy tính, máy in, bàn ghế, tủ hồ sơ, điều hòa, camera.'
    },
    {
        'name': 'Kết cấu hạ tầng',
        'description': 'Đường, cầu, hệ thống chiếu sáng, công viên, trạm biến áp, trường học, bệnh viện.'
    },
    {
        'name': 'Tài sản doanh nghiệp Nhà nước',
        'description': 'Nhà xưởng, máy móc sản xuất, kho bãi, phương tiện vận tải, trạm thu phí.'
    },
    {
        'name': 'Tài sản dự án',
        'description': 'Máy móc thiết bị dự án, công trình đang thi công, phần mềm, vật tư dự phòng.'
    },
    {
        'name': 'Sở hữu toàn dân',
        'description': 'Tài sản tịch thu, tài sản vô chủ, tài sản hiến tặng, hàng hóa tịch thu.'
    },
    {
        'name': 'Tiền & quỹ Nhà nước',
        'description': 'Tiền ngân sách, quỹ BHXH, quỹ bảo trì đường bộ, dự trữ ngoại hối.'
    },
    {
        'name': 'Tài nguyên quốc gia',
        'description': 'Đất đai, rừng, khoáng sản, nguồn nước, tài nguyên biển, tần số, kho số viễn thông.'
    }
]

def update_asset_types():
    """Xóa tất cả loại tài sản cũ và thêm loại tài sản mới"""
    with app.app_context():
        try:
            print("=" * 60)
            print("CAP NHAT LOAI TAI SAN")
            print("=" * 60)
            
            # Kiểm tra số lượng tài sản đang sử dụng các loại cũ
            old_asset_types = AssetType.query.filter(AssetType.deleted_at.is_(None)).all()
            assets_count = Asset.query.filter(Asset.deleted_at.is_(None)).count()
            
            print(f"\nTim thay {len(old_asset_types)} loai tai san hien tai")
            print(f"Tim thay {assets_count} tai san dang su dung")
            
            if assets_count > 0:
                print("\n⚠️  CANH BAO: Co tai san dang su dung cac loai tai san cu!")
                print("Cac tai san se bi gan vao loai tai san dau tien trong danh sach moi.")
                print("Tiep tuc tu dong...")
            
            # Soft delete tất cả loại tài sản cũ
            print("\nDang xoa cac loai tai san cu...")
            deleted_count = 0
            for asset_type in old_asset_types:
                asset_type.soft_delete()
                deleted_count += 1
                print(f"  - Da xoa: {asset_type.name}")
            
            db.session.commit()
            print(f"\n✓ Da xoa {deleted_count} loai tai san cu")
            
            # Cập nhật các tài sản đang sử dụng loại cũ
            if assets_count > 0:
                print("\nDang cap nhat tai san...")
                # Lấy loại tài sản đầu tiên mới (sẽ được tạo sau)
                # Tạm thời gán vào loại đầu tiên trong danh sách mới
                first_new_type_name = NEW_ASSET_TYPES[0]['name']
                
                # Tạo loại tài sản đầu tiên trước để có thể gán
                first_new_type = AssetType(
                    name=first_new_type_name,
                    description=NEW_ASSET_TYPES[0]['description']
                )
                db.session.add(first_new_type)
                db.session.flush()  # Lấy ID mà không commit
                
                # Cập nhật tất cả tài sản sang loại mới đầu tiên
                assets = Asset.query.filter(Asset.deleted_at.is_(None)).all()
                updated_count = 0
                for asset in assets:
                    asset.asset_type_id = first_new_type.id
                    updated_count += 1
                
                db.session.commit()
                print(f"✓ Da cap nhat {updated_count} tai san sang loai '{first_new_type_name}'")
            
            # Thêm các loại tài sản mới
            print("\nDang them cac loai tai san moi...")
            added_count = 0
            for asset_type_data in NEW_ASSET_TYPES:
                # Kiểm tra xem đã tồn tại chưa (có thể đã được tạo ở bước trước)
                existing = AssetType.query.filter(
                    AssetType.name == asset_type_data['name'],
                    AssetType.deleted_at.is_(None)
                ).first()
                
                if not existing:
                    asset_type = AssetType(
                        name=asset_type_data['name'],
                        description=asset_type_data['description']
                    )
                    db.session.add(asset_type)
                    added_count += 1
                    print(f"  + Da them: {asset_type_data['name']}")
                else:
                    print(f"  ~ Da ton tai: {asset_type_data['name']}")
            
            db.session.commit()
            print(f"\n✓ Da them {added_count} loai tai san moi")
            
            # Hiển thị kết quả
            print("\n" + "=" * 60)
            print("KET QUA")
            print("=" * 60)
            all_types = AssetType.query.filter(AssetType.deleted_at.is_(None)).order_by(AssetType.created_at).all()
            print(f"\nTong so loai tai san hien tai: {len(all_types)}")
            for i, asset_type in enumerate(all_types, 1):
                asset_count = Asset.query.filter(
                    Asset.asset_type_id == asset_type.id,
                    Asset.deleted_at.is_(None)
                ).count()
                print(f"  {i}. {asset_type.name} ({asset_count} tai san)")
            
            print("\n✓ Hoan thanh!")
            print("=" * 60)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ LOI: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    update_asset_types()

