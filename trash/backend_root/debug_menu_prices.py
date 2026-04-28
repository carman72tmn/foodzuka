
import httpx
import asyncio
import os
import json

async def debug_iiko_menu():
    api_url = "https://api-ru.iiko.services"
    api_login = "86dfd64bd15c42199b789edf6adcb289"
    org_id = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
    menu_id = "68484"
    
    # Get token
    resp = await httpx.AsyncClient().post(f"{api_url}/api/1/access_token", json={"apiLogin": api_login})
    token = resp.json().get("token")
    print(f"Token: {token[:10]}...")

    # Get menu list to see price categories
    resp_menu = await httpx.AsyncClient().post(
        f"{api_url}/api/2/menu",
        headers={"Authorization": f"Bearer {token}"},
        json={"organizationIds": [org_id]}
    )
    menus = resp_menu.json()
    print("Available Menus and Price Categories:")
    for m in menus.get("externalMenus", []):
        if str(m.get("id")) == menu_id:
            print(f"Target Menu {menu_id}: {m.get('name')}")
            print(f"Price Categories for this menu: {m.get('priceCategories')}")
    
    # List all available price categories for org
    print("\nGlobal Price Categories for Org:")
    for pc in menus.get("priceCategories", []):
        print(f"  - {pc.get('name')}: {pc.get('id')}")

    # Get actual menu data
    payload = {
        "externalMenuId": menu_id,
        "organizationIds": [org_id]
    }
    
    resp_v2 = await httpx.AsyncClient().post(
        f"{api_url}/api/2/menu/by_id",
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )
    
    if resp_v2.status_code != 200:
        print(f"v2 fetch failed: {resp_v2.status_code} {resp_v2.text}")
    else:
        menu_data = resp_v2.json()
        print(f"Fetched menu {menu_data.get('name')} via v2")
        found_any_v2_price = False
        count = 0
        for cat in menu_data.get("itemCategories", []):
            for item in cat.get("items", []):
                name = item.get("name")
                size_prices = item.get("sizePrices", [])
                print(f"Product (v2): {name}")
                for sp in size_prices:
                    p = sp.get("price", {}).get("currentPrice")
                    print(f"  Size: {sp.get('name')} - Price: {p}")
                    if p and p > 0:
                        found_any_v2_price = True
                count += 1
                if count > 3: break
            if count > 3: break
        if not found_any_v2_price:
            print("!!! WARNING: V2 PRICES ARE 0 !!!")

    # --- NOMENCLATURE V1 CHECK ---
    print("\n--- NOMENCLATURE (V1) CHECK ---")
    resp_v1 = await httpx.AsyncClient().post(
        f"{api_url}/api/1/nomenclature",
        headers={"Authorization": f"Bearer {token}"},
        json={"organizationId": org_id}
    )
    if resp_v1.status_code == 200:
        nom = resp_v1.json()
        print(f"Fetched nomenclature. Total products: {len(nom.get('products', []))}")
        count = 0
        for p_data in nom.get("products", []):
            name = p_data.get("name")
            size_prices = p_data.get("sizePrices", [])
            print(f"Product (v1): {name}")
            for sp in size_prices:
                p = sp.get("price", {}).get("currentPrice")
                print(f"  Size: {sp.get('sizeId')} - Price: {p}")
            count += 1
            if count > 5: break
    else:
        print(f"Error fetching nomenclature: {resp_v1.status_code}")

if __name__ == "__main__":
    asyncio.run(debug_iiko_menu())
