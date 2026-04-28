from app.core.database import SessionLocal
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

with SessionLocal() as db:
    settings = db.exec(select(IikoSettings)).first()
    if settings:
        print(f"ORG_ID={settings.organization_id}")
        print(f"LAST_REVISION={settings.last_order_revision}")
    else:
        print("NO_SETTINGS")
