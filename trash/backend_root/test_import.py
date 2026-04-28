
import asyncio
import logging
import os
import sys

# Ensure current directory is in path
sys.path.insert(0, os.getcwd())

try:
    from app.core.database import SessionLocal
    from app.services.iiko_sync_service import IikoSyncService
    print("Import successful")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    session = SessionLocal()
    try:
        logger.info("Starting manual hybrid sync...")
        sync_service = IikoSyncService()
        result = await sync_service.sync_menu(session)
        logger.info(f"Sync Result: {result}")
        
        # Verify a few products in DB
        from app.models.product import Product
        from sqlalchemy import select
        products = session.exec(select(Product).where(Product.price > 0).limit(5)).all()
        print("\nProducts with non-zero prices (Success!):")
        for p in products:
            print(f"- {p.name}: {p.price} rub")
            
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(main())
