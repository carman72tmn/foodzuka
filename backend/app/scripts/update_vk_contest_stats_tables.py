import logging
from sqlmodel import Session, create_engine, text
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL)

def upgrade():
    logger.info("Starting database migration for VK Contest stats tables...")
    
    # 1. Добавляем колонки в vk_contest_winners
    winners_columns = {
        "is_activated": ("BOOLEAN", "FALSE"),
        "activated_at": ("TIMESTAMP WITHOUT TIME ZONE", "NULL"),
        "order_id": ("VARCHAR(255)", "NULL")
    }

    with Session(engine) as session:
        try:
            res = session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'vk_contest_winners'"))
            existing_columns = [row[0] for row in res.fetchall()]
            
            for col_name, (col_type, default_val) in winners_columns.items():
                if col_name not in existing_columns:
                    logger.info(f"Adding column '{col_name}' to vk_contest_winners...")
                    session.execute(text(f"ALTER TABLE vk_contest_winners ADD COLUMN {col_name} {col_type} DEFAULT {default_val}"))
                    session.commit()
                    logger.info(f"Column '{col_name}' successfully added.")
                else:
                    logger.info(f"Column '{col_name}' already exists.")
        except Exception as e:
            session.rollback()
            logger.error(f"Error during vk_contest_winners migration: {e}")
            raise e

        # 2. Создаем таблицу vk_contest_actions
        try:
            logger.info("Creating table 'vk_contest_actions' if not exists...")
            create_table_query = """
            CREATE TABLE IF NOT EXISTS vk_contest_actions (
                id SERIAL PRIMARY KEY,
                contest_id INTEGER NOT NULL REFERENCES vk_contests(id) ON DELETE CASCADE,
                vk_user_id BIGINT NOT NULL,
                first_name VARCHAR(255) NOT NULL,
                last_name VARCHAR(255) NOT NULL,
                action_type VARCHAR(50) NOT NULL,
                detail TEXT NOT NULL,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_vk_contest_actions_contest_id ON vk_contest_actions(contest_id);
            CREATE INDEX IF NOT EXISTS idx_vk_contest_actions_vk_user_id ON vk_contest_actions(vk_user_id);
            """
            session.execute(text(create_table_query))
            session.commit()
            logger.info("Table 'vk_contest_actions' and indexes successfully checked/created.")
        except Exception as e:
            session.rollback()
            logger.error(f"Error during vk_contest_actions table creation: {e}")
            raise e

    logger.info("Stats tables migration completed successfully!")

if __name__ == "__main__":
    upgrade()
