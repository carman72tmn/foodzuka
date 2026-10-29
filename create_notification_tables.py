from app.core.database import engine
from sqlalchemy import text

create_settings_sql = """
CREATE TABLE IF NOT EXISTS admin_notification_settings (
    id SERIAL PRIMARY KEY,
    new_order_sound_enabled BOOLEAN DEFAULT TRUE,
    new_order_sound_file VARCHAR(255) DEFAULT 'bell.mp3',
    new_order_push_enabled BOOLEAN DEFAULT TRUE,
    new_payment_sound_enabled BOOLEAN DEFAULT TRUE,
    new_payment_sound_file VARCHAR(255) DEFAULT 'cash.mp3',
    new_payment_push_enabled BOOLEAN DEFAULT TRUE,
    vapid_public_key TEXT,
    vapid_private_key TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

create_subscriptions_sql = """
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(1000) UNIQUE NOT NULL,
    p256dh VARCHAR(500) NOT NULL,
    auth VARCHAR(500) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

insert_default_settings_sql = """
INSERT INTO admin_notification_settings (id, new_order_sound_enabled, new_order_sound_file, new_order_push_enabled, new_payment_sound_enabled, new_payment_sound_file, new_payment_push_enabled, created_at, updated_at)
VALUES (1, TRUE, 'bell.mp3', TRUE, TRUE, 'cash.mp3', TRUE, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;
"""

with engine.connect() as connection:
    print("Creating admin_notification_settings table...")
    connection.execute(text(create_settings_sql))
    print("Creating push_subscriptions table...")
    connection.execute(text(create_subscriptions_sql))
    print("Inserting default settings row...")
    connection.execute(text(insert_default_settings_sql))
    connection.commit()
    print("Database migration completed successfully!")
