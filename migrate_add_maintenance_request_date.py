#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script migration để thêm cột request_date vào bảng maintenance_record
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

def migrate():
    """Thêm cột request_date vào bảng maintenance_record nếu chưa có"""
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            existing_columns = {col['name'] for col in inspector.get_columns('maintenance_record')}
            
            if 'request_date' not in existing_columns:
                try:
                    # Thêm cột request_date với giá trị mặc định
                    db.session.execute(text('ALTER TABLE maintenance_record ADD COLUMN request_date DATE DEFAULT CURRENT_DATE'))
                    db.session.commit()
                    print("  [OK] Da them cot: request_date")
                    return True
                except Exception as e:
                    db.session.rollback()
                    print(f"  [ERROR] Loi khi them cot request_date: {e}")
                    return False
            else:
                print("  [OK] Cot request_date da ton tai")
                return True
                
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] Loi migration: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("MIGRATION: Them cot request_date vao bang maintenance_record")
    print("=" * 60)
    print()
    
    if migrate():
        print("\n[OK] Migration hoan tat!")
    else:
        print("\n[ERROR] Migration that bai!")
        sys.exit(1)





