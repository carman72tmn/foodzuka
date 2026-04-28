ALTER TABLE custom_polygons ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE custom_polygons ADD COLUMN IF NOT EXISTS min_delivery_time INTEGER;
ALTER TABLE custom_polygons ADD COLUMN IF NOT EXISTS max_delivery_time INTEGER;
ALTER TABLE custom_polygons ADD COLUMN IF NOT EXISTS min_order_amount DOUBLE PRECISION DEFAULT 0.0;
ALTER TABLE custom_polygons ADD COLUMN IF NOT EXISTS delivery_cost DOUBLE PRECISION DEFAULT 0.0;
ALTER TABLE custom_polygons ADD COLUMN IF NOT EXISTS free_delivery_threshold DOUBLE PRECISION DEFAULT 0.0;
ALTER TABLE custom_polygons ADD COLUMN IF NOT EXISTS fill_color VARCHAR DEFAULT '#4caf50';

-- Set defaults for existing records
UPDATE custom_polygons SET min_order_amount = 0.0 WHERE min_order_amount IS NULL;
UPDATE custom_polygons SET delivery_cost = 0.0 WHERE delivery_cost IS NULL;
UPDATE custom_polygons SET free_delivery_threshold = 0.0 WHERE free_delivery_threshold IS NULL;
UPDATE custom_polygons SET fill_color = '#4caf50' WHERE fill_color IS NULL;
