-- Добавление поля price_category_id в настройки iiko
ALTER TABLE iiko_settings ADD COLUMN IF NOT EXISTS price_category_id VARCHAR(255);
COMMENT ON COLUMN iiko_settings.price_category_id IS 'UUID выбранной категории цен для выгрузки меню';
