-- Миграция для интеграции Яндекс Карт
-- 1. Создание таблицы yandex_settings
CREATE TABLE IF NOT EXISTS yandex_settings (
    id SERIAL PRIMARY KEY,
    api_key_js VARCHAR(500),
    api_key_suggest VARCHAR(500),
    api_key_matrix VARCHAR(500),
    api_key_monitoring VARCHAR(500),
    api_key_static VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Добавление полей в таблицу orders
ALTER TABLE orders ADD COLUMN IF NOT EXISTS latitude FLOAT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS longitude FLOAT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS resolved_delivery_zone_id INTEGER;

-- 3. Добавление внешнего ключа (опционально, так как SQLModel не всегда требует строгого FK в БД для работы)
-- ALTER TABLE orders ADD CONSTRAINT fk_orders_resolved_delivery_zone FOREIGN KEY (resolved_delivery_zone_id) REFERENCES delivery_zones(id);
