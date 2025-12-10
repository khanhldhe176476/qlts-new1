# -*- coding: utf-8 -*-
"""
Script tự động xóa tất cả tài sản trùng lặp
Chạy: py remove_duplicates_auto.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from remove_duplicate_assets import remove_all_duplicates

if __name__ == "__main__":
    print("=" * 60)
    print("TỰ ĐỘNG XÓA TẤT CẢ TÀI SẢN TRÙNG LẶP")
    print("=" * 60)
    
    total_removed, total_groups = remove_all_duplicates()
    
    print("\n" + "=" * 60)
    print(f"TỔNG KẾT:")
    print(f"  - Đã xóa: {total_removed} tài sản trùng lặp")
    print(f"  - Số nhóm xử lý: {total_groups}")
    print("=" * 60)

