from sqlmodel import Session, select, desc
from datetime import datetime, timezone
from app.core.database import engine
from app.models import IikoWebhookEvent

def check_today():
    with Session(engine) as session:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        events = session.exec(
            select(IikoWebhookEvent)
            .where(IikoWebhookEvent.created_at >= today)
            .order_by(desc(IikoWebhookEvent.id))
        ).all()
        
        print(f"Found {len(events)} events since {today}")
        print(f"{'ID':<5} | {'Type':<25} | {'Created At'}")
        print("-" * 60)
        for e in events:
            print(f"{e.id:<5} | {e.event_type:<25} | {e.created_at}")

if __name__ == "__main__":
    check_today()
