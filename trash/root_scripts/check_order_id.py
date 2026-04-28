import json
import urllib.request
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings

def get_token(api_login):
    url = "https://api-ru.iiko.services/api/1/access_token"
    payload = {"apiLogin": api_login}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())["token"]

def get_order_by_id(token, org_id, order_id):
    url = "https://api-ru.iiko.services/api/1/deliveries/by_id"
    payload = {
        "organizationIds": [org_id],
        "orderIds": [order_id]
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"Error fetching order by ID: {e}")
        return None

db = SessionLocal()
settings = db.query(IikoSettings).filter(IikoSettings.organization_id == "2704eeae-dc5f-4c9f-9b81-375c454dd5bd").first()
db.close()

if not settings:
    print("Settings not found")
    exit()

token = get_token(settings.api_login)
org_id = settings.organization_id

test_order_id = "17e5ac36-1cc1-4654-9de8-eaad7cd4709f"
print(f"Fetching specific order {test_order_id}...")
order_details = get_order_by_id(token, org_id, test_order_id)
if order_details:
    print(json.dumps(order_details, indent=2, ensure_ascii=False))
else:
    print("Failed to fetch order details")
