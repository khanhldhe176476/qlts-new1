# -*- coding: utf-8 -*-
"""Script to test PostgreSQL connection"""
import os
import sys
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', '')
print(f"DATABASE_URL: {DATABASE_URL}")

# Test kết nối với SQLAlchemy
try:
    from sqlalchemy import create_engine, text
    
    # Tạo engine
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    # Test kết nối
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"\n✓ PostgreSQL connection successful!")
        print(f"PostgreSQL version: {version}")
        
        # Check current database
        result = conn.execute(text("SELECT current_database();"))
        db_name = result.fetchone()[0]
        print(f"Current database: {db_name}")
        
        # List tables
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        tables = result.fetchall()
        print(f"\nNumber of tables in database: {len(tables)}")
        if tables:
            print("Tables:")
            for table in tables[:10]:  # Show first 10 tables
                print(f"  - {table[0]}")
            if len(tables) > 10:
                print(f"  ... and {len(tables) - 10} more tables")
        else:
            print("⚠ Database has no tables. Need to run migration.")
        
except Exception as e:
    print(f"\n✗ PostgreSQL connection error:")
    print(f"  {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
