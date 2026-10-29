import sys
import os
import logging
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    logger.info("Starting database migration v4 for adding vk_bot_token override to all bot settings...")
    
    tables = [
        "vk_birthday_bots",
        "vk_cover_bots",
        "vk_activity_settings",
        "vk_first_comment_settings",
        "vk_contests"
    ]
    
    with engine.begin() as conn:
        for table in tables:
            q = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS vk_bot_token VARCHAR;"
            try:
                conn.execute(text(q))
                logger.info(f"Executed query successfully: {q}")
            except Exception as e:
                logger.error(f"Error executing query '{q}': {e}")
                
    logger.info("Migration v4 completed.")

if __name__ == "__main__":
    migrate()
