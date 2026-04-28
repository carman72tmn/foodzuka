-- Добавление телефона для связи с клиентами
ALTER TABLE vk_bot_accounts ADD COLUMN IF NOT EXISTS phone VARCHAR(20);

-- Таблица шаблонов сообщений
CREATE TABLE IF NOT EXISTS vk_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    text TEXT NOT NULL,
    keyboard_json JSONB, -- Для кнопок
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица рассылок
CREATE TABLE IF NOT EXISTS vk_mailings (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES vk_templates(id),
    title VARCHAR(255) NOT NULL,
    audience_filters JSONB, -- Фильтры (например, сегменты клиентов)
    status VARCHAR(20) DEFAULT 'draft', -- draft, scheduled, running, completed, cancelled
    target_count INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
