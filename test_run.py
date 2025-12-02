#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script test chạy ứng dụng với output rõ ràng
"""
import sys
import os
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

print("=" * 60)
print("BAT DAU KHOI DONG UNG DUNG")
print("=" * 60)

try:
    from app import app
    from models import db
    
    # Initialize database
    with app.app_context():
        db.create_all()
        print("[OK] Database da san sang")
    
    # Get host and port
    host = os.getenv('HOST', '127.0.0.1')
    try:
        port = int(os.getenv('PORT', '5000'))
    except:
        port = 5000
    
    print("\n" + "=" * 60)
    print(f"UNG DUNG DANG CHAY TAI:")
    print(f"  http://{host}:{port}")
    print(f"  http://localhost:{port}")
    print("=" * 60)
    print("\nTai khoan mac dinh:")
    print(f"  Username: {os.getenv('ADMIN_USERNAME', 'admin')}")
    print(f"  Password: {os.getenv('ADMIN_PASSWORD', 'admin123')}")
    print("\nNhan Ctrl+C de dung ung dung")
    print("=" * 60 + "\n")
    
    # Run app
    app.run(debug=True, host=host, port=port, use_reloader=False)
    
except OSError as e:
    if "Address already in use" in str(e) or "Only one usage" in str(e):
        print(f"\n[ERROR] Port {port} dang duoc su dung!")
        print(f"Thu dung port khac: http://127.0.0.1:5050")
        try:
            app.run(debug=True, host=host, port=5050, use_reloader=False)
        except Exception as e2:
            print(f"[ERROR] Khong the chay ung dung: {e2}")
            sys.exit(1)
    else:
        print(f"\n[ERROR] Loi khi khoi dong: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
except Exception as e:
    print(f"\n[ERROR] Loi khong xac dinh: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

