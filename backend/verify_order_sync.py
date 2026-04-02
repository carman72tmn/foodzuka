import asyncio
import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.core.database import engine
from app.services.iiko_sync_service import IikoSyncService
from app.models.order import Order, OrderStatus

async def verify():
    print("Starting order sync verification...")
    order_id = str(uuid.uuid4())
    
    # Mock iiko order data
    mock_data = {
        "id": order_id,
        "organizationId": "test-org-id",
        "terminalGroupId": "test-terminal-id",
        "creationStatus": "New",
        "order": {
            "id": order_id,
            "status": "New",
            "creationTime": (datetime.utcnow() - timedelta(hours=3)).isoformat() + "Z",
            "completeBefore": (datetime.utcnow()).isoformat() + "Z",
            "sum": 1500.0,
            "totalSum": 1200.0, # 300 discount
            "customer": {
                "name": "Test User",
                "phone": "+79998887766"
            },
            "deliveryPoint": {
                "address": {
                    "street": {"name": "Test Street"},
                    "house": "10",
                    "flat": "5"
                },
                "zone": {"name": "North Zone"}
            },
            "courierInfo": {
                "courier": {"name": "John Doe"}
            },
            "conveyorDetails": {
                "cashier": {"name": "Alice Admin"}
            },
            "orderType": {"name": "Delivery"},
            "payments": [
                {"paymentType": {"name": "Card", "kind": "Cashless"}, "sum": 1000.0},
                {"paymentType": {"name": "Bonus", "kind": "Loyalty"}, "sum": 200.0}
            ],
            "items": [
                {"productId": "prod-1", "name": "Pizza", "amount": 1, "price": 1000.0, "sum": 1000.0},
                {"productId": "prod-2", "name": "Coke", "amount": 2, "price": 250.0, "sum": 500.0}
            ],
            "discountsInfo": {
                "discounts": [
                    {"name": "Promo Code SAVE300", "sum": 300.0}
                ]
            }
        }
    }
    
    sync_service = IikoSyncService()
    
    with Session(engine) as session:
        await sync_service.process_iiko_order(session, mock_data, "test-org-id")
        
        # Verify
        order = session.exec(select(Order).where(Order.iiko_order_id == order_id)).first()
        
        if not order:
            print("FAILED: Order not found in database")
            return

        print(f"Order found: ID {order.id}")
        print(f"Total Amount: {order.total_amount} (Expected 1500.0)")
        print(f"Total with Discount: {order.total_with_discount} (Expected 1200.0)")
        print(f"Total Discount: {order.total_discount} (Expected 300.0)")
        print(f"Bonus Spent: {order.bonus_spent} (Expected 200.0)")
        print(f"Delivery Zone: {order.delivery_zone} (Expected North Zone)")
        print(f"Courier: {order.courier_name} (Expected John Doe)")
        print(f"Admin: {order.admin_name} (Expected Alice Admin)")
        print(f"Is On Time: {order.is_on_time} (Expected True - because 3 hours diff > 2 hours)")
        
        # Cleanup
        # session.delete(order)
        # session.commit()
        
    print("Verification completed successfully!")

if __name__ == "__main__":
    asyncio.run(verify())
