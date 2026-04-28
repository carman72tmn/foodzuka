from sqlalchemy import create_engine, text
from app.core.config import settings

def force_update_api_key():
    # Мы используем сырой SQL, чтобы не зависеть от моделей, если они меняются
    engine = create_engine(settings.DATABASE_URL)
    new_key = "86dfd64bd15c42199b789edf6adcb289"
    
    with engine.connect() as connection:
        # Проверяем наличие записей
        result = connection.execute(text("SELECT id, api_login FROM iiko_settings"))
        rows = result.fetchall()
        
        if not rows:
            print("No records found in iiko_settings. Please save settings in UI first.")
            return
            
        for row in rows:
            print(f"Updating record ID {row[0]}... Current key: {row[1]}")
            connection.execute(
                text("UPDATE iiko_settings SET api_login = :key, updated_at = NOW() WHERE id = :id"),
                {"key": new_key, "id": row[0]}
            )
        
        connection.commit()
        print(f"✓ Successfully updated API Key to: {new_key}")

if __name__ == "__main__":
    try:
        force_update_api_key()
    except Exception as e:
        print(f"Error: {e}")
