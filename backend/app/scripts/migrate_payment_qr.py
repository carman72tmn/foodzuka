import logging
import sys
import os

# Добавляем путь к backend в sys.path для импорта модулей
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import text
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate_payment_qr")

def migrate():
    logger.info("=== STARTING PAYMENT QR DATABASE MIGRATION ===")
    
    statements = [
        # Добавляем новые колонки в vk_bot_accounts
        "ALTER TABLE vk_bot_accounts ADD COLUMN IF NOT EXISTS send_payment_qr BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE vk_bot_accounts ADD COLUMN IF NOT EXISTS payment_qr_mode VARCHAR(50) DEFAULT 'all';"
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
