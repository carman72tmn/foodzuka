import logging
from sqlalchemy import text
from app.core.database import engine

logger = logging.getLogger(__name__)

def migrate():
    print("Starting database migration to create vk_post_scheduler table...")
    with engine.connect() as conn:
        # Создаем таблицу, если она не существует
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vk_post_scheduler (
                id SERIAL PRIMARY KEY,
                vk_bot_connection_id INTEGER NOT NULL REFERENCES vk_bot_connections(id) ON DELETE CASCADE,
                type VARCHAR(50) NOT NULL DEFAULT 'post',
                content_text TEXT,
                media_url TEXT,
                publish_at TIMESTAMP NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                error_message TEXT,
                link_url TEXT,
                button_text TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
        """))
        
        # Создаем индекс на статус и время публикации для быстрой выборки планировщиком
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vk_scheduler_status_time ON vk_post_scheduler(status, publish_at);"))
        conn.commit()
        print("Table 'vk_post_scheduler' and indexes checked/created successfully.")

if __name__ == "__main__":
    migrate()
