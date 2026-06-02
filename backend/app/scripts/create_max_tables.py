
import sys
import os

# Добавляем путь к backend, чтобы можно было импортировать модули приложения
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlmodel import SQLModel
from app.core.database import engine
from app.models.max_settings import MaxSettings, MaxBot

def create_tables():
    print("Creating MAX integration tables...")
    try:
        SQLModel.metadata.create_all(engine)
        print("Tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    create_tables()
