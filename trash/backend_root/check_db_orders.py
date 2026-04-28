import asyncio
import os
import sys
from sqlmodel import Session, select, create_engine
from datetime import datetime

# Добавляем путь к приложению
sys.path.append("/app")
from app.core.config import settings
from app.models.order import Order

engine = create_engine(settings.DATABASE_URL)

async def check_orders():
    org_id = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
    with Session(engine) as session:
        statement = select(Order).where(Order.organization_id == org_id).order_by(Order.created_at.desc()).limit(5)
        results = session.exec(statement).all()
        print(f"Total orders for org in DB: {len(results)}")
        for order in results:
            print(f"Order ID: {order.id}, Created At: {order.created_at}")

if __name__ == "__main__":
    asyncio.run(check_orders())
