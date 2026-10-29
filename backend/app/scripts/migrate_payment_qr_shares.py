import logging
import sys
import os

# Добавляем путь к backend в sys.path для импорта модулей
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import text
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate_payment_qr_shares")

def migrate():
    logger.info("=== STARTING PAYMENT QR SHARES DATABASE MIGRATION ===")
    
    statements = [
        # Создаем таблицу order_payment_qr_shares
        """
        CREATE TABLE IF NOT EXISTS order_payment_qr_shares (
            id SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            channel VARCHAR(50) NOT NULL,
            chat_id VARCHAR(100) NOT NULL,
            message_id VARCHAR(100) NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        );
        """,
        # Добавляем индекс на order_id
        "CREATE INDEX IF NOT EXISTS idx_order_payment_qr_shares_order_id ON order_payment_qr_shares(order_id);"
    ]
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            for statement in statements:
                logger.info(f"Executing: {statement.strip()}")
                conn.execute(text(statement))
            trans.commit()
            logger.info("=== MIGRATION COMPLETED SUCCESSFULLY ===")
        except Exception as e:
            trans.rollback()
            logger.error(f"Migration failed: {e}")
            raise e

if __name__ == "__main__":
    migrate()
