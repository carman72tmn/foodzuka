import asyncio
import httpx

async def test_transport_api(api_login, org_id):
    print(f"\\n=== Testing Transport API: {api_login} ===")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "https://api-ru.iiko.services/api/1/access_token",
                json={"apiLogin": api_login}
            )
            print(f"Token Status: {resp.status_code}")
            if resp.status_code != 200:
                print(resp.json())
                return
            
            token = resp.json().get("token")
            # Test employees
            resp_emp = await client.post(
                "https://api-ru.iiko.services/api/1/employees",
                headers={"Authorization": f"Bearer {token}"},
                json={"organizationIds": [org_id]}
            )
            print(f"/api/1/employees Status: {resp_emp.status_code}")
            if resp_emp.status_code == 200:
                print(f"Got {len(resp_emp.json().get('employees', []))} organizations data")
            else:
                print(resp_emp.text)
        except Exception as e:
            print(f"Error: {e}")

async def test_biz_api(login, password):
    print(f"\\n=== Testing iikoBiz API (POS Loyalty): {login} ===")
    async with httpx.AsyncClient() as client:
        try:
            # iiko.biz API auth
            resp = await client.get(f"https://iiko.biz:9900/api/0/auth/access_token?user_id={login}&user_secret={password}")
            print(f"Auth Status: {resp.status_code}")
            if resp.status_code == 200:
                token = resp.text.strip('"')
                print(f"Success token: {token[:10]}...")
            else:
                print(resp.text)
        except Exception as e:
            print(f"Error: {e}")

async def main():
    org_id = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
    
    # Check the keymyapp
    await test_transport_api("0ad3d7aa-aef1-456a-866c-f39e6ac1ba9e", org_id)
    
    # Check existing main API login from your DB just to contrast
    await test_transport_api("7ee66de3aee", org_id) # The one from DB was different, skipping
    
    # Check POS login
    await test_biz_api("fb17d496969545628d8f", "VoXn2fzEMGuY")

if __name__ == "__main__":
    asyncio.run(main())
