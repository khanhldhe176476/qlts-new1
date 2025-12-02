#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script test để kiểm tra ứng dụng có thể khởi động không
"""
import sys
import os
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 50)
print("KIEM TRA KHOI DONG UNG DUNG")
print("=" * 50)

# Kiểm tra Python version
print(f"\n1. Python version: {sys.version}")

# Kiem tra cac dependencies
print("\n2. Kiem tra dependencies...")
try:
    import flask
    print(f"   [OK] Flask {flask.__version__}")
except ImportError as e:
    print(f"   [ERROR] Flask khong tim thay: {e}")
    sys.exit(1)

try:
    import flask_sqlalchemy
    print(f"   [OK] Flask-SQLAlchemy")
except ImportError as e:
    print(f"   [ERROR] Flask-SQLAlchemy khong tim thay: {e}")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    print(f"   [OK] python-dotenv")
except ImportError as e:
    print(f"   [ERROR] python-dotenv khong tim thay: {e}")
    sys.exit(1)

# Kiem tra import app
print("\n3. Kiem tra import app...")
try:
    from app import app
    print("   [OK] Import app thanh cong")
except Exception as e:
    print(f"   [ERROR] Loi import app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Kiem tra config
print("\n4. Kiem tra config...")
try:
    has_secret = 'Da cau hinh' if app.config.get('SECRET_KEY') else 'Chua cau hinh'
    print(f"   [OK] SECRET_KEY: {has_secret}")
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri:
        # Mask password in URI
        if '@' in db_uri:
            parts = db_uri.split('@')
            if len(parts) > 1:
                masked = parts[0].split(':')[0] + ':***@' + '@'.join(parts[1:])
            else:
                masked = db_uri
        else:
            masked = db_uri
        print(f"   [OK] DATABASE_URI: {masked[:80]}...")
    else:
        print("   [ERROR] DATABASE_URI chua duoc cau hinh")
except Exception as e:
    print(f"   [ERROR] Loi kiem tra config: {e}")

# Kiem tra database connection
print("\n5. Kiem tra ket noi database...")
try:
    from models import db
    with app.app_context():
        # Test connection
        db.engine.connect()
        print("   [OK] Ket noi database thanh cong")
except Exception as e:
    print(f"   [ERROR] Loi ket noi database: {e}")
    import traceback
    traceback.print_exc()

# Kiem tra routes
print("\n6. Kiem tra routes...")
try:
    routes = [str(rule) for rule in app.url_map.iter_rules()]
    print(f"   [OK] Tim thay {len(routes)} routes")
    print(f"   [OK] Route chinh: /")
    print(f"   [OK] Route login: /login")
except Exception as e:
    print(f"   [ERROR] Loi kiem tra routes: {e}")

print("\n" + "=" * 50)
print("KIEM TRA HOAN TAT")
print("=" * 50)
print("\nNeu khong co loi, ban co the chay: py run.py")
print("Sau do mo trinh duyet: http://127.0.0.1:5000")

