import sys
sys.path.append("/app")

from app.core.database import engine
from sqlmodel import Session, select
from app.models.iiko_settings import IikoSettings

def check_rev():
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if settings:
            print(f"Current Last Revision in DB: {settings.last_order_revision}")
        else:
            print("No settings found")

if __name__ == "__main__":
    check_rev()
