from sqlmodel import Session, select, desc
import json
from app.core.database import engine
from app.models import IikoWebhookEvent

def check_payload():
    with Session(engine) as session:
        event = session.exec(
            select(IikoWebhookEvent)
            .where(IikoWebhookEvent.event_type == "DeliveryOrderUpdate")
            .order_by(desc(IikoWebhookEvent.id))
            .limit(1)
        ).first()
        
        if event:
            print(f"Event ID: {event.id}")
            print(f"Event Type: {event.event_type}")
            print("Payload:")
            print(json.dumps(event.payload, indent=2, ensure_ascii=False))
        else:
            print("No event found")

if __name__ == "__main__":
    check_payload()
