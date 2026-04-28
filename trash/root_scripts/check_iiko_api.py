import asyncio
import os
import sys
import json
import httpx

# Добавляем путь к приложению
sys.path.append('/app')

from app.services.iiko_service import iiko_service
from app.core.database import Session, engine
from sqlmodel import select
from app.models.iiko_settings import IikoSettings

async def check_api():
    print("--- ТЕСТ IIKO API ---")
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("Ошибка: Настройки не найдены")
            return
        
        login = settings.api_login
        print(f"Используем логин: {login[:10]}...")
        
        try:
            # 1. Получаем ВСЕ организации
            token = await iiko_service._get_access_token(api_login=login)
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"{iiko_service.api_url}/api/1/organizations",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"organizationIds": [], "returnAdditionalInfo": True}
                )
                orgs_data = res.json()
                orgs = orgs_data.get("organizations", [])
                print(f"Найдено организаций: {len(orgs)}")
                
                org_ids = [o.get("id") for o in orgs]
                for o in orgs:
                    print(f" - {o.get('name')} (ID: {o.get('id')})")
                
                # 2. Пробуем получить типы оплаты для КАЖДОЙ организации отдельно
                for o_id in org_ids:
                    print(f"\nЗапрос типов оплаты для организации {o_id}...")
                    res = await client.post(
                        f"{iiko_service.api_url}/api/1/payment_types",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"organizationIds": [o_id]}
                    )
                    data = res.json()
                    p_types = data.get("paymentTypes", [])
                    total = 0
                    for group in p_types:
                        total += len(group.get("items", []))
                    print(f" Результат: найдено {total} типов оплаты")
                    
                    if total > 0:
                        for group in p_types:
                            for item in group.get("items", []):
                                print(f"  * {item.get('name')} ({item.get('id')})")

                # 3. Пробуем общий запрос по всем ID сразу
                print(f"\nОбщий запрос для всех {len(org_ids)} организаций...")
                res = await client.post(
                    f"{iiko_service.api_url}/api/1/payment_types",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"organizationIds": org_ids}
                )
                print(f" Общий результат: {len(res.json().get('paymentTypes', []))} групп")

        except Exception as e:
            print(f"Ошибка при выполнении: {e}")

if __name__ == "__main__":
    asyncio.run(check_api())
