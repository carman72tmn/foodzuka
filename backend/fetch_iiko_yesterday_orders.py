import sys
import os
import asyncio
import traceback
sys.path.insert(0, '/app')

from datetime import datetime, timezone
from sqlmodel import select, Session
from app.core.database import engine
from app.models.iiko_settings import IikoSettings
from app.services.iiko_service import iiko_service

async def main():
    with Session(engine) as session:
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db or not settings_db.organization_id:
            print("Ошибка: Настройки iiko не найдены")
            return
            
        date_from = datetime(2026, 6, 20, 0, 0, 0)
        date_to = datetime(2026, 6, 21, 6, 0, 0)
        
        print(f"Запрос заказов из iiko Cloud с {date_from} по {date_to}...")
        try:
            orders = await iiko_service.get_orders_by_date(
                date_from=date_from,
                date_to=date_to,
                organization_id=settings_db.organization_id,
                api_login=settings_db.api_login,
                log_error=True
            )
            print(f"Получено {len(orders)} заказов из iiko Cloud")
            
            print(f"{'ExternalNum':<12} | {'Total':<10} | {'Status':<15} | {'Operator':<15} | {'Created'}")
            print("-" * 75)
            for o in sorted(orders, key=lambda x: (x.get("order", {}).get("whenCreated") or x.get("whenCreated") or "")):
                o_data = o.get("order") or o
                total = float(o_data.get("sum") or 0.0)
                status = o_data.get("status", "")
                op = o_data.get("operator", {})
                op_name = op.get("name") if isinstance(op, dict) else "None"
                created = o_data.get("whenCreated") or o_data.get("creationDate") or ""
                num = o_data.get("number") or o_data.get("externalNumber")
                
                num_str = str(num) if num is not None else ""
                status_str = str(status) if status is not None else ""
                op_name_str = str(op_name) if op_name is not None else "None"
                created_str = str(created) if created is not None else ""
                print(f"{num_str:<12} | {total:<10.2f} | {status_str:<15} | {op_name_str:<15} | {created_str}")
                
        except Exception as e:
            print("Ошибка при получении заказов:")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
