import asyncio
import os
import logging
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.core.database import engine
from app.models.iiko_settings import IikoSettings
from app.services.iiko_sync_service import iiko_sync_service
from app.services.iiko_service import iiko_service

logging.basicConfig(level=logging.INFO)

async def force_sync_recent_orders():
    print("Starting force synchronization of orders...")
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("Error: Iiko settings not found.")
            return

        try:
            # Используем уже существующий метод для получения активных заказов
            # Он точно работает и не вызывает 400
            print("Fetching active orders via IikoService.get_active_orders()...")
            orders = await iiko_service.get_active_orders(
                api_login=settings.api_login,
                organization_id=settings.organization_id
            )
            
            print(f"Found {len(orders)} active orders.")
            
            synced_count = 0
            for order_data in orders:
                order_id = order_data.get("id")
                # Оборачиваем для process_iiko_order
                wrapped_data = {"order": order_data}
                await iiko_sync_service.process_iiko_order(
                    session, 
                    wrapped_data, 
                    settings.organization_id
                )
                synced_count += 1
            
            print(f"Sync completed. Processed {synced_count} active orders.")
            
        except Exception as e:
            print(f"Critical error during sync: {e}")

if __name__ == "__main__":
    asyncio.run(force_sync_recent_orders())
