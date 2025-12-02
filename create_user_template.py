#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tạo file Excel mẫu để import người dùng
"""

import pandas as pd

# Tạo dữ liệu mẫu
data = {
    'Username': [
        'user1',
        'user2',
        'user3',
        'manager1',
        'admin2'
    ],
    'Email': [
        'user1@company.com',
        'user2@company.com',
        'user3@company.com',
        'manager1@company.com',
        'admin2@company.com'
    ],
    'Role': [
        'user',
        'user',
        'user',
        'manager',
        'admin'
    ],
    'Password': [
        'password123',
        'password123',
        'password123',
        'password123',
        'password123'
    ]
}

# Tạo DataFrame
df = pd.DataFrame(data)

# Lưu file Excel
output_file = 'danh_sach_nguoi_dung.xlsx'
df.to_excel(output_file, index=False, engine='openpyxl')

print(f'Da tao file mau: {output_file}')
print(f'\nCau truc file:')
print(f'   - Cot 1: Username (bat buoc)')
print(f'   - Cot 2: Email/Gmail (bat buoc)')
print(f'   - Cot 3: Role (tuy chon: user/manager/admin, mac dinh: user)')
print(f'   - Cot 4: Password (tuy chon, mac dinh: password123)')
print(f'\nHay dien thong tin nguoi dung vao file va chay:')
print(f'   py import_users.py {output_file}')

