import sys
import os

# Добавляем путь к корню бэкенда, чтобы импортировать базу данных
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.database import engine
from sqlalchemy import text

# Скрипт миграции: добавляет колонки, если они отсутствуют
alter_statements = [
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE;",
    
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS new_order_repeat_enabled BOOLEAN DEFAULT FALSE;",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS new_order_repeat_interval INTEGER DEFAULT 30;",
    
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS courier_delivery_sound_enabled BOOLEAN DEFAULT TRUE;",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS courier_delivery_sound_file VARCHAR(255) DEFAULT 'chime.mp3';",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS courier_delivery_push_enabled BOOLEAN DEFAULT TRUE;",
    
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS chat_message_sound_enabled BOOLEAN DEFAULT TRUE;",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS chat_message_sound_file VARCHAR(255) DEFAULT 'sonar.mp3';",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS chat_message_push_enabled BOOLEAN DEFAULT TRUE;",
    
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS order_cancelled_sound_enabled BOOLEAN DEFAULT TRUE;",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS order_cancelled_sound_file VARCHAR(255) DEFAULT 'bell.mp3';",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS order_cancelled_push_enabled BOOLEAN DEFAULT TRUE;",
    
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS order_changed_sound_enabled BOOLEAN DEFAULT FALSE;",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS order_changed_sound_file VARCHAR(255) DEFAULT 'bell.mp3';",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS order_changed_push_enabled BOOLEAN DEFAULT FALSE;",

    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS delivery_unassigned_sound_enabled BOOLEAN DEFAULT TRUE;",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS delivery_unassigned_sound_file VARCHAR(255) DEFAULT 'chime.mp3';",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS delivery_unassigned_push_enabled BOOLEAN DEFAULT TRUE;",
    
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS delivery_assigned_sound_enabled BOOLEAN DEFAULT TRUE;",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS delivery_assigned_sound_file VARCHAR(255) DEFAULT 'chime.mp3';",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS delivery_assigned_push_enabled BOOLEAN DEFAULT TRUE;",
    
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS change_cooking_time_sound_enabled BOOLEAN DEFAULT TRUE;",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS change_cooking_time_sound_file VARCHAR(255) DEFAULT 'click.mp3';",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS change_cooking_time_push_enabled BOOLEAN DEFAULT TRUE;",
    
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS change_items_sound_enabled BOOLEAN DEFAULT TRUE;",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS change_items_sound_file VARCHAR(255) DEFAULT 'click.mp3';",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS change_items_push_enabled BOOLEAN DEFAULT TRUE;",
    
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS change_amount_sound_enabled BOOLEAN DEFAULT TRUE;",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS change_amount_sound_file VARCHAR(255) DEFAULT 'click.mp3';",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS change_amount_push_enabled BOOLEAN DEFAULT TRUE;",
    
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS change_payment_sound_enabled BOOLEAN DEFAULT TRUE;",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS change_payment_sound_file VARCHAR(255) DEFAULT 'click.mp3';",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS change_payment_push_enabled BOOLEAN DEFAULT TRUE;",
    
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS change_address_sound_enabled BOOLEAN DEFAULT TRUE;",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS change_address_sound_file VARCHAR(255) DEFAULT 'click.mp3';",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS change_address_push_enabled BOOLEAN DEFAULT TRUE;",
    "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS order_changed_scope VARCHAR(50) DEFAULT 'all';"
]

with engine.connect() as connection:
    print("Running migration for admin_notification_settings table...")
    for statement in alter_statements:
        try:
            connection.execute(text(statement))
            print(f"Executed: {statement[:50]}...")
        except Exception as e:
            print(f"Skipped/Failed: {e}")
            
    # Сброс последовательности id
    try:
        connection.execute(text("SELECT setval('admin_notification_settings_id_seq', COALESCE((SELECT MAX(id) FROM admin_notification_settings), 1));"))
        print("Successfully reset sequence admin_notification_settings_id_seq")
    except Exception as seq_err:
        print(f"Sequence reset failed: {seq_err}")
        
    connection.commit()
    print("Migration finished!")
