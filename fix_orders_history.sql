ALTER TABLE customers ADD COLUMN IF NOT EXISTS orders_history JSONB DEFAULT '[]'::jsonb;
