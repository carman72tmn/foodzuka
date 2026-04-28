SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'orders' AND column_name IN ('created_at', 'iiko_creation_time');
