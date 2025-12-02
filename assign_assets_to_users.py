"""
Script để gan tai san cho user (moi nguoi 1-2 thiet bi)
"""
import sys
import random
import io
from app import app
from models import db, User, Asset, Role

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def assign_assets_to_users():
    """Gán tài sản cho user, mỗi người 2-3 thiết bị"""
    with app.app_context():
        try:
            # Lấy tất cả user đang hoạt động (bao gồm admin/manager)
            users = User.query.filter(
                User.deleted_at.is_(None),
                User.is_active == True
            ).order_by(User.id).all()
            
            if not users:
                print("[ERROR] Khong co user nao de gan tai san")
                return
            
            # Lấy tất cả tài sản đang hoạt động
            assets = Asset.query.filter(
                Asset.deleted_at.is_(None),
                Asset.status == 'active'
            ).all()
            
            if not assets:
                print("[ERROR] Khong co tai san nao trong he thong")
                return
            
            total_assets = len(assets)
            user_count = len(users)
            
            print(f"\n{'='*60}")
            print("DANG GAN TAI SAN CHO USER")
            print(f"{'='*60}\n")
            print(f"So luong user hoat dong: {user_count}")
            print(f"So luong tai san hoat dong: {total_assets}\n")
            
            # Reset toàn bộ gán trước đó để phân phối lại
            for asset in assets:
                asset.user_id = None
            
            random.shuffle(assets)
            
            assigned_count = 0
            asset_index = 0
            user_assignments = {user.id: [] for user in users}
            
            # Vòng 1: đảm bảo mỗi user có tối thiểu 2 tài sản (nếu đủ)
            min_per_user = 2
            extra_per_user = 1  # tài sản thứ 3
            
            for _ in range(min_per_user):
                for user in users:
                    if asset_index >= total_assets:
                        break
                    asset = assets[asset_index]
                    asset.user_id = user.id
                    user_assignments[user.id].append(asset)
                    asset_index += 1
                    assigned_count += 1
            
            # Vòng 2: gán thêm tài sản thứ 3 nếu còn
            for user in users:
                if asset_index >= total_assets:
                    break
                asset = assets[asset_index]
                asset.user_id = user.id
                user_assignments[user.id].append(asset)
                asset_index += 1
                assigned_count += 1
            
            # Nếu vẫn còn tài sản, phân bổ vòng tròn
            idx = 0
            while asset_index < total_assets and users:
                user = users[idx % user_count]
                asset = assets[asset_index]
                asset.user_id = user.id
                user_assignments[user.id].append(asset)
                asset_index += 1
                assigned_count += 1
                idx += 1
            
            # In kết quả
            for user in users:
                assigned_assets = user_assignments[user.id]
                if assigned_assets:
                    asset_names = [a.name for a in assigned_assets]
                    preview = ', '.join(asset_names[:3])
                    suffix = '...' if len(asset_names) > 3 else ''
                    print(f"  [OK] {user.username} ({user.name or user.email}) <= {len(assigned_assets)} thiet bi: {preview}{suffix}")
                else:
                    print(f"  [WARN] {user.username} chua du tai san de gan.")
            
            # Commit tất cả thay đổi
            db.session.commit()
            
            print(f"\n{'='*60}")
            print(f"[OK] HOAN THANH!")
            print(f"{'='*60}")
            print(f"Da gan {assigned_count} thiet bi cho {user_count} user")
            print(f"So tai san con lai: {max(total_assets - assigned_count, 0)}")
            print(f"{'='*60}\n")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] Loi: {str(e)}\n")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    assign_assets_to_users()

