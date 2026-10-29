"""
Скрипт миграции базы данных для полной интеграции MAX (Bot API + Web Bridge)
Добавляет необходимые поля в max_bots, max_settings, customers и создает таблицы max_message_logs, max_webhook_events.
"""
import sys
import os

# Добавляем путь к backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlalchemy import text
from sqlmodel import SQLModel
from app.core.database import engine
from app.models.max_settings import MaxSettings, MaxBot, MaxMessageLog, MaxWebhookEvent
from app.models.customer import Customer

def run_migration():
    print("Начинаем миграцию MAX v2...")
    
    # 1. Создаем новые таблицы если они отсутствуют
    try:
        SQLModel.metadata.create_all(engine)
        print("Таблицы проверены/созданы через SQLModel.metadata.create_all")
    except Exception as e:
        print(f"Предупреждение при create_all: {e}")

    # 2. Добавляем недостающие колонки в существующие таблицы
    alter_statements = [
        # max_bots
        "ALTER TABLE max_bots ADD COLUMN IF NOT EXISTS bot_username VARCHAR NULL;",
        "ALTER TABLE max_bots ADD COLUMN IF NOT EXISTS bot_avatar VARCHAR NULL;",
        "ALTER TABLE max_bots ADD COLUMN IF NOT EXISTS is_default_for_notifications BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE max_bots ADD COLUMN IF NOT EXISTS webhook_url VARCHAR NULL;",
        "ALTER TABLE max_bots ADD COLUMN IF NOT EXISTS webhook_set BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE max_bots ADD COLUMN IF NOT EXISTS webhook_updated_at TIMESTAMP WITHOUT TIME ZONE NULL;",
        "ALTER TABLE max_bots ADD COLUMN IF NOT EXISTS commands_json TEXT NULL;",
        "ALTER TABLE max_bots ADD COLUMN IF NOT EXISTS welcome_message TEXT DEFAULT 'Здравствуйте! Я официальный бот для уведомлений о ваших заказах.';",
        "ALTER TABLE max_bots ADD COLUMN IF NOT EXISTS request_contact_on_start BOOLEAN DEFAULT TRUE;",
        
        # max_settings
        "ALTER TABLE max_settings ADD COLUMN IF NOT EXISTS send_priority VARCHAR DEFAULT 'bot_first';",
        "ALTER TABLE max_settings ADD COLUMN IF NOT EXISTS auto_search_phone BOOLEAN DEFAULT TRUE;",
        "UPDATE max_settings SET base_url = 'https://platform-api2.max.ru' WHERE base_url IS NULL OR base_url LIKE '%max-service.ru%';",
        
        # customers
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS max_user_id VARCHAR NULL;",
        
        # Создание таблиц если create_all по какой-то причине пропустил
        """
        CREATE TABLE IF NOT EXISTS max_message_logs (
            id SERIAL PRIMARY KEY,
            recipient VARCHAR NOT NULL,
            customer_id INTEGER NULL,
            channel_type VARCHAR NOT NULL DEFAULT 'bot',
            bot_id INTEGER NULL,
            text TEXT NOT NULL,
            format VARCHAR NOT NULL DEFAULT 'markdown',
            notify BOOLEAN NOT NULL DEFAULT TRUE,
            buttons_json TEXT NULL,
            status VARCHAR NOT NULL DEFAULT 'sent',
            error_text TEXT NULL,
            max_message_id VARCHAR NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_max_message_logs_created_at ON max_message_logs (created_at);",
        "CREATE INDEX IF NOT EXISTS ix_max_message_logs_customer_id ON max_message_logs (customer_id);",
        
        """
        CREATE TABLE IF NOT EXISTS max_webhook_events (
            id SERIAL PRIMARY KEY,
            bot_id INTEGER NULL,
            event_type VARCHAR NOT NULL,
            user_id VARCHAR NULL,
            chat_id VARCHAR NULL,
            payload_json TEXT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
        );
        """,
        "CREATE INDEX IF NOT EXISTS ix_max_webhook_events_created_at ON max_webhook_events (created_at);",
        "CREATE INDEX IF NOT EXISTS ix_max_webhook_events_bot_id ON max_webhook_events (bot_id);",
        "CREATE INDEX IF NOT EXISTS ix_max_webhook_events_user_id ON max_webhook_events (user_id);"
    ]

    with engine.begin() as conn:
        for stmt in alter_statements:
            try:
                conn.execute(text(stmt))
            except Exception as ex:
                print(f"Ошибка при выполнении: {stmt.strip()[:60]}... -> {ex}")

    print("Миграция MAX v2 успешно завершена!")

if __name__ == "__main__":
    run_migration()
