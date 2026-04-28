import asyncio
import os
import sys

# Добавляем путь к приложению для импортов
sys.path.append(os.getcwd())

from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

async def main():
    print("Testing iiko Cloud connection...")
    with SessionLocal() as session:
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db:
            print("No iiko settings in DB!")
            return
            
        api_login = settings_db.api_login
        org_id = settings_db.organization_id
        print(f"Using Org ID: {org_id}")
        
        try:
            # 1. Тест авторизации и организаций
            orgs = await iiko_service.get_organizations(api_login=api_login)
            print(f"Success! Found {len(orgs)} organizations.")
            for o in orgs:
                print(f" - {o.get('name')} (ID: {o.get('id')})")
            
            # 2. Тест активных заказов
            print("\nFetching active orders...")
            active = await iiko_service.get_active_orders(org_id, api_login=api_login)
            print(f"Found {len(active)} active orders.")
            
            # 3. Тест последних заказов за 24 часа
            from datetime import datetime, timedelta
            date_to = datetime.utcnow()
            date_from = date_to - timedelta(hours=24)
            print(f"\nFetching orders from {date_from} to {date_to}...")
            history = await iiko_service.get_orders_by_date(date_from, date_to, org_id, api_login=api_login)
            print(f"Found {len(history)} orders in history.")
            
        except Exception as e:
            print(f"Error during test: {e}")

if __name__ == "__main__":
    asyncio.run(main())
