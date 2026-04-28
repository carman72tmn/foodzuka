from sqlmodel import Session, select, desc
from app.core.database import engine
from app.models import IikoWebhookEvent

def check_webhooks():
    with Session(engine) as session:
        # Последние 20 вебхуков
        events = session.exec(select(IikoWebhookEvent).order_by(desc(IikoWebhookEvent.id)).limit(20)).all()
        print(f"{'ID':<5} | {'Type':<25} | {'Processed':<10} | {'Error'}")
        print("-" * 60)
        for e in events:
            err = (e.error or "")[:30]
            print(f"{e.id:<5} | {e.event_type:<25} | {str(e.processed):<10} | {err}")

if __name__ == "__main__":
    check_webhooks()
