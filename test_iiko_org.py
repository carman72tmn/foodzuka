import asyncio
import httpx
import json

async def test():
    api_login = "86dfd64bd15c42199b789edf6adcb289"
    org_id = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
    api_url = "https://api-ru.iiko.services"
    
    async with httpx.AsyncClient() as client:
        # 1. Get token
        resp = await client.post(f"{api_url}/api/1/access_token", json={"apiLogin": api_login})
        if resp.status_code != 200:
            print(f"Failed to get token: {resp.text}")
            return
        token = resp.json()["token"]
        print(f"Token obtained successfully")
        
        # 2. Get organizations
        resp = await client.get(f"{api_url}/api/1/organizations", headers={"Authorization": f"Bearer {token}"})
        if resp.status_code != 200:
            print(f"Failed to get organizations: {resp.text}")
        else:
            orgs = resp.json().get("organizations", [])
            print(f"Found {len(orgs)} organizations")
            found = False
            for o in orgs:
                if o["id"] == org_id:
                    print(f"MATCH FOUND: {o['name']} ({o['id']})")
                    found = True
            if not found:
                print(f"ORGAZINATION {org_id} NOT FOUND IN LIST!")
                if orgs:
                    print(f"First org in list: {orgs[0]['name']} ({orgs[0]['id']})")

        # 3. Try to get webhook settings for this org
        payload = {"organizationIds": [org_id]}
        resp = await client.post(f"{api_url}/api/1/webhooks/settings", headers={"Authorization": f"Bearer {token}"}, json=payload)
        print(f"Webhook settings response ({resp.status_code}): {resp.text}")

if __name__ == '__main__':
    asyncio.run(test())
