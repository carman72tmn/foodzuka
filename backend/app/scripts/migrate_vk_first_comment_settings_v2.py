import sys
import os
import logging
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    logger.info("Starting database migration for vk_first_comment_settings...")
    
    queries = [
        "ALTER TABLE vk_first_comment_settings ADD COLUMN IF NOT EXISTS post_type_filter VARCHAR(255) DEFAULT 'all';",
        "ALTER TABLE vk_first_comment_settings ADD COLUMN IF NOT EXISTS include_keywords TEXT;",
        "ALTER TABLE vk_first_comment_settings ADD COLUMN IF NOT EXISTS exclude_keywords TEXT;",
        "ALTER TABLE vk_first_comment_settings ADD COLUMN IF NOT EXISTS delay_seconds INTEGER DEFAULT 0;",
        "ALTER TABLE vk_first_comment_settings ADD COLUMN IF NOT EXISTS ignore_empty_text BOOLEAN DEFAULT FALSE;"
    ]
    
    with engine.begin() as conn:
        for q in queries:
            try:
                conn.execute(text(q))
                logger.info(f"Executed query successfully: {q}")
            except Exception as e:
                logger.error(f"Error executing query '{q}': {e}")
                
    logger.info("Migration completed.")

if __name__ == "__main__":
    migrate()
