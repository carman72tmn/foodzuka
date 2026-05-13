
-- Добавление новых полей для импорта клиентов
ALTER TABLE customers ADD COLUMN IF NOT EXISTS registration_date TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_high_risk BOOLEAN DEFAULT FALSE;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_synced_to_iiko_cards BOOLEAN DEFAULT FALSE;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_loyalty_messages_consented BOOLEAN DEFAULT TRUE;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS last_order_date TIMESTAMP WITHOUT TIME ZONE;

-- Проверка существования других полей на всякий случай
-- is_marketing_consented и is_system_notifications_consented обычно уже есть
