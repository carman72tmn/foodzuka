import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.iiko_sync_service import iiko_sync_service
from app.core.database import get_session

async def main():
    db = next(get_session())
    try:
        result = await iiko_sync_service.sync_employees_and_shifts(db)
        print("Sync result:", result)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
