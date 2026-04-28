import asyncio
import logging
from sqlmodel import Session, select
from app.core.database import engine
from app.services.iiko_service import iiko_service
from app.models import IikoSettings, IikoWebhookEvent

async def run_diagnostic():
    logging.basicConfig(level=logging.INFO)
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("No IikoSettings in DB")
            return
            
        print(f"Organization ID: {settings.organization_id}")
        
        # 1. Проверка настроек вебхука в Cloud
        print("\n--- Checking Webhook Settings in iiko Cloud ---")
        try:
            webhook_info = await iiko_service.get_webhook_settings(
                api_login=settings.api_login,
                organization_id=settings.organization_id
            )
            print(f"Webhook Settings in Cloud: {webhook_info}")
        except Exception as e:
            print(f"Error getting webhook settings: {e}")

        # 2. Проверка последних событий в базе
        print("\n--- Last 5 Webhook Events in Local DB ---")
        events = session.exec(select(IikoWebhookEvent).order_by(IikoWebhookEvent.id.desc()).limit(5)).all()
        for e in events:
            print(f"ID {e.id}: {e.event_type} at {e.created_at}, processed={e.processed}, error={e.error}")

if __name__ == "__main__":
    asyncio.run(run_diagnostic())
