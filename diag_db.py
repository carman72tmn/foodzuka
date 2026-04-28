from app.core.database import engine
from sqlmodel import Session, select
from app.models.iiko_settings import IikoSettings
from app.models.order import Order
from app.models.employee import CourierOrder, Employee
import json

with Session(engine) as session:
    settings = session.exec(select(IikoSettings)).first()
    print(f"--- SETTINGS ---")
    print(f"Address Format: {settings.address_format if settings else 'None'}")
    print(f"City: {settings.city_name if settings else 'None'}")
    print()
    
    print("--- LAST 5 ORDERS ---")
    orders = session.exec(select(Order).order_by(Order.created_at.desc()).limit(5)).all()
    for o in orders:
        print(f"ID: {o.id}, Num: {o.external_number}, Addr: {o.delivery_address}")
    
    print("\n--- LAST 5 COURIER ORDERS ---")
    c_orders = session.exec(select(CourierOrder).order_by(CourierOrder.created_at.desc()).limit(5)).all()
    for co in c_orders:
        emp = session.get(Employee, co.employee_id)
        print(f"ID: {co.id}, Num: {co.order_num}, Courier: {emp.name if emp else '?'}, Addr: {co.address}, Date: {co.actual_delivery_time}")

    print("\n--- COURIER ORDERS COUNT TODAY ---")
    from datetime import datetime, timezone, timedelta
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    count = session.exec(select(func.count(CourierOrder.id)).where(CourierOrder.created_at >= today)).one()
    print(f"Orders synced today (by created_at): {count}")
