import asyncio
import sys
import os
from sqlmodel import Session, select, create_engine

# Add the current directory to sys.path to find 'app'
sys.path.append('/app')

from app.core.config import settings
from app.core.database import engine
from app.models.iiko_settings import IikoSettings
from app.services.iiko_service import iiko_service

async def check_current_settings():
    # Clear cooling endpoints to force a real request
    iiko_service._cooling_endpoints.clear()
    
    with Session(engine) as session:
        db_settings = session.exec(select(IikoSettings)).first()
        if not db_settings:
            print("No IikoSettings found in DB.")
            return

        print(f"Checking current iiko webhook settings for org {db_settings.organization_id}...")
        try:
            current = await iiko_service.get_webhook_settings(
                api_login=db_settings.api_login,
                organization_id=db_settings.organization_id
            )
            print(f"Current Iiko Cloud Settings: {current}")
        except Exception as e:
            print(f"Failed to get current settings: {e}")

if __name__ == "__main__":
    asyncio.run(check_current_settings())
