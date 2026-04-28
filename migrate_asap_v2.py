import sys
import os

# Добавляем текущую директорию в path для импорта app
sys.path.append(os.getcwd())

try:
    from app.core.database import engine
    from sqlalchemy import text
except ImportError as e:
    print(f"Error importing engine: {e}")
    sys.exit(1)

def migrate():
    print("Starting migration: adding is_asap to orders table...")
    try:
        with engine.connect() as conn:
            # PostgreSQL syntax to add column if not exists
            conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS is_asap BOOLEAN DEFAULT TRUE"))
            conn.commit()
            print("Successfully added is_asap column to orders table.")
    except Exception as e:
        print(f"Error during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
