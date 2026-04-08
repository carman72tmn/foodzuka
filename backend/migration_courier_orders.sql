-- Миграция: создание таблицы для детальной статистики заказов курьеров
CREATE TABLE IF NOT EXISTS courier_orders (
    id SERIAL PRIMARY KEY,
    iiko_id VARCHAR(255) UNIQUE NOT NULL,
    employee_id INTEGER REFERENCES employees(id),
    shift_id INTEGER REFERENCES shifts(id),
    address TEXT,
    items_summary TEXT,
    delivery_zone VARCHAR(255),
    created_at_iiko TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    cooking_completed_at TIMESTAMP WITHOUT TIME ZONE,
    expected_delivery_time TIMESTAMP WITHOUT TIME ZONE,
    actual_delivery_time TIMESTAMP WITHOUT TIME ZONE,
    is_late BOOLEAN DEFAULT FALSE,
    cooking_late BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc')
);

CREATE INDEX IF NOT EXISTS idx_courier_orders_iiko_id ON courier_orders(iiko_id);
CREATE INDEX IF NOT EXISTS idx_courier_orders_employee_id ON courier_orders(employee_id);
CREATE INDEX IF NOT EXISTS idx_courier_orders_shift_id ON courier_orders(shift_id);
