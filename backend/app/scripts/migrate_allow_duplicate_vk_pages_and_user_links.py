import logging
import sys
import os

# Добавляем путь к backend в sys.path для импорта модулей
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import text
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('migrate_allow_duplicate_vk_pages_and_user_links')

def migrate():
    logger.info('=== STARTING ALLOW DUPLICATE VK PAGES AND USER LINKS MIGRATION ===')
    
    statements = [
        # 1. Удаление уникального ограничения и уникального индекса для vk_user_id
        'ALTER TABLE vk_bot_accounts DROP CONSTRAINT IF EXISTS vk_bot_accounts_vk_user_id_key;',
        'DROP INDEX IF EXISTS ix_vk_bot_accounts_vk_user_id;',
        'CREATE INDEX IF NOT EXISTS ix_vk_bot_accounts_vk_user_id ON vk_bot_accounts (vk_user_id);',
        
        # 2. Добавление поля user_id со ссылкой на таблицу users
        'ALTER TABLE vk_bot_accounts ADD COLUMN IF NOT EXISTS user_id INTEGER DEFAULT NULL REFERENCES users(id) ON DELETE SET NULL;',
        'CREATE INDEX IF NOT EXISTS ix_vk_bot_accounts_user_id ON vk_bot_accounts (user_id);'
    ]
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            for statement in statements:
                logger.info(f'Executing: {statement}')
                conn.execute(text(statement))
            trans.commit()
            logger.info('=== MIGRATION COMPLETED SUCCESSFULLY ===')
        except Exception as e:
            trans.rollback()
            logger.error(f'Migration failed: {e}')
            raise e

if __name__ == '__main__':
    migrate()
