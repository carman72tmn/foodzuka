import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

# Add parent dir to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.iiko_sync_service import iiko_sync_service

async def main():
    # Тюмень UTC+5
    tz = timezone(timedelta(hours=5))
    now = datetime.now(tz)
    # Синхронизируем за последние 2 дня
    date_from = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    # До конца сегодняшнего дня
    date_to = now + timedelta(hours=1) # небольшой запас
    
    print(f"Force syncing deliveries from {date_from} to {date_to}...")
    await iiko_sync_service.sync_courier_deliveries_bg(date_from=date_from, date_to=date_to)
    print("Sync process finished. Check logs for details.")

if __name__ == "__main__":
    asyncio.run(main())
