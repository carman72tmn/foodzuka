import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.database import engine
from sqlalchemy import text

def run_migration():
    print("Running migration for target_mode in vk_templates...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            query = text("ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS target_mode VARCHAR(50) DEFAULT 'all';")
            conn.execute(query)
            print("Column 'target_mode' added or already exists in vk_templates.")
            trans.commit()
            print("Migration completed successfully!")
        except Exception as e:
            trans.rollback()
            print(f"Error executing migration: {e}")
            raise e

if __name__ == "__main__":
    run_migration()
