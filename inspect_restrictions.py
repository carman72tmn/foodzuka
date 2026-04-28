import asyncio
import logging
from app.services.iiko_service import iiko_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings

logging.basicConfig(level=logging.INFO)

async def main():
    print("Inspecting delivery restrictions...")
    with SessionLocal() as db:
        s = db.query(IikoSettings).first()
        if not s:
            print("No Iiko settings found")
            return
        
        try:
            res = await iiko_service.get_delivery_restrictions(
                api_login=s.api_login,
                organization_id=s.organization_id
            )
            print(f"Response type: {type(res)}")
            print(f"Response content: {res}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
