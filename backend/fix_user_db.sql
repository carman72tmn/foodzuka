-- Исправление ограничений в таблице пользователей
ALTER TABLE users ALTER COLUMN email DROP NOT NULL;

-- Исправление типов данных для корректного сопоставления iiko_id
-- Если iiko_id в users - VARCHAR, а в employees - UUID, приводим к одному типу
-- Сначала проверяем типы (этот скрипт предполагает запуск в psql или аналогичном инструменте)

-- Принудительное приведение iiko_id в users к UUID (если там хранятся UUID)
-- ALTER TABLE users ALTER COLUMN iiko_id TYPE UUID USING iiko_id::UUID;

-- Или просто убеждаемся что оба могут сравниваться. 
-- В Postgres лучше всего иметь одинаковые типы. 
-- По логам employees.iiko_id - это UUID.

-- Попробуем привести iiko_id в users к UUID, так как iiko всегда отдает UUID
DO $$ 
BEGIN 
    BEGIN
        ALTER TABLE users ALTER COLUMN iiko_id TYPE UUID USING iiko_id::UUID;
    EXCEPTION WHEN others THEN 
        RAISE NOTICE 'Could not convert users.iiko_id to UUID, skipping...';
    END;
END $$;
