рпродолжиimport json
import asyncio
from app.core.database import SessionLocal
from app.models.iiko_webhook_event import IikoWebhookEvent

async def main():
    db = SessionLocal()
    events = db.query(IikoWebhookEvent).filter(IikoWebhookEvent.event_type == "DeliveryOrderUpdate").order_by(IikoWebhookEvent.created_at.desc()).all()
    
    for event in events:
        info = event.payload.get("eventInfo", {})
        order = info.get("order", {})
        org_id = event.payload.get("organizationId")
        if order.get("orderType", {}).get("orderServiceType") == "DeliveryByCourier":
            print(f"Number: {order.get('number')}, ID: {info.get('id')}, OrgID: {org_id}")

if __name__ == "__main__":
    asyncio.run(main())
