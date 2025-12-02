#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để reset password cho tất cả users về mh123#@!
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
    """Reset password cho tất cả users"""
    new_password = "mh123#@!"
    
    with app.app_context():
        users = User.query.filter(User.deleted_at.is_(None)).all()
        
        if not users:
            print("Không tìm thấy user nào!")
            return
        
        print(f"Đang reset password cho {len(users)} users...")
        
        for user in users:
            user.set_password(new_password)
            print(f"  ✓ Đã reset password cho: {user.username} ({user.email})")
        
        db.session.commit()
        
        print(f"\n✅ Đã reset password thành công cho tất cả users!")
        print(f"   Password mới: {new_password}")
        print(f"\n📋 Danh sách users:")
        for user in users:
            print(f"   - {user.username} ({user.email})")

if __name__ == "__main__":
    reset_all_passwords()

