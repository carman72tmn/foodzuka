import logging
from sqlalchemy import text
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    logger.info("Starting database migration for VK Activity Penalty Timers...")
    try:
        with engine.connect() as conn:
            # 1. Добавляем новые колонки в vk_activity_settings, если их нет
            logger.info("Checking/adding penalty columns to vk_activity_settings...")
            
            # penalty_duration_seconds
            conn.execute(text("""
                ALTER TABLE vk_activity_settings 
                ADD COLUMN IF NOT EXISTS penalty_duration_seconds INTEGER DEFAULT 3600;
            """))
            
            # penalty_points
            conn.execute(text("""
                ALTER TABLE vk_activity_settings 
                ADD COLUMN IF NOT EXISTS penalty_points INTEGER DEFAULT 0;
            """))
            
            # msg_penalty
            conn.execute(text("""
                ALTER TABLE vk_activity_settings 
                ADD COLUMN IF NOT EXISTS msg_penalty VARCHAR(500) DEFAULT NULL;
            """))
            
            # 2. Создаем таблицу vk_activity_penalty_timers, если ее нет
            logger.info("Checking/creating vk_activity_penalty_timers table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS vk_activity_penalty_timers (
                    id SERIAL PRIMARY KEY,
                    vk_id BIGINT NOT NULL,
                    vk_bot_connection_id INTEGER NOT NULL REFERENCES vk_bot_connections(id) ON DELETE CASCADE,
                    target_type VARCHAR(50) NOT NULL,
                    target_id VARCHAR(100) NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
            """))
            
            # Создаем индекс для быстрой проверки активных таймеров
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_vk_penalty_timers_lookup 
                ON vk_activity_penalty_timers(vk_id, vk_bot_connection_id, target_type, target_id, expires_at);
            """))
            
            conn.commit()
            logger.info("Database migration completed successfully.")
    except Exception as e:
        logger.error(f"Database migration failed: {e}", exc_info=True)
        raise e

if __name__ == "__main__":
    migrate()
