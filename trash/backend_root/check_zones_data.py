from app.core.database import SessionLocal
from app.models.company import DeliveryZone
from sqlmodel import select

with SessionLocal() as session:
    zones = session.exec(select(DeliveryZone)).all()
    print(f"Total zones: {len(zones)}")
    for z in zones:
        print(f"Zone: {z.name}, MinSum: {z.min_order_amount}, Time: {z.min_delivery_time}-{z.max_delivery_time}")
