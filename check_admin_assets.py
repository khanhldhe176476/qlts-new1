#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để kiểm tra số tài sản được gán cho admin
"""
import sys
import io
from app import app
from models import db, Asset, User
from models import asset_user

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_admin_assets():
    """Kiểm tra số tài sản được gán cho admin"""
    with app.app_context():
        try:
            # Tìm user admin
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("[ERROR] Khong tim thay user admin")
                return
            
            print(f"\n{'='*60}")
            print(f"KIEM TRA TAI SAN CUA USER: {admin.username} (ID: {admin.id})")
            print(f"{'='*60}\n")
            
            # 1. Tài sản có user_id == admin.id (người sở hữu) - không bao gồm disposed
            assets_owned = Asset.query.filter(
                Asset.user_id == admin.id,
                Asset.deleted_at.is_(None),
                Asset.status != 'disposed'
            ).all()
            
            print(f"Tai san co user_id == {admin.id}: {len(assets_owned)}")
            
            # 2. Tài sản được gán qua bảng asset_user (assigned_users) - không bao gồm disposed
            assets_assigned = Asset.query.join(
                asset_user, Asset.id == asset_user.c.asset_id
            ).filter(
                asset_user.c.user_id == admin.id,
                Asset.deleted_at.is_(None),
                Asset.status != 'disposed'
            ).all()
            
            print(f"Tai san duoc gan qua asset_user: {len(assets_assigned)}")
            
            # Gộp và loại bỏ trùng lặp (dùng set với id)
            all_asset_ids = set()
            all_assets = []
            for asset in assets_owned + assets_assigned:
                if asset.id not in all_asset_ids:
                    all_asset_ids.add(asset.id)
                    all_assets.append(asset)
            
            print(f"Tong tai san cua admin (sau khi gop va loai bo trung): {len(all_assets)}")
            
            # So sánh với tổng số tài sản
            total_assets = Asset.query.filter(
                Asset.deleted_at.is_(None),
                Asset.status != 'disposed'
            ).count()
            
            print(f"\nTong tai san (khong bi thanh ly): {total_assets}")
            print(f"Chenh lech: {total_assets - len(all_assets)}")
            
            # Kiểm tra tài sản nào không thuộc admin
            if total_assets != len(all_assets):
                print(f"\nDanh sach tai san KHONG thuoc admin:")
                print("-" * 60)
                all_assets_set = {a.id for a in all_assets}
                other_assets = Asset.query.filter(
                    Asset.deleted_at.is_(None),
                    Asset.status != 'disposed'
                ).all()
                
                for asset in other_assets:
                    if asset.id not in all_assets_set:
                        user = User.query.get(asset.user_id) if asset.user_id else None
                        print(f"  ID: {asset.id}")
                        print(f"  Ten: {asset.name}")
                        print(f"  user_id: {asset.user_id}")
                        if user:
                            print(f"  User: {user.username}")
                        print("-" * 60)
            
            # Thống kê phân bổ tài sản theo user
            print(f"\n{'='*60}")
            print("THONG KE PHAN BO TAI SAN THEO USER")
            print(f"{'='*60}\n")
            
            users = User.query.filter(
                User.deleted_at.is_(None),
                User.is_active == True
            ).all()
            
            for user in users:
                user_assets = Asset.query.filter(
                    Asset.user_id == user.id,
                    Asset.deleted_at.is_(None),
                    Asset.status != 'disposed'
                ).count()
                if user_assets > 0:
                    print(f"  {user.username}: {user_assets} tai san")
            
            print(f"\n{'='*60}\n")
            
        except Exception as e:
            print(f"[ERROR] Loi khi kiem tra: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    check_admin_assets()

