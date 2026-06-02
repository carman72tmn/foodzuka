import asyncio
import os
import sys

# Добавляем путь к приложению
sys.path.append('/app')

from app.services.iiko_service import IikoService
from app.core.config import settings
from app.core.database import SessionLocal

async def main():
    service = IikoService()
    # Берем из БД текущие настройки (уже обновленные)
    with SessionLocal() as db:
        from app.models.iiko_settings import IikoSettings
        db_settings = db.query(IikoSettings).first()
        if not db_settings:
            print("No settings in DB!")
            return
            
        api_login = db_settings.api_login
        org_id = db_settings.organization_id
    
    print(f"Starting registration for org {org_id} with login {api_login}...")
    # Принудительно передаем сессию и базу
    with SessionLocal() as db:
        result = await service.auto_register_webhook(
            session=db,
            api_login=api_login,
            organization_id=org_id,
            base_url="https://vezuroll.ru"
        )
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
