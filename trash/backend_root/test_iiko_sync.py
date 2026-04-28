import asyncio
from app.services.iiko_service import iiko_service
from app.core.database import engine
from sqlmodel import Session

async def main():
    print("Testing iiko connection...")
    orgs = await iiko_service.get_organizations()
    print("Organizations:")
    for o in orgs:
        print(f"- {o.get('id')} / {o.get('name')}")
        
    print("\nTerminal Groups:")
    tgs = await iiko_service.get_terminal_groups()
    for tg in tgs:
        print(f"- {tg.get('id')} / {tg.get('name')} / OrgId: {tg.get('organizationId')}")

if __name__ == "__main__":
    asyncio.run(main())
