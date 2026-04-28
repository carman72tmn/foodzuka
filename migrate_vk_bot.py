import os
import sys
from sqlmodel import Session, create_engine, text

# Добавляем путь к backend, чтобы импортировать конфиг если нужно
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from app.core.config import settings
    DATABASE_URL = settings.DATABASE_URL
except ImportError:
    # Если не получается импортировать, пробуем из .env напрямую
    from dotenv import load_dotenv
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL not found")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

with Session(engine) as session:
    print(f"Connecting to {DATABASE_URL.split('@')[-1]}")
    try:
        # Проверяем наличие колонок перед добавлением
        result = session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='vk_bot_subscriptions' AND column_name='active_start_hour'"))
        if not result.fetchone():
            session.execute(text("ALTER TABLE vk_bot_subscriptions ADD COLUMN active_start_hour INTEGER DEFAULT 0"))
            print("Added column active_start_hour")
        
        result = session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='vk_bot_subscriptions' AND column_name='active_end_hour'"))
        if not result.fetchone():
            session.execute(text("ALTER TABLE vk_bot_subscriptions ADD COLUMN active_end_hour INTEGER DEFAULT 23"))
            print("Added column active_end_hour")
            
        session.commit()
        print("Migration completed successfully")
    except Exception as e:
        session.rollback()
        print(f"Migration failed: {e}")
