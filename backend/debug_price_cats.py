import os
import sys
import asyncio
import json
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from app.services.iiko_service import iiko_service
from sqlmodel import select

async def main():
    session = SessionLocal()
    try:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("Настройки не найдены")
            return
            
        print("Запрашиваем /api/2/menu...")
        data = await iiko_service._request(
            "POST", "/api/2/menu", 
            {"organizationIds": [settings.organization_id]},
            api_login=settings.api_login,
            organization_id=settings.organization_id
        )
        print("СЫРОЙ ОТВЕТ ОТ IIKO /api/2/menu:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    asyncio.run(main())
