import asyncio
import httpx
import xml.etree.ElementTree as ET

async def test_biz_employees(login, password):
    print(f"\\n=== Testing iikoBiz API: {login} ===")
    async with httpx.AsyncClient() as client:
        try:
            # 1. Auth token
            resp = await client.get(
                f"https://iiko.biz:9900/api/0/auth/access_token?user_id={login}&user_secret={password}",
                timeout=10.0
            )
            print(f"Auth Status: {resp.status_code}")
            if resp.status_code != 200:
                print(resp.text)
                return
            token = resp.text.strip('"')
            print(f"Token: {token[:10]}...")
            
            # 2. Get Employees (XML response usually for /resto/api)
            # wait, the repo uses /resto/api/employees. Let's try it on iiko.biz
            resp_emp = await client.get(
                f"https://iiko.biz:9900/resto/api/employees?access_token={token}",
                timeout=10.0
            )
            print(f"/resto/api/employees Status: {resp_emp.status_code}")
            print(f"Content-Type: {resp_emp.headers.get('content-type')}")
            content = resp_emp.text
            print(f"Response (first 500 chars): {content[:500]}")
            
        except Exception as e:
            print(f"Error: {e}")

async def main():
    await test_biz_employees("fb17d496969545628d8f", "VoXn2fzEMGuY")

if __name__ == "__main__":
    asyncio.run(main())
