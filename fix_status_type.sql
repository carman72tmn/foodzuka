-- Ensure orderstatus type exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'orderstatus') THEN
        CREATE TYPE orderstatus AS ENUM ('new', 'awaiting_confirmation', 'cooking', 'waiting_for_delivery', 'delivery', 'completed', 'cancelled');
    END IF;
END$$;

-- Drop default
ALTER TABLE orders ALTER COLUMN status DROP DEFAULT;

-- Alter column status
ALTER TABLE orders ALTER COLUMN status TYPE orderstatus USING status::orderstatus;

-- Restore default
ALTER TABLE orders ALTER COLUMN status SET DEFAULT 'new'::orderstatus;
