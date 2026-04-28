import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.getcwd())

try:
    from app.models.iiko_settings import IikoSettings
    from app.core.database import SessionLocal
    from sqlmodel import select

    with SessionLocal() as session:
        statement = select(IikoSettings)
        s = session.exec(statement).first()
        if s:
            print(f"Timezone Name: {s.timezone_name}")
            print(f"Manual Timezone: {s.manual_timezone}")
            print(f"City Name: {s.city_name}")
        else:
            print("No iiko settings found in database.")
except Exception as e:
    print(f"Error: {e}")
