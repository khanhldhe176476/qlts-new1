# -*- coding: utf-8 -*-
"""Script để kiểm tra số lượng tài sản và tìm nguyên nhân thiếu"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    from models import db, Asset
    from collections import defaultdict
    
    print("Đang kết nối database...")
    
    with app.app_context():
        # Lấy tất cả tài sản không bị xóa
        all_assets = Asset.query.filter(Asset.deleted_at.is_(None)).all()
        
        print("=" * 60)
        print("KIỂM TRA SỐ LƯỢNG TÀI SẢN")
        print("=" * 60)
        
        # Đếm theo status
        status_count = defaultdict(lambda: {'count': 0, 'quantity': 0, 'assets': []})
        
        for asset in all_assets:
            status = asset.status if asset.status else 'NULL'
            quantity = asset.quantity or 1
            status_count[status]['count'] += 1
            status_count[status]['quantity'] += quantity
            status_count[status]['assets'].append({
                'id': asset.id,
                'name': asset.name,
                'quantity': quantity,
                'status': asset.status
            })
        
        # In kết quả
        print(f"\nTổng số bản ghi tài sản: {len(all_assets)}")
        print(f"\nPhân tích theo STATUS:")
        print("-" * 60)
        
        total_quantity = 0
        for status, data in sorted(status_count.items()):
            print(f"\nStatus: '{status}'")
            print(f"  - Số bản ghi: {data['count']}")
            print(f"  - Tổng quantity: {data['quantity']}")
            total_quantity += data['quantity']
            
            # Nếu có status lạ, in ra một vài ví dụ
            if status not in ['active', 'inactive', 'maintenance', 'NULL']:
                print(f"  - ⚠️  Status không chuẩn! Ví dụ:")
                for asset_info in data['assets'][:3]:
                    print(f"      ID {asset_info['id']}: {asset_info['name']} (qty: {asset_info['quantity']})")
        
        print("\n" + "=" * 60)
        print(f"TỔNG QUANTITY: {total_quantity}")
        print("=" * 60)
        
        # Tính theo logic hiện tại
        active_count = sum(a.quantity or 1 for a in all_assets if a.status == 'active')
        inactive_count = sum(a.quantity or 1 for a in all_assets if a.status == 'inactive')
        maintenance_count = sum(a.quantity or 1 for a in all_assets if a.status == 'maintenance')
        other_count = sum(a.quantity or 1 for a in all_assets 
                         if (a.status is None) or (a.status not in ['active', 'inactive', 'maintenance']))
        
        calculated_total = active_count + inactive_count + maintenance_count + other_count
        
        print(f"\nTính theo logic dashboard:")
        print(f"  - Active: {active_count}")
        print(f"  - Inactive: {inactive_count}")
        print(f"  - Maintenance: {maintenance_count}")
        print(f"  - Other: {other_count}")
        print(f"  - Tổng tính được: {calculated_total}")
        print(f"  - Tổng thực tế: {total_quantity}")
        
        if calculated_total != total_quantity:
            print(f"\n⚠️  KHÔNG KHỚP! Chênh lệch: {abs(calculated_total - total_quantity)}")
        else:
            print(f"\n✅ KHỚP!")
        
        # Kiểm tra tài sản có quantity = 0 hoặc null
        zero_qty = [a for a in all_assets if a.quantity == 0]
        if zero_qty:
            print(f"\n⚠️  Tìm thấy {len(zero_qty)} tài sản có quantity = 0:")
            for asset in zero_qty[:5]:
                print(f"  - ID {asset.id}: {asset.name} (status: {asset.status})")
        
        print("\nHoàn thành kiểm tra!")
except Exception as e:
    print(f"Lỗi: {e}")
    import traceback
    traceback.print_exc()
