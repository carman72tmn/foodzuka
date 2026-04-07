-- Миграция: Добавление терминальных групп в таблицу заказов
ALTER TABLE orders ADD COLUMN IF NOT EXISTS terminal_group_id VARCHAR(255);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS terminal_group_name VARCHAR(255);

-- Комментарии к колонкам для документации
COMMENT ON COLUMN orders.terminal_group_id IS 'UUID терминальной группы iiko';
COMMENT ON COLUMN orders.terminal_group_name IS 'Название терминальной группы (Тюмень, Тобольск и т.д.)';
