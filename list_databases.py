# -*- coding: utf-8 -*-
"""List all databases on PostgreSQL server"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', '')
print(f"Current DATABASE_URL: {DATABASE_URL}")
print("=" * 60)

# Connect to postgres database to list all databases
base_url = DATABASE_URL.rsplit('/', 1)[0] + '/postgres'
engine = create_engine(base_url, pool_pre_ping=True)

with engine.connect() as conn:
    result = conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;"))
    databases = result.fetchall()
    
    print(f"\nAvailable databases on server:")
    for db in databases:
        db_name = db[0]
        # Check if this is the current database
        current = " <- CURRENT" if db_name in DATABASE_URL else ""
        print(f"  - {db_name}{current}")
        
        # Count users in each database
        try:
            db_url = DATABASE_URL.rsplit('/', 1)[0] + '/' + db_name
            db_engine = create_engine(db_url, pool_pre_ping=True)
            with db_engine.connect() as db_conn:
                user_result = db_conn.execute(text('SELECT COUNT(*) FROM "user";'))
                user_count = user_result.fetchone()[0]
                if user_count > 0:
                    print(f"    -> Has {user_count} users")
        except Exception:
            pass

print("\n" + "=" * 60)
print("\nIf you want to use a different database, update DATABASE_URL in .env file")
