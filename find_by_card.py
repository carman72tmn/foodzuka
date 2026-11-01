import asyncio
from app.core.database import get_session
from app.services.iiko_service import iiko_service

async def test():
    db = next(get_session())
    card = "4329441241"
    print(f"Searching by cardNumber {card}...")
    
    payload = {
        "organizationId": iiko_service.organization_id,
        "type": "cardNumber",
        "cardNumber": card
    }
    
    try:
        res = await iiko_service._request("POST", "/api/1/loyalty/iiko/customer/info", payload)
        import json
        print("Result:")
        print(json.dumps(res, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, "response") and e.response is not None:
            print("Response body:", e.response.text)

asyncio.run(test())
