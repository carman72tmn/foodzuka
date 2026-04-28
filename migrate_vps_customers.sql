-- Добавление новых полей в таблицу customers
ALTER TABLE customers ADD COLUMN IF NOT EXISTS total_orders_count INTEGER DEFAULT 0;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS total_orders_amount DECIMAL(12, 2) DEFAULT 0.00;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS registration_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_new_guest BOOLEAN DEFAULT FALSE;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS iiko_customer_id VARCHAR(100);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS bonus_points DECIMAL(10, 2) DEFAULT 0;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS last_order_date TIMESTAMP WITH TIME ZONE;

-- Новые поля для синхронизации с Laravel (по ТЗ пользователя)
ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_high_risk BOOLEAN DEFAULT FALSE;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS risk_reason TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS iiko_notes TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS total_purchases_sum DECIMAL(12, 2) DEFAULT 0.00;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS last_iiko_order_id VARCHAR(255);

-- Старые поля для обратной совместимости
ALTER TABLE customers ADD COLUMN IF NOT EXISTS high_risk_status BOOLEAN DEFAULT FALSE;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS high_risk_reason TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS iiko_comment TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS loyalty_categories TEXT;

-- Создание таблицы истории бонусов (Python-legacy)
CREATE TABLE IF NOT EXISTS bonus_transactions_history (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    transaction_date TIMESTAMP WITH TIME ZONE NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    type VARCHAR(20) NOT NULL, 
    comment TEXT,
    external_id VARCHAR(100) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы адресов (Laravel-совместимая)
CREATE TABLE IF NOT EXISTS client_addresses_history (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    city VARCHAR(255),
    street VARCHAR(255),
    house VARCHAR(50),
    apartment VARCHAR(50),
    address TEXT NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    orders_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы истории бонусов (Laravel-совместимая)
CREATE TABLE IF NOT EXISTS client_bonus_history (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL, -- 'accrual' или 'deduction'
    amount DECIMAL(10, 2) NOT NULL,
    transaction_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_customers_iiko_id ON customers(iiko_customer_id);
CREATE INDEX IF NOT EXISTS idx_client_addr_client_id ON client_addresses_history(client_id);
CREATE INDEX IF NOT EXISTS idx_client_bonus_client_id ON client_bonus_history(client_id);
