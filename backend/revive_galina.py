import asyncio
from app.core.database import get_session
from app.services.iiko_service import iiko_service

async def test():
    db = next(get_session())
    phone = "+79292002279"
    payload = {
        "phone": phone,
        "name": "Галина",
        "surname": "Савельева",
        "sex": 2 # 2 = female
    }
    print(f"Calling create_or_update_customer for {phone}...")
    res = await iiko_service.create_or_update_customer(payload)
    print("Result:")
    import json
    print(json.dumps(res, indent=2, ensure_ascii=False))
    
    print("\nRequesting get_customer_info again...")
    res_info = await iiko_service.get_customer_info(phone)
    print("isDeleted status now:", res_info.get("isDeleted"))

asyncio.run(test())
