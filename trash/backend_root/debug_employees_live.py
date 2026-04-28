import httpx
import asyncio
import json

async def test_employees():
    api_url = "https://api-ru.iiko.services"
    api_login = "86dfd64bd15c42199b789edf6adcb289"
    org_id = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
    
    async with httpx.AsyncClient() as client:
        # 1. Get Token
        print(f"Step 1: Getting token...")
        resp = await client.post(f"{api_url}/api/1/access_token", json={"apiLogin": api_login})
        if resp.status_code != 200:
            print(f"Token error: {resp.status_code} {resp.text}")
            return
        token = resp.json().get("token")
        
        # 2. Test /api/1/employees (POST)
        print("\nStep 2: Testing /api/1/employees (POST)...")
        resp = await client.post(
            f"{api_url}/api/1/employees",
            headers={"Authorization": f"Bearer {token}"},
            json={"organizationIds": [org_id]}
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            emps = data.get("employees", [])
            if emps:
                items = emps[0].get("items", [])
                print(f"Success! Found {len(items)} employees.")
                if items:
                    print(f"Sample employee: {items[0].get('displayName')} (Roles: {items[0].get('roles')})")
            else:
                print("Success, but no employees returned for this org.")
        else:
            print(f"Error: {resp.text}")

        # 3. Test /api/1/employees/info (POST)
        print("\nStep 3: Testing /api/1/employees/info (POST)...")
        resp = await client.post(
            f"{api_url}/api/1/employees/info",
            headers={"Authorization": f"Bearer {token}"},
            json={"organizationIds": [org_id]}
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("Success! /info endpoint is available.")
        else:
            print(f"Error: {resp.text}")

        # 4. Test /api/1/employees/couriers (POST)
        print("\nStep 4: Testing /api/1/employees/couriers (POST)...")
        resp = await client.post(
            f"{api_url}/api/1/employees/couriers",
            headers={"Authorization": f"Bearer {token}"},
            json={"organizationIds": [org_id]}
        )
        print(f"Status: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(test_employees())
