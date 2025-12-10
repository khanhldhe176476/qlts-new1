# -*- coding: utf-8 -*-
"""
Script để xóa các tài sản trùng lặp
Giữ lại bản đầu tiên (id nhỏ nhất), xóa các bản còn lại
"""

import sys
import os

# Thêm thư mục hiện tại vào path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Asset
from collections import defaultdict

def find_duplicate_assets():
    """Tìm các tài sản trùng lặp dựa trên tên và mã tài sản"""
    with app.app_context():
        # Lấy tất cả tài sản chưa bị xóa
        assets = Asset.query.filter(Asset.deleted_at.is_(None)).order_by(Asset.id).all()
        
        # Nhóm theo tên và device_code
        duplicates_by_name = defaultdict(list)
        duplicates_by_code = defaultdict(list)
        duplicates_by_both = defaultdict(list)
        
        for asset in assets:
            # Nhóm theo tên
            if asset.name:
                name_key = asset.name.strip().lower()
                duplicates_by_name[name_key].append(asset)
            
            # Nhóm theo device_code
            if asset.device_code:
                code_key = asset.device_code.strip().upper()
                duplicates_by_code[code_key].append(asset)
            
            # Nhóm theo cả tên và mã
            if asset.name and asset.device_code:
                both_key = (asset.name.strip().lower(), asset.device_code.strip().upper())
                duplicates_by_both[both_key].append(asset)
        
        # Tìm các nhóm có nhiều hơn 1 tài sản
        name_duplicates = {k: v for k, v in duplicates_by_name.items() if len(v) > 1}
        code_duplicates = {k: v for k, v in duplicates_by_code.items() if len(v) > 1}
        both_duplicates = {k: v for k, v in duplicates_by_both.items() if len(v) > 1}
        
        return name_duplicates, code_duplicates, both_duplicates

def remove_duplicates(duplicates_dict, criteria_name):
    """Xóa các tài sản trùng lặp, giữ lại bản đầu tiên (id nhỏ nhất)"""
    total_removed = 0
    groups_processed = 0
    
    with app.app_context():
        for key, assets in duplicates_dict.items():
            if len(assets) <= 1:
                continue
            
            # Sắp xếp theo id để giữ lại bản đầu tiên
            assets_sorted = sorted(assets, key=lambda x: x.id)
            keep_asset = assets_sorted[0]
            remove_assets = assets_sorted[1:]
            
            print(f"\n[{criteria_name}] Tìm thấy {len(assets)} tài sản trùng lặp:")
            print(f"  - Giữ lại: ID={keep_asset.id}, Tên='{keep_asset.name}', Mã='{keep_asset.device_code or 'N/A'}'")
            
            for asset in remove_assets:
                print(f"  - Xóa: ID={asset.id}, Tên='{asset.name}', Mã='{asset.device_code or 'N/A'}'")
                asset.soft_delete()
                total_removed += 1
            
            groups_processed += 1
        
        if total_removed > 0:
            db.session.commit()
            print(f"\n✓ Đã xóa {total_removed} tài sản trùng lặp từ {groups_processed} nhóm ({criteria_name})")
        else:
            print(f"\n✓ Không có tài sản trùng lặp nào cần xóa ({criteria_name})")
    
    return total_removed, groups_processed

def remove_all_duplicates():
    """Xóa tất cả các tài sản trùng lặp (tự động)"""
    total_removed = 0
    total_groups = 0
    
    # Tìm các tài sản trùng lặp
    name_dups, code_dups, both_dups = find_duplicate_assets()
    
    # Xóa theo thứ tự: cả tên và mã -> mã -> tên
    if both_dups:
        removed, groups = remove_duplicates(both_dups, "Theo tên và mã")
        total_removed += removed
        total_groups += groups
    
    # Tìm lại các trùng lặp còn lại sau khi xóa
    name_dups, code_dups, _ = find_duplicate_assets()
    
    if code_dups:
        removed, groups = remove_duplicates(code_dups, "Theo mã")
        total_removed += removed
        total_groups += groups
    
    # Tìm lại các trùng lặp còn lại
    name_dups, _, _ = find_duplicate_assets()
    
    if name_dups:
        removed, groups = remove_duplicates(name_dups, "Theo tên")
        total_removed += removed
        total_groups += groups
    
    return total_removed, total_groups

def main():
    """Hàm chính"""
    print("=" * 60)
    print("TÌM VÀ XÓA TÀI SẢN TRÙNG LẶP")
    print("=" * 60)
    
    # Tìm các tài sản trùng lặp
    print("\nĐang tìm các tài sản trùng lặp...")
    name_dups, code_dups, both_dups = find_duplicate_assets()
    
    print(f"\nKết quả tìm kiếm:")
    print(f"  - Trùng theo tên: {len(name_dups)} nhóm")
    print(f"  - Trùng theo mã: {len(code_dups)} nhóm")
    print(f"  - Trùng theo cả tên và mã: {len(both_dups)} nhóm")
    
    if len(name_dups) == 0 and len(code_dups) == 0 and len(both_dups) == 0:
        print("\n✓ Không có tài sản trùng lặp nào!")
        return
    
    # Hỏi người dùng muốn xóa theo tiêu chí nào
    print("\n" + "=" * 60)
    print("Chọn tiêu chí xóa trùng lặp:")
    print("1. Xóa trùng theo tên tài sản")
    print("2. Xóa trùng theo mã tài sản")
    print("3. Xóa trùng theo cả tên và mã (khuyến nghị)")
    print("4. Xóa tất cả các loại trùng lặp")
    print("0. Hủy")
    
    choice = input("\nNhập lựa chọn (0-4): ").strip()
    
    total_removed = 0
    total_groups = 0
    
    if choice == "1":
        if name_dups:
            removed, groups = remove_duplicates(name_dups, "Theo tên")
            total_removed += removed
            total_groups += groups
    elif choice == "2":
        if code_dups:
            removed, groups = remove_duplicates(code_dups, "Theo mã")
            total_removed += removed
            total_groups += groups
    elif choice == "3":
        if both_dups:
            removed, groups = remove_duplicates(both_dups, "Theo tên và mã")
            total_removed += removed
            total_groups += groups
    elif choice == "4":
        total_removed, total_groups = remove_all_duplicates()
    elif choice == "0":
        print("\nĐã hủy.")
        return
    else:
        print("\nLựa chọn không hợp lệ!")
        return
    
    print("\n" + "=" * 60)
    print(f"TỔNG KẾT:")
    print(f"  - Đã xóa: {total_removed} tài sản trùng lặp")
    print(f"  - Số nhóm xử lý: {total_groups}")
    print("=" * 60)

if __name__ == "__main__":
    main()

