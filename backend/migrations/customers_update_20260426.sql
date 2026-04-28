-- Миграция для расширения данных клиентов и истории бонусов
-- Дата: 26.04.2026

-- 1. Добавление новых полей в таблицу customers
ALTER TABLE customers ADD COLUMN IF NOT EXISTS registration_date TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS high_risk_status BOOLEAN DEFAULT FALSE;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS high_risk_reason TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS iiko_comment TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS loyalty_categories TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_new_guest BOOLEAN DEFAULT TRUE;

-- 2. Создание таблицы guest_addresses (дополнительные адреса)
CREATE TABLE IF NOT EXISTS guest_addresses (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    address TEXT NOT NULL,
    is_main BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_guest_addresses_customer_id ON guest_addresses(customer_id);

-- 3. Создание таблицы bonus_transactions_history (история бонусов)
CREATE TABLE IF NOT EXISTS bonus_transactions_history (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    transaction_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    type VARCHAR(50) NOT NULL, -- accrual / deduction
    amount NUMERIC(10,2) NOT NULL,
    order_id VARCHAR(100),
    balance_after NUMERIC(10,2),
    comment TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_bonus_transactions_history_customer_id ON bonus_transactions_history(customer_id);
CREATE INDEX IF NOT EXISTS ix_bonus_transactions_history_transaction_date ON bonus_transactions_history(transaction_date);

-- Комментарий к миграции
COMMENT ON COLUMN customers.registration_date IS 'Дата регистрации в IIKO';
COMMENT ON COLUMN customers.high_risk_status IS 'Статус высокого риска (проблемный гость)';
COMMENT ON COLUMN customers.is_new_guest IS 'Статус нового гостя до завершения первого заказа';
