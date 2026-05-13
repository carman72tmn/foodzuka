
import asyncio
import os
import sys
import json

# Добавляем путь к приложению
sys.path.append("/app")

from app.services.iiko_service import IikoService
from app.core.config import settings

async def dump_customer(phone):
    iiko = IikoService()
    # Инициализация токена
    await iiko._get_access_token()
    
    print(f"Fetching info for {phone}...")
    info = await iiko.get_customer_info(phone)
    
    print("\n--- IIKO CUSTOMER INFO ---")
    print(json.dumps(info, indent=4, ensure_ascii=False))
    print("--------------------------\n")

if __name__ == "__main__":
    phone = "79220079019"
    if len(sys.argv) > 1:
        phone = sys.argv[1]
    asyncio.run(dump_customer(phone))
