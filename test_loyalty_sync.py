import asyncio
from app.services.iiko_sync_service import iiko_sync_service
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

async def main():
    session = SessionLocal()
    try:
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db:
            print("Error: iiko settings not found in DB")
            return

        api_login = settings_db.api_login
        org_id = settings_db.organization_id
        
        print(f"Using Org ID: {org_id}")
        
        print("Fetching data summary...")
        results = await asyncio.gather(
            iiko_sync_service.iiko.get_loyalty_programs(api_login, org_id),
            iiko_sync_service.iiko.get_loyalty_coupons_series(api_login, org_id),
            iiko_sync_service.iiko.get_loyalty_manual_conditions(api_login, org_id),
            iiko_sync_service.iiko.get_discount_types(api_login, org_id),
            return_exceptions=True
        )
        
        programs = results[0] if not isinstance(results[0], Exception) else {}
        coupons = results[1] if not isinstance(results[1], Exception) else {}
        manual = results[2] if not isinstance(results[2], Exception) else {}
        discounts = results[3] if not isinstance(results[3], Exception) else []
        
        prog_list = programs.get("Programs", []) if isinstance(programs, dict) else []
        coup_list = coupons.get("seriesWithNotActivatedCoupons", []) if isinstance(coupons, dict) else []
        man_list = manual.get("manualConditions", []) if isinstance(manual, dict) else []
        disc_list = discounts if isinstance(discounts, list) else []
        
        print(f"Programs count: {len(prog_list)}")
        for p in prog_list:
            print(f"  - Program: {p.get('name')} (ID: {p.get('id')})")
            campaigns = p.get("marketingCampaigns", [])
            print(f"    Campaigns count: {len(campaigns)}")
            for c in campaigns:
                print(f"      - Campaign: {c.get('name')} (ID: {c.get('id')})")
        
        print(f"Coupons count: {len(coup_list)}")
        print(f"Manual conditions count: {len(man_list)}")
        for m in man_list:
             print(f"  - Manual: {m.get('caption')} (ID: {m.get('id')})")
             
        print(f"Discounts count: {len(disc_list)}")
        # Печатаем первые 5 скидок для примера
        for d in disc_list[:5]:
            print(f"  - Discount: {d.get('name')} (ID: {d.get('id')})")
        
        print("\nStarting full sync...")
        res = await iiko_sync_service.sync_loyalty_items(session)
        print(f"Full Sync Result: {res}")
        
    except Exception as e:
        print(f"Test script error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(main())
