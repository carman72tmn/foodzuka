import sys
import os

# Добавляем путь к backend, чтобы импорты работали
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlmodel import Session, text
from app.core.database import engine

def migrate():
    print("Starting migration: Add iiko dev fields to iiko_settings table...")
    with Session(engine) as session:
        try:
            # Проверим и добавим app_id
            session.execute(text(
                "ALTER TABLE iiko_settings ADD COLUMN IF NOT EXISTS app_id VARCHAR(255) DEFAULT '19de15e4-bce3-4742-b120-72a33813c025';"
            ))
            # Проверим и добавим client_secret
            session.execute(text(
                "ALTER TABLE iiko_settings ADD COLUMN IF NOT EXISTS client_secret VARCHAR(255) DEFAULT '9BryJrlsxs9aA863hjNPQLFSmlNvMZ0piUQFWCLBSec=';"
            ))
            session.commit()
            print("Migration completed successfully!")
        except Exception as e:
            session.rollback()
            print(f"Migration failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    migrate()
