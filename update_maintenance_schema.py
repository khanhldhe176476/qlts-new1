#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để cập nhật database schema cho MaintenanceRecord
Thêm các trường mới nếu chưa có
"""

from app import app
from models import db, MaintenanceRecord
from sqlalchemy import inspect, text

def update_schema():
    """Cập nhật schema cho MaintenanceRecord"""
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('maintenance_record')]
        
        print("Cac cot hien co:", columns)
        
        # Danh sach cac cot can them
        new_columns = {
            'request_date': 'DATE',
            'requested_by_id': 'INTEGER',
            'maintenance_reason': 'VARCHAR(50)',
            'condition_before': 'TEXT',
            'damage_level': 'VARCHAR(20)',
            'vendor_phone': 'VARCHAR(50)',
            'estimated_cost': 'FLOAT',
            'completed_date': 'DATE',
            'replaced_parts': 'TEXT',
            'result_status': 'VARCHAR(20)',
            'result_notes': 'TEXT',
            'invoice_file': 'VARCHAR(500)',
            'acceptance_file': 'VARCHAR(500)',
            'before_image': 'VARCHAR(500)',
            'after_image': 'VARCHAR(500)'
        }
        
        added = []
        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                try:
                    if col_type == 'DATE':
                        db.session.execute(text(f"ALTER TABLE maintenance_record ADD COLUMN {col_name} DATE"))
                    elif col_type == 'INTEGER':
                        db.session.execute(text(f"ALTER TABLE maintenance_record ADD COLUMN {col_name} INTEGER"))
                    elif col_type.startswith('VARCHAR'):
                        size = col_type.replace('VARCHAR(', '').replace(')', '')
                        db.session.execute(text(f"ALTER TABLE maintenance_record ADD COLUMN {col_name} VARCHAR({size})"))
                    elif col_type == 'FLOAT':
                        db.session.execute(text(f"ALTER TABLE maintenance_record ADD COLUMN {col_name} FLOAT"))
                    elif col_type == 'TEXT':
                        db.session.execute(text(f"ALTER TABLE maintenance_record ADD COLUMN {col_name} TEXT"))
                    
                    db.session.commit()
                    added.append(col_name)
                    print(f"OK: Da them cot: {col_name}")
                except Exception as e:
                    db.session.rollback()
                    print(f"ERROR: Loi khi them cot {col_name}: {str(e)}")
            else:
                print(f"- Cot {col_name} da ton tai")
        
        if added:
            print(f"\nOK: Da them {len(added)} cot moi: {', '.join(added)}")
        else:
            print("\nOK: Tat ca cac cot da ton tai, khong can cap nhat")
        
        # Kiem tra lai
        columns_after = [col['name'] for col in inspector.get_columns('maintenance_record')]
        print(f"\nTong so cot sau khi cap nhat: {len(columns_after)}")

if __name__ == "__main__":
    update_schema()
