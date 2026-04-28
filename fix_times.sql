UPDATE orders SET iiko_creation_time = iiko_creation_time - INTERVAL '5 hours' WHERE iiko_creation_time > created_at + INTERVAL '2 hours';
UPDATE orders SET expected_time = expected_time - INTERVAL '5 hours' WHERE expected_time IS NOT NULL AND expected_time > created_at + INTERVAL '2 hours';
UPDATE orders SET actual_time = actual_time - INTERVAL '5 hours' WHERE actual_time IS NOT NULL AND actual_time > created_at + INTERVAL '2 hours';
