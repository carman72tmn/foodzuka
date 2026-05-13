import sys
import os

# Добавляем путь к backend
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.database import get_session_sync
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

def get_creds():
    try:
        with get_session_sync() as session:
            statement = select(IikoSettings)
            results = session.exec(statement).all()
            for res in results:
                print(f"Org: {res.organization_id}")
                print(f"Resto URL: {res.resto_url}")
                print(f"Resto Login: {res.resto_login}")
                print(f"Resto Password: {res.resto_password}")
                print("-" * 20)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_creds()
