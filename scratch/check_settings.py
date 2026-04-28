from app.core.database import SessionLocal
from app.models import IikoSettings
from sqlmodel import select

def check():
    with SessionLocal() as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("No settings found")
            return
        print(f"Resto URL: {settings.resto_url}")
        print(f"Resto Login: {settings.resto_login}")
        # print(f"Resto Pass: {settings.resto_password}") # Better not print full password
        print(f"Resto Pass Length: {len(settings.resto_password) if settings.resto_password else 0}")

if __name__ == "__main__":
    check()
