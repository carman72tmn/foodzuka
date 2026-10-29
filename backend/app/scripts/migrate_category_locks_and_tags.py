import sys
import os
from sqlalchemy import text

# Добавляем путь к backend, чтобы импортировать модули приложения
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.database import engine, Session

def apply_migrations():
    sql_statements = [
        "ALTER TABLE categories ADD COLUMN IF NOT EXISTS lock_name BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE categories ADD COLUMN IF NOT EXISTS lock_description BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE categories ADD COLUMN IF NOT EXISTS lock_image BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS tags VARCHAR(255) DEFAULT NULL;"
    ]
    
    print("Applying locks and tags migrations to database...")
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
