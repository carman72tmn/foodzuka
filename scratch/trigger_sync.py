#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, '/app')

async def main():
    from app.services.iiko_sync_service import iiko_sync_service
    from app.core.database import SessionLocal
    
    with SessionLocal() as session:
        print("Синхронизация сотрудников (с обновлением имен)...")
        await iiko_sync_service.sync_employees_full(session)
        
        print("Синхронизация доставок...")
        await iiko_sync_service.sync_courier_deliveries(session)
    
    print("Готово.")

if __name__ == "__main__":
    asyncio.run(main())
