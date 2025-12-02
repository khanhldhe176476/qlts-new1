#!/usr/bin/env python3
"""
Script tạo file Excel mẫu để test chức năng import
"""
import pandas as pd
from datetime import date

# Tạo dữ liệu mẫu
data = {
    'Tên tài sản': [
        'USB WIFI',
        'Màn Hình HKC MB24V9 23.8"',
        'Chuột Newmen',
        'Cây máy tính Xigmatek XA-20-O Core i5',
        'Cap HDMI',
        'Bàn Phím Newmen',
        'Màn hình HKC',
        'Cây máy tính core i5 13400'
    ],
    'Loại tài sản': [
        'Thiết bị mạng',
        'Thiết bị văn phòng',
        'Thiết bị văn phòng',
        'Máy tính',
        'Thiết bị',
        'Thiết bị văn phòng',
        'Thiết bị văn phòng',
        'Máy tính'
    ],
    'Giá tiền': [
        3090000,
        11800000,
        660000,
        12300000,
        123000,
        3300000,
        9000000,
        14850000
    ],
    'Số lượng': [
        1,
        1,
        2,
        1,
        1,
        1,
        1,
        1
    ],
    'Trạng thái': [
        'Đang sử dụng',
        'Đang sử dụng',
        'Bảo trì',
        'Đang sử dụng',
        'Đang sử dụng',
        'Đang sử dụng',
        'Đang sử dụng',
        'Đang sử dụng'
    ],
    'Ngày mua': [
        '08/08/2022',
        '22/03/2024',
        '25/05/2021',
        '15/01/2023',
        '10/06/2023',
        '20/07/2023',
        '05/08/2023',
        '12/09/2023'
    ],
    'Mã thiết bị': [
        'USB01',
        'MH01',
        'MOUSE01',
        'CAY01',
        'HDMI01',
        'BP01',
        'MH02',
        'CAY02'
    ],
    'Người sử dụng': [
        'Admin',
        'User1',
        'User2',
        'User3',
        'User4',
        'User5',
        'User6',
        'User7'
    ]
}

# Tạo DataFrame
df = pd.DataFrame(data)

# Lưu file Excel
output_file = 'test_import_assets.xlsx'
df.to_excel(output_file, index=False, engine='openpyxl')

print(f'Created file {output_file} successfully!')
print(f'Number of rows: {len(df)}')
print('Columns created in Excel file')

