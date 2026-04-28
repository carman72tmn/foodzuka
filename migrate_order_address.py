from app.core.database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    try:
        with engine.connect() as conn:
            logger.info("Adding address_parts to orders table...")
            conn.execute(text('ALTER TABLE orders ADD COLUMN IF NOT EXISTS address_parts JSONB'))
            conn.commit()
            logger.info("Migration successful!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
