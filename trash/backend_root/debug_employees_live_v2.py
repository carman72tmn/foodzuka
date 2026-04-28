import httpx
import asyncio
import json

async def test_employees():
    api_url = "https://api-ru.iiko.services"
    api_login = "86dfd64bd15c42199b789edf6adcb289"
    org_id = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
    
    async with httpx.AsyncClient() as client:
        # 1. Get Token
        resp = await client.post(f"{api_url}/api/1/access_token", json={"apiLogin": api_login})
        token = resp.json().get("token")
        
        # Test /api/1/employees/info with singular organizationId
        print(f"\nTesting /api/1/employees/info with organizationId...")
        resp = await client.post(
            f"{api_url}/api/1/employees/info",
            headers={"Authorization": f"Bearer {token}"},
            json={"organizationId": org_id}
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("Success! /info works with singular organizationId")
            print(f"Sample info: {resp.text[:200]}...")
        else:
            print(f"Error: {resp.text}")

        # Test /api/1/employees/info with organizationIds
        print(f"\nTesting /api/1/employees/info with organizationIds...")
        resp = await client.post(
            f"{api_url}/api/1/employees/info",
            headers={"Authorization": f"Bearer {token}"},
            json={"organizationIds": [org_id]}
        )
        print(f"Status: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(test_employees())
