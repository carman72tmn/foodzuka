-- Миграция: добавление новых полей для модуля «Сотрудники»
-- Применяется в контейнере foodtech-db

-- 1. Флаги типа сотрудника в таблице employees
ALTER TABLE employees
    ADD COLUMN IF NOT EXISTS is_courier BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;

-- Автоматически проставить флаги по существующим ролям
UPDATE employees
SET is_courier = TRUE
WHERE role ILIKE '%курьер%' OR role ILIKE '%courier%';

UPDATE employees
SET is_admin = TRUE
WHERE role ILIKE '%администратор%'
   OR role ILIKE '%оператор%'
   OR role ILIKE '%manager%'
   OR role ILIKE '%старший%';

-- 2. Новые поля в таблице courier_orders
ALTER TABLE courier_orders
    ADD COLUMN IF NOT EXISTS order_num        VARCHAR,
    ADD COLUMN IF NOT EXISTS amount           DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS departure_time   TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS close_time       TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS delay_minutes    INTEGER;

-- created_at_iiko — было NOT NULL, делаем nullable чтобы OLAP-строки без UUID добавлялись
ALTER TABLE courier_orders
    ALTER COLUMN created_at_iiko DROP NOT NULL;

-- Индекс по order_num для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_courier_orders_order_num ON courier_orders (order_num);

-- 3. Итоговая проверка
SELECT
    'employees.is_courier'  AS field, COUNT(*) FILTER (WHERE is_courier) AS flagged FROM employees
UNION ALL
SELECT
    'employees.is_admin', COUNT(*) FILTER (WHERE is_admin) FROM employees
UNION ALL
SELECT
    'courier_orders.amount', COUNT(*) FILTER (WHERE amount IS NOT NULL) FROM courier_orders;
