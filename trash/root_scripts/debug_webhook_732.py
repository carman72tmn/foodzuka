import json
from app.core.database import SessionLocal
from app.models.iiko_webhook_event import IikoWebhookEvent

db = SessionLocal()
ev = db.query(IikoWebhookEvent).filter(IikoWebhookEvent.id == 732).first()
db.close()

if ev:
    payload = ev.payload
    order = payload.get("eventInfo", {}).get("order", {})
    print("ORDER ID:", order.get("id"))
    print("ORDER ADDRESS:", json.dumps(order.get("address"), indent=2, ensure_ascii=False))
    print("DELIVERY POINT:", json.dumps(order.get("deliveryPoint"), indent=2, ensure_ascii=False))
    print("ORDER TYPE:", json.dumps(order.get("orderType"), indent=2, ensure_ascii=False))
