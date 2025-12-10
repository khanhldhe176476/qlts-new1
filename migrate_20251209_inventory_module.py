"""
Migration script to upgrade existing inventory tables to the new
inventory module schema and create supporting tables.

Usage (Windows PowerShell / CMD, từ thư mục `qlts-new8`):

    py migrate_20251209_inventory_module.py

Script này an toàn để chạy nhiều lần – nó tự kiểm tra cột/bảng đã tồn tại.
"""
from sqlalchemy import create_engine, inspect, text
from config import Config


def column_exists(inspector, table_name: str, column_name: str) -> bool:
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def table_exists(inspector, table_name: str) -> bool:
    return inspector.has_table(table_name)


def add_column(engine, inspector, table_name: str, column_name: str, ddl: str):
    if not table_exists(inspector, table_name):
        print(f"[WARN] Table {table_name} does not exist, skip column {column_name}")
        return
    if column_exists(inspector, table_name, column_name):
        print(f"[OK] Column {table_name}.{column_name} already exists")
        return
    with engine.begin() as conn:
        conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN {column_name} {ddl}'))
    print(f"[ADD] Column {table_name}.{column_name}")


def create_table(engine, inspector, table_name: str, ddl_sql: str):
    if table_exists(inspector, table_name):
        print(f"[OK] Table {table_name} already exists")
        return
    with engine.begin() as conn:
        conn.execute(text(ddl_sql))
    print(f"[ADD] Table {table_name}")


def main():
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    inspector = inspect(engine)

    # --- 1. Nâng cấp bảng inventory ---
    add_column(engine, inspector, "inventory", "inventory_time", "DATETIME NULL")
    add_column(engine, inspector, "inventory", "inventory_type", "VARCHAR(20) NULL")
    add_column(engine, inspector, "inventory", "scope_type", "VARCHAR(30) NULL")
    add_column(engine, inspector, "inventory", "scope_locations", "TEXT NULL")
    add_column(engine, inspector, "inventory", "scope_asset_groups", "TEXT NULL")
    add_column(engine, inspector, "inventory", "decision_number", "VARCHAR(100) NULL")
    add_column(engine, inspector, "inventory", "decision_date", "DATE NULL")
    add_column(engine, inspector, "inventory", "decision_file_path", "VARCHAR(255) NULL")
    add_column(engine, inspector, "inventory", "locked_at", "DATETIME NULL")
    add_column(engine, inspector, "inventory", "locked_by_id", "INTEGER NULL")
    add_column(engine, inspector, "inventory", "closed_at", "DATETIME NULL")
    add_column(engine, inspector, "inventory", "closed_by_id", "INTEGER NULL")

    # --- 2. Nâng cấp bảng inventory_result ---
    add_column(engine, inspector, "inventory_result", "book_quantity", "INTEGER DEFAULT 1")
    add_column(engine, inspector, "inventory_result", "book_location_id", "INTEGER NULL")
    add_column(engine, inspector, "inventory_result", "book_asset_type_id", "INTEGER NULL")
    add_column(engine, inspector, "inventory_result", "book_status", "VARCHAR(20) NULL")

    add_column(engine, inspector, "inventory_result", "actual_quantity", "INTEGER NULL")
    add_column(engine, inspector, "inventory_result", "actual_condition", "VARCHAR(20) NULL")
    add_column(engine, inspector, "inventory_result", "actual_location_id", "INTEGER NULL")
    add_column(engine, inspector, "inventory_result", "actual_serial_plate", "VARCHAR(100) NULL")

    # --- 3. Bảng tổ kiểm kê ---
    create_table(
        engine,
        inspector,
        "inventory_team",
        """
        CREATE TABLE inventory_team (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            inventory_id INTEGER NOT NULL,
            name VARCHAR(200) NOT NULL,
            leader_id INTEGER NOT NULL,
            created_at DATETIME,
            updated_at DATETIME,
            FOREIGN KEY(inventory_id) REFERENCES inventory (id),
            FOREIGN KEY(leader_id) REFERENCES user (id)
        )
        """,
    )

    create_table(
        engine,
        inspector,
        "inventory_team_member",
        """
        CREATE TABLE inventory_team_member (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role VARCHAR(50),
            FOREIGN KEY(team_id) REFERENCES inventory_team (id),
            FOREIGN KEY(user_id) REFERENCES user (id)
        )
        """,
    )

    # --- 4. Tài sản thừa trong kiểm kê ---
    create_table(
        engine,
        inspector,
        "inventory_surplus_asset",
        """
        CREATE TABLE inventory_surplus_asset (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            inventory_id INTEGER NOT NULL,
            team_id INTEGER,
            name VARCHAR(255) NOT NULL,
            asset_type_id INTEGER,
            location_id INTEGER,
            quantity INTEGER NOT NULL DEFAULT 1,
            estimated_start_year INTEGER,
            origin VARCHAR(100),
            status VARCHAR(20) NOT NULL DEFAULT 'surplus',
            notes TEXT,
            increase_voucher_id INTEGER,
            created_by_id INTEGER,
            created_at DATETIME,
            updated_at DATETIME,
            FOREIGN KEY(inventory_id) REFERENCES inventory (id),
            FOREIGN KEY(team_id) REFERENCES inventory_team (id),
            FOREIGN KEY(created_by_id) REFERENCES user (id)
        )
        """,
    )

    # --- 5. Ảnh minh chứng ---
    create_table(
        engine,
        inspector,
        "inventory_line_photo",
        """
        CREATE TABLE inventory_line_photo (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            inventory_result_id INTEGER NOT NULL,
            file_path VARCHAR(255) NOT NULL,
            uploaded_by_id INTEGER,
            created_at DATETIME,
            FOREIGN KEY(inventory_result_id) REFERENCES inventory_result (id),
            FOREIGN KEY(uploaded_by_id) REFERENCES user (id)
        )
        """,
    )

    # --- 6. Nhật ký kiểm kê ---
    create_table(
        engine,
        inspector,
        "inventory_log",
        """
        CREATE TABLE inventory_log (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            inventory_id INTEGER NOT NULL,
            action VARCHAR(50) NOT NULL,
            from_status VARCHAR(30),
            to_status VARCHAR(30),
            reason TEXT,
            payload TEXT,
            actor_id INTEGER NOT NULL,
            created_at DATETIME,
            FOREIGN KEY(inventory_id) REFERENCES inventory (id),
            FOREIGN KEY(actor_id) REFERENCES user (id)
        )
        """,
    )

    print("[DONE] Inventory module migration completed.")


if __name__ == "__main__":
    main()


