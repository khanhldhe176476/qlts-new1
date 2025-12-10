#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để xóa tất cả bản ghi bàn giao tài sản
"""
import sys
import io

# Configure UTF-8 encoding for stdout/stderr on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app import app, db
from models import AssetTransfer

def reset_transfers():
    """Xóa tất cả bản ghi bàn giao tài sản"""
    with app.app_context():
        try:
            print("=" * 60)
            print("XOA TAT CA BAN GHI BAN GIAO TAI SAN")
            print("=" * 60)
            
            # Đếm số bản ghi hiện có (bao gồm cả đã xóa nếu có)
            existing_transfers = AssetTransfer.query.all()
            count = len(existing_transfers)
            
            print(f"\nTim thay {count} ban ghi ban giao hien co")
            
            if count == 0:
                print("Khong co ban ghi nao de xoa!")
                return True
            
            # Hiển thị danh sách trước khi xóa
            print("\nDanh sach ban ghi se bi xoa:")
            for transfer in existing_transfers[:10]:  # Hiển thị 10 đầu tiên
                asset_name = transfer.asset.name if transfer.asset else 'N/A'
                print(f"  - {transfer.transfer_code} (ID: {transfer.id}) - {asset_name}")
            if count > 10:
                print(f"  ... va {count - 10} ban ghi khac")
            
            # Xóa tất cả bản ghi (tự động, không cần xác nhận)
            print(f"\nDang xoa tat ca {count} ban ghi ban giao...")
            deleted_count = 0
            for transfer in existing_transfers:
                try:
                    db.session.delete(transfer)
                    deleted_count += 1
                    if deleted_count <= 10:
                        print(f"  - Da xoa: {transfer.transfer_code} (ID: {transfer.id})")
                except Exception as e:
                    print(f"  ✗ Loi khi xoa {transfer.transfer_code}: {str(e)}")
            
            db.session.commit()
            print(f"\n✓ Da xoa {deleted_count}/{count} ban ghi ban giao")
            print("=" * 60)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ LOI: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    reset_transfers()

