"""
Migration script for asset extended modules (legal docs, sources, locations,
usage status, inventory, disposal, change logs) and new fields.

Usage:
    py migrate_20251205_asset_extensions.py
"""
from sqlalchemy import create_engine, inspect, text
from config import Config


def column_exists(inspector, table_name, column_name):
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def table_exists(inspector, table_name):
    return inspector.has_table(table_name)


def add_column(engine, inspector, table_name, column_name, ddl):
    if not table_exists(inspector, table_name):
        print(f"[WARN] Table {table_name} does not exist, skip column {column_name}")
        return
    if column_exists(inspector, table_name, column_name):
        print(f"[OK] Column {table_name}.{column_name} already exists")
        return
    with engine.begin() as conn:
        conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN {column_name} {ddl}'))
    print(f"[ADD] Column {table_name}.{column_name}")


def create_table(engine, inspector, table_name, ddl_sql):
    if table_exists(inspector, table_name):
        print(f"[OK] Table {table_name} already exists")
        return
    with engine.begin() as conn:
        conn.execute(text(ddl_sql))
    print(f"[ADD] Table {table_name}")


def main():
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    inspector = inspect(engine)

    # Asset: thêm tinh_trang_danh_gia, usage_status
    add_column(engine, inspector, "asset", "tinh_trang_danh_gia", "VARCHAR(100) NULL")
    add_column(engine, inspector, "asset", "usage_status", "VARCHAR(50) NULL")

    # AssetTransfer: thêm decision_number, agency_from, agency_to
    add_column(engine, inspector, "asset_transfer", "decision_number", "VARCHAR(100) NULL")
    add_column(engine, inspector, "asset_transfer", "agency_from", "VARCHAR(255) NULL")
    add_column(engine, inspector, "asset_transfer", "agency_to", "VARCHAR(255) NULL")

    # legal_document
    create_table(
        engine,
        inspector,
        "legal_document",
        """
        CREATE TABLE legal_document (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            so_quyet_dinh VARCHAR(100),
            ngay_ban_hanh DATE,
            loai_van_ban VARCHAR(100),
            co_quan_ban_hanh VARCHAR(255),
            noi_dung TEXT,
            file_dinh_kem VARCHAR(500),
            created_at DATETIME,
            FOREIGN KEY(asset_id) REFERENCES asset (id)
        )
        """,
    )

    # asset_source
    create_table(
        engine,
        inspector,
        "asset_source",
        """
        CREATE TABLE asset_source (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            nguon VARCHAR(50) NOT NULL,
            nha_cung_cap VARCHAR(255),
            so_hop_dong VARCHAR(100),
            so_hoa_don VARCHAR(100),
            gia_tri FLOAT DEFAULT 0,
            ghi_chu TEXT,
            created_at DATETIME,
            FOREIGN KEY(asset_id) REFERENCES asset (id)
        )
        """,
    )

    # asset_location
    create_table(
        engine,
        inspector,
        "asset_location",
        """
        CREATE TABLE asset_location (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            toa_nha VARCHAR(255),
            phong_ban VARCHAR(255),
            nguoi_quan_ly_id INTEGER,
            hieu_luc_tu DATE,
            hieu_luc_den DATE,
            created_at DATETIME,
            FOREIGN KEY(asset_id) REFERENCES asset (id),
            FOREIGN KEY(nguoi_quan_ly_id) REFERENCES user (id)
        )
        """,
    )

    # asset_location_history
    create_table(
        engine,
        inspector,
        "asset_location_history",
        """
        CREATE TABLE asset_location_history (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            tu_toa_nha VARCHAR(255),
            tu_phong_ban VARCHAR(255),
            den_toa_nha VARCHAR(255),
            den_phong_ban VARCHAR(255),
            tu_nguoi_quan_ly_id INTEGER,
            den_nguoi_quan_ly_id INTEGER,
            changed_by_id INTEGER,
            changed_at DATETIME,
            FOREIGN KEY(asset_id) REFERENCES asset (id),
            FOREIGN KEY(tu_nguoi_quan_ly_id) REFERENCES user (id),
            FOREIGN KEY(den_nguoi_quan_ly_id) REFERENCES user (id),
            FOREIGN KEY(changed_by_id) REFERENCES user (id)
        )
        """,
    )

    # asset_usage_status_log
    create_table(
        engine,
        inspector,
        "asset_usage_status_log",
        """
        CREATE TABLE asset_usage_status_log (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            trang_thai VARCHAR(50) NOT NULL,
            ghi_chu TEXT,
            user_id INTEGER,
            changed_at DATETIME,
            FOREIGN KEY(asset_id) REFERENCES asset (id),
            FOREIGN KEY(user_id) REFERENCES user (id)
        )
        """,
    )

    # inventory_batch
    create_table(
        engine,
        inspector,
        "inventory_batch",
        """
        CREATE TABLE inventory_batch (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            ma_dot VARCHAR(50) NOT NULL UNIQUE,
            ten_dot VARCHAR(255) NOT NULL,
            loai_kiem_ke VARCHAR(100),
            pham_vi VARCHAR(255),
            so_quyet_dinh VARCHAR(100),
            trang_thai VARCHAR(20),
            created_by_id INTEGER,
            approved_by_id INTEGER,
            created_at DATETIME,
            approved_at DATETIME,
            FOREIGN KEY(created_by_id) REFERENCES user (id),
            FOREIGN KEY(approved_by_id) REFERENCES user (id)
        )
        """,
    )

    # inventory_item
    create_table(
        engine,
        inspector,
        "inventory_item",
        """
        CREATE TABLE inventory_item (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER NOT NULL,
            asset_id INTEGER NOT NULL,
            so_thuc_te INTEGER DEFAULT 0,
            so_he_thong INTEGER DEFAULT 0,
            chenhlech INTEGER DEFAULT 0,
            ghi_chu TEXT,
            created_at DATETIME,
            FOREIGN KEY(batch_id) REFERENCES inventory_batch (id),
            FOREIGN KEY(asset_id) REFERENCES asset (id)
        )
        """,
    )

    # disposal_request
    create_table(
        engine,
        inspector,
        "disposal_request",
        """
        CREATE TABLE disposal_request (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            de_nghi_thanh_ly TEXT,
            phe_duyet TEXT,
            so_quyet_dinh VARCHAR(100),
            gia_tri_con_lai FLOAT DEFAULT 0,
            gia_tri_ban FLOAT DEFAULT 0,
            file_dinh_kem VARCHAR(500),
            trang_thai VARCHAR(20),
            created_at DATETIME,
            approved_at DATETIME,
            FOREIGN KEY(asset_id) REFERENCES asset (id)
        )
        """,
    )

    # asset_change_log
    create_table(
        engine,
        inspector,
        "asset_change_log",
        """
        CREATE TABLE asset_change_log (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            loai_bien_dong VARCHAR(50) NOT NULL,
            truoc TEXT,
            sau TEXT,
            user_id INTEGER,
            created_at DATETIME,
            FOREIGN KEY(asset_id) REFERENCES asset (id),
            FOREIGN KEY(user_id) REFERENCES user (id)
        )
        """,
    )


if __name__ == "__main__":
    main()

