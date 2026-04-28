import hashlib
import httpx
import asyncio

async def test_resto_connection(url, login, password):
    # Calculate SHA-1 hash of the password
    password_sha1 = hashlib.sha1(password.encode()).hexdigest()
    
    async with httpx.AsyncClient(verify=False, timeout=20.0) as client:
        # Attempt to login to get a token.
        base_url = url.rstrip('/')
        if not base_url.endswith('/api'):
            if base_url.endswith('/resto'):
                base_url = f"{base_url}/api"
            else:
                base_url = f"{base_url}/resto/api"
        
        auth_url = f"{base_url}/auth"
        params = {"login": login, "pass": password_sha1}
        
        print(f"DEBUG: Testing Resto connection to {auth_url} with login {login}")
        print(f"DEBUG: SHA1 hash: {password_sha1}")
        
        try:
            response = await client.get(auth_url, params=params)
            print(f"DEBUG: SHA1 response: {response.status_code} - {response.text}")
            
            # Try fallback without hashing
            params_plain = {"login": login, "pass": password}
            response_plain = await client.get(auth_url, params=params_plain)
            print(f"DEBUG: Plain response: {response_plain.status_code} - {response_plain.text}")
            
        except Exception as e:
            print(f"DEBUG: Error: {e}")

if __name__ == "__main__":
    url = "https://dovezzuka-tyumen.iiko.it/resto"
    login = "superapi"
    password = "7r6zp53q"
    asyncio.run(test_resto_connection(url, login, password))
