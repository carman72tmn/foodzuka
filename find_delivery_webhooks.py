import json
from app.core.database import SessionLocal
from app.models.iiko_webhook_event import IikoWebhookEvent

db = SessionLocal()
events = db.query(IikoWebhookEvent).order_by(IikoWebhookEvent.id.desc()).limit(100).all()
db.close()

for ev in events:
    payload = ev.payload
    order = payload.get("eventInfo", {}).get("order", {})
    order_type = order.get("orderType", {}).get("name", "")
    if "курьер" in order_type.lower() or "доставка" in order_type.lower():
        print(f"ID: {ev.id}, Type: {order_type}, Number: {order.get('number')}")
