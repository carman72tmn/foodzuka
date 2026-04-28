import httpx
import json

def get_iiko_data():
    api_login = '86dfd64bd15c42199b789edf6adcb289'
    org_id = '2704eeae-dc5f-4c9f-9b81-375c454dd5bd'
    api_url = 'https://api-ru.iiko.services'
    
    try:
        # 1. Токен
        r = httpx.post(f"{api_url}/api/1/access_token", json={'apiLogin': api_login})
        r.raise_for_status()
        token = r.json()['token']
        
        # 2. Список меню
        r2 = httpx.post(
            f"{api_url}/api/2/menu", 
            headers={'Authorization': f'Bearer {token}'}, 
            json={'organizationIds': [org_id]}
        )
        r2.raise_for_status()
        data = r2.json()
        
        print(json.dumps(data, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'response'):
            print(f"Details: {e.response.text}")

if __name__ == "__main__":
    get_iiko_data()
