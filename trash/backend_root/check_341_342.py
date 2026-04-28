from sqlmodel import Session, select
from app.core.database import engine
from app.models.order import Order
from app.services.iiko_service import iiko_service
import json
import asyncio

async def test_max_revision():
    print("Testing safe get_max_revision...")
    max_rev = await iiko_service.get_max_revision()
    print(f"Resulting Max Revision: {max_rev}")

def check_orders():
    with Session(engine) as session:
        statement = select(Order).where(Order.external_number.in_([341, 342, '341', '342']))
        results = session.exec(statement).all()
        
        if not results:
            print("Orders 341 and 342 not found.")
            return
            
        for o in results:
            print(f"Order #{o.external_number} (ID: {o.id}):")
            print(f"  Status: {o.status}")
            print(f"  Is Paid: {o.is_paid}")
            print(f"  Payments: {o.payments_details}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_max_revision())
    check_orders()
