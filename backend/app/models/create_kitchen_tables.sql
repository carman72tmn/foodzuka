-- Создание таблицы зон приготовления блюд
CREATE TABLE IF NOT EXISTS kitchen_zones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    color VARCHAR(7) DEFAULT '#2196F3',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы технологических карт блюд
CREATE TABLE IF NOT EXISTS product_recipes (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    ingredients JSONB DEFAULT '[]'::jsonb,
    technology TEXT,
    appearance TEXT,
    critical_points TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Добавление kitchen_zone_id в таблицу товаров
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS kitchen_zone_id INTEGER REFERENCES kitchen_zones(id) ON DELETE SET NULL;

-- Добавление полей кухонного контроля в позиции заказа
ALTER TABLE order_items 
ADD COLUMN IF NOT EXISTS kitchen_status VARCHAR(50) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS kitchen_started_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS kitchen_ready_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS kitchen_zone_id INTEGER REFERENCES kitchen_zones(id) ON DELETE SET NULL;
