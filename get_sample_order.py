import asyncio
import os
import sys
import json
from datetime import datetime, timedelta

# Добавляем путь к приложению
sys.path.append('/app')

from app.services.iiko_service import iiko_service
from app.core.database import Session, engine
from sqlmodel import select
from app.models.iiko_settings import IikoSettings

async def get_sample_order():
    print("--- ПОЛУЧЕНИЕ ПРИМЕРА ЗАКАЗА ---")
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("Ошибка: Настройки не найдены")
            return
        
        now = datetime.utcnow()
        # Ищем заказы за последние 48 часов
        date_from = now - timedelta(days=2)
        date_to = now
        
        try:
            orders = await iiko_service.get_orders_by_date(
                date_from=date_from, 
                date_to=date_to,
                api_login=settings.api_login,
                organization_id=settings.organization_id
            )
            
            if not orders:
                print("Заказов не найдено за последние 48 часов.")
                return
            
            print(f"Найдено заказов: {len(orders)}")
            # Берем первый для анализа
            sample = orders[0]
            print("\nЛОГ ПЕРВОГО ЗАКАЗА (RAW JSON):")
            print(json.dumps(sample, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(get_sample_order())
