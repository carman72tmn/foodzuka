import logging
from sqlalchemy import text
from app.core.database import engine

logger = logging.getLogger(__name__)

def migrate():
    print("Starting database migration to create vk_group_posting tables...")
    with engine.connect() as conn:
        # 1. Таблица пресетов (списков групп)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vk_group_presets (
                id SERIAL PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                description TEXT,
                groups_data JSONB DEFAULT '[]'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
        """))

        # 2. Таблица кампаний постинга
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vk_group_post_campaigns (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                text TEXT NOT NULL,
                media_urls JSONB DEFAULT '[]'::jsonb,
                account_id INTEGER NOT NULL,
                account_name VARCHAR(150),
                preset_id INTEGER,
                status VARCHAR(50) NOT NULL DEFAULT 'completed',
                delay_seconds INTEGER NOT NULL DEFAULT 20,
                total_count INTEGER NOT NULL DEFAULT 0,
                success_count INTEGER NOT NULL DEFAULT 0,
                failed_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
        """))

        # 3. Таблица истории опубликованных постов и метрик
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vk_group_post_history (
                id SERIAL PRIMARY KEY,
                campaign_id INTEGER,
                account_id INTEGER NOT NULL,
                account_name VARCHAR(150),
                group_id BIGINT NOT NULL,
                group_name VARCHAR(255),
                group_screen_name VARCHAR(100),
                group_photo TEXT,
                post_id BIGINT,
                post_url TEXT,
                text TEXT,
                media_urls JSONB DEFAULT '[]'::jsonb,
                status VARCHAR(50) NOT NULL DEFAULT 'published',
                error_message TEXT,
                views_count INTEGER NOT NULL DEFAULT 0,
                likes_count INTEGER NOT NULL DEFAULT 0,
                reposts_count INTEGER NOT NULL DEFAULT 0,
                comments_count INTEGER NOT NULL DEFAULT 0,
                published_at TIMESTAMP WITH TIME ZONE,
                last_checked_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
        """))

        # Индексы для быстрой фильтрации и поиска
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vk_group_presets_name ON vk_group_presets(name);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vk_post_hist_account ON vk_group_post_history(account_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vk_post_hist_group ON vk_group_post_history(group_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vk_post_hist_post_id ON vk_group_post_history(post_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vk_post_hist_status ON vk_group_post_history(status);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vk_post_hist_created ON vk_group_post_history(created_at DESC);"))
        
        # 4. Добавляем системные права доступа RBAC
        conn.execute(text("""
            INSERT INTO permissions (name, code, category, description)
            VALUES 
                ('Постинг в группах (Просмотр)', 'marketing_group_posting_view', 'Акции и Лояльность', 'Просмотр страницы постинга в группах ВК, списков и аналитики'),
                ('Постинг в группах (Публикация)', 'marketing_group_posting_edit', 'Акции и Лояльность', 'Публикация постов на стенах сообществ ВК и управление блоками')
            ON CONFLICT (code) DO NOTHING;
        """))

        conn.commit()
        print("Tables 'vk_group_presets', 'vk_group_post_campaigns', 'vk_group_post_history' and permissions created successfully.")

if __name__ == "__main__":
    migrate()
