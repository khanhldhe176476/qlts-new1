# -*- coding: utf-8 -*-
"""Check data in mh_cursor_test database"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', '')
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

print("Checking data in current database...")
print("=" * 60)

with engine.connect() as conn:
    result = conn.execute(text("SELECT current_database();"))
    db_name = result.fetchone()[0]
    print(f"Connected to: {db_name}")
    print("=" * 60)
    
    # Check users
    result = conn.execute(text('SELECT COUNT(*) FROM "user";'))
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
    
    print("=" * 60)
    print(f"\nDatabase '{db_name}' has:")
    print(f"  - {user_count} users")
    print(f"  - {asset_count} assets")
    print(f"  - {asset_type_count} asset types")
    print(f"  - {role_count} roles")
