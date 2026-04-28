import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

async def main():
    try:
        from app.services.iiko_sync_service import IikoSyncService
        from app.core.database import SessionLocal
        
        sync_service = IikoSyncService()
        session = SessionLocal()
        
        print(">>> Syncing customers...")
        # Syncing first 5 customers to test
        from app.models.customer import Customer
        from sqlmodel import select
        
        customers = session.exec(select(Customer).limit(5)).all()
        for customer in customers:
            print(f"Syncing customer: {customer.phone} ({customer.name})")
            await sync_service.sync_single_customer(session, customer)
            
        session.commit()
        print(">>> Customer sync test complete!")
    except Exception as e:
        print(f"!!! Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
