import sys
import os
import logging
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    logger.info("Starting database migration v3 for vk_first_comment_settings...")
    
    queries = [
        "ALTER TABLE vk_first_comment_settings ADD COLUMN IF NOT EXISTS exclude_reposts BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE vk_first_comment_settings ADD COLUMN IF NOT EXISTS delay_min INTEGER DEFAULT 0;",
        "ALTER TABLE vk_first_comment_settings ADD COLUMN IF NOT EXISTS delay_max INTEGER DEFAULT 0;"
    ]
    
    with engine.begin() as conn:
        for q in queries:
            try:
                conn.execute(text(q))
                logger.info(f"Executed query successfully: {q}")
            except Exception as e:
                logger.error(f"Error executing query '{q}': {e}")
                
    logger.info("Migration v3 completed.")

if __name__ == "__main__":
    migrate()
