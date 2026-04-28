from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings

db = SessionLocal()
try:
    s = db.query(IikoSettings).first()
    if s:
        print(f"Current address_format: {s.address_format}")
        print(f"Organization ID: {s.organization_id}")
        print(f"City Name: {s.city_name}")
        if s.address_format == "string" or s.address_format is None:
            s.address_format = "line1"
            db.add(s)
            db.commit()
            print("Updated address_format to 'line1'")
        else:
            print("Value is already correct or different from 'string'")
    else:
        print("Settings not found")
finally:
    db.close()
