#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script migration để thêm các trường bảo hành vào bảng asset
Chạy script này một lần để cập nhật database
"""
import sys
import os
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import inspect, text
from models import Asset

def migrate():
    """Thêm các cột mới vào bảng asset nếu chưa có"""
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            existing_columns = {col['name'] for col in inspector.get_columns('asset')}
            
            columns_to_add = [
                ('warranty_contact_name', 'VARCHAR(200) NULL'),
                ('warranty_contact_phone', 'VARCHAR(50) NULL'),
                ('warranty_contact_email', 'VARCHAR(200) NULL'),
                ('warranty_website', 'VARCHAR(500) NULL'),
                ('warranty_start_date', 'DATE NULL'),
                ('warranty_end_date', 'DATE NULL'),
                ('warranty_period_months', 'INTEGER NULL'),
                ('invoice_file_path', 'VARCHAR(500) NULL'),
            ]
            
            added = []
            for col_name, col_type in columns_to_add:
                if col_name not in existing_columns:
                    try:
                        # SQLite uses different syntax
                        if db.engine.url.drivername == 'sqlite':
                            db.session.execute(text(f'ALTER TABLE asset ADD COLUMN {col_name} {col_type}'))
                        else:
                            # PostgreSQL/MySQL
                            db.session.execute(text(f'ALTER TABLE asset ADD COLUMN {col_name} {col_type}'))
                        added.append(col_name)
                        print(f"  [OK] Da them cot: {col_name}")
                    except Exception as e:
                        print(f"  [ERROR] Loi khi them cot {col_name}: {e}")
            
            if added:
                db.session.commit()
                print(f"\n[OK] Da them {len(added)} cot moi vao bang asset")
            else:
                print("\n[OK] Tat ca cac cot da ton tai, khong can migration")
                
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] Loi migration: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("MIGRATION: Them cac truong bao hanh vao bang asset")
    print("=" * 60)
    print()
    
    if migrate():
        print("\n[OK] Migration hoan tat!")
    else:
        print("\n[ERROR] Migration that bai!")
        sys.exit(1)

