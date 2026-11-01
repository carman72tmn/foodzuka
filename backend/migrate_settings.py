from app.core.database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    with engine.connect() as conn:
        logger.info("Checking for bonus_program_ids column in iiko_settings...")
        try:
            # PostgreSQL syntax
            conn.execute(text("ALTER TABLE iiko_settings ADD COLUMN IF NOT EXISTS bonus_program_ids TEXT DEFAULT '[]';"))
            conn.commit()
            logger.info("Successfully added bonus_program_ids column.")
        except Exception as e:
            logger.error(f"Error adding column: {e}")
            
if __name__ == "__main__":
    migrate()
