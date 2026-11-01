
from app.core.database import engine
from sqlmodel import SQLModel
from app.models.backup_settings import BackupSettings, AiPromptInstruction

SQLModel.metadata.create_all(engine, tables=[BackupSettings.__table__, AiPromptInstruction.__table__])
print('BACKUP_TABLES_CREATED_OK')
