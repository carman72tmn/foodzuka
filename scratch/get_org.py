from app.core.database import engine
from sqlalchemy import text
from sqlmodel import Session

with Session(engine) as session:
    res = session.execute(text("SELECT organization_id FROM iiko_settings LIMIT 1")).first()
    print(res[0] if res else "None")
