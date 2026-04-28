
import asyncio
import os
import sys

# Добавляем путь к backend
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.revenue_sync import revenue_sync_service
from app.core.database import engine
from sqlmodel import Session, select
from app.models.iiko_settings import IikoSettings

async def main():
    print("Testing revenue sync...")
    try:
        # Синхронизируем за неделю
        await revenue_sync_service.sync_period("week")
        print("Sync period completed.")
        
        # Проверяем результат в БД
        with Session(engine) as db:
            from app.models.olap_revenue import OlapRevenueRecord
            records = db.exec(select(OlapRevenueRecord).where(OlapRevenueRecord.period_type == "week")).all()
            print(f"Found {len(records)} records for week.")
            for r in records:
                print(f"Date: {r.business_date}, Terminal: {r.terminal_name}, Revenue: {r.revenue}, Cash: {r.cash_sum}, Card: {r.card_sum}")
                
    except Exception as e:
        print(f"Error during sync test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
