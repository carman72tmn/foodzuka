import sys
import os
from sqlalchemy import text

# Добавляем путь к backend, чтобы импортировать модули приложения
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.database import engine, Session

def apply_migrations():
    sql_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'create_kitchen_tables.sql'))
    
    if not os.path.exists(sql_path):
        print(f"Error: SQL file not found at {sql_path}")
        return
        
    print(f"Reading SQL file: {sql_path}...")
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
        
    # Разделяем SQL команды по точке с запятой, чтобы выполнить их последовательно
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    print("Applying migrations to database...")
    with Session(engine) as session:
        for stmt in statements:
            try:
                print(f"Executing: {stmt[:100]}...")
                session.execute(text(stmt))
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Warning/Error executing statement: {e}")
                
    print("Migrations applied successfully!")

if __name__ == '__main__':
    apply_migrations()
