#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để reset mật khẩu tất cả user thành mh123#@!
Chạy: py reset_all_passwords.py
"""

import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app import app
from models import db, User

def reset_all_passwords():
    """Reset mật khẩu tất cả user thành mh123#@!"""
    # Khởi tạo app context
    with app.app_context():
        default_password = 'mh123#@!'
        users = User.query.filter(User.deleted_at.is_(None)).all()
        updated_count = 0
        
        print(f"\n{'='*60}")
        print("ĐANG RESET MAT KHAU CHO TAT CA USER")
        print(f"{'='*60}\n")
        
        for user in users:
            try:
                user.set_password(default_password)
                updated_count += 1
                print(f"  ✓ Đã reset mật khẩu cho: {user.username} ({user.email})")
            except Exception as e:
                print(f"  ✗ Lỗi khi reset cho {user.username}: {str(e)}")
        
        try:
            db.session.commit()
            print(f"\n{'='*60}")
            print(f"✅ HOÀN THÀNH!")
            print(f"{'='*60}")
            print(f"Đã reset mật khẩu thành công cho {updated_count} người dùng")
            print(f"Mật khẩu mới cho tất cả user: {default_password}")
            print(f"{'='*60}\n")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Lỗi khi commit: {str(e)}\n")

if __name__ == "__main__":
    reset_all_passwords()

