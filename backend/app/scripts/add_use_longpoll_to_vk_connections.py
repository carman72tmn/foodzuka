import logging
from sqlmodel import Session, create_engine, text
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL)

def upgrade():
    logger.info("Starting database migration to add use_longpoll to vk_bot_connections...")
    
    with Session(engine) as session:
        try:
            res = session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'vk_bot_connections'"))
            existing_columns = [row[0] for row in res.fetchall()]
            
            if "use_longpoll" not in existing_columns:
                logger.info("Adding column 'use_longpoll' to vk_bot_connections...")
                session.execute(text("ALTER TABLE vk_bot_connections ADD COLUMN use_longpoll BOOLEAN DEFAULT FALSE"))
                session.commit()
                logger.info("Column 'use_longpoll' successfully added.")
            else:
                logger.info("Column 'use_longpoll' already exists.")
                
        except Exception as e:
            session.rollback()
            logger.error(f"Error during vk_bot_connections migration: {e}")
            raise e

    logger.info("Migration completed successfully!")

if __name__ == "__main__":
    upgrade()
