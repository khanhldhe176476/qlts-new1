#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để tìm tài sản không thuộc admin và xem nó thuộc user nào
"""
import sys
import io
from app import app
from models import db, Asset, User
from models import asset_user

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def find_asset_owner():
    """Tìm tài sản không thuộc admin"""
    with app.app_context():
        try:
            # Tìm user admin
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("[ERROR] Khong tim thay user admin")
                return
            
            print(f"\n{'='*60}")
            print(f"TIM TAI SAN KHONG THUOC ADMIN")
            print(f"{'='*60}\n")
            print(f"Admin ID: {admin.id}, Username: {admin.username}\n")
            
            # Lấy tất cả tài sản không bị xóa mềm và không bị thanh lý
            all_assets = Asset.query.filter(
                Asset.deleted_at.is_(None),
                Asset.status != 'disposed'
            ).all()
            
            print(f"Tong tai san: {len(all_assets)}\n")
            
            # Tìm tài sản của admin
            admin_asset_ids = set()
            
            # 1. Tài sản có user_id == admin.id
            assets_owned = Asset.query.filter(
                Asset.user_id == admin.id,
                Asset.deleted_at.is_(None),
                Asset.status != 'disposed'
            ).all()
            for asset in assets_owned:
                admin_asset_ids.add(asset.id)
            
            # 2. Tài sản được gán qua bảng asset_user
            assets_assigned = Asset.query.join(
                asset_user, Asset.id == asset_user.c.asset_id
            ).filter(
                asset_user.c.user_id == admin.id,
                Asset.deleted_at.is_(None),
                Asset.status != 'disposed'
            ).all()
            for asset in assets_assigned:
                admin_asset_ids.add(asset.id)
            
            print(f"Tai san cua admin: {len(admin_asset_ids)}\n")
            
            # Tìm tài sản không thuộc admin
            other_assets = []
            for asset in all_assets:
                if asset.id not in admin_asset_ids:
                    other_assets.append(asset)
            
            print(f"Tai san KHONG thuoc admin: {len(other_assets)}\n")
            
            if other_assets:
                print("Danh sach tai san khong thuoc admin:")
                print("=" * 60)
                for asset in other_assets:
                    print(f"\nID: {asset.id}")
                    print(f"Ten: {asset.name}")
                    print(f"Trang thai: {asset.status}")
                    print(f"user_id: {asset.user_id}")
                    
                    if asset.user_id:
                        user = User.query.get(asset.user_id)
                        if user:
                            print(f"User: {user.username} (ID: {user.id})")
                            print(f"  - Email: {user.email}")
                            print(f"  - Vai tro: {user.role.name if user.role else 'N/A'}")
                            print(f"  - Trang thai: {'Hoạt động' if user.is_active else 'Không hoạt động'}")
                            print(f"  - Deleted at: {user.deleted_at if user.deleted_at else 'Không'}")
                        else:
                            print(f"User ID {asset.user_id} KHONG TON TAI!")
                    else:
                        print("user_id = NULL")
                    
                    # Kiểm tra assigned_users
                    try:
                        if asset.assigned_users:
                            print(f"Assigned users: {len(asset.assigned_users)}")
                            for u in asset.assigned_users:
                                print(f"  - {u.username} (ID: {u.id})")
                        else:
                            print("Assigned users: 0")
                    except:
                        print("Assigned users: Không thể kiểm tra")
                    
                    print("-" * 60)
            else:
                print("✓ Tat ca tai san deu thuoc admin!")
            
            # Thống kê phân bổ tài sản theo user
            print(f"\n{'='*60}")
            print("THONG KE PHAN BO TAI SAN THEO USER")
            print(f"{'='*60}\n")
            
            # Đếm tài sản theo user_id
            user_asset_count = {}
            for asset in all_assets:
                if asset.user_id:
                    if asset.user_id not in user_asset_count:
                        user_asset_count[asset.user_id] = 0
                    user_asset_count[asset.user_id] += 1
            
            # Sắp xếp theo số lượng giảm dần
            sorted_users = sorted(user_asset_count.items(), key=lambda x: x[1], reverse=True)
            
            for user_id, count in sorted_users:
                user = User.query.get(user_id)
                if user:
                    print(f"  {user.username:20s} (ID: {user.id:3d}): {count:3d} tai san")
                else:
                    print(f"  User ID {user_id} (KHONG TON TAI): {count:3d} tai san")
            
            print(f"\n{'='*60}\n")
            
        except Exception as e:
            print(f"[ERROR] Loi khi kiem tra: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    find_asset_owner()

