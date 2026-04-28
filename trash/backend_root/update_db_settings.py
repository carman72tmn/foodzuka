from sqlmodel import Session, select
from app.core.database import engine
from app.models.iiko_settings import IikoSettings
from datetime import datetime

def update_settings():
    with Session(engine) as session:
        s = session.exec(select(IikoSettings)).first()
        if not s:
            s = IikoSettings(
                api_login="86dfd64bd15c42199b789edf6adcb289",
                organization_id="2704eeae-dc5f-4c9f-9b81-375c454dd5bd",
                updated_at=datetime.utcnow()
            )
            session.add(s)
        else:
            s.api_login = "86dfd64bd15c42199b789edf6adcb289"
            s.organization_id = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
            s.updated_at = datetime.utcnow()
            session.add(s)
        
        session.commit()
        print(f"Updated settings: login={s.api_login}, org_id={s.organization_id}")

if __name__ == "__main__":
    update_settings()
