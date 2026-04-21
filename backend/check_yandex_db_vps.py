from app.models.yandex_settings import YandexSettings
from sqlmodel import Session, select
from app.core.database import engine

def check():
    with Session(engine) as session:
        s = session.exec(select(YandexSettings)).first()
        if s:
            print(f"Yandex Settings ID: {s.id}")
            print(f"JS Key: {s.api_key_js[:10] if s.api_key_js else 'None'}...")
            print(f"Active: {s.is_active}")
        else:
            print("No Yandex Settings found in DB")

if __name__ == "__main__":
    check()
