import asyncio
import sys
from datetime import datetime, timedelta

sys.path.append("/app")

from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from app.models.employee import Employee
from app.services.iiko_service import iiko_service

async def run():
    session = SessionLocal()
    settings = session.query(IikoSettings).first()
    if not settings:
        print("No settings found")
        return
        
    date_from = datetime.now() - timedelta(days=3)
    date_to = datetime.now()
    org_id = settings.organization_id or ""
    
    # Загрузим всех сотрудников-курьеров для сравнения
    all_employees = session.query(Employee).all()
    couriers_db = []
    for emp in all_employees:
        is_c = emp.is_courier or any(k in (emp.role or "").lower() for k in ["курьер", "courier", "cur"])
        if is_c:
            couriers_db.append(emp.name)
    print("Курьеры в локальной БД:", couriers_db)
    
    try:
        print(f"\nFetching raw deliveries from Resto OLAP ({date_from} to {date_to})...")
        deliveries = await iiko_service.get_resto_detailed_deliveries(
            date_from=date_from,
            date_to=date_to,
            organization_id=org_id,
            resto_url=settings.resto_url,
            resto_login=settings.resto_login,
            resto_password=settings.resto_password
        )
        print(f"Successfully fetched {len(deliveries)} deliveries.")
        
        non_pickup = []
        for d in deliveries:
            c_info = d.get("courierInfo", {}) or {}
            c_name = c_info.get("courier", {}).get("name") or d.get("Delivery.Courier")
            if c_name and c_name.lower() != "самовывоз":
                non_pickup.append(d)
                
        print(f"Из них не самовывозов: {len(non_pickup)}")
        
        for idx, d in enumerate(non_pickup[:10]):
            c_info = d.get("courierInfo", {}) or {}
            c_name = c_info.get("courier", {}).get("name") or d.get("Delivery.Courier")
            c_id = c_info.get("courier", {}).get("id") or d.get("Delivery.Courier.Id")
            print(f"\nДоставка {idx+1}:")
            print(f"  ID/Номер: {d.get('id') or d.get('Delivery.Number')}")
            print(f"  Курьер в iiko: {c_name} (ID: {c_id})")
            print(f"  Время доставки: {d.get('whenDelivered') or d.get('Delivery.ActualTime')}")
            print(f"  Сумма: {d.get('sum') or d.get('fullSum')}")
            
            # Проверим, мапится ли курьер
            matched = False
            for c_db in couriers_db:
                if c_name and c_db.lower().strip() == c_name.lower().strip():
                    matched = True
                    print(f"  --> СОВПАДЕНИЕ НАЙДЕНО в БД: '{c_db}'")
                    break
            if not matched:
                print(f"  --> НЕТ СОВПАДЕНИЯ в БД для курьера '{c_name}'!")
                
    except Exception as e:
        print(f"Failed to fetch deliveries: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(run())
