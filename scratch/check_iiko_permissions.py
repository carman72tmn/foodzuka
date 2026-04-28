import asyncio
import httpx
import json
from datetime import datetime, timedelta

async def check():
    api_url = "https://api-ru.iiko.services"
    api_login = "86dfd64bd15c42199b789edf6adcb289"
    org_id = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
    
    print(f"--- IIKO API PERMISSION CHECK ---")
    print(f"Organization ID: {org_id}")
    print(f"API Login: {api_login[:8]}...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Get Access Token
        try:
            res = await client.post(f"{api_url}/api/1/access_token", json={"apiLogin": api_login})
            res.raise_for_status()
            token = res.json()["token"]
            print("[+] Access Token: SUCCESS")
        except Exception as e:
            print(f"[-] Access Token: FAILED - {e}")
            if hasattr(e, 'response'):
                print(f"    Response: {e.response.text}")
            return

        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Check Organizations
        try:
            res = await client.post(f"{api_url}/api/1/organizations", headers=headers, json={"organizationIds": [], "returnAdditionalInfo": True})
            if res.status_code == 200:
                print(f"[+] Organizations: SUCCESS ({len(res.json().get('organizations', []))} found)")
            else:
                print(f"[-] Organizations: FAILED ({res.status_code}) - {res.text}")
        except Exception as e:
            print(f"[-] Organizations: ERROR - {e}")

        # 3. Check Employees (Staff Management)
        try:
            res = await client.post(f"{api_url}/api/1/employees", headers=headers, json={"organizationIds": [org_id]})
            if res.status_code == 200:
                print(f"[+] Employees (/api/1/employees): SUCCESS")
            elif res.status_code == 403:
                print(f"[-] Employees (/api/1/employees): FORBIDDEN (No Staff Management rights)")
            else:
                print(f"[-] Employees (/api/1/employees): FAILED ({res.status_code}) - {res.text}")
        except Exception as e:
            print(f"[-] Employees: ERROR - {e}")

        # 4. Check Couriers (Fallback)
        try:
            res = await client.post(f"{api_url}/api/1/employees/couriers", headers=headers, json={"organizationIds": [org_id]})
            if res.status_code == 200:
                print(f"[+] Couriers (/api/1/employees/couriers): SUCCESS")
            else:
                print(f"[-] Couriers (/api/1/employees/couriers): FAILED ({res.status_code}) - {res.text}")
        except Exception as e:
            print(f"[-] Couriers: ERROR - {e}")

        # 5. Check Shifts (Attendance)
        now = datetime.now()
        date_from = (now - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00.000")
        date_to = now.strftime("%Y-%m-%d 23:59:59.000")
        try:
            res = await client.post(f"{api_url}/api/1/employees/shift", headers=headers, json={
                "organizationIds": [org_id],
                "dateFrom": date_from,
                "dateTo": date_to
            })
            if res.status_code == 200:
                print(f"[+] Shifts (/api/1/employees/shift): SUCCESS")
            elif res.status_code == 403:
                print(f"[-] Shifts (/api/1/employees/shift): FORBIDDEN (No Attendance rights)")
            else:
                print(f"[-] Shifts (/api/1/employees/shift): FAILED ({res.status_code}) - {res.text}")
        except Exception as e:
            print(f"[-] Shifts: ERROR - {e}")

        # 6. Check Schedules
        try:
            res = await client.post(f"{api_url}/api/1/employees/schedule", headers=headers, json={
                "organizationIds": [org_id],
                "from": date_from,
                "to": date_to
            })
            if res.status_code == 200:
                print(f"[+] Schedules (/api/1/employees/schedule): SUCCESS")
            else:
                print(f"[-] Schedules (/api/1/employees/schedule): FAILED ({res.status_code}) - {res.text}")
        except Exception as e:
            print(f"[-] Schedules: ERROR - {e}")

if __name__ == "__main__":
    asyncio.run(check())
