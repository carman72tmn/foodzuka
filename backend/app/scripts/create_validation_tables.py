import sys
import os

# Добавляем путь к backend, чтобы можно было импортировать модули приложения
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlmodel import SQLModel
from app.core.database import engine
from app.models.validation_settings import ValidationSettings
from app.scripts.seed_rbac import seed_rbac

def create_tables_and_seed():
    print("Creating validation integration tables...")
    try:
        SQLModel.metadata.create_all(engine)
        print("Tables created successfully!")
        
        print("Seeding RBAC permissions...")
        seed_rbac()
        print("RBAC seeded successfully!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_tables_and_seed()
