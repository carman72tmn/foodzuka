from sqlmodel import Session, text
from app.core.database import engine

with Session(engine) as s:
    s.exec(text("DELETE FROM shifts WHERE iiko_id LIKE 'olap_%'"))
    s.commit()
    print("Old OLAP shifts deleted")
