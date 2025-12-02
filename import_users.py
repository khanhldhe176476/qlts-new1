#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script import danh sách người dùng từ file Excel
Cấu trúc file Excel:
- Cột 1: Username (bắt buộc)
- Cột 2: Email (bắt buộc)
- Cột 3: Role (tùy chọn, mặc định: user)
- Cột 4: Password (tùy chọn, mặc định: password123)

Cách sử dụng:
py import_users.py <ten_file.xlsx>
"""

import sys
import os
import pandas as pd
from app import app
from models import db, User, Role
from werkzeug.security import generate_password_hash

def normalize_role(role_str):
    """Chuẩn hóa tên role"""
    if not role_str:
        return 'user'
    role_str = str(role_str).strip().lower()
    if role_str in ['admin', 'administrator', 'quản trị', 'quan tri']:
        return 'admin'
    elif role_str in ['manager', 'quản lý', 'quan ly']:
        return 'manager'
    else:
        return 'user'

def import_users_from_excel(file_path):
    """Import users từ file Excel"""
    try:
        # Đọc file Excel
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Kiểm tra cột bắt buộc
        required_columns = []
        if 'Username' in df.columns or 'username' in df.columns or 'Tên đăng nhập' in df.columns:
            username_col = next((col for col in df.columns if col.lower() in ['username', 'tên đăng nhập']), None)
        elif len(df.columns) >= 1:
            username_col = df.columns[0]
        else:
            print("❌ Lỗi: File Excel không có cột Username")
            return
        
        if 'Email' in df.columns or 'email' in df.columns or 'Gmail' in df.columns or 'gmail' in df.columns:
            email_col = next((col for col in df.columns if col.lower() in ['email', 'gmail']), None)
        elif len(df.columns) >= 2:
            email_col = df.columns[1]
        else:
            print("❌ Lỗi: File Excel không có cột Email")
            return
        
        # Tìm các cột khác
        role_col = next((col for col in df.columns if col.lower() in ['role', 'vai trò', 'vai tro']), None)
        password_col = next((col for col in df.columns if col.lower() in ['password', 'mật khẩu', 'mat khau']), None)
        
        created = 0
        updated = 0
        skipped = 0
        errors = []
        
        print(f"\n📋 Đang import {len(df)} người dùng...\n")
        
        for index, row in df.iterrows():
            try:
                # Lấy thông tin từ các cột
                username = str(row[username_col]).strip() if pd.notna(row[username_col]) else None
                email = str(row[email_col]).strip() if pd.notna(row[email_col]) else None
                role_str = str(row[role_col]).strip() if role_col and pd.notna(row[role_col]) else 'user'
                password = str(row[password_col]).strip() if password_col and pd.notna(row[password_col]) else 'mh123#@!'
                
                # Kiểm tra dữ liệu
                if not username or username == 'nan':
                    errors.append(f"Dòng {index + 2}: Thiếu Username")
                    skipped += 1
                    continue
                
                if not email or email == 'nan':
                    errors.append(f"Dòng {index + 2}: Thiếu Email cho user {username}")
                    skipped += 1
                    continue
                
                # Chuẩn hóa email
                email = email.lower().strip()
                
                # Kiểm tra email hợp lệ
                if '@' not in email:
                    errors.append(f"Dòng {index + 2}: Email không hợp lệ: {email}")
                    skipped += 1
                    continue
                
                # Chuẩn hóa role
                role_name = normalize_role(role_str)
                
                # Kiểm tra role tồn tại
                role = Role.query.filter_by(name=role_name).first()
                if not role:
                    # Tạo role nếu chưa có
                    role = Role(name=role_name, description=f"Auto created: {role_name}")
                    db.session.add(role)
                    db.session.commit()
                
                # Kiểm tra user đã tồn tại chưa
                existing_user = User.query.filter_by(username=username).first()
                if existing_user:
                    # Cập nhật thông tin
                    existing_user.email = email
                    existing_user.role_id = role.id
                    if password and password != 'mh123#@!':
                        existing_user.set_password(password)
                    updated += 1
                    print(f"  ✓ Cập nhật: {username} ({email}) - Role: {role_name}")
                else:
                    # Tạo user mới
                    new_user = User(
                        username=username,
                        email=email,
                        role_id=role.id,
                        is_active=True
                    )
                    new_user.set_password(password)
                    db.session.add(new_user)
                    created += 1
                    print(f"  ✓ Tạo mới: {username} ({email}) - Role: {role_name}")
                
            except Exception as e:
                errors.append(f"Dòng {index + 2}: Lỗi - {str(e)}")
                skipped += 1
                continue
        
        # Commit tất cả
        db.session.commit()
        
        # Báo cáo kết quả
        print(f"\n{'='*60}")
        print("📊 KẾT QUẢ IMPORT:")
        print(f"{'='*60}")
        print(f"✅ Đã tạo mới: {created} người dùng")
        print(f"🔄 Đã cập nhật: {updated} người dùng")
        print(f"⚠️  Đã bỏ qua: {skipped} dòng")
        
        if errors:
            print(f"\n❌ Các lỗi gặp phải:")
            for error in errors[:10]:  # Chỉ hiển thị 10 lỗi đầu
                print(f"   - {error}")
            if len(errors) > 10:
                print(f"   ... và {len(errors) - 10} lỗi khác")
        
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ Lỗi khi đọc file Excel: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Thiếu tên file Excel!")
        print("\nCách sử dụng:")
        print("  py import_users.py <ten_file.xlsx>")
        print("\nCấu trúc file Excel:")
        print("  - Cột 1: Username (bắt buộc)")
        print("  - Cột 2: Email/Gmail (bắt buộc)")
        print("  - Cột 3: Role (tùy chọn, mặc định: user)")
        print("  - Cột 4: Password (tùy chọn, mặc định: mh123#@!)")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"❌ File không tồn tại: {file_path}")
        sys.exit(1)
    
    if not file_path.endswith(('.xlsx', '.xls')):
        print("❌ File phải có định dạng Excel (.xlsx hoặc .xls)")
        sys.exit(1)
    
    with app.app_context():
        import_users_from_excel(file_path)



