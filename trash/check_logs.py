
import os
import sys
from datetime import datetime
from sqlmodel import Session, select, create_engine
from typing import Optional

# Добавляем путь к backend, чтобы можно было импортировать модули
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.models.system_log import SystemLog
from app.models.iiko_settings import IikoSettings
from app.core.config import settings

def check_everything():
    # Мы не знаем DATABASE_URL, попробуем взять из .env если он есть, 
    # или используем sqlite если это локальный тест (но нам нужна реальная БД)
    # Попробуем прочитать .env вручную если он лежит в backend
    env_path = os.path.join(os.getcwd(), "backend", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    os.environ["DATABASE_URL"] = line.split("=", 1)[1].strip()
                if line.startswith("SECRET_KEY="):
                    os.environ["SECRET_KEY"] = line.split("=", 1)[1].strip()

    try:
        from app.core.config import settings
        engine = create_engine(settings.DATABASE_URL)
    except Exception as e:
        print(f"Error initializing engine: {e}")
        return

    with Session(engine) as session:
        print("--- Iiko Settings ---")
        try:
            iiko_set = session.exec(select(IikoSettings)).first()
            if iiko_set:
                print(f"Organization ID: {iiko_set.organization_id}")
                print(f"Resto URL: {iiko_set.resto_url}")
                print(f"Resto Login: {iiko_set.resto_login}")
                print(f"Has Resto Password: {'Yes' if iiko_set.resto_password else 'No'}")
            else:
                print("No IikoSettings found.")
        except Exception as e:
            print(f"Error reading IikoSettings: {e}")

        print("\n--- Last 20 System Logs ---")
        try:
            statement = select(SystemLog).order_by(SystemLog.id.desc()).limit(20)
            logs = session.exec(statement).all()
            
            if not logs:
                print("No logs found.")
            else:
                for log in logs:
                    print(f"[{log.created_at}] {log.level} | {log.module} | {log.message}")
                    if log.stack_trace:
                        print(f"Stack trace: {log.stack_trace[:300]}...")
                    print("-" * 20)
        except Exception as e:
            print(f"Error reading SystemLog: {e}")

if __name__ == "__main__":
    check_everything()
