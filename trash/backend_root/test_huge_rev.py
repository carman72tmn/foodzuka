import asyncio
import os
import sys

# Добавляем путь к приложению
sys.path.append("/app")
from app.services.iiko_service import iiko_service

async def test_huge_revision():
    org_id = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
    huge_rev = 999999999
    print(f"Testing by_revision with huge startRevision={huge_rev}...")
    try:
        data = await iiko_service._request(
            "POST", "/api/1/deliveries/by_revision", 
            {
                "organizationIds": [org_id],
                "startRevision": huge_rev
            },
            organization_id=org_id,
            log_error=True
        )
        print(f"SUCCESS! Result: {data.get('maxRevision')}")
        print(f"Full response: {data}")
    except Exception as e:
        print(f"FAILED with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_huge_revision())
