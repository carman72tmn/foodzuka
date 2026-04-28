from sqlmodel import Session, select, create_engine
from app.models.iiko_settings import IikoSettings
from app.core.config import settings

def check_db_settings():
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as session:
        statement = select(IikoSettings)
        results = session.exec(statement).all()
        print(f"Total settings records: {len(results)}")
        for idx, s in enumerate(results):
            print(f"--- Record {idx} (ID: {s.id}) ---")
            print(f"api_login: {s.api_login}")
            print(f"organization_id: {s.organization_id}")
            print(f"resto_login: {s.resto_login}")
            print(f"resto_password: {s.resto_password}")
            print(f"updated_at: {s.updated_at}")

if __name__ == "__main__":
    check_db_settings()
