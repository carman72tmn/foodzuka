from app.core.database import engine
from sqlalchemy import text
from sqlmodel import Session

with Session(engine) as session:
    res = session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'customers'")).fetchall()
    cols = [r[0] for r in res]
    print(cols)
