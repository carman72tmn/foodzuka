import logging
from sqlmodel import Session
from app.core.database import engine
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("add_cooking_time_updated_at")

def run():
    logger.info("Starting migration to add cooking_time_updated_at column...")
    with Session(engine) as session:
        try:
            # Добавляем колонку, если её нет
            session.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS cooking_time_updated_at TIMESTAMP WITH TIME ZONE;"))
            session.commit()
            logger.info("Successfully added cooking_time_updated_at column to orders table.")
        except Exception as e:
            session.rollback()
            logger.error(f"Error executing migration: {e}")

if __name__ == "__main__":
    run()
