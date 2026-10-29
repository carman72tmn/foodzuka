-- SQL обновление для расширения модуля "Закуп"

-- 1. Дропнем старую таблицу records, созданную на предыдущем шаге, так как структура полностью меняется
DROP TABLE IF EXISTS purchase_records;

-- 2. Создание таблицы поставщиков
CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(100),
    comment TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(name);

-- 3. Обновление таблицы позиций закупа: добавляем subcategory и supplier_id
ALTER TABLE purchase_positions ADD COLUMN IF NOT EXISTS subcategory VARCHAR(255);
ALTER TABLE purchase_positions ADD COLUMN IF NOT EXISTS supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_purchase_positions_subcategory ON purchase_positions(subcategory);

-- 4. Создание таблицы списков закупа
CREATE TABLE IF NOT EXISTS purchase_lists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'supply', 'shop' (было products), 'household'
    date DATE NOT NULL, -- дата закупа / поставки
    status VARCHAR(50) DEFAULT 'draft', -- 'draft' (черновик), 'sent' (отправлен)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_purchase_lists_category ON purchase_lists(category);
CREATE INDEX IF NOT EXISTS idx_purchase_lists_date ON purchase_lists(date);
CREATE INDEX IF NOT EXISTS idx_purchase_lists_status ON purchase_lists(status);

-- 5. Создание таблицы элементов списка закупа
CREATE TABLE IF NOT EXISTS purchase_list_items (
    id SERIAL PRIMARY KEY,
    list_id INTEGER NOT NULL REFERENCES purchase_lists(id) ON DELETE CASCADE,
    position_id INTEGER NOT NULL REFERENCES purchase_positions(id) ON DELETE CASCADE,
    quantity DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_purchase_list_items_unique ON purchase_list_items(list_id, position_id);

-- 6. Добавление дефолтного системного шаблона для рассылки списка закупа
INSERT INTO vk_templates (name, text, event_type)
SELECT 
    '[Системный] Отправка списка закупа', 
    '📦 Отправлен список закупа: {{purchase_list.name}}\nНаправление: {{purchase_list.category_name}}\nДата поставки: {{purchase_list.date}}\n\nПозиции к закупу:\n{{purchase_list.items_summary}}', 
    'purchase_list_sent'
WHERE NOT EXISTS (
    SELECT 1 FROM vk_templates WHERE event_type = 'purchase_list_sent'
);

