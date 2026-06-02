import asyncio
import sys
import os
from sqlmodel import Session, select, create_engine, text

# Add the current directory to sys.path to find 'app'
sys.path.append('/app')

from app.core.config import settings
from app.core.database import engine
from app.models.iiko_settings import IikoSettings

async def update_token():
    with Session(engine) as session:
        db_settings = session.exec(select(IikoSettings)).first()
        if not db_settings:
            print("No IikoSettings found.")
            return

        new_token = "9a471a278c00b4eeb0b46536706153cf"
        old_token = db_settings.webhook_auth_token
        db_settings.webhook_auth_token = new_token
        session.add(db_settings)
        
        # Log the change
        session.execute(text("INSERT INTO audit_logs (action, resource_type, resource_id, changes, message, created_at) VALUES ('UPDATE', 'IikoSettings', '1', '{}', 'Синхронизация токена вебхука с iiko Cloud', NOW())"))
        
        session.commit()
        print(f"Token updated successfully: {old_token} -> {new_token}")

if __name__ == "__main__":
    asyncio.run(update_token())
