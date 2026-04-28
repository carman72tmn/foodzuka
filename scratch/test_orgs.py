import asyncio
from app.services.iiko_service import iiko_service

async def test():
    orgs = await iiko_service.get_organizations()
    print(f"Organizations: {orgs}")

if __name__ == "__main__":
    asyncio.run(test())
