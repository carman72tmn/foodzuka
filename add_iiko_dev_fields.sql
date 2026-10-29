-- Миграция: Добавление полей app_id и client_secret в таблицу iiko_settings
ALTER TABLE iiko_settings ADD COLUMN IF NOT EXISTS app_id VARCHAR(255) DEFAULT '19de15e4-bce3-4742-b120-72a33813c025';
ALTER TABLE iiko_settings ADD COLUMN IF NOT EXISTS client_secret VARCHAR(255) DEFAULT '9BryJrlsxs9aA863hjNPQLFSmlNvMZ0piUQFWCLBSec=';
