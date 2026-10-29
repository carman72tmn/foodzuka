from sqlalchemy import text
from app.core.database import engine

def migrate():
    with engine.begin() as conn:
        print("Starting DB Migration for VK Cover 2.0...")
        
        # 1. Снимаем уникальный индекс для поддержки нескольких обложек
        conn.execute(text("DROP INDEX IF EXISTS ix_vk_cover_bots_vk_bot_connection_id;"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_vk_cover_bots_vk_bot_connection_id ON vk_cover_bots(vk_bot_connection_id);"))
        print("Index ix_vk_cover_bots_vk_bot_connection_id updated to non-unique.")
        
        # 2. Добавляем новые колонки
        columns = [
            ("name", "VARCHAR(100) DEFAULT 'Основная обложка'"),
            ("is_rotation_enabled", "BOOLEAN DEFAULT true"),
            ("schedule_type", "VARCHAR(50) DEFAULT 'always'"),
            ("schedule_start_time", "VARCHAR(5) DEFAULT NULL"),
            ("schedule_end_time", "VARCHAR(5) DEFAULT NULL"),
            ("rotation_order", "INTEGER DEFAULT 0"),
            ("slideshow_images", "JSON DEFAULT '[]'"),
            ("slideshow_interval_minutes", "INTEGER DEFAULT 5"),
            ("slideshow_mode", "VARCHAR(20) DEFAULT 'sequence'")
        ]
        
        for col_name, col_type in columns:
            conn.execute(text(f"""
                ALTER TABLE vk_cover_bots 
                ADD COLUMN IF NOT EXISTS {col_name} {col_type};
            """))
            print(f"Column {col_name} checked/added.")
            
        print("DB Migration successfully completed!")

if __name__ == "__main__":
    migrate()
