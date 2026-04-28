
import asyncio
import logging
import sys
from app.core.database import SessionLocal
from app.services.iiko_sync_service import iiko_sync_service
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

# Set logging to see what's happening
root = logging.getLogger()
root.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
root.addHandler(handler)

async def main():
    with SessionLocal() as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print("Settings not found")
            return
        
        org_id = settings.organization_id
        print(f"--- DEBUG SYNC START ---")
        print(f"Org ID: {org_id}")
        print(f"Current last_order_revision: {settings.last_order_revision}")
        
        # 1. Test revision sync
        print("\n--- Testing Revision Sync ---")
        try:
            # We bypass the 20s check by clearing the cache
            iiko_sync_service._last_rev_sync = {} 
            await iiko_sync_service.sync_orders_by_revision(session, org_id)
        except Exception as e:
            print(f"Revision sync error: {e}")
            import traceback
            traceback.print_exc()

        # 2. Test getting max revision
        print("\n--- Checking Max Revision ---")
        from app.services.iiko_service import iiko_service
        try:
            max_rev = await iiko_service.get_max_revision(org_id, api_login=settings.api_login)
            print(f"Max Revision on server: {max_rev}")
        except Exception as e:
            print(f"Max revision error: {e}")

        # 3. Test webhooks update (optional, but good to know)
        print("\n--- Testing Webhooks Update ---")
        if settings.webhook_url and settings.webhook_auth_token:
             res = await iiko_service.update_webhooks(
                 webhook_url=settings.webhook_url,
                 auth_token=settings.webhook_auth_token,
                 organization_id=org_id,
                 api_login=settings.api_login
             )
             print(f"Webhooks update result: {res}")
        else:
             print("Webhook settings missing")

if __name__ == "__main__":
    asyncio.run(main())
