import asyncio
import logging
import sys

# Добавляем путь, чтобы Python видел модули backend
sys.path.append("/app")

from app.services.iiko_sync_service import iiko_sync_service
from app.core.database import SessionLocal

# Настраиваем логирование в stdout
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def main():
    print("Starting recipe and zones sync on VPS...")
    with SessionLocal() as session:
        result = await iiko_sync_service.sync_kitchen_recipes_and_zones(session)
        print("Recipe sync result:", result)

if __name__ == "__main__":
    asyncio.run(main())
