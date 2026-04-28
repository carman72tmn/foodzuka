import json
from app.core.database import SessionLocal
from app.models.iiko_webhook_event import IikoWebhookEvent

db = SessionLocal()
ev = db.query(IikoWebhookEvent).filter(IikoWebhookEvent.id == 737).first()
db.close()

if ev:
    payload = ev.payload
    print("OrgID from webhook:", payload.get("organizationId"))
    event_info = payload.get("eventInfo") or {}
    print("Order ID from webhook:", event_info.get("id"))
