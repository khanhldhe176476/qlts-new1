-- PostgreSQL Database Schema for Quan Ly Tai San
-- This file will be automatically executed when PostgreSQL container starts for the first time

-- Enable UUID extension if needed
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TABLES
-- ============================================

-- Role table
CREATE TABLE IF NOT EXISTS public.role (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User table
CREATE TABLE IF NOT EXISTS public."user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    role_id INTEGER NOT NULL REFERENCES public.role(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Asset Type table
CREATE TABLE IF NOT EXISTS public.asset_type (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Asset table
CREATE TABLE IF NOT EXISTS public.asset (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    quantity INTEGER,
    status VARCHAR(20),
    asset_type_id INTEGER NOT NULL REFERENCES public.asset_type(id),
    user_id INTEGER REFERENCES public."user"(id),
    user_text TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    purchase_date DATE,
    device_code VARCHAR(100),
    condition_label VARCHAR(100),
    deleted_at TIMESTAMP
);

-- Asset-User association table (many-to-many)
CREATE TABLE IF NOT EXISTS public.asset_user (
    asset_id INTEGER NOT NULL REFERENCES public.asset(id),
    user_id INTEGER NOT NULL REFERENCES public."user"(id),
    PRIMARY KEY (asset_id, user_id)
);

-- Audit Log table
CREATE TABLE IF NOT EXISTS public.audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES public."user"(id),
    module VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL,
    entity_id INTEGER,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Maintenance Record table
CREATE TABLE IF NOT EXISTS public.maintenance_record (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL REFERENCES public.asset (id),
    maintenance_date DATE NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    vendor VARCHAR(200),
    person_in_charge VARCHAR(120),
    cost DOUBLE PRECISION,
    next_due_date DATE,
    status VARCHAR(30),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- ============================================
-- INDEXES (for better performance)
-- ============================================

CREATE INDEX IF NOT EXISTS idx_user_role_id ON public."user"(role_id);

CREATE INDEX IF NOT EXISTS idx_user_username ON public."user"(username);

CREATE INDEX IF NOT EXISTS idx_user_email ON public."user"(email);

CREATE INDEX IF NOT EXISTS idx_asset_type_id ON public.asset (asset_type_id);

CREATE INDEX IF NOT EXISTS idx_asset_user_id ON public.asset (user_id);

CREATE INDEX IF NOT EXISTS idx_asset_status ON public.asset (status);

CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON public.audit_log (user_id);

CREATE INDEX IF NOT EXISTS idx_audit_log_module ON public.audit_log (module);

CREATE INDEX IF NOT EXISTS idx_maintenance_asset_id ON public.maintenance_record (asset_id);

CREATE INDEX IF NOT EXISTS idx_maintenance_date ON public.maintenance_record (maintenance_date);

-- ============================================
-- SAMPLE DATA
-- ============================================

-- Insert Roles
INSERT INTO
    public.role (
        id,
        name,
        description,
        created_at,
        updated_at
    )
VALUES (
        1,
        'admin',
        'Quản trị viên hệ thống',
        '2025-10-23 12:18:02.580893',
        '2025-10-23 12:18:02.580907'
    ),
    (
        2,
        'manager',
        'Quản lý tài sản',
        '2025-10-23 12:18:02.580914',
        '2025-10-23 12:18:02.580918'
    ),
    (
        3,
        'user',
        'Người dùng thông thường',
        '2025-10-23 12:18:02.580923',
        '2025-10-23 12:18:02.580926'
    ) ON CONFLICT (id) DO NOTHING;

-- Reset sequence for role
SELECT setval (
        'public.role_id_seq', (
            SELECT MAX(id)
            FROM public.role
        )
    );

-- Insert Users (password mặc định: mh123#@! cho tất cả users)
-- Password hash tạo runtime thông qua ứng dụng
INSERT INTO public."user" (id, username, password_hash, email, role_id, is_active, created_at, updated_at, last_login, deleted_at) VALUES
(1, 'admin', 'pbkdf2:sha256:1000000$UN0cTRYBBhB9D4Eg$ea2bdad95d78eae4df54abb5578287bcf00136881577b752d71d1805683c85e4', 'admin@company.com', 1, TRUE, '2025-10-23 12:18:04.875183', '2025-11-17 06:59:41.817382', NULL, NULL),
(2, 'manager1', 'pbkdf2:sha256:1000000$UN0cTRYBBhB9D4Eg$ea2bdad95d78eae4df54abb5578287bcf00136881577b752d71d1805683c85e4', 'manager@company.com', 2, TRUE, '2025-10-23 12:18:04.875189', '2025-10-23 12:18:04.87519', NULL, NULL),
(3, 'user1', 'pbkdf2:sha256:1000000$UN0cTRYBBhB9D4Eg$ea2bdad95d78eae4df54abb5578287bcf00136881577b752d71d1805683c85e4', 'user1@company.com', 3, TRUE, '2025-10-23 12:18:04.875191', '2025-10-23 12:18:04.875193', NULL, NULL),
(4, 'user2', 'pbkdf2:sha256:1000000$UN0cTRYBBhB9D4Eg$ea2bdad95d78eae4df54abb5578287bcf00136881577b752d71d1805683c85e4', 'user2@company.com', 3, TRUE, '2025-10-23 12:18:04.875194', '2025-10-23 12:18:04.875195', NULL, NULL)
ON CONFLICT (id) DO NOTHING;

-- Reset sequence for user
SELECT setval('public.user_id_seq', (SELECT MAX(id) FROM public."user"));

-- Insert Asset Types
INSERT INTO
    public.asset_type (
        id,
        name,
        description,
        created_at,
        updated_at,
        deleted_at
    )
VALUES (
        1,
        'Máy tính',
        'Máy tính để bàn, laptop, máy tính bảng',
        '2025-10-23 12:18:04.88886',
        '2025-10-23 12:18:04.888864',
        NULL
    ),
    (
        2,
        'Thiết bị văn phòng',
        'Máy in, máy photocopy, máy fax',
        '2025-10-23 12:18:04.888866',
        '2025-10-23 12:18:04.888867',
        NULL
    ),
    (
        3,
        'Nội thất',
        'Bàn ghế, tủ, kệ',
        '2025-10-23 12:18:04.888868',
        '2025-10-23 12:18:04.88887',
        NULL
    ),
    (
        4,
        'Thiết bị mạng',
        'Router, switch, modem',
        '2025-10-23 12:18:04.888871',
        '2025-10-23 12:18:04.888872',
        NULL
    ),
    (
        5,
        'Thiết bị điện tử',
        'Điện thoại, máy ảnh, loa',
        '2025-10-23 12:18:04.888873',
        '2025-10-23 12:18:04.888874',
        NULL
    ) ON CONFLICT (id) DO NOTHING;

-- Reset sequence for asset_type
SELECT setval (
        'public.asset_type_id_seq', (
            SELECT MAX(id)
            FROM public.asset_type
        )
    );

-- Insert Assets
INSERT INTO
    public.asset (
        id,
        name,
        price,
        quantity,
        status,
        asset_type_id,
        user_id,
        user_text,
        notes,
        created_at,
        updated_at,
        purchase_date,
        device_code,
        condition_label,
        deleted_at
    )
VALUES (
        1,
        'Laptop Dell XPS 13',
        25000000,
        1,
        'active',
        1,
        1,
        'Laptop cao cấp cho developer',
        'Được cấp cho phòng IT',
        '2025-10-23 12:18:04.913728',
        '2025-10-23 12:18:04.918062',
        NULL,
        NULL,
        NULL,
        NULL
    ),
    (
        2,
        'Máy in HP LaserJet',
        3500000,
        2,
        'active',
        2,
        2,
        'Máy in laser đen trắng',
        'Đặt tại phòng hành chính',
        '2025-10-23 12:18:04.914053',
        '2025-10-23 12:18:04.918067',
        NULL,
        NULL,
        NULL,
        NULL
    ),
    (
        3,
        'Bàn làm việc gỗ',
        2000000,
        10,
        'active',
        3,
        3,
        'Bàn làm việc gỗ cao cấp',
        'Bàn tiêu chuẩn cho nhân viên',
        '2025-10-23 12:18:04.91423',
        '2025-10-23 12:18:04.918069',
        NULL,
        NULL,
        NULL,
        NULL
    ),
    (
        4,
        'Router Cisco',
        5000000,
        1,
        'active',
        4,
        1,
        'Router mạng doanh nghiệp',
        'Router chính của công ty',
        '2025-10-23 12:18:04.91447',
        '2025-10-23 12:18:04.918071',
        NULL,
        NULL,
        NULL,
        NULL
    ),
    (
        5,
        'iPhone 14 Pro',
        30000000,
        1,
        'active',
        5,
        2,
        'Điện thoại di động cao cấp',
        'Điện thoại công ty cho quản lý',
        '2025-10-23 12:18:04.914912',
        '2025-10-23 12:18:04.918072',
        NULL,
        NULL,
        NULL,
        NULL
    ),
    (
        6,
        'Máy tính để bàn HP',
        15000000,
        5,
        'maintenance',
        1,
        4,
        'Máy tính văn phòng',
        'Đang bảo trì định kỳ',
        '2025-10-23 12:18:04.915539',
        '2025-10-23 12:18:04.918073',
        NULL,
        NULL,
        NULL,
        NULL
    ),
    (
        7,
        'Ghế văn phòng',
        3000000,
        15,
        'active',
        3,
        3,
        'Ghế văn phòng ergonomic',
        'Ghế tiêu chuẩn cho nhân viên',
        '2025-10-23 12:18:04.915718',
        '2025-10-23 12:18:04.918075',
        NULL,
        NULL,
        NULL,
        NULL
    ),
    (
        8,
        'Chuột Newmen',
        100,
        1,
        'active',
        2,
        3,
        NULL,
        NULL,
        '2025-10-29 04:16:42.945918',
        '2025-10-29 04:16:42.945926',
        NULL,
        NULL,
        NULL,
        NULL
    ),
    (
        9,
        'Server',
        1000000,
        1,
        'active',
        5,
        2,
        NULL,
        NULL,
        '2025-11-12 04:35:13.563279',
        '2025-11-12 04:35:13.56329',
        NULL,
        NULL,
        NULL,
        NULL
    ) ON CONFLICT (id) DO NOTHING;

-- Reset sequence for asset
SELECT setval (
        'public.asset_id_seq', (
            SELECT MAX(id)
            FROM public.asset
        )
    );

-- Insert Audit Log
INSERT INTO
    public.audit_log (
        id,
        user_id,
        module,
        action,
        entity_id,
        details,
        created_at
    )
VALUES (
        1,
        1,
        'assets',
        'create',
        9,
        'name=Server',
        '2025-11-12 04:35:13.582698'
    ) ON CONFLICT (id) DO NOTHING;

-- Reset sequence for audit_log
SELECT setval (
        'public.audit_log_id_seq', (
            SELECT MAX(id)
            FROM public.audit_log
        )
    );

-- Insert Maintenance Records
INSERT INTO public.maintenance_record (id, asset_id, maintenance_date, type, description, vendor, person_in_charge, cost, next_due_date, status, created_at, updated_at, deleted_at) VALUES
(1, 1, '2025-11-05', 'maintenance', 'Lịch bảo trì định kỳ (tự động)', NULL, 'System', 0, '2026-11-05', 'scheduled', '2025-11-05 01:47:33.237423', '2025-11-05 01:47:33.237427', NULL),
(2, 2, '2025-11-05', 'maintenance', 'Lịch bảo trì định kỳ (tự động)', NULL, 'System', 0, '2026-11-05', 'scheduled', '2025-11-05 01:47:33.24457', '2025-11-05 01:47:33.244576', NULL),
(3, 3, '2025-11-05', 'maintenance', 'Lịch bảo trì định kỳ (tự động)', NULL, 'System', 0, '2026-11-05', 'scheduled', '2025-11-05 01:47:33.246303', '2025-11-05 01:47:33.246307', NULL),
(4, 4, '2025-11-05', 'maintenance', 'Lịch bảo trì định kỳ (tự động)', NULL, 'System', 0, '2026-11-05', 'scheduled', '2025-11-05 01:47:33.248624', '2025-11-05 01:47:33.248629', NULL),
(5, 5, '2025-11-05', 'maintenance', 'Lịch bảo trì định kỳ (tự động)', NULL, 'System', 0, '2026-11-05', 'scheduled', '2025-11-05 01:47:33.250523', '2025-11-05 01:47:33.250527', NULL),
(6, 6, '2025-11-05', 'maintenance', 'Lịch bảo trì định kỳ (tự động)', NULL, 'System', 0, '2026-11-05', 'scheduled', '2025-11-05 01:47:33.252318', '2025-11-05 01:47:33.252322', NULL),
(7, 7, '2025-11-05', 'maintenance', 'Lịch bảo trì định kỳ (tự động)', NULL, 'System', 0, '2026-11-05', 'scheduled', '2025-11-05 01:47:33.254359', '2025-11-05 01:47:33.254364', NULL),
(8, 8, '2025-11-05', 'maintenance', 'Lịch bảo trì định kỳ (tự động)', NULL, 'System', 0, '2026-11-05', 'scheduled', '2025-11-05 01:47:33.25614', '2025-11-05 01:47:33.256144', NULL),
(9, 9, '2025-11-12', 'maintenance', 'Lịch bảo trì định kỳ (tự động)', NULL, 'System', 0, '2026-11-12', 'scheduled', '2025-11-12 04:35:40.684387', '2025-11-12 04:35:40.684395', NULL)
ON CONFLICT (id) DO NOTHING;

-- Reset sequence for maintenance_record
SELECT setval (
        'public.maintenance_record_id_seq', (
            SELECT MAX(id)
            FROM public.maintenance_record
        )
    );