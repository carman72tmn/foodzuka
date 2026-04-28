import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.iiko_sync_service import iiko_sync_service
from app.core.database import engine
from sqlmodel import Session

async def main():
    print("🚀 Запуск синхронизации активных заказов...")
    try:
        with Session(engine) as session:
            result = await iiko_sync_service.sync_orders(session, hours=720)
            print(f"✅ Синхронизация завершена успешно!")
            print(f"📊 Результат: {result}")
    except Exception as e:
        print(f"❌ Ошибка при синхронизации: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
