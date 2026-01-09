#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script phan bo dong deu tai san cho tat ca nhan vien
Distributes assets evenly among all active users
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import app, db
from models import User, Asset, asset_user
from sqlalchemy import func

def distribute_assets_evenly():
    """
    Phan bo dong deu tat ca tai san cho tat ca nhan vien dang hoat dong
    """
    with app.app_context():
        print("=" * 70)
        print("BAT DAU PHAN BO TAI SAN")
        print("=" * 70)
        
        # 1. Lay tat ca users dang hoat dong
        users = User.query.filter(User.deleted_at.is_(None), User.is_active == True).all()
        
        if not users:
            print("Khong tim thay user nao dang hoat dong!")
            return
        
        print(f"Tim thay {len(users)} nhan vien dang hoat dong:")
        for i, u in enumerate(users, 1):
            print(f"   {i}. {u.name or u.username} ({u.role.description if u.role else 'No role'})")
        
        # 2. Lay tat ca assets dang hoat dong
        assets = Asset.query.filter(Asset.deleted_at.is_(None)).all()
        
        if not assets:
            print("Khong tim thay tai san nao!")
            return
        
        print(f"\nTim thay {len(assets)} tai san can phan bo")
        
        # 3. Xoa tat ca phan bo cu
        print("\nXoa phan bo cu...")
        db.session.execute(asset_user.delete())
        db.session.commit()
        print("Da xoa phan bo cu")
        
        # 4. Phan bo dong deu theo round-robin
        print("\nBat dau phan bo dong deu...")
        
        user_index = 0
        assignments = {u.id: [] for u in users}
        
        for asset in assets:
            # Chon user theo vong tron
            current_user = users[user_index % len(users)]
            
            # Them vao bang asset_user
            db.session.execute(
                asset_user.insert().values(
                    asset_id=asset.id,
                    user_id=current_user.id
                )
            )
            
            # Track assignments
            assignments[current_user.id].append(asset.name)
            
            user_index += 1
        
        # 5. Commit tat ca
        db.session.commit()
        
        print("\n" + "=" * 70)
        print("PHAN BO HOAN TAT")
        print("=" * 70)
        
        # 6. Hien thi ket qua
        print("\nKET QUA PHAN BO:\n")
        
        for user in users:
            count = len(assignments[user.id])
            print(f"{user.name or user.username:<30} | {count:>3} tai san")
            
            # Hien thi mot vai tai san mau
            if assignments[user.id]:
                sample = assignments[user.id][:3]
                for asset_name in sample:
                    print(f"   - {asset_name}")
                if count > 3:
                    print(f"   - ...va {count - 3} tai san khac")
            print()
        
        # 7. Thong ke tong quan
        total_assigned = sum(len(a) for a in assignments.values())
        avg_per_user = total_assigned / len(users) if users else 0
        
        print("=" * 70)
        print(f"THONG KE:")
        print(f"   - Tong tai san da phan bo: {total_assigned}")
        print(f"   - So nhan vien: {len(users)}")
        print(f"   - Trung binh moi nguoi: {avg_per_user:.1f} tai san")
        print("=" * 70)
        
        return True

if __name__ == "__main__":
    try:
        print("\nCANH BAO: Script nay se:")
        print("   1. XOA TAT CA phan bo tai san hien tai")
        print("   2. PHAN BO LAI dong deu cho tat ca nhan vien")
        print()
        
        confirm = input("Ban co chac chan muon tiep tuc? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y', 'co']:
            distribute_assets_evenly()
        else:
            print("\nDa huy thao tac")
    
    except Exception as e:
        print(f"\nLOI: {str(e)}")
        import traceback
        traceback.print_exc()
