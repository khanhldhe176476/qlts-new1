#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để chạy ứng dụng Flask
"""
import sys
import io

# Configure UTF-8 encoding for stdout/stderr on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app import app, db
from sqlalchemy import inspect, text
try:
    from app import ensure_asset_columns
except ImportError:
    ensure_asset_columns = None
from models import Asset, Role, User, AssetType, AssetTransfer, Permission, UserPermission

if __name__ == '__main__':
    with app.app_context():
        # Tạo bảng database nếu chưa tồn tại
        db.create_all()
        # Ensure legacy tables have new nullable columns to avoid crashes without migrations
        try:
            inspector = inspect(db.engine)
            existing_user_columns = {col['name'] for col in inspector.get_columns('user')}
            ddl_statements = []
            # Add nullable columns safely if they don't exist yet
            if 'deleted_at' not in existing_user_columns:
                ddl_statements.append('ALTER TABLE "user" ADD COLUMN deleted_at TIMESTAMP NULL')
            if 'last_login' not in existing_user_columns:
                ddl_statements.append('ALTER TABLE "user" ADD COLUMN last_login TIMESTAMP NULL')
            if 'asset_quota' not in existing_user_columns:
                ddl_statements.append('ALTER TABLE "user" ADD COLUMN asset_quota INTEGER DEFAULT 0')
            if 'name' not in existing_user_columns:
                ddl_statements.append('ALTER TABLE "user" ADD COLUMN name VARCHAR(200) NULL')
            for ddl in ddl_statements:
                try:
                    db.session.execute(text(ddl))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
        except Exception:
            # Non-fatal: continue startup; queries will raise if schema is still incompatible
            pass
        # Ensure asset table has all required columns
        try:
            inspector = inspect(db.engine)
            existing_asset_columns = {col['name'] for col in inspector.get_columns('asset')}
            asset_ddl_statements = []
            # Add nullable columns safely if they don't exist yet
            if 'purchase_date' not in existing_asset_columns:
                asset_ddl_statements.append('ALTER TABLE "asset" ADD COLUMN purchase_date DATE NULL')
            if 'device_code' not in existing_asset_columns:
                asset_ddl_statements.append('ALTER TABLE "asset" ADD COLUMN device_code VARCHAR(100) NULL')
            if 'condition_label' not in existing_asset_columns:
                asset_ddl_statements.append('ALTER TABLE "asset" ADD COLUMN condition_label VARCHAR(100) NULL')
            # asset_extensions (used by routes_api)
            if 'tinh_trang_danh_gia' not in existing_asset_columns:
                asset_ddl_statements.append('ALTER TABLE "asset" ADD COLUMN tinh_trang_danh_gia VARCHAR(100) NULL')
            if 'usage_status' not in existing_asset_columns:
                asset_ddl_statements.append('ALTER TABLE "asset" ADD COLUMN usage_status VARCHAR(50) NULL')
            if 'user_text' not in existing_asset_columns:
                asset_ddl_statements.append('ALTER TABLE "asset" ADD COLUMN user_text TEXT NULL')
            if 'deleted_at' not in existing_asset_columns:
                asset_ddl_statements.append('ALTER TABLE "asset" ADD COLUMN deleted_at TIMESTAMP NULL')
            if 'display_order' not in existing_asset_columns:
                asset_ddl_statements.append('ALTER TABLE "asset" ADD COLUMN display_order INTEGER NULL')
            for ddl in asset_ddl_statements:
                try:
                    db.session.execute(text(ddl))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
        except Exception:
            # Non-fatal: continue startup
            pass
        # Ensure asset_transfer table has new optional columns (asset_extensions)
        try:
            inspector = inspect(db.engine)
            existing_transfer_columns = {col['name'] for col in inspector.get_columns('asset_transfer')}
            transfer_ddl_statements = []
            if 'decision_number' not in existing_transfer_columns:
                transfer_ddl_statements.append('ALTER TABLE "asset_transfer" ADD COLUMN decision_number VARCHAR(100) NULL')
            if 'agency_from' not in existing_transfer_columns:
                transfer_ddl_statements.append('ALTER TABLE "asset_transfer" ADD COLUMN agency_from VARCHAR(255) NULL')
            if 'agency_to' not in existing_transfer_columns:
                transfer_ddl_statements.append('ALTER TABLE "asset_transfer" ADD COLUMN agency_to VARCHAR(255) NULL')
            for ddl in transfer_ddl_statements:
                try:
                    db.session.execute(text(ddl))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
        except Exception:
            pass
        # Ensure asset_type table has all required columns
        try:
            inspector = inspect(db.engine)
            existing_asset_type_columns = {col['name'] for col in inspector.get_columns('asset_type')}
            asset_type_ddl_statements = []
            # Add nullable columns safely if they don't exist yet
            if 'deleted_at' not in existing_asset_type_columns:
                asset_type_ddl_statements.append('ALTER TABLE "asset_type" ADD COLUMN deleted_at TIMESTAMP NULL')
            for ddl in asset_type_ddl_statements:
                try:
                    db.session.execute(text(ddl))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
        except Exception:
            # Non-fatal: continue startup
            pass
        # Ensure maintenance_record table has all required columns
        try:
            inspector = inspect(db.engine)
            existing_maintenance_columns = {col['name'] for col in inspector.get_columns('maintenance_record')}
            maintenance_ddl_statements = []
            # Add nullable columns safely if they don't exist yet
            if 'deleted_at' not in existing_maintenance_columns:
                maintenance_ddl_statements.append('ALTER TABLE "maintenance_record" ADD COLUMN deleted_at TIMESTAMP NULL')
            for ddl in maintenance_ddl_statements:
                try:
                    db.session.execute(text(ddl))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
        except Exception:
            # Non-fatal: continue startup
            pass

        # Ensure asset_process_request table has all required columns
        try:
            inspector = inspect(db.engine)
            existing_process_columns = {col['name'] for col in inspector.get_columns('asset_process_request')}
            process_ddl_statements = []
            
            new_cols = [
                ('request_date', 'DATE DEFAULT CURRENT_DATE'),
                ('unit_name', 'VARCHAR(255)'),
                ('current_status', 'VARCHAR(100)'),
                ('quantity', 'INTEGER DEFAULT 1'),
                ('original_price', 'FLOAT'),
                ('remaining_value', 'FLOAT'),
                ('attachment_path', 'VARCHAR(500)'),
                ('verifier_id', 'INTEGER'),
                ('verified_at', 'TIMESTAMP'),
                ('verification_notes', 'TEXT')
            ]
            
            for col_name, col_type in new_cols:
                if col_name not in existing_process_columns:
                    process_ddl_statements.append(f'ALTER TABLE "asset_process_request" ADD COLUMN {col_name} {col_type}')
            
            for ddl in process_ddl_statements:
                try:
                    db.session.execute(text(ddl))
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    # SQLite workaround for CURRENT_DATE
                    if 'request_date' in ddl and 'CURRENT_DATE' in str(e):
                        try:
                            # Use a constant for SQLite if CURRENT_DATE fails in ALTER
                            db.session.execute(text("ALTER TABLE \"asset_process_request\" ADD COLUMN request_date DATE DEFAULT '2026-01-01'"))
                            db.session.commit()
                        except:
                            db.session.rollback()
        except Exception:
            pass
        # Ensure permission tables exist
        try:
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            if 'permission' not in tables:
                db.create_all()
        except Exception:
            pass
        # Auto-bootstrap minimal data so login always works on first run
        try:
            if Role.query.count() == 0:
                roles = [
                    Role(name='admin', description='Quản trị'),
                    Role(name='manager', description='Quản lý'),
                    Role(name='user', description='Nhân viên'),
                ]
                db.session.add_all(roles)
                db.session.commit()
            # Ensure an admin exists
            admin_username = app.config.get('ADMIN_USERNAME', 'admin')
            admin_email = app.config.get('ADMIN_EMAIL', 'admin@example.com')
            admin_password = app.config.get('ADMIN_PASSWORD', 'admin123')
            if User.query.filter_by(username=admin_username).first() is None:
                admin_role = Role.query.filter_by(name='admin').first()
                if not admin_role:
                    admin_role = Role(name='admin', description='Quản trị')
                    db.session.add(admin_role)
                    db.session.commit()
                u = User(username=admin_username, email=admin_email, role_id=admin_role.id, is_active=True)
                u.set_password(admin_password)
                db.session.add(u)
                db.session.commit()
        except Exception as e:
            # Non-fatal, print diagnostic
            print("Bootstrap error:", e)
        # Initialize default permissions
        try:
            default_perms = Permission.get_default_permissions()
            for perm_data in default_perms:
                existing = Permission.query.filter_by(
                    module=perm_data['module'],
                    action=perm_data['action']
                ).first()
                if not existing:
                    perm = Permission(
                        module=perm_data['module'],
                        action=perm_data['action'],
                        name=perm_data['name'],
                        category=perm_data['category']
                    )
                    db.session.add(perm)
            db.session.commit()
        except Exception as e:
            print("Permission bootstrap error:", e)
            db.session.rollback()
        # Ensure new optional columns exist
        if ensure_asset_columns:
            try:
                ensure_asset_columns()
            except Exception:
                pass
    import os
    # Avoid emojis to prevent UnicodeEncodeError on some Windows consoles
    # Use 127.0.0.1 instead of 0.0.0.0 for better Windows compatibility
    host = os.getenv('HOST', '0.0.0.0')
    try:
        port = int(os.getenv('PORT', '5000'))
    except Exception:
        port = 5000
    print("=" * 60)
    print("KHOI DONG UNG DUNG QUAN LY TAI SAN")
    print("=" * 60)
    print(f"\nUNG DUNG DANG CHAY TAI:")
    print(f"  http://{host}:{port}")
    print(f"  http://localhost:{port}")
    print("\nTai khoan mac dinh:")
    print(f"  Username: {app.config.get('ADMIN_USERNAME', os.getenv('ADMIN_USERNAME', 'admin'))}")
    print(f"  Password: {app.config.get('ADMIN_PASSWORD', os.getenv('ADMIN_PASSWORD', 'admin123'))}")
    print("\nNhan Ctrl+C de dung ung dung")
    print("=" * 60 + "\n")
    
    # Auto-open browser disabled - user can manually open browser if needed
    # def open_browser():
    #     import time
    #     import webbrowser
    #     time.sleep(1.5)  # Wait for server to start
    #     url = f"http://{host}:{port}"
    #     print(f"\n[DANG MO TRINH DUYET: {url}]")
    #     webbrowser.open(url)
    # 
    # import threading
    # browser_thread = threading.Thread(target=open_browser, daemon=True)
    # browser_thread.start()
    
    try:
        app.run(debug=app.config.get('DEBUG', False), host=host, port=port)
    except OSError as e:
        # Common case: port in use
        if "Address already in use" in str(e):
            alt_port = 5050
            print(f"Cong {port} dang duoc su dung. Thu chay lai voi cong {alt_port} ...")
            app.run(debug=app.config.get('DEBUG', False), host=host, port=alt_port)
        else:
            raise
