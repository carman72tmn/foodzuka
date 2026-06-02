import asyncio
import logging
from app.services.iiko_sync_service import iiko_sync_service
from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from sqlmodel import select
from app.models.iiko_settings import IikoSettings
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)

async def debug_courier_sync():
    session = SessionLocal()
    settings_db = session.exec(select(IikoSettings)).first()
    if not settings_db:
        print("Settings not found")
        return
        
    date_to = datetime.now()
    date_from = date_to - timedelta(days=3)
    
    print(f"Fetching deliveries from {date_from} to {date_to}...")
    deliveries = await iiko_service.get_resto_detailed_deliveries(
        date_from=date_from,
        date_to=date_to,
        organization_id=settings_db.organization_id
    )
    
    print(f"Fetched {len(deliveries)} deliveries.")
    if not deliveries:
        return
        
    print("Sample delivery data (couriers):")
    couriers_in_report = set()
    for d in deliveries[:20]:
        c_name = d.get("Delivery.Courier")
        c_id = d.get("Delivery.Courier.Id")
        couriers_in_report.add((c_name, c_id))
        print(f"  Name: {c_name}, ID: {c_id}")
        
    from app.models.employee import Employee
    employees = session.exec(select(Employee).where(Employee.is_courier == True)).all()
    print(f"Total couriers in DB: {len(employees)}")
    for emp in employees[:10]:
        print(f"  DB Courier: {emp.name}, IikoID: {emp.iiko_id}")

if __name__ == "__main__":
    asyncio.run(debug_courier_sync())
