
import asyncio
import json
import os
import sys

# Добавляем путь к backend
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.iiko_service import iiko_service
from app.core.database import engine
from sqlmodel import Session, select
from app.models.iiko_settings import IikoSettings

async def main():
    print("Fetching OLAP columns...")
    with Session(engine) as db:
        s = db.exec(select(IikoSettings)).first()
        if not s:
            print("Settings not found")
            return
        
        try:
            # Запрос колонок для SALES
            response = await iiko_service._resto_request(
                "GET", "/v2/reports/olap/columns?reportType=SALES",
                resto_url=s.resto_url,
                resto_login=s.resto_login,
                resto_password=s.resto_password,
                organization_id=s.organization_id
            )
            
            # Сохраняем результат в файл для анализа
            with open("olap_columns_sales.json", "w", encoding="utf-8") as f:
                json.dump(response, f, indent=2, ensure_ascii=False)
            
            print("Columns saved to olap_columns_sales.json")
            
            # Проверяем наличие полей типа Terminal или CashRegister
            fields = [c.get("id") for c in response if c.get("id")]
            matches = [f for f in fields if "terminal" in f.lower() or "cash" in f.lower()]
            print(f"Potential terminal fields: {matches}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
