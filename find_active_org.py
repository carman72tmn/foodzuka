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

async def find_active_org():
    print("--- ПОИСК АКТИВНОЙ ОРГАНИЗАЦИИ ---")
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("Ошибка: Настройки не найдены")
            return
        
        login = settings.api_login
        print(f"Используем логин: {login[:10]}...")
        
        try:
            # 1. Получаем ВСЕ организации
            orgs = await iiko_service.get_organizations(api_login=login)
            print(f"Доступно организаций: {len(orgs)}")
            
            now = datetime.utcnow()
            date_from = now - timedelta(days=7)
            date_to = now
            
            for o in orgs:
                o_id = o.get("id")
                o_name = o.get("name")
                print(f"Проверка {o_name} ({o_id})...")
                
                try:
                    orders = await iiko_service.get_orders_by_date(
                        date_from=date_from,
                        date_to=date_to,
                        api_login=login,
                        organization_id=o_id
                    )
                    if orders:
                        print(f"  [!!!] НАЙДЕНО ЗАКАЗОВ: {len(orders)}")
                        # Анализируем поля первого заказа
                        sample = orders[0]
                        print("  Пример заказа (поля):", list(sample.keys()))
                        print(f"  externalNumber: {sample.get('externalNumber')}")
                        print(f"  orderNumber: {sample.get('orderNumber')}")
                    else:
                        print("  Заказов нет")
                except Exception as e:
                    print(f"  Ошибка при проверке этой организации: {e}")

        except Exception as e:
            print(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(find_active_org())
