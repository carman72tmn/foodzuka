import logging
import sys
import os

# Добавляем путь к backend в sys.path для импорта модулей
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import text
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("add_max_user_id_to_customers")

def migrate():
    logger.info("=== STARTING ADD MAX_USER_ID TO CUSTOMERS MIGRATION ===")
    
    statements = [
        "ALTER TABLE customers ADD COLUMN IF NOT EXISTS max_user_id VARCHAR(255) DEFAULT NULL;"
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
