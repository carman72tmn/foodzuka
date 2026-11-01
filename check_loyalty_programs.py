import asyncio
from app.core.database import get_session
from app.services.iiko_service import iiko_service

async def test():
    db = next(get_session())
    print("Getting loyalty programs from iiko...")
    res = await iiko_service.get_loyalty_programs()
    print("Result:")
    import json
    print(json.dumps(res, indent=2, ensure_ascii=False))

asyncio.run(test())
