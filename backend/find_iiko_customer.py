import asyncio
from app.core.database import get_session
from app.services.iiko_service import iiko_service

async def test():
    db = next(get_session())
    phone = "+79292002279"
    print(f"Requesting get_customer_info for {phone}...")
    res_info = await iiko_service.get_customer_info(phone)
    print("get_customer_info result:")
    import json
    print(json.dumps(res_info, indent=2, ensure_ascii=False))
    
    print(f"\nRequesting get_customers search for {phone}...")
    res_list = await iiko_service.get_customers(phone=phone)
    print("get_customers result:")
    print(json.dumps(res_list, indent=2, ensure_ascii=False))

asyncio.run(test())
