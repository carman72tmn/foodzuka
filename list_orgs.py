import asyncio
import os
import json
import httpx
from datetime import datetime
import sys

async def main():
    # Настройки
    api_url = 'https://api-ru.iiko.services'
    
    if len(sys.argv) < 2:
        print("Usage: python3 list_orgs.py <api_login>")
        return
        
    login = sys.argv[1]
    print(f'Using login: {login}')
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Auth
        resp = await client.post(f'{api_url}/api/1/access_token', json={'apiLogin': login})
        token_data = resp.json()
        token = token_data.get('token')
        if not token:
            print(f"Failed to get token: {token_data}")
            return
            
        print(f'Token obtained: {token[:10]}...')
        
        # 2. List Orgs
        resp = await client.get(f'{api_url}/api/1/organizations', headers={'Authorization': f'Bearer {token}'})
        orgs = resp.json().get('organizations', [])
        print('\nAvailable Organizations:')
        for org in orgs:
            print(f"- {org.get('name')} (ID: {org.get('id')})")

if __name__ == '__main__':
    asyncio.run(main())
