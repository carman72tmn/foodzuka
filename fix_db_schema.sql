-- Ensure orderstatus type exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'orderstatus') THEN
        CREATE TYPE orderstatus AS ENUM ('new', 'awaiting_confirmation', 'cooking', 'waiting_for_delivery', 'delivery', 'completed', 'cancelled');
    END IF;
END$$;

-- Alter column status
ALTER TABLE orders ALTER COLUMN status TYPE orderstatus USING status::orderstatus;

-- Also fix bigints to integers if Alembic wants that
ALTER TABLE orders ALTER COLUMN branch_id TYPE INTEGER;
ALTER TABLE orders ALTER COLUMN customer_id TYPE INTEGER;
ALTER TABLE orders ALTER COLUMN promo_code_id TYPE INTEGER;

-- Fix users table (Alembic complained about it too)
ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_superuser BOOLEAN DEFAULT FALSE;
