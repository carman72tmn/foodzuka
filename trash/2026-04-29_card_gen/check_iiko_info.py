import asyncio
import json
from app.services.iiko_service import iiko_service

async def check_info():
    phone = "+79199325704"
    info = await iiko_service.get_customer_info(phone=phone)
    print(json.dumps(info, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(check_info())
