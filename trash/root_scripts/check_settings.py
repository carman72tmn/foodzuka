from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

with SessionLocal() as db:
    s = db.exec(select(IikoSettings)).first()
    if s:
        print(f"OrgID: {s.organization_id}")
        print(f"API Login: {s.api_login}")
    else:
        print("No settings found")
