-- SQL миграция для добавления модуля "Закуп"

-- 1. Создание таблицы purchase_positions
CREATE TABLE IF NOT EXISTS purchase_positions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'supply', 'products', 'household'
    unit VARCHAR(50) DEFAULT 'шт',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_purchase_positions_name ON purchase_positions(name);
CREATE INDEX IF NOT EXISTS idx_purchase_positions_category ON purchase_positions(category);

-- 2. Создание таблицы purchase_records
CREATE TABLE IF NOT EXISTS purchase_records (
    id SERIAL PRIMARY KEY,
    position_id INTEGER NOT NULL REFERENCES purchase_positions(id) ON DELETE CASCADE,
    quantity DOUBLE PRECISION DEFAULT 1.0,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'completed', 'cancelled'
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_purchase_records_status ON purchase_records(status);

-- 3. Добавление прав доступа в permissions (если их нет)
INSERT INTO permissions (name, code, category) 
VALUES ('Просмотр закупа', 'purchase_view', 'Закупки')
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (name, code, category) 
VALUES ('Управление закупом', 'purchase_manage', 'Закупки')
ON CONFLICT (code) DO NOTHING;

-- 4. Привязка новых прав к роли SUPER_ADMIN
INSERT INTO role_permission_links (role_id, permission_id)
SELECT r.id, p.id 
FROM roles r, permissions p
WHERE r.code = 'SUPER_ADMIN' AND p.code IN ('purchase_view', 'purchase_manage')
ON CONFLICT DO NOTHING;
