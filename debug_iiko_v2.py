import asyncio
import os
import json
import httpx
from app.core.config import settings
from app.services.iiko_service import IikoService

async def debug_iiko_endpoints():
    print(f"DEBUG: IIKO_API_LOGIN from settings: {settings.IIKO_API_LOGIN}")
    print(f"DEBUG: IIKO_API_LOGIN from os.environ: {os.environ.get('IIKO_API_LOGIN')}")
    
    if not settings.IIKO_API_LOGIN:
        print("Settings IIKO_API_LOGIN is None, trying to force load .env...")
        from dotenv import load_dotenv
        load_dotenv("/app/.env")
        print(f"DEBUG: IIKO_API_LOGIN from os.environ after load_dotenv: {os.environ.get('IIKO_API_LOGIN')}")
        # We might need to re-instantiate settings if pydantic didn't pick it up
        from app.core.config import Settings
        force_settings = Settings()
        print(f"DEBUG: IIKO_API_LOGIN from force_settings: {force_settings.IIKO_API_LOGIN}")
        service = IikoService()
        service.api_login = force_settings.IIKO_API_LOGIN or os.environ.get('IIKO_API_LOGIN')
    else:
        service = IikoService()

    if not service.api_login:
        print("FAILED: No IIKO_API_LOGIN found even after forcing.")
        return

    token = await service._get_access_token()
    org_id = service.organization_id or os.environ.get('IIKO_ORGANIZATION_ID')
    
    print(f"Token: {token[:10]}...")
    print(f"Org ID: {org_id}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test payment_types
        print("\n--- Testing /api/1/payment_types ---")
        res = await client.post(
            f"{service.api_url}/api/1/payment_types",
            headers={"Authorization": f"Bearer {token}"},
            json={"organizationIds": [org_id]}
        )
        print(f"Status: {res.status_code}")
        # Try singular if plural fails or just see body
        print(f"Body: {json.dumps(res.json(), indent=2, ensure_ascii=False)}")
        
        # Test deliveries/by_id
        # We need a real order ID from the log or something.
        # But let's test the singular organizationId requirement.
        print("\n--- Testing /api/1/deliveries/by_id with organizationId (singular) ---")
        res = await client.post(
            f"{service.api_url}/api/1/deliveries/by_id",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "organizationId": org_id, 
                "organizationIds": [org_id], 
                "orderIds": ["04b9a1e9-a603-488c-b2b7-74d9cb258b1d"]
            }
        )
        print(f"Status: {res.status_code}")
        print(f"Body: {json.dumps(res.json(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(debug_iiko_endpoints())
