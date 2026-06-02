import asyncio
import sys
import os
from sqlmodel import Session, select, create_engine
from app.models.sync_log import SyncLog # Using any model just to have a reference if needed
# We need to manually import IikoSettings and system_logs logic if not in models
# But we can just use raw SQL for logs

# Add the current directory to sys.path to find 'app'
sys.path.append('/app')

from app.core.config import settings
from app.core.database import engine
from sqlalchemy import text

async def check_logs():
    with Session(engine) as session:
        # Query system_logs
        result = session.execute(text("SELECT created_at, level, message FROM system_logs WHERE message ILIKE '%Webhook%' ORDER BY id DESC LIMIT 20"))
        rows = result.all()
        print(f"Found {len(rows)} webhook-related logs:")
        for row in rows:
            print(f"{row[0]} | {row[1]} | {row[2]}")

if __name__ == "__main__":
    asyncio.run(check_logs())
