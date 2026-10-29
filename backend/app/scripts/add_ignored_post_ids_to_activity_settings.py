import logging
from sqlmodel import text
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_column():
    """Добавляет колонку ignored_post_ids в таблицу vk_activity_settings, если ее нет"""
    logger.info("Checking ignored_post_ids column in vk_activity_settings...")
    query = text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name='vk_activity_settings' AND column_name='ignored_post_ids'
            ) THEN
                ALTER TABLE vk_activity_settings ADD COLUMN ignored_post_ids VARCHAR;
                RAISE NOTICE 'Column ignored_post_ids added successfully.';
            ELSE
                RAISE NOTICE 'Column ignored_post_ids already exists.';
            END IF;
        END $$;
    """)
    try:
        with engine.connect() as conn:
            conn.execute(query)
            conn.commit()
        logger.info("Migration completed successfully.")
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)

if __name__ == "__main__":
    add_column()
