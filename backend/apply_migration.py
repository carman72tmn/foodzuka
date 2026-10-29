from app.core.database import engine
from sqlalchemy import text

def run():
    print("Connecting to database...")
    with engine.connect() as conn:
        print("Executing migration...")
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_data JSONB DEFAULT '{}'::jsonb;"))
        conn.commit()
        print("Migration applied successfully!")

if __name__ == "__main__":
    run()
