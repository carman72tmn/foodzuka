INSERT INTO payment_types (iiko_id, name, kind, is_active, created_at, updated_at) 
VALUES 
('00000000-0000-0000-0000-000000000001', 'Наличные', 'Cash', true, now(), now()), 
('00000000-0000-0000-0000-000000000002', 'Карта', 'Card', true, now(), now())
ON CONFLICT (iiko_id) DO UPDATE SET name = EXCLUDED.name, updated_at = now();
