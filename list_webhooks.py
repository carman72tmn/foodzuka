import json
from app.core.database import SessionLocal
from app.models.iiko_webhook_event import IikoWebhookEvent

db = SessionLocal()
events = db.query(IikoWebhookEvent).order_by(IikoWebhookEvent.id.desc()).limit(20).all()
db.close()

for ev in events:
    print(f"ID: {ev.id}, Type: {ev.event_type}, HasOrder: {'order' in (ev.payload.get('eventInfo', {}) if isinstance(ev.payload, dict) else {})}")
