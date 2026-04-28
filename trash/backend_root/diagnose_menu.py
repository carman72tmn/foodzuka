import asyncio
import os
import sys
import json

# Absolute path for the container
sys.path.insert(0, '/app')

async def diagnose():
    try:
        from app.db.session import SessionLocal
        from app.models.iiko_settings import IikoSettings
        from app.services.iiko_service import iiko_service
        from sqlmodel import select
        
        s = SessionLocal()
        settings = s.exec(select(IikoSettings)).first()
        if not settings or not settings.external_menu_id:
            print("No external menu ID configured.")
            return

        print(f"Fetching menu {settings.external_menu_id}...")
        menu = await iiko_service.get_external_menu_by_id(
            settings.external_menu_id, 
            api_login=settings.api_login, 
            organization_id=settings.organization_id
        )
        
        print(f"Main keys: {list(menu.keys())}")
        
        # Check for products
        prods = menu.get("items") or menu.get("products") or []
        print(f"Root products found: {len(prods)}")
        
        # Check inside categories
        cats = menu.get("itemCategories") or menu.get("groups") or []
        if cats:
            print(f"Categories count: {len(cats)}")
            cat_items = cats[0].get("items") or cats[0].get("products") or []
            print(f"First category items count: {len(cat_items)}")
            if cat_items:
                print(f"First item type: {type(cat_items[0])}")
                print(f"First item: {json.dumps(cat_items[0], indent=2, ensure_ascii=False)[:300]}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(diagnose())
