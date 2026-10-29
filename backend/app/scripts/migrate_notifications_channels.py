import logging
import sys
import os

# Добавляем путь к backend в sys.path для импорта модулей
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import text
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate_notifications_channels")

def migrate():
    logger.info("=== STARTING NOTIFICATION CHANNELS DATABASE MIGRATION ===")
    
    statements = [
        # Таблица vk_bot_accounts
        "ALTER TABLE vk_bot_accounts ALTER COLUMN vk_user_id DROP NOT NULL;",
        "ALTER TABLE vk_bot_accounts ADD COLUMN IF NOT EXISTS tg_user_id BIGINT DEFAULT NULL;",
        "ALTER TABLE vk_bot_accounts ADD COLUMN IF NOT EXISTS max_user_id VARCHAR(255) DEFAULT NULL;",
        "ALTER TABLE vk_bot_accounts ADD COLUMN IF NOT EXISTS use_vk BOOLEAN DEFAULT TRUE;",
        "ALTER TABLE vk_bot_accounts ADD COLUMN IF NOT EXISTS use_tg BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE vk_bot_accounts ADD COLUMN IF NOT EXISTS use_max BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE vk_bot_accounts ADD COLUMN IF NOT EXISTS use_sms BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE vk_bot_accounts ADD COLUMN IF NOT EXISTS is_tg_verified BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE vk_bot_accounts ADD COLUMN IF NOT EXISTS is_max_verified BOOLEAN DEFAULT FALSE;",
        
        # Таблица vk_bot_subscriptions
        "ALTER TABLE vk_bot_subscriptions ADD COLUMN IF NOT EXISTS send_vk BOOLEAN DEFAULT TRUE;",
        "ALTER TABLE vk_bot_subscriptions ADD COLUMN IF NOT EXISTS send_tg BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE vk_bot_subscriptions ADD COLUMN IF NOT EXISTS send_max BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE vk_bot_subscriptions ADD COLUMN IF NOT EXISTS send_sms BOOLEAN DEFAULT FALSE;"
    ]
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            for statement in statements:
                logger.info(f"Executing: {statement}")
                conn.execute(text(statement))
            trans.commit()
            logger.info("=== MIGRATION COMPLETED SUCCESSFULLY ===")
        except Exception as e:
            trans.rollback()
            logger.error(f"Migration failed: {e}")
            raise e

if __name__ == "__main__":
    migrate()
