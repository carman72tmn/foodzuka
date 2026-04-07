from app.services.iiko_service import iiko_service
from sqlmodel import Session, create_engine, select
from app.models.iiko_settings import IikoSettings
import os
import asyncio

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

async def register():
    print("[register_hook] Starting registration...")
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("[register_hook] Error: No IikoSettings found in database.")
            return

        print(f"[register_hook] Using API Login: {settings.api_login}")
        # Принудительно вызываем с правильным URL
        success = await iiko_service.auto_register_webhook(session)
        print(f"[register_hook] Registration result: {success}")

if __name__ == "__main__":
    asyncio.run(register())
