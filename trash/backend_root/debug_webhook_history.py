import sys
import os
from sqlmodel import Session, select, create_engine
from app.models.iiko_webhook_event import IikoWebhookEvent
from app.models.iiko_settings import IikoSettings
from app.core.config import settings

def debug_webhook_history():
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as session:
        # Проверяем настройки iiko
        iiko_settings = session.exec(select(IikoSettings)).first()
        if iiko_settings:
            print("=== IIKO SETTINGS ===")
            print(f"Organization ID: {iiko_settings.organization_id}")
            print(f"Webhook URL: {iiko_settings.webhook_url}")
            print(f"Webhook Auth Token: {'Set' if iiko_settings.webhook_auth_token else 'Not Set'}")
        else:
            print("!!! No iiko settings found in DB !!!")

        # Проверяем последние события вебхуков
        events = session.exec(
            select(IikoWebhookEvent)
            .order_by(IikoWebhookEvent.created_at.desc())
            .limit(10)
        ).all()

        print("\n=== LAST 10 WEBHOOK EVENTS ===")
        if not events:
            print("No events found in iiko_webhook_events table.")
        else:
            for event in events:
                print(f"[{event.created_at}] Type: {event.event_type}, ID: {event.event_id}, Processed: {event.processed}")
                if event.error:
                    print(f"  Error/Details: {event.error}")

if __name__ == "__main__":
    # Добавляем путь к приложению
    sys.path.append(os.getcwd())
    try:
        debug_webhook_history()
    except Exception as e:
        print(f"Error during debugging: {e}")
