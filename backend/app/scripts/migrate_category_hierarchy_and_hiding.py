import sys
import os
from sqlalchemy import text

# Добавляем путь к backend, чтобы импортировать модули приложения
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.database import engine, Session

def apply_migrations():
    sql_statements = [
        "ALTER TABLE categories ADD COLUMN IF NOT EXISTS hide_category_only BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE categories ADD COLUMN IF NOT EXISTS hide_category_and_products BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE categories ADD COLUMN IF NOT EXISTS lock_parent BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE product_modifiers ADD COLUMN IF NOT EXISTS is_visible BOOLEAN DEFAULT TRUE;",
        "ALTER TABLE iiko_settings ADD COLUMN IF NOT EXISTS hide_empty_categories BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE iiko_settings ADD COLUMN IF NOT EXISTS hide_stopped_products BOOLEAN DEFAULT FALSE;"
    ]
    
    print("Applying locks, hierarchy and hiding migrations to database...")
    with Session(engine) as session:
        for stmt in sql_statements:
            try:
                print(f"Executing: {stmt}")
                session.execute(text(stmt))
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error executing statement: {e}")
                
    print("Migrations completed!")

if __name__ == '__main__':
    apply_migrations()
