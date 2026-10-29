import logging
import sys
import os

# Добавляем путь к backend в sys.path для импорта модулей
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import text
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("add_ignored_ids_to_vk_settings")

def migrate():
    logger.info("=== STARTING ADD VK_PARSER_IGNORED_IDS TO VK_SETTINGS MIGRATION ===")
    
    statements = [
        "ALTER TABLE vk_settings ADD COLUMN IF NOT EXISTS vk_parser_ignored_ids TEXT DEFAULT NULL;"
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
