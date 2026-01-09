import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv('SQLALCHEMY_DATABASE_URI') or "postgresql://postgres:123456@10.56.11.121:5432/mh_cursor_test"

def update_process_request_table():
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Add columns if they don't exist
        columns_to_add = [
            ("request_date", "DATE DEFAULT CURRENT_DATE"),
            ("unit_name", "VARCHAR(255)"),
            ("current_status", "VARCHAR(100)"),
            ("quantity", "INTEGER DEFAULT 1"),
            ("original_price", "FLOAT"),
            ("remaining_value", "FLOAT"),
            ("attachment_path", "VARCHAR(500)"),
            ("verifier_id", "INTEGER REFERENCES \"user\"(id)"),
            ("verified_at", "TIMESTAMP"),
            ("verification_notes", "TEXT")
        ]
        
        # Also update request_type to allow longer strings if needed, though 30 is usually enough
        
        for col_name, col_type in columns_to_add:
            try:
                cur.execute(f"ALTER TABLE asset_process_request ADD COLUMN {col_name} {col_type};")
                print(f"Added column: {col_name}")
            except psycopg2.Error as e:
                conn.rollback()
                if "already exists" in str(e):
                    print(f"Column {col_name} already exists.")
                else:
                    print(f"Error adding {col_name}: {e}")
            else:
                conn.commit()
        
        cur.close()
        conn.close()
        print("Database update completed.")
    except Exception as e:
        print(f"Error connecting to database: {e}")

if __name__ == "__main__":
    update_process_request_table()
