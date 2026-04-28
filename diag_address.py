from app.models.order import Order
from sqlmodel import Session, select
from app.core.database import engine
import json

with Session(engine) as session:
    # Latest 10 delivery orders
    statement = select(Order).where(Order.order_type == "Доставка").order_by(Order.id.desc()).limit(10)
    orders = session.exec(statement).all()
    
    print(f"{'ID':<10} | {'City':<15} | {'Street':<20} | {'House':<10} | {'Full Address'}")
    print("-" * 100)
    for o in orders:
        street = o.street if o.street else "---"
        house = o.house if o.house else "---"
        city = o.city if o.city else "---"
        print(f"{o.id:<5} | {o.external_number if o.external_number else '---':<10} | {str(o.iiko_order_id):<40} | {str(city):<10} | {o.delivery_address}")
