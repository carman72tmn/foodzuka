from app.core.database import Session, engine
from app.models.iiko_settings import IikoSettings
from sqlmodel import select
import logging

logging.basicConfig(level=logging.INFO)

def check():
    with Session(engine) as session:
        s = session.exec(select(IikoSettings)).first()
        if not s:
            print("Settings NOT FOUND in database!")
            return
        
        print("--- IIKO SETTINGS ---")
        print(f"Organization ID: {s.organization_id}")
        print(f"API Login (first 4): {s.api_login[:4] if s.api_login else 'NONE'}...")
        print(f"Resto URL: {s.resto_url}")
        print(f"Resto Login: {s.resto_login}")
        print(f"Terminal Group ID: {s.terminal_group_id}")
        print("---------------------")

if __name__ == "__main__":
    check()
