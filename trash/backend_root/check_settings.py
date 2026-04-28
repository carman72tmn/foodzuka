
from app.core.database import Session, engine
from app.models.iiko_settings import IikoSettings
from sqlmodel import select
with Session(engine) as db:
    s = db.exec(select(IikoSettings)).first()
    if s:
        print(f"URL: {s.resto_url}")
        print(f"Login: {s.resto_login}")
        # print(f"Pass: {s.resto_password}") # Better not to print pass, but I need to know if it changed
        print(f"Pass set: {'Yes' if s.resto_password else 'No'}")
