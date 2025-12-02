#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tạo file Excel từ danh sách người dùng và import vào hệ thống
"""

import pandas as pd
from app import app
from models import db, User, Role

# Danh sách người dùng từ hình ảnh
users_data = [
    # Bảng 1
    {"Người sử dụng": "Bùi Đức Anh", "User": "anhbd", "Mail": "anhbd@mhsolution.vn"},
    {"Người sử dụng": "Bùi Thị Anh", "User": "anhbt", "Mail": "anhbt@mhsolution.vn"},
    {"Người sử dụng": "Lê Phương Anh", "User": "anhlp", "Mail": "anhlp@mhsolution.vn"},
    {"Người sử dụng": "Lê Thị Mai Anh", "User": "anhltm", "Mail": "anhltm@mhsolution.vn"},
    {"Người sử dụng": "Nguyễn Minh Anh", "User": "anhnm", "Mail": "anhnm@mhsolution.vn"},
    {"Người sử dụng": "Nguyễn Thục Anh", "User": "anhnt", "Mail": "anhnt@mhsolution.vn"},
    {"Người sử dụng": "Phùng Việt Anh", "User": "anhpv", "Mail": "anhpv@mhsolution.vn"},
    {"Người sử dụng": "Trương Tuấn Anh", "User": "anhtt", "Mail": "anhtt@mhsolution.vn"},
    {"Người sử dụng": "Đồng Công Định", "User": "dinhdc", "Mail": "dinhdc@mhsolution.vn"},
    {"Người sử dụng": "Ngô Ngọc Bính", "User": "binhnn", "Mail": "binhnn@mhsolution.vn"},
    {"Người sử dụng": "Đặng Việt Đức", "User": "ducdv1", "Mail": "ducdv1@mhsolution.vn"},
    {"Người sử dụng": "Nguyễn Đức Đức", "User": "ducnd", "Mail": "ducnd@mhsolution.vn"},
    {"Người sử dụng": "Nguyễn Thùy Dương", "User": "duongtn", "Mail": "duongtn@mhsolution.vn"},
    {"Người sử dụng": "Cao Thị Thanh Hằng", "User": "hangctt", "Mail": "hangctt@mhsolution.vn"},
    {"Người sử dụng": "Trương Tứ Hải", "User": "haitt", "Mail": "haitt@mhsolution.vn"},
    {"Người sử dụng": "Nguyễn Thị Thu Hà", "User": "hatt2", "Mail": "hantt2@mhsolution.vn"},
    {"Người sử dụng": "Trịnh Minh Hiếu", "User": "hieutm", "Mail": "hieutm@mhsolution.vn"},
    {"Người sử dụng": "Vũ Quang Hiếu", "User": "hieuvq", "Mail": "hieuvq@mhsolution.vn"},
    {"Người sử dụng": "Lê Khánh Hòa", "User": "hoalk", "Mail": "hoalk@mhsolution.vn"},
    {"Người sử dụng": "Trần Huy Hoàng", "User": "hoangth", "Mail": "hoangth@mhsolution.vn"},
    {"Người sử dụng": "Lưu Quang Hùng", "User": "hunglq", "Mail": "hunglq@mhsolution.vn"},
    {"Người sử dụng": "Vũ Khánh Huyền", "User": "huyenvk", "Mail": "huyenvk@mhsolution.vn"},
    {"Người sử dụng": "Vũ Thị Ngọc Huyền", "User": "huyenvtn", "Mail": "huyenvtn@mhsolution.vn"},
    {"Người sử dụng": "Lê Duy Khánh", "User": "khanhld", "Mail": "khanhld@mhsolution.vn"},
    # Bảng 2
    {"Người sử dụng": "Thiều Kim Quang", "User": "quangtk", "Mail": "quangtk@mhsolution.vn"},
    {"Người sử dụng": "Nguyễn Hồng Lĩnh", "User": "linhng", "Mail": "linhnh@mhsolution.vn"},
    {"Người sử dụng": "Lê Minh Hưng", "User": "minhu4u", "Mail": "minhu4u@gmail.com"},
    {"Người sử dụng": "Nguyễn Duy Thành Nam", "User": "namndt", "Mail": "namndt@mhsolution.vn"},
    {"Người sử dụng": "Đinh Khánh Vy", "User": "vydk", "Mail": "vydk@mhsolution.vn"},
    {"Người sử dụng": "Lê Văn Long", "User": "longnn2", "Mail": "longnn2@mhsolution.vn"},
    {"Người sử dụng": "Nguyễn Văn Nam", "User": "namnv", "Mail": "namnv@mhsolution.vn"},
    {"Người sử dụng": "Trần Văn Hùng", "User": "hungtv", "Mail": "hungtv@mhsolution.vn"},
    {"Người sử dụng": "Phạm Thị Lan", "User": "lanpt", "Mail": "lanpt@mhsolution.vn"},
    {"Người sử dụng": "Hoàng Văn Đức", "User": "duchv", "Mail": "duchv@mhsolution.vn"},
    {"Người sử dụng": "Vũ Thị Mai", "User": "maivt", "Mail": "maivt@mhsolution.vn"},
    {"Người sử dụng": "Đỗ Văn Tuấn", "User": "tuandv", "Mail": "tuandv@mhsolution.vn"},
    {"Người sử dụng": "Bùi Thị Hoa", "User": "hoabt", "Mail": "hoabt@mhsolution.vn"},
    {"Người sử dụng": "Lý Văn Thành", "User": "thanhlv", "Mail": "thanhlv@mhsolution.vn"},
    {"Người sử dụng": "Ngô Thị Linh", "User": "linhnt", "Mail": "linhnt@mhsolution.vn"},
    {"Người sử dụng": "Phan Văn Hải", "User": "haipv", "Mail": "haipv@mhsolution.vn"},
    {"Người sử dụng": "Trương Thị Nga", "User": "ngatt", "Mail": "ngatt@mhsolution.vn"},
    {"Người sử dụng": "Lê Văn Sơn", "User": "sonlv", "Mail": "sonlv@mhsolution.vn"},
    {"Người sử dụng": "Võ Thị Hương", "User": "huongvt", "Mail": "huongvt@mhsolution.vn"},
    {"Người sử dụng": "Đặng Văn Minh", "User": "minhdv", "Mail": "minhdv@mhsolution.vn"},
]

def create_excel_and_import():
    """Tạo file Excel và import vào database"""
    # Chuẩn bị dữ liệu cho DataFrame
    excel_data = []
    for user in users_data:
        excel_data.append({
            'Username': user['User'],
            'Email': user['Mail'],
            'Role': 'user',  # Mặc định role là user
            'Password': 'mh123#@!'  # Mật khẩu mặc định
        })
    
    # Tạo DataFrame
    df = pd.DataFrame(excel_data)
    
    # Lưu file Excel
    excel_file = 'danh_sach_nguoi_dung_mhsolution.xlsx'
    df.to_excel(excel_file, index=False, engine='openpyxl')
    print(f'Da tao file Excel: {excel_file}')
    print(f'Tong so nguoi dung: {len(excel_data)}')
    
    # Import vào database
    print('\nDang import vao database...')
    created = 0
    updated = 0
    skipped = 0
    errors = []
    
    # Đảm bảo role 'user' tồn tại
    user_role = Role.query.filter_by(name='user').first()
    if not user_role:
        user_role = Role(name='user', description='Nhân viên')
        db.session.add(user_role)
        db.session.commit()
    
    for user_info in excel_data:
        try:
            username = user_info['Username']
            email = user_info['Email']
            
            # Kiểm tra user đã tồn tại chưa
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                # Cập nhật email nếu khác
                if existing_user.email != email:
                    existing_user.email = email
                    updated += 1
                    print(f'  Cap nhat: {username} ({email})')
                else:
                    skipped += 1
                    print(f'  Bo qua (da ton tai): {username}')
            else:
                # Tạo user mới
                new_user = User(
                    username=username,
                    email=email,
                    role_id=user_role.id,
                    is_active=True
                )
                new_user.set_password('mh123#@!')
                db.session.add(new_user)
                created += 1
                print(f'  Tao moi: {username} ({email})')
        except Exception as e:
            errors.append(f"{user_info['Username']}: {str(e)}")
            skipped += 1
            print(f'  Loi: {user_info["Username"]} - {str(e)}')
    
    # Commit tất cả
    try:
        db.session.commit()
        print(f'\n{"="*60}')
        print('KET QUA IMPORT:')
        print(f'{"="*60}')
        print(f'Tao moi: {created} nguoi dung')
        print(f'Cap nhat: {updated} nguoi dung')
        print(f'Bo qua: {skipped} nguoi dung')
        if errors:
            print(f'\nLoi: {len(errors)}')
            for error in errors[:5]:
                print(f'  - {error}')
        print(f'{"="*60}\n')
    except Exception as e:
        db.session.rollback()
        print(f'Loi khi commit: {str(e)}')

if __name__ == "__main__":
    with app.app_context():
        create_excel_and_import()



