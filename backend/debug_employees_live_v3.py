import httpx
import asyncio
import json

async def test_employees():
    api_url = "https://api-ru.iiko.services"
    api_login = "86dfd64bd15c42199b789edf6adcb289"
    org_id = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{api_url}/api/1/access_token", json={"apiLogin": api_login})
        token = resp.json().get("token")
        
        print(f"\nTesting /api/1/employees/couriers (POST)...")
        resp = await client.post(
            f"{api_url}/api/1/employees/couriers",
            headers={"Authorization": f"Bearer {token}"},
            json={"organizationIds": [org_id]}
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])

if __name__ == "__main__":
    asyncio.run(test_employees())
