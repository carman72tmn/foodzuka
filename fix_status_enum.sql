-- Drop existing type to recreate it with all statuses
DROP TYPE IF EXISTS orderstatus CASCADE;

CREATE TYPE orderstatus AS ENUM (
    'new', 
    'unconfirmed', 
    'confirmed', 
    'preparing', 
    'cooking', 
    'ready', 
    'ready_for_pickup', 
    'delivering', 
    'delivered', 
    'closed', 
    'cancelled'
);

-- Alter column status with mapping
ALTER TABLE orders ALTER COLUMN status DROP DEFAULT;
ALTER TABLE orders ALTER COLUMN status TYPE orderstatus USING status::orderstatus;
ALTER TABLE orders ALTER COLUMN status SET DEFAULT 'new'::orderstatus;
