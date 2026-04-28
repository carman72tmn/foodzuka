import json
from app.core.database import SessionLocal
from app.models.iiko_webhook_event import IikoWebhookEvent

db = SessionLocal()
ev = db.query(IikoWebhookEvent).filter(IikoWebhookEvent.id == 737).first()
db.close()

if ev:
    print(json.dumps(ev.payload.get("eventInfo"), indent=2, ensure_ascii=False))
