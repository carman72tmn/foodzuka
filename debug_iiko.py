import asyncio
import os
import sys
import json
import httpx

# Добавляем путь к приложению для импорта
sys.path.append('/app')

from app.services.iiko_service import iiko_service
from app.core.database import Session, engine
from sqlmodel import select
from app.models.iiko_settings import IikoSettings

async def debug_iiko():
    print("--- ГЛУБОКАЯ ОТЛАДКА IIKO ---")
    
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("Ошибка: Настройки iiko не найдены в базе данных.")
            return
        
        api_login = settings.api_login or os.getenv("IIKO_API_LOGIN")
        org_id = settings.organization_id or os.getenv("IIKO_ORGANIZATION_ID")
        
        print(f"Используемый логин: {api_login[:5]}... (скрыто)")
        print(f"Используемый ID организации: {org_id}")
        
        try:
            # 1. Проверка авторизации
            token = await iiko_service._get_access_token(api_login=api_login)
            print("Аутентификация: Успешно (токен получен)")
            
            # 2. Получение списка ВСЕХ доступных организаций
            orgs_resp = await iiko_service.get_organizations(api_login=api_login)
            print(f"Доступные организации ({len(orgs_resp)}):")
            for o in orgs_resp:
                print(f" - {o.get('name')} (ID: {o.get('id')})")
                if str(o.get('id')) == str(org_id):
                    print("   ^--- СОВПАДАЕТ С ТЕКУЩИМИ НАСТРОЙКАМИ")
            
            # 3. Проверка типов оплаты для текущей организации
            print(f"\nЗапрос типов оплаты для {org_id}...")
            pt_resp = await iiko_service.get_payment_types(api_login=api_login, organization_id=org_id)
            print(f"Получено типов оплаты: {len(pt_resp)}")
            if pt_resp:
                for p in pt_resp:
                    print(f" - {p.get('name')} (Kind: {p.get('paymentTypeKind')})")
            else:
                # Попытка запроса без фильтра по организациям
                print("\nПопытка запроса типов оплаты БЕЗ фильтра по ID организации...")
                async with httpx.AsyncClient() as client:
                    res = await client.post(
                        f"{iiko_service.api_url}/api/1/payment_types",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"organizationIds": []}
                    )
                    data = res.json()
                    all_pts = data.get('paymentTypes', [])
                    print(f"Всего типов оплаты в системе (по всем орг): {len(all_pts)}")
                    for org_pts in all_pts:
                        o_id = org_pts.get('organizationId')
                        items = org_pts.get('items', [])
                        print(f" Org: {o_id} -> Типов оплаты: {len(items)}")
                        for item in items:
                            print(f"    - {item.get('name')} ({item.get('id')})")

        except Exception as e:
            print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_iiko())
