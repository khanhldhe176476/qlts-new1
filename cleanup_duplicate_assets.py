# -*- coding: utf-8 -*-
"""
Script để xóa tài sản trùng lặp và làm sạch tên tài sản
- Xóa các số trong ngoặc đơn ở cuối tên (ví dụ: "Tên tài sản (1)" -> "Tên tài sản")
- Xóa các tài sản trùng lặp, chỉ giữ lại 1 bản
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Asset

def clean_asset_names():
    """Làm sạch tên tài sản - xóa số trong ngoặc đơn ở cuối"""
    with app.app_context():
        assets = Asset.query.filter(Asset.deleted_at.is_(None)).all()
        cleaned_count = 0
        
        for asset in assets:
            if not asset.name:
                continue
            
            # Tìm và xóa pattern: (số) ở cuối tên
            # Ví dụ: "Bàn làm việc gỗ cao cấp (1)" -> "Bàn làm việc gỗ cao cấp"
            pattern = r'\s*\(\d+\)\s*$'
            original_name = asset.name
            cleaned_name = re.sub(pattern, '', original_name).strip()
            
            if cleaned_name != original_name:
                asset.name = cleaned_name
                cleaned_count += 1
                print(f"  - ID={asset.id}: '{original_name}' -> '{cleaned_name}'")
        
        if cleaned_count > 0:
            db.session.commit()
            print(f"\n✓ Đã làm sạch {cleaned_count} tên tài sản")
        else:
            print("\n✓ Không có tên tài sản nào cần làm sạch")
        
        return cleaned_count

def remove_duplicate_assets():
    """Xóa tài sản trùng lặp dựa trên tên (sau khi đã làm sạch)"""
    with app.app_context():
        # Làm sạch tên trước
        clean_asset_names()
        
        # Lấy lại tất cả tài sản sau khi làm sạch
        assets = Asset.query.filter(Asset.deleted_at.is_(None)).order_by(Asset.id).all()
        
        # Nhóm theo tên (đã làm sạch)
        from collections import defaultdict
        duplicates_by_name = defaultdict(list)
        
        for asset in assets:
            if asset.name:
                name_key = asset.name.strip().lower()
                duplicates_by_name[name_key].append(asset)
        
        # Tìm các nhóm có nhiều hơn 1 tài sản
        name_duplicates = {k: v for k, v in duplicates_by_name.items() if len(v) > 1}
        
        if not name_duplicates:
            print("\n✓ Không có tài sản trùng lặp nào!")
            return 0, 0
        
        total_removed = 0
        groups_processed = 0
        
        for name_key, assets_list in name_duplicates.items():
            if len(assets_list) <= 1:
                continue
            
            # Sắp xếp theo id để giữ lại bản đầu tiên
            assets_sorted = sorted(assets_list, key=lambda x: x.id)
            keep_asset = assets_sorted[0]
            remove_assets = assets_sorted[1:]
            
            print(f"\n[Tên: '{name_key}'] Tìm thấy {len(assets_list)} tài sản trùng lặp:")
            print(f"  - Giữ lại: ID={keep_asset.id}, Tên='{keep_asset.name}', Mã='{keep_asset.device_code or 'N/A'}'")
            
            for asset in remove_assets:
                print(f"  - Xóa: ID={asset.id}, Tên='{asset.name}', Mã='{asset.device_code or 'N/A'}'")
                asset.soft_delete()
                total_removed += 1
            
            groups_processed += 1
        
        if total_removed > 0:
            db.session.commit()
            print(f"\n✓ Đã xóa {total_removed} tài sản trùng lặp từ {groups_processed} nhóm")
        else:
            print(f"\n✓ Không có tài sản trùng lặp nào cần xóa")
        
        return total_removed, groups_processed

def main():
    """Hàm chính"""
    print("=" * 60)
    print("LÀM SẠCH TÀI SẢN TRÙNG LẶP VÀ TÊN TÀI SẢN")
    print("=" * 60)
    
    print("\n1. Đang làm sạch tên tài sản (xóa số trong ngoặc đơn)...")
    clean_asset_names()
    
    print("\n2. Đang tìm và xóa tài sản trùng lặp...")
    total_removed, groups_processed = remove_duplicate_assets()
    
    print("\n" + "=" * 60)
    print(f"TỔNG KẾT:")
    print(f"  - Đã xóa: {total_removed} tài sản trùng lặp")
    print(f"  - Số nhóm xử lý: {groups_processed}")
    print("=" * 60)

if __name__ == "__main__":
    main()

