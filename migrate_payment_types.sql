-- Миграция: Добавление таблицы типов оплаты iiko
CREATE TABLE IF NOT EXISTS payment_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    iiko_id VARCHAR(255) NOT NULL UNIQUE,
    kind VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_types_iiko_id ON payment_types(iiko_id);
CREATE INDEX IF NOT EXISTS idx_payment_types_name ON payment_types(name);
