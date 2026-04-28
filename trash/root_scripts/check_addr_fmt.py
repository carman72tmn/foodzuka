from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

with SessionLocal() as db:
    s = db.exec(select(IikoSettings)).first()
    print(f"Address Format: {s.address_format}")
