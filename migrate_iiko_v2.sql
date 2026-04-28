-- Миграция для интеграции iiko (Типы оплат и Зоны доставки)
-- 1. Добавление полей в payment_types
ALTER TABLE payment_types ADD COLUMN IF NOT EXISTS mapping_type VARCHAR(50);
ALTER TABLE payment_types ADD COLUMN IF NOT EXISTS is_processed_externally BOOLEAN DEFAULT FALSE;

-- 2. Добавление полей в delivery_zones
ALTER TABLE delivery_zones ADD COLUMN IF NOT EXISTS free_delivery_sum FLOAT;
ALTER TABLE delivery_zones ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 0;
ALTER TABLE delivery_zones ADD COLUMN IF NOT EXISTS is_default BOOLEAN DEFAULT FALSE;
ALTER TABLE delivery_zones ADD COLUMN IF NOT EXISTS is_manual_override BOOLEAN DEFAULT FALSE;
