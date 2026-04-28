ALTER TABLE vk_bot_accounts ADD COLUMN IF NOT EXISTS enabled_events JSONB DEFAULT '[]'::jsonb;
