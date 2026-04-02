from sqlalchemy import text
from app.core.database import engine
from sqlmodel import SQLModel

import app.models.iiko_settings
import app.models.bot_settings

if __name__ == "__main__":
    print("Creating any missing tables...")
    SQLModel.metadata.create_all(engine)

    print("Adding Resto columns if missing...")
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE iiko_settings ADD COLUMN resto_url VARCHAR(500)"))
        except Exception as e:
            print(f"URL exists: {e}")
        try:
            conn.execute(text("ALTER TABLE iiko_settings ADD COLUMN resto_login VARCHAR"))
        except Exception as e:
            print(f"Login exists: {e}")
        try:
            conn.execute(text("ALTER TABLE iiko_settings ADD COLUMN resto_password VARCHAR"))
        except Exception as e:
            print(f"Password exists: {e}")

    print("DB schema forced successfully.")
