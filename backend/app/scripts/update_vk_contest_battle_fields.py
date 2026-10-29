import logging
from sqlmodel import Session, create_engine, text
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL)

def upgrade():
    logger.info("Starting database migration for VK Contest beach battle settings...")
    
    # Новые столбцы для vk_contests
    contests_columns = {
        "penalty_percent": ("INTEGER", "10"),
        "bonus_percent": ("INTEGER", "20")
    }

    # Новые столбцы для vk_contest_players
    players_columns = {
        "penalties_hit": ("INTEGER", "0"),
        "is_game_over": ("BOOLEAN", "FALSE")
    }

    with Session(engine) as session:
        # 1. Обновляем vk_contests
        try:
            res = session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'vk_contests'"))
            existing_columns = [row[0] for row in res.fetchall()]
            
            for col_name, (col_type, default_val) in contests_columns.items():
                if col_name not in existing_columns:
                    logger.info(f"Adding column '{col_name}' to vk_contests...")
                    session.execute(text(f"ALTER TABLE vk_contests ADD COLUMN {col_name} {col_type} DEFAULT {default_val}"))
                    session.commit()
                    logger.info(f"Column '{col_name}' successfully added.")
                else:
                    logger.info(f"Column '{col_name}' already exists.")
        except Exception as e:
            session.rollback()
            logger.error(f"Error during vk_contests migration: {e}")
            raise e

        # 2. Обновляем vk_contest_players
        try:
            res = session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'vk_contest_players'"))
            existing_columns = [row[0] for row in res.fetchall()]
            
            for col_name, (col_type, default_val) in players_columns.items():
                if col_name not in existing_columns:
                    logger.info(f"Adding column '{col_name}' to vk_contest_players...")
                    session.execute(text(f"ALTER TABLE vk_contest_players ADD COLUMN {col_name} {col_type} DEFAULT {default_val}"))
                    session.commit()
                    logger.info(f"Column '{col_name}' successfully added.")
                else:
                    logger.info(f"Column '{col_name}' already exists.")
        except Exception as e:
            session.rollback()
            logger.error(f"Error during vk_contest_players migration: {e}")
            raise e

    logger.info("Beach battle settings migration completed successfully!")

if __name__ == "__main__":
    upgrade()
