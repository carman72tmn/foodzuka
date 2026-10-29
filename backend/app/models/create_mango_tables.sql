-- Создание таблиц для интеграции с телефонией Mango Office (ВАТС)

CREATE TABLE IF NOT EXISTS mango_settings (
    id SERIAL PRIMARY KEY,
    vpbx_api_key VARCHAR(255),
    vpbx_api_salt VARCHAR(255),
    vpbx_url VARCHAR(255) NOT NULL DEFAULT 'https://app.mango-office.ru/vpbx/',
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    default_extension VARCHAR(50),
    auto_lookup_customer BOOLEAN NOT NULL DEFAULT TRUE,
    create_customer_if_missing BOOLEAN NOT NULL DEFAULT FALSE,
    notify_incoming_call BOOLEAN NOT NULL DEFAULT TRUE,
    recording_storage_mode VARCHAR(50) NOT NULL DEFAULT 'stream',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS mango_call_logs (
    id SERIAL PRIMARY KEY,
    entry_id VARCHAR(100),
    call_id VARCHAR(100),
    call_state VARCHAR(50),
    direction VARCHAR(20) NOT NULL DEFAULT 'incoming',
    from_number VARCHAR(50),
    from_extension VARCHAR(50),
    to_number VARCHAR(50),
    to_extension VARCHAR(50),
    line_number VARCHAR(50),
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    disconnect_reason VARCHAR(100),
    duration_wait INTEGER NOT NULL DEFAULT 0,
    duration_talk INTEGER NOT NULL DEFAULT 0,
    recording_id VARCHAR(100),
    recording_url TEXT,
    customer_id INTEGER,
    customer_name VARCHAR(255),
    order_id INTEGER,
    comment TEXT,
    raw_data TEXT,
    started_at TIMESTAMP WITHOUT TIME ZONE,
    connected_at TIMESTAMP WITHOUT TIME ZONE,
    ended_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE INDEX IF NOT EXISTS ix_mango_call_logs_entry_id ON mango_call_logs (entry_id);
CREATE INDEX IF NOT EXISTS ix_mango_call_logs_call_id ON mango_call_logs (call_id);
CREATE INDEX IF NOT EXISTS ix_mango_call_logs_direction ON mango_call_logs (direction);
CREATE INDEX IF NOT EXISTS ix_mango_call_logs_from_number ON mango_call_logs (from_number);
CREATE INDEX IF NOT EXISTS ix_mango_call_logs_to_number ON mango_call_logs (to_number);
CREATE INDEX IF NOT EXISTS ix_mango_call_logs_status ON mango_call_logs (status);
CREATE INDEX IF NOT EXISTS ix_mango_call_logs_recording_id ON mango_call_logs (recording_id);
CREATE INDEX IF NOT EXISTS ix_mango_call_logs_customer_id ON mango_call_logs (customer_id);

-- Добавление прав доступа RBAC
INSERT INTO permissions (name, code, category, description)
VALUES 
    ('Интеграция с Mango (Просмотр)', 'settings_mango_view', 'Система', 'Просмотр настроек Mango Office и журнала звонков'),
    ('Интеграция с Mango (Редактирование)', 'settings_mango_edit', 'Система', 'Изменение настроек Mango, звонки из CRM и записи разговоров')
ON CONFLICT (code) DO NOTHING;

-- Назначение прав супер-администратору и администратору (role_id = 1)
INSERT INTO role_permission_links (role_id, permission_id)
SELECT 1, id FROM permissions WHERE code IN ('settings_mango_view', 'settings_mango_edit')
ON CONFLICT DO NOTHING;
