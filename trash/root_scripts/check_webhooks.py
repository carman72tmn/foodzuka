from app.core.database import SessionLocal
from app.models.iiko_webhook_event import IikoWebhookEvent
from sqlmodel import select

with SessionLocal() as db:
    logs = db.exec(select(IikoWebhookEvent).order_by(IikoWebhookEvent.created_at.desc()).limit(10)).all()
    print("Recent webhooks:")
    for l in logs:
        print(f"Time: {l.created_at} | Event: {l.event_type} | Processed: {l.processed} | Error: {l.error}")
