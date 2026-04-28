import hashlib
import httpx
import asyncio

async def test_iiko_resto():
    url = "https://dovezzuka-tyumen.iiko.it/resto/api"
    login = "superapi"
    password = "7r6zp53q"
    
    password_sha1 = hashlib.sha1(password.encode()).hexdigest()
    
    async with httpx.AsyncClient(verify=False, timeout=20.0) as client:
        # 1. Тест с SHA-1 (стандарт iiko)
        auth_url = f"{url}/auth"
        params = {"login": login, "pass": password_sha1}
        print(f"Testing with SHA-1 hash to {auth_url}...")
        try:
            resp = await client.get(auth_url, params=params)
            print(f"SHA-1 Response: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"SHA-1 Error: {e}")

        # 2. Тест без хеширования
        print(f"\nTesting with plain password to {auth_url}...")
        params_plain = {"login": login, "pass": password}
        try:
            resp = await client.get(auth_url, params=params_plain)
            print(f"Plain Response: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"Plain Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_iiko_resto())
