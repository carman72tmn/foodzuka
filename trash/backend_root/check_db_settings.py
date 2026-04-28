from sqlmodel import Session, select
from app.core.database import engine
from app.models.iiko_settings import IikoSettings
import json

def check_db_settings():
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("Settings not found in DB")
            return
        
        # Выводим настройки (маскируя чувствительные данные)
        print(f"Iiko Cloud Login: {settings.api_login}")
        print(f"Iiko Resto URL: {settings.resto_url}")
        print(f"Iiko Resto Login: {settings.resto_login}")
        print(f"Iiko Resto Password Set: {'Yes' if settings.resto_password else 'No'}")

if __name__ == "__main__":
    check_db_settings()
