# -*- coding: utf-8 -*-
"""Check data in SQLite database"""
import os
import sys
from sqlalchemy import create_engine, text

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

SQLITE_DB = 'sqlite:///./instance/app.db'
engine = create_engine(SQLITE_DB)

print("Checking data in SQLite database...")
print("=" * 60)

try:
    with engine.connect() as conn:
        # Check users
        result = conn.execute(text("SELECT COUNT(*) FROM \"user\";"))
        user_count = result.fetchone()[0]
        print(f"Users: {user_count}")
        
        # Check assets
        result = conn.execute(text("SELECT COUNT(*) FROM asset WHERE deleted_at IS NULL;"))
        asset_count = result.fetchone()[0]
        print(f"Assets: {asset_count}")
        
        # Check asset types
        result = conn.execute(text("SELECT COUNT(*) FROM asset_type WHERE deleted_at IS NULL;"))
        asset_type_count = result.fetchone()[0]
        print(f"Asset Types: {asset_type_count}")
        
        # Check roles
        result = conn.execute(text("SELECT COUNT(*) FROM role;"))
        role_count = result.fetchone()[0]
        print(f"Roles: {role_count}")
        
        # Check maintenance records
        result = conn.execute(text("SELECT COUNT(*) FROM maintenance_record WHERE deleted_at IS NULL;"))
        maint_count = result.fetchone()[0]
        print(f"Maintenance Records: {maint_count}")
        
        print("=" * 60)
        print(f"\nSQLite has: {user_count} users, {asset_count} assets, {asset_type_count} asset types")
        
        if asset_count > 0:
            print("\n=> SQLite database has data. You can migrate this data to PostgreSQL.")
        
except Exception as e:
    print(f"Error: {e}")
