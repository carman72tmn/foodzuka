import json
import urllib.request
from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings

def get_token(api_login):
    url = "https://api-ru.iiko.services/api/1/access_token"
    payload = {"apiLogin": api_login}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())["token"]

def get_orgs(token):
    url = "https://api-ru.iiko.services/api/1/organizations"
    req = urllib.request.Request(url, data=json.dumps({}).encode(), headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

db = SessionLocal()
settings = db.query(IikoSettings).first()
db.close()

if not settings:
    print("Settings not found")
    exit()

token = get_token(settings.api_login)
orgs_data = get_orgs(token)

print(f"Found {len(orgs_data.get('organizations', []))} organizations:")
for org in orgs_data.get('organizations', []):
    print(f"ID: {org['id']}, Name: {org['name']}")
