import httpx
import asyncio
import json

async def test_iiko():
    api_url = "https://api-ru.iiko.services"
    api_login = "86dfd64bd15c42199b789edf6adcb289"
    
    async with httpx.AsyncClient() as client:
        # 1. Get Token
        print(f"Step 1: Getting token for {api_login}...")
        try:
            resp = await client.post(
                f"{api_url}/api/1/access_token",
                json={"apiLogin": api_login}
            )
            print(f"Token status: {resp.status_code}")
            if resp.status_code != 200:
                print(f"Token error: {resp.text}")
                return
            
            token = resp.json().get("token")
            print(f"Token received: {token[:10]}...")
            
            # 2. Get Organizations
            print("\nStep 2: Getting organizations...")
            payload = {"organizationIds": [], "returnAdditionalInfo": True}
            resp = await client.post(
                f"{api_url}/api/1/organizations",
                headers={"Authorization": f"Bearer {token}"},
                json=payload
            )
            print(f"Orgs status: {resp.status_code}")
            print(f"Orgs response: {resp.text}")
            
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_iiko())
