import asyncio
import sys
import os
from sqlmodel import select

# Add /app to path if running inside docker
sys.path.append("/app")

from app.core.database import SessionLocal
from app.models.employee import CourierOrder

async def run():
    session = SessionLocal()
    try:
        orders = session.exec(select(CourierOrder).order_by(CourierOrder.id.desc()).limit(10)).all()
        print(f"Recent Courier Orders (Total {len(orders)} in last 10):")
        for o in orders:
            print(f"ID: {o.id} | Num: {o.order_num} | Zone: {o.delivery_zone} | Amt: {o.amount} | CourierID: {o.employee_id}")
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(run())
