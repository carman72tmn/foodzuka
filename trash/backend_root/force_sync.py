import asyncio
import logging
import sys
import os

# Добавляем корень проекта в путь поиска модулей
sys.path.append("/app")

from app.core.database import SessionLocal
from app.services.iiko_sync_service import IikoSyncService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    sync_service = IikoSyncService()
    # SessionLocal в этом проекте возвращает синхронную сессию SQLModel
    # Нам нужно обернуть ее в контекстный менеджер или просто использовать
    session = SessionLocal()
    try:
        logger.info("Starting manual full order sync (48 hours)...")
        await sync_service.sync_orders(session, hours=48)
        logger.info("Manual sync completed.")
    except Exception as e:
        logger.error(f"Error during manual sync: {e}", exc_info=True)
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(main())
