-- Миграция для расширения анкеты клиента и управления телефонами
ALTER TABLE customers ADD COLUMN IF NOT EXISTS middle_name VARCHAR(255);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS referrer VARCHAR(255);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS registration_source VARCHAR(255);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS registered_organization VARCHAR(255);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS iiko_card_numbers JSONB DEFAULT '[]'::jsonb;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS iiko_notes TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS surname VARCHAR(255);

-- Переименование или добавление флага риска для соответствия UI
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='customers' AND column_name='is_high_risk') THEN
        ALTER TABLE customers ADD COLUMN is_high_risk BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Таблица для дополнительных телефонов
CREATE TABLE IF NOT EXISTS guest_phones (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    phone VARCHAR(20) NOT NULL,
    is_main BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_guest_phones_customer_id ON guest_phones(customer_id);
CREATE INDEX IF NOT EXISTS idx_guest_phones_phone ON guest_phones(phone);
