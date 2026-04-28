import asyncio
import json
import logging
from app.services.iiko_service import iiko_service
from app.core.database import Session, engine
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

logging.basicConfig(level=logging.INFO)

async def debug_is_paid():
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("No settings found")
            return
            
        print(f"Fetching recent orders from Iiko for organization {settings.organization_id}...")
        try:
            # Get orders for today
            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)
            date_from = (now - timedelta(days=1)).strftime("%Y-%m-%d 00:00:00.000")
            date_to = (now + timedelta(days=1)).strftime("%Y-%m-%d 23:59:59.000")
            
            data = await iiko_service._request(
                "POST", "/api/1/deliveries/by_delivery_date_and_status", 
                {
                    "organizationIds": [settings.organization_id],
                    "deliveryDateFrom": date_from,
                    "deliveryDateTo": date_to,
                    "statuses": ["New", "WaitApproval", "Accepted", "CookingStarted", "CookingCompleted", "Waiting", "OnWay", "Delivered", "Closed", "Cancelled"]
                }
            )
            
            orders = data.get("orders", [])
            print(f"Found {len(orders)} orders")
            
            for o in orders[:5]: # Check first 5 orders
                order_id = o.get("id")
                status = o.get("status")
                num = o.get("number")
                proc_sum = o.get("processedPaymentsSum")
                payments = o.get("payments", [])
                
                print(f"\nOrder {num} ({order_id}):")
                print(f"  Status: {status}")
                print(f"  processedPaymentsSum: {proc_sum}")
                print(f"  Payments count: {len(payments)}")
                
                for p in payments:
                    pn = p.get("paymentType", {}).get("name") or p.get("paymentTypeKind") or p.get("kind")
                    psum = p.get("sum")
                    pext = p.get("isProcessedExternally") or p.get("processedExternally")
                    ppre = p.get("isPrepay") or p.get("prepay")
                    
                    print(f"    - {pn}: sum={psum}, isProcessedExternally={pext}, isPrepay={ppre}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_is_paid())
