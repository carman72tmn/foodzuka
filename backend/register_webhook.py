import asyncio
import os
import sys

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_session
from app.models.iiko_settings import IikoSettings
from app.services.iiko_service import iiko_service
from sqlmodel import Session, select

async def main():
    print("--- Регистрация вебхука iiko ---")
    with next(get_session()) as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("Ошибка: Настройки iiko не найдены в БД")
            return

        print(f"Текущий URL в БД: {settings.webhook_url}")
        print(f"Текущий токен в БД: {settings.webhook_auth_token}")
        
        try:
            # Обновляем настройки в iiko
            res = await iiko_service.update_webhook_settings(
                webhook_url=settings.webhook_url,
                auth_token=settings.webhook_auth_token,
                api_login=settings.api_login,
                organization_id=settings.organization_id
            )
            print("Результат регистрации iiko:", res)
        except Exception as e:
            print(f"Ошибка при регистрации: {e}")

if __name__ == "__main__":
    asyncio.run(main())
