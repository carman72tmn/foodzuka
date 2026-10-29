ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS event_type VARCHAR(100) NULL;
ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS keyboard_telegram TEXT NULL;
ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS keyboard_max TEXT NULL;

CREATE INDEX IF NOT EXISTS idx_vk_templates_event_type ON vk_templates(event_type);
