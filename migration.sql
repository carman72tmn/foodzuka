-- Миграция: orders + delivery_zones
-- Добавляем недостающие колонки в таблицу orders

ALTER TABLE orders ADD COLUMN IF NOT EXISTS external_number VARCHAR(100);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS terminal_group_id VARCHAR(255);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS terminal_group_name VARCHAR(255);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS source VARCHAR(100);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS bonus_accrued NUMERIC(10,2) NOT NULL DEFAULT 0;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS total_with_discount NUMERIC(10,2) NOT NULL DEFAULT 0;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_method VARCHAR(255);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_type VARCHAR(255);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS courier_name VARCHAR(255);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS iiko_creation_time TIMESTAMP;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS expected_time TIMESTAMP;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS actual_time TIMESTAMP;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS delay_minutes INTEGER;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS is_on_time BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS admin_name VARCHAR(255);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS city VARCHAR(255);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_zone VARCHAR(255);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS is_paid BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_items_details JSONB;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS discounts_details JSONB;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_info_details JSONB;

-- Индексы для orders
CREATE INDEX IF NOT EXISTS orders_iiko_creation_time_idx ON orders (iiko_creation_time DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS orders_external_number_idx ON orders (external_number);
CREATE INDEX IF NOT EXISTS orders_terminal_group_id_idx ON orders (terminal_group_id);

-- Добавляем iiko_id в delivery_zones
ALTER TABLE delivery_zones ADD COLUMN IF NOT EXISTS iiko_id VARCHAR(255);
CREATE INDEX IF NOT EXISTS delivery_zones_iiko_id_idx ON delivery_zones (iiko_id);

-- Проверка: покажем все колонки orders
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'orders' 
ORDER BY ordinal_position;
