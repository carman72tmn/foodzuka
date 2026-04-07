ALTER TABLE delivery_zones ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE delivery_zones ADD COLUMN IF NOT EXISTS additional_info JSONB;
