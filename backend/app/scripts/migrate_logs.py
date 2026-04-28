from sqlmodel import SQLModel, create_engine
from app.core.config import settings
from app.models.system_log import SystemLog
from app.models.audit_log import AuditLog

# Используем URL базы данных из настроек
engine = create_engine(settings.DATABASE_URL)

def migrate():
    print("Starting migration for logs tables...")
    # Создает только отсутствующие таблицы
    SQLModel.metadata.create_all(engine, tables=[
        SystemLog.__table__,
        AuditLog.__table__
    ])
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
