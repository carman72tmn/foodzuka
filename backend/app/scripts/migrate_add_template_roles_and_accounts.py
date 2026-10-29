from sqlalchemy import text
from app.core.database import engine

def migrate():
    print('Applying migration for target_roles and target_accounts in vk_templates...')
    with engine.connect() as conn:
        conn.execute(text('ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS target_roles TEXT DEFAULT NULL;'))
        conn.execute(text('ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS target_accounts TEXT DEFAULT NULL;'))
        conn.commit()
    print('Migration complete: target_roles and target_accounts added to vk_templates.')

if __name__ == '__main__':
    migrate()
