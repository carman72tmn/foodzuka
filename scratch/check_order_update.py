import asyncio
import sys
import os
from sqlmodel import select

# Add /app to path if running inside docker
sys.path.append("/app")

from app.core.database import SessionLocal
from app.models.order import Order

async def run():
    session = SessionLocal()
    try:
        # Check order 73572
        order = session.exec(select(Order).where(Order.external_number == "73572")).first()
        if order:
            print(f"Order 73572: Courier: {order.courier_name} | ActualTime: {order.actual_time}")
        else:
            print("Order 73572 not found in Order table")
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(run())
