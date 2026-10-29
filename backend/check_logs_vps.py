import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(__file__))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from sqlmodel import select, text

def main():
    session = SessionLocal()
    try:
        print("ПОСЛЕДНИЕ ЛОГИ СИНХРОНИЗАЦИИ:")
        res = session.execute(text("SELECT id, sync_type, status, details, created_at FROM sync_logs ORDER BY id DESC LIMIT 10")).all()
        for r in res:
            print(f"ID: {r[0]} | Type: {r[1]} | Status: {r[2]} | CreatedAt: {r[4]}")
            print(f"Details: {r[3]}\n{'-'*50}")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    main()
