INSERT INTO users (login, password, name, email, created_at, updated_at, username, hashed_password, is_active, is_superuser) 
VALUES ('0001', '$2y$12$m/vyyH5wo28cW1mEHtm0../ntO1ogo/BzpI9xwQkP7E4plIeMAipW', 'SuperAdmin', 'admin@72roll.ru', NOW(), NOW(), '0001', 'hashed_pass', true, true)
ON CONFLICT (email) DO UPDATE SET login = EXCLUDED.login, password = EXCLUDED.password;
