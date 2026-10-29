import logging
from sqlmodel import Session, create_engine, text
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL)

def upgrade():
    logger.info("Starting database migration for VK Cover Bot advanced update and callback fields...")
    
    with Session(engine) as session:
        try:
            res = session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'vk_cover_bots'"))
            existing_columns = [row[0] for row in res.fetchall()]
            
            # 1. Добавляем update_interval
            if "update_interval" not in existing_columns:
                logger.info("Adding column 'update_interval' to vk_cover_bots...")
                session.execute(text("ALTER TABLE vk_cover_bots ADD COLUMN update_interval VARCHAR(50) DEFAULT '1m'"))
                session.commit()
                logger.info("Column 'update_interval' successfully added.")
            else:
                logger.info("Column 'update_interval' already exists.")
                
            # 2. Добавляем use_custom_callback
            if "use_custom_callback" not in existing_columns:
                logger.info("Adding column 'use_custom_callback' to vk_cover_bots...")
                session.execute(text("ALTER TABLE vk_cover_bots ADD COLUMN use_custom_callback BOOLEAN DEFAULT FALSE"))
                session.commit()
                logger.info("Column 'use_custom_callback' successfully added.")
            else:
                logger.info("Column 'use_custom_callback' already exists.")
                
            # 3. Добавляем callback_confirmation_code
            if "callback_confirmation_code" not in existing_columns:
                logger.info("Adding column 'callback_confirmation_code' to vk_cover_bots...")
                session.execute(text("ALTER TABLE vk_cover_bots ADD COLUMN callback_confirmation_code TEXT NULL"))
                session.commit()
                logger.info("Column 'callback_confirmation_code' successfully added.")
            else:
                logger.info("Column 'callback_confirmation_code' already exists.")
                
            # 4. Добавляем callback_secret_key
            if "callback_secret_key" not in existing_columns:
                logger.info("Adding column 'callback_secret_key' to vk_cover_bots...")
                session.execute(text("ALTER TABLE vk_cover_bots ADD COLUMN callback_secret_key TEXT NULL"))
                session.commit()
                logger.info("Column 'callback_secret_key' successfully added.")
            else:
                logger.info("Column 'callback_secret_key' already exists.")
                
        except Exception as e:
            session.rollback()
            logger.error(f"Error during vk_cover_bots migration: {e}")
            raise e

    logger.info("VK Cover Bot fields migration completed successfully!")

if __name__ == "__main__":
    upgrade()
