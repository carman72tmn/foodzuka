-- SQL обновление для модуля "Закуп": Просмотр, отметка купленного и логирование изменений

-- 1. Добавление колонок создателя и последнего редактора в purchase_lists
ALTER TABLE purchase_lists ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE purchase_lists ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

-- 2. Добавление колонки is_bought в purchase_list_items
ALTER TABLE purchase_list_items ADD COLUMN IF NOT EXISTS is_bought BOOLEAN DEFAULT FALSE;

-- 3. Создание таблицы истории изменений (аудит)
CREATE TABLE IF NOT EXISTS purchase_list_changes (
    id SERIAL PRIMARY KEY,
    list_id INTEGER NOT NULL REFERENCES purchase_lists(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(50) NOT NULL, -- 'create', 'update_meta', 'update_items', 'send', 'toggle_bought'
    details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_purchase_list_changes_list_id ON purchase_list_changes(list_id);
