
import asyncio
import logging
from app.db.session import SessionLocal
from app.services.iiko_sync_service import IikoSyncService

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
        products = session.exec(select(Product).limit(10)).all()
        print("\nPrdouct Price Verification:")
        for p in products:
            print(f"- {p.name}: {p.price} rub (iiko_id: {p.iiko_id})")
            
    except Exception as e:
        logger.error(f"Sync failed: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(main())
