#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để kiểm tra tài sản có user_id nhưng user không tồn tại hoặc bị xóa
"""
import sys
import io
from app import app
from models import db, Asset, User

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_asset_user_mismatch():
    """Kiểm tra tài sản có user_id nhưng user không tồn tại hoặc bị xóa"""
    with app.app_context():
        try:
            # Lấy tất cả tài sản không bị xóa mềm và không bị thanh lý
            all_assets = Asset.query.filter(
                Asset.deleted_at.is_(None),
                Asset.status != 'disposed'
            ).all()
            
            print(f"\n{'='*60}")
            print("KIEM TRA TAI SAN CO USER_ID NHUNG USER KHONG TON TAI")
            print(f"{'='*60}\n")
            print(f"Tong tai san: {len(all_assets)}\n")
            
            # Kiểm tra tài sản có user_id nhưng user không tồn tại hoặc bị xóa
            problem_assets = []
            
            for asset in all_assets:
                if asset.user_id is not None:
                    # Kiểm tra user có tồn tại không
                    user = User.query.get(asset.user_id)
                    if user is None:
                        problem_assets.append({
                            'asset': asset,
                            'reason': 'User không tồn tại',
                            'user_id': asset.user_id
                        })
                    elif user.deleted_at is not None:
                        problem_assets.append({
                            'asset': asset,
                            'reason': 'User đã bị xóa mềm',
                            'user_id': asset.user_id,
                            'user': user
                        })
                    elif not user.is_active:
                        problem_assets.append({
                            'asset': asset,
                            'reason': 'User không hoạt động',
                            'user_id': asset.user_id,
                            'user': user
                        })
            
            print(f"Tai san co van de: {len(problem_assets)}\n")
            
            if problem_assets:
                print("Danh sach tai san co van de:")
                print("-" * 60)
                for item in problem_assets:
                    asset = item['asset']
                    print(f"  ID: {asset.id}")
                    print(f"  Ten: {asset.name}")
                    print(f"  user_id: {item['user_id']}")
                    print(f"  Ly do: {item['reason']}")
                    if 'user' in item:
                        print(f"  User: {item['user'].username}")
                    print("-" * 60)
            else:
                print("✓ Tat ca tai san deu co user hop le!")
            
            # Đếm số tài sản được gán (theo logic trong profile)
            # 1. Tài sản có user_id và user hợp lệ
            assets_with_valid_user = 0
            for asset in all_assets:
                if asset.user_id is not None:
                    user = User.query.get(asset.user_id)
                    if user and user.deleted_at is None and user.is_active:
                        assets_with_valid_user += 1
            
            # 2. Tài sản được gán qua bảng asset_user
            from models import asset_user
            from sqlalchemy import and_
            assets_assigned_via_table = Asset.query.join(
                asset_user, Asset.id == asset_user.c.asset_id
            ).filter(
                Asset.deleted_at.is_(None),
                Asset.status != 'disposed'
            ).distinct().count()
            
            print(f"\n{'='*60}")
            print("THONG KE THEO LOGIC PROFILE")
            print(f"{'='*60}\n")
            print(f"Tai san co user_id hop le: {assets_with_valid_user}")
            print(f"Tai san duoc gan qua asset_user: {assets_assigned_via_table}")
            print(f"Tong tai san (khong bi thanh ly): {len(all_assets)}")
            print(f"\nChenh lech: {len(all_assets) - assets_with_valid_user}")
            
            print(f"\n{'='*60}\n")
            
        except Exception as e:
            print(f"[ERROR] Loi khi kiem tra: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    check_asset_user_mismatch()

