from app.models.iiko_settings import IikoSettings
from app.core.database import Session, engine
from sqlmodel import select

with Session(engine) as session:
    settings_db = session.exec(select(IikoSettings)).first()
    print(f"Type: {type(settings_db)}")
    if settings_db:
        print(f"Has api_login: {hasattr(settings_db, 'api_login')}")
        print(f"Attributes: {dir(settings_db)}")
    else:
        print("No settings found in DB")
