import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.database import engine
from sqlalchemy import text

def run_migration():
    print("Running migration for VK verification fields in validation_settings...")
    
    columns = [
        ("vk_alternative_methods", "VARCHAR(255) DEFAULT 'fcall,wcall,tg,max'"),
        ("vk_msg_start", "TEXT"),
        ("vk_msg_choose_method", "TEXT"),
        ("vk_msg_fcall_prompt", "TEXT"),
        ("vk_msg_fcall_code", "TEXT"),
        ("vk_msg_wcall_prompt", "TEXT"),
        ("vk_msg_wcall_instruct", "TEXT"),
        ("vk_msg_tg_instruct", "TEXT"),
        ("vk_msg_max_instruct", "TEXT"),
        ("vk_msg_success", "TEXT"),
        ("vk_msg_error_code", "TEXT")
    ]
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            for col_name, col_type in columns:
                query = text(f"ALTER TABLE validation_settings ADD COLUMN IF NOT EXISTS {col_name} {col_type};")
                conn.execute(query)
                print(f"Column '{col_name}' added or already exists.")
            trans.commit()
            print("Migration completed successfully!")
        except Exception as e:
            trans.rollback()
            print(f"Error executing migration: {e}")
            raise e

if __name__ == "__main__":
    run_migration()
