import sys
import os

# Добавляем путь к backend, чтобы можно было импортировать модули приложения
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlmodel import SQLModel
from app.core.database import engine
from app.models.chat import MultichatTag, MultichatDialogTag

def create_tables():
    print("Creating Multichat Tags database tables...")
    try:
        SQLModel.metadata.create_all(engine)
        print("Multichat Tags tables created successfully!")
    except Exception as e:
        print(f"Error creating multichat tags tables: {e}")

if __name__ == "__main__":
    create_tables()
