import asyncio
import os
import json
import httpx
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv('.env')

API_URL = os.getenv('IIKO_API_URL', 'https://api-ru.iiko.services')
API_LOGIN = os.getenv('IIKO_API_LOGIN')
ORG_ID = os.getenv('IIKO_ORGANIZATION_ID')

async def get_token():
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_URL}/api/1/access_token", json={"apiLogin": API_LOGIN})
        resp.raise_for_status()
        return resp.json()["token"]

async def check_prices():
    token = await get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"--- Checking via Nomenclature (v1) ---")
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{API_URL}/api/1/nomenclature", headers=headers, json={"organizationId": ORG_ID})
        if resp.status_code == 200:
            data = resp.json()
            products = data.get("products", [])
            print(f"Found {len(products)} products in nomenclature.")
            # Check first 5 products with non-zero price and 5 with zero price
            zeros = [p for p in products if not p.get("sizePrices") or p["sizePrices"][0].get("price", {}).get("currentPrice", 0) == 0]
            non_zeros = [p for p in products if p.get("sizePrices") and p["sizePrices"][0].get("price", {}).get("currentPrice", 0) > 0]
            
            print(f"Products with 0 price: {len(zeros)}")
            print(f"Products with > 0 price: {len(non_zeros)}")
            
            if non_zeros:
                p = non_zeros[0]
                print(f"Example non-zero: {p['name']} - {p['sizePrices'][0]['price']['currentPrice']}")
            if zeros:
                p = zeros[0]
                print(f"Example zero: {p['name']} - {p['sizePrices'][0]['price']['currentPrice'] if p.get('sizePrices') else 'N/A'}")
        else:
            print(f"Nomenclature failed: {resp.status_code} {resp.text}")

    print(f"\n--- Checking External Menus (v2) ---")
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_URL}/api/2/menu", headers=headers, json={"organizationIds": [ORG_ID]})
        if resp.status_code == 200:
            menus = resp.json().get("externalMenus", [])
            print(f"Found {len(menus)} external menus.")
            for m in menus:
                print(f"Menu: {m.get('name')} (ID: {m.get('id')})")
                # Try to fetch this menu
                m_id = m.get('id')
                m_resp = await client.post(f"{API_URL}/api/2/menu/by_id", headers=headers, json={
                    "externalMenuId": m_id,
                    "organizationIds": [ORG_ID]
                })
                if m_resp.status_code == 200:
                    m_data = m_resp.json()
                    item_count = 0
                    price_zero_count = 0
                    for cat in m_data.get("itemCategories", []):
                        for item in cat.get("items", []):
                            item_count += 1
                            sp = item.get("sizePrices", [])
                            if sp:
                                price = sp[0].get("price", {}).get("currentPrice", 0)
                                if price == 0:
                                    price_zero_count += 1
                    print(f"  -> Items: {item_count}, Zeros: {price_zero_count}")
                else:
                    print(f"  -> Failed to fetch menu: {m_resp.status_code}")
        else:
            print(f"External menus failed: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    asyncio.run(check_prices())
