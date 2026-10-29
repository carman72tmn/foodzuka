import os
import sys
from sqlmodel import Session, create_engine, text

# Мы запускаемся внутри папки backend, поэтому sys.path уже содержит нужные пути
sys.path.append(os.getcwd())

try:
    from app.core.config import settings
    DATABASE_URL = settings.DATABASE_URL
except ImportError:
    from dotenv import load_dotenv
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL not found")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

with Session(engine) as session:
    print(f"Connecting to DB...")
    try:
        # 1. Создаем Sequence
        session.execute(text("CREATE SEQUENCE IF NOT EXISTS bot_commands_id_seq START WITH 100;"))
        
        # 2. Создаем таблицу bot_commands
        session.execute(text("""
        CREATE TABLE IF NOT EXISTS bot_commands (
            id INTEGER DEFAULT nextval('bot_commands_id_seq') PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            trigger_phrase VARCHAR(255) NOT NULL,
            action_type VARCHAR(50) NOT NULL DEFAULT 'get_balance',
            channels JSONB NOT NULL DEFAULT '[]'::jsonb,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            response_text TEXT,
            request_phone_text TEXT,
            phone_not_found_text TEXT,
            register_confirm_text TEXT,
            register_success_text TEXT,
            balance_text TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
        );
        """))
        
        # Индекс для trigger_phrase
        session.execute(text("CREATE INDEX IF NOT EXISTS ix_bot_commands_trigger_phrase ON bot_commands (trigger_phrase);"))
        
        # 3. Создаем таблицу bot_user_states
        session.execute(text("""
        CREATE TABLE IF NOT EXISTS bot_user_states (
            id SERIAL PRIMARY KEY,
            messenger VARCHAR(50) NOT NULL,
            peer_id VARCHAR(100) NOT NULL,
            state VARCHAR(100) NOT NULL,
            command_id INTEGER,
            context_data JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
        );
        """))
        
        # Индексы для bot_user_states
        session.execute(text("CREATE INDEX IF NOT EXISTS ix_bot_user_states_messenger ON bot_user_states (messenger);"))
        session.execute(text("CREATE INDEX IF NOT EXISTS ix_bot_user_states_peer_id ON bot_user_states (peer_id);"))
        
        # 4. Вставляем дефолтную запись с ID = 100
        session.execute(text("""
        INSERT INTO bot_commands (
            id, name, trigger_phrase, action_type, channels, is_active, 
            request_phone_text, phone_not_found_text, register_confirm_text, 
            register_success_text, balance_text
        )
        SELECT 100, 'Мой бонусный баланс', 'Мой бонусный баланс', 'get_balance', '["vk", "telegram", "whatsapp", "max"]'::jsonb, TRUE, 
        'Ваш аккаунт не привязан к номеру телефона. Пожалуйста, отправьте ваш номер телефона (в формате 7**********) для привязки к карте гостя.', 
        'К сожалению, данный номер в базе не определен.', 
        'Хотите зарегистрироваться в нашей бонусной системе? Ответьте Да или Нет.', 
        'Вы успешно зарегистрированы в нашей бонусной системе! Ваш бонусный баланс: {balance} бонусов.', 
        'Ваш бонусный баланс: {balance} бонусов.'
        WHERE NOT EXISTS (SELECT 1 FROM bot_commands WHERE id = 100);
        """))

        # 4.5. Вставляем дефолтную запись для отвязки телефона с ID = 101
        session.execute(text("""
        INSERT INTO bot_commands (
            id, name, trigger_phrase, action_type, channels, is_active, 
            response_text
        )
        SELECT 101, 'Отвязать мой номер телефона от аккаунта', 'Отвязать мой номер телефона от аккаунта', 'unlink_phone', '["vk", "telegram", "whatsapp", "max"]'::jsonb, TRUE, 
        'Ваш номер телефона успешно отвязан от аккаунта. Для повторной привязки отправьте команду узнать баланс.'
        WHERE NOT EXISTS (SELECT 1 FROM bot_commands WHERE id = 101);
        """))
        
        # Синхронизируем Sequence
        session.execute(text("SELECT setval('bot_commands_id_seq', COALESCE((SELECT MAX(id) FROM bot_commands), 100));"))
        
        session.commit()
        print("Migration for Bot Commands completed successfully")
    except Exception as e:
        session.rollback()
        print(f"Migration failed: {e}")
        sys.exit(1)
