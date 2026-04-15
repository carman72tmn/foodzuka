import asyncio
import logging
import json
from sqlmodel import Session, select
from app.core.database import engine
from app.services.iiko_sync_service import iiko_sync_service
from app.models import IikoWebhookEvent

async def debug_sync_payload():
    logging.basicConfig(level=logging.INFO)
    with Session(engine) as session:
        # Берем тот самый событие 39
        event = session.get(IikoWebhookEvent, 39)
        if not event:
            print("Event 39 not found")
            return
            
        print(f"Processing event 39: {event.event_type}")
        payload = event.payload
        event_info = payload.get("eventInfo", {})
        order_guid = event_info.get("id")
        org_id = payload.get("organizationId")
        
        # Запускаем обработку напрямую по данным из вебхука
        # В iiko_sync_service.py нет метода для обработки ПРЯМОГО заказа из вебхука,
        # кроме как через создание мока или расширение метода.
        
        # На самом деле, iiko_sync_service.process_iiko_order ожидает iiko_order_data, 
        # который в вебхуке находится в event_info.
        
        try:
            print(f"Starting process_iiko_order for GUID: {order_guid}")
            # В вебхуке структура: eventInfo = { id, order, ... }
            # process_iiko_order ожидает объект, у которого есть .get("id") и .get("order")
            await iiko_sync_service.process_iiko_order(session, event_info, org_id)
            session.commit()
            print("Successfully processed and committed!")
        except Exception as e:
            print(f"FATAL ERROR while processing: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_sync_payload())
