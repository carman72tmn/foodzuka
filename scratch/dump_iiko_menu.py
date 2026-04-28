import asyncio
import json
import os
import sys
from typing import Dict, Any

# Добавляем путь к /app, чтобы импортировать app.services
sys.path.append('/app')

from app.services.iiko_service import iiko_service

async def dump_menu():
    # Настройки из БД VPS
    api_login = "86dfd64bd15c42199b789edf6adcb289"
    org_id = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
    
    try:
        print(f"Fetching menu list for organization {org_id}...")
        menus = await iiko_service.get_external_menus(api_login=api_login, organization_id=org_id)
        print(f"Found {len(menus)} external menus.")
        
        if not menus:
            print("No external menus found.")
            return

        for menu in menus:
            m_id = menu.get('id')
            m_name = menu.get('name')
            print(f"Processing menu: {m_name} (ID: {m_id})")
            
            menu_data = await iiko_service.get_external_menu_by_id(str(m_id), api_login=api_login, organization_id=org_id)
            
            filename = f"/app/scratch/menu_{m_id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(menu_data, f, ensure_ascii=False, indent=2)
            print(f"Saved menu data to {filename}")
            
            items = menu_data.get('items', []) or menu_data.get('products', [])
            print(f"Total items in menu: {len(items)}")
            
            if items:
                # Ищем пример с размерами и модификаторами
                for item in items:
                    sizes = item.get('itemSizes', [])
                    mods = item.get('itemModifierGroups', [])
                    if len(sizes) > 1 or mods:
                        print(f"Example item: {item.get('name')} (ID: {item.get('itemId')})")
                        print(f"  Sizes: {len(sizes)}")
                        for s in sizes:
                            print(f"    - {s.get('sizeName')} (ID: {s.get('sizeId')}) Price: {s.get('prices')}")
                        print(f"  Modifier Groups: {len(mods)}")
                        for mg in mods:
                            print(f"    - {mg.get('name')} (ID: {mg.get('modifierGroupId')})")
                        break

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(dump_menu())
