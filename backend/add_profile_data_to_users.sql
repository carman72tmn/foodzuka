-- Добавление колонки profile_data для хранения дополнительных настроек пользователя
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_data JSONB DEFAULT '{}'::jsonb;
