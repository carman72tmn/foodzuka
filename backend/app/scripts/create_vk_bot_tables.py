import sys
import os
from sqlalchemy import text

# Добавляем путь к backend, чтобы можно было импортировать модули приложения
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlmodel import SQLModel, Session, select
from app.core.database import engine
from app.models.vk_bot_connection import VkBotConnection
from app.models.vk_settings import VkSettings

def migrate_db():
    print("=== STARTING VK MULTIBOT MIGRATION ===")
    
    # 1. Создаем новые таблицы (vk_bot_connections)
    print("1. Creating vk_bot_connections table...")
    try:
        SQLModel.metadata.create_all(engine)
        print("Table vk_bot_connections created (if not existed).")
    except Exception as e:
        print(f"Error creating tables: {e}")
        return

    # 2. Добавляем колонку vk_group_id в существующие таблицы
    print("2. Adding vk_group_id column to existing tables...")
    alter_queries = [
        "ALTER TABLE vk_users ADD COLUMN IF NOT EXISTS vk_group_id BIGINT;",
        "ALTER TABLE vk_messages ADD COLUMN IF NOT EXISTS vk_group_id BIGINT;",
        "ALTER TABLE vk_webhook_logs ADD COLUMN IF NOT EXISTS vk_group_id BIGINT;"
    ]
    
    with engine.begin() as conn:
        for q in alter_queries:
            try:
                conn.execute(text(q))
                print(f"Executed: {q}")
            except Exception as e:
                print(f"Error executing query '{q}': {e}")

    # 3. Переносим существующие настройки из VkSettings в VkBotConnection
    print("3. Checking for existing VK settings to migrate...")
    with Session(engine) as session:
        try:
            # Проверяем, есть ли уже боты
            existing_bots = session.exec(select(VkBotConnection)).all()
            if not existing_bots:
                vk_settings = session.exec(select(VkSettings)).first()
                if vk_settings and vk_settings.vk_bot_token and vk_settings.vk_group_id:
                    print(f"Found existing bot with group_id {vk_settings.vk_group_id}. Migrating...")
                    main_bot = VkBotConnection(
                        name="Основной бот",
                        vk_bot_token=vk_settings.vk_bot_token,
                        vk_group_id=vk_settings.vk_group_id,
                        vk_confirmation_code=vk_settings.vk_confirmation_code,
                        vk_secret_key=vk_settings.vk_secret_key,
                        is_active=True,
                        is_main=True
                    )
                    session.add(main_bot)
                    session.commit()
                    print("Migration completed successfully: main bot created!")
                else:
                    print("No existing VK settings found or they are incomplete. Skipping migration of settings.")
            else:
                print(f"vk_bot_connections is not empty ({len(existing_bots)} bots found). Skipping migration of settings.")
        except Exception as e:
            print(f"Error during settings migration: {e}")
            session.rollback()
            
    print("=== VK MULTIBOT MIGRATION FINISHED ===")

if __name__ == "__main__":
    migrate_db()
