import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.append(os.getcwd())

from app.services.iiko_sync_service import IikoSyncService
from app.tasks.customer_tasks import sync_customers_batch
from app.core.database import SessionLocal

async def main():
    sync = IikoSyncService()
    
    print('1. Syncing employees and shifts (last 14 days)...')
    with SessionLocal() as session:
        try:
            await sync.sync_employees_full(session, days=14)
            print('Employees sync completed.')
        except Exception as e:
            print(f'Employees sync failed: {e}')

    print('\n2. Syncing orders (last 7 days) and ensuring customers exist...')
    with SessionLocal() as session:
        try:
            # hours=168 is 7 days
            await sync.sync_orders(session, hours=168)
            print('Orders sync completed.')
        except Exception as e:
            print(f'Orders sync failed: {e}')

    print('\n3. Triggering background batch sync for ALL customers from iiko...')
    try:
        # We call it via Celery to not block and let it run in background as a recurring task
        sync_customers_batch.apply_async(args=[0, 0, True])
        print('Batch customer sync task scheduled.')
    except Exception as e:
        print(f'Failed to schedule batch sync: {e}')

    print('\nForce sync script finished.')

if __name__ == '__main__':
    asyncio.run(main())
