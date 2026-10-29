"""
Миграция таблицы bot_settings для расширенных настроек Telegram:
- Управление активностью каналов (вкл/выкл бота и рассылок, чтобы не грузить систему пустыми запросами)
- Системный канал для уведомлений (system_channel_id)
- Поддержка отправки с личного номера / аккаунта Telegram (User API / MTProto)
"""
from app.core.database import SessionLocal
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def migrate():
    session = SessionLocal()
    try:
        queries = [
            "ALTER TABLE bot_settings ADD COLUMN IF NOT EXISTS is_bot_active BOOLEAN DEFAULT false;",
            "ALTER TABLE bot_settings ADD COLUMN IF NOT EXISTS bot_username VARCHAR(255);",
            "ALTER TABLE bot_settings ADD COLUMN IF NOT EXISTS system_channel_id VARCHAR(255);",
            "ALTER TABLE bot_settings ADD COLUMN IF NOT EXISTS is_system_notifications_active BOOLEAN DEFAULT false;",
            "ALTER TABLE bot_settings ADD COLUMN IF NOT EXISTS is_client_broadcast_active BOOLEAN DEFAULT false;",
            "ALTER TABLE bot_settings ADD COLUMN IF NOT EXISTS is_user_client_active BOOLEAN DEFAULT false;",
            "ALTER TABLE bot_settings ADD COLUMN IF NOT EXISTS user_phone VARCHAR(50);",
            "ALTER TABLE bot_settings ADD COLUMN IF NOT EXISTS user_api_id VARCHAR(100);",
            "ALTER TABLE bot_settings ADD COLUMN IF NOT EXISTS user_api_hash VARCHAR(255);",
            "ALTER TABLE bot_settings ADD COLUMN IF NOT EXISTS user_session_string TEXT;",
            "ALTER TABLE bot_settings ADD COLUMN IF NOT EXISTS user_account_status VARCHAR(50) DEFAULT 'not_connected';",
        ]
        
        for q in queries:
            session.execute(text(q))
            
        session.commit()
        print("Telegram bot_settings migration applied successfully!")
    except Exception as e:
        session.rollback()
        print(f"Error migrating bot_settings: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    migrate()
