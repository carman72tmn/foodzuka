from sqlmodel import Session, create_engine, select
import os
from app.models.iiko_settings import IikoSettings
import json

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def check():
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if settings:
            print(json.dumps(settings.model_dump(), default=str))
        else:
            print("null")

if __name__ == "__main__":
    check()
