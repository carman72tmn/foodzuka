import asyncio
import sys

from sqlmodel import select
from app.models.iiko_settings import IikoSettings
from app.core.database import get_session
from app.services.iiko_service import iiko_service

async def main():
    iterator = get_session()
    db = next(iterator)
    try:
        settings = db.exec(select(IikoSettings)).first()
        if not settings:
            print("Settings not found in database!")
            sys.exit(1)
            
        print(f"Current webhook URL in DB: {settings.webhook_url}")
        print("Testing auto_register_webhook...")
        
        try:
            result = await iiko_service.auto_register_webhook(
                request_url="http://localhost:8000/",
                api_login=settings.api_login,
                organization_id=settings.organization_id
            )
            print("SUCCESS:")
            print(result)
        except Exception as e:
            print("ERROR:")
            print(str(e))
            sys.exit(1)
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())
