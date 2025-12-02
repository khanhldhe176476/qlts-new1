#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kiểm tra và tạo file .env nếu chưa có hoặc thiếu cấu hình email
"""
import os
import sys
import io
import shutil

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_and_create_env():
    """Kiểm tra và tạo .env từ env.example nếu cần"""
    env_file = '.env'
    example_file = 'env.example'
    
    if not os.path.exists(env_file):
        if os.path.exists(example_file):
            print(f"File .env chua ton tai. Dang copy tu {example_file}...")
            shutil.copy(example_file, env_file)
            print(f"✅ Da tao file .env tu {example_file}")
            print("\n⚠️  VUI LONG KIEM TRA VA CAP NHAT FILE .env:")
            print("   - DATABASE_URL (dung PostgreSQL cua Docker)")
            print("   - MAIL_PASSWORD (app password moi)")
            return True
        else:
            print("❌ Khong tim thay file env.example!")
            return False
    else:
        print(f"✅ File .env da ton tai")
        # Kiểm tra xem có cấu hình email không
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'EMAIL_ENABLED=true' not in content:
                print("⚠️  Chua co cau hinh EMAIL_ENABLED trong .env")
            if 'MAIL_PASSWORD=' not in content or 'MAIL_PASSWORD=your-' in content:
                print("⚠️  Chua co MAIL_PASSWORD hoac dang dung placeholder")
        return True

if __name__ == '__main__':
    print("=" * 60)
    print("KIEM TRA FILE .ENV")
    print("=" * 60)
    print()
    
    check_and_create_env()
    print()
    print("=" * 60)





