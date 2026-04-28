import json
from app.core.database import SessionLocal
from app.models.iiko_webhook_event import IikoWebhookEvent

db = SessionLocal()
ev = db.query(IikoWebhookEvent).filter(IikoWebhookEvent.id == 737).first()
db.close()

if ev:
    payload = ev.payload
    order = payload.get("eventInfo", {}).get("order", {})
    print("ORDER ID:", order.get("id"))
    print("ORDER ADDRESS:", json.dumps(order.get("address"), indent=2, ensure_ascii=False))
    print("DELIVERY POINT:", json.dumps(order.get("deliveryPoint"), indent=2, ensure_ascii=False))
    # Print the whole order object but only the top level keys to see what's there
    print("ORDER KEYS:", list(order.keys()))
