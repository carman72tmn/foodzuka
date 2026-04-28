from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings

db = SessionLocal()
s = db.query(IikoSettings).first()
db.close()

if s:
    print(f"Address Format: {s.address_format}")
    print(f"City Name: {s.city_name}")
else:
    print("Settings not found")
