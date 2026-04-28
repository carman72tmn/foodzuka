import json
from app.core.database import SessionLocal
from app.models.iiko_webhook_event import IikoWebhookEvent

db = SessionLocal()
ev = db.query(IikoWebhookEvent).order_by(IikoWebhookEvent.id.desc()).first()
db.close()

if ev:
    payload = ev.payload
    order = payload.get("eventInfo", {}).get("order", {})
    print("ORDER ADDRESS:", json.dumps(order.get("address"), indent=2, ensure_ascii=False))
    print("DELIVERY POINT:", json.dumps(order.get("deliveryPoint"), indent=2, ensure_ascii=False))
    print("CUSTOMER:", json.dumps(order.get("customer"), indent=2, ensure_ascii=False))
