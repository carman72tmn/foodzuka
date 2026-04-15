import sys
import os

# Добавляем путь к приложению
sys.path.append(os.getcwd())

from sqlalchemy import text
from app.core.database import engine

def apply_migration():
    print("Applying migration: adding price_category_id to iiko_settings...")
    query = text("ALTER TABLE iiko_settings ADD COLUMN IF NOT EXISTS price_category_id VARCHAR(255);")
    comment_query = text("COMMENT ON COLUMN iiko_settings.price_category_id IS 'UUID выбранной категории цен для выгрузки меню';")
    
    with engine.connect() as conn:
        conn.execute(query)
        try:
            conn.execute(comment_query)
        except:
            pass # Comments might fail depending on DB permissions/flavor, not critical
        conn.commit()
    print("Migration applied successfully.")

if __name__ == "__main__":
    try:
        apply_migration()
    except Exception as e:
        print(f"Error applying migration: {e}")
        sys.exit(1)
