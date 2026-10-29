"""
Модели данных для системы резервного копирования и ИИ-инструкций
"""
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field

class BackupSettings(SQLModel, table=True):
    """Настройки расписания и политик ротации резервных копий"""
    __tablename__ = "backup_settings"

    id: Optional[int] = Field(default=None, primary_key=True)
    auto_backup_enabled: bool = Field(default=True, description="Включено ли автоматическое создание бэкапов")
    schedule_interval: str = Field(default="daily_night", max_length=50, description="daily_night, every_12h, weekly, disabled")
    backup_type: str = Field(default="db_and_code", max_length=50, description="db_only, code_only, db_and_code, full_with_media")
    retention_days: int = Field(default=14, description="Удалять бэкапы старше указанного количества дней")
    max_backup_count: int = Field(default=10, description="Максимальное количество хранимых копий")
    min_disk_free_gb: float = Field(default=3.0, description="Минимальный порог свободного места на диске в ГБ")
    notify_admin_panel: bool = Field(default=True, description="Уведомлять в админке при создании/ошибке")
    last_backup_at: Optional[datetime] = None
    last_backup_status: Optional[str] = Field(default="idle", max_length=50)
    last_backup_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class AiPromptInstruction(SQLModel, table=True):
    """Единые системные инструкции и требования к работе ИИ-агентов"""
    __tablename__ = "ai_prompt_instructions"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(..., max_length=200, description="Название протокола или регламента")
    code: str = Field(..., max_length=100, unique=True, index=True, description="system_protocol, preflight_checklist, site_rules")
    content: str = Field(..., description="Полный текст промпта / регламента")
    is_active: bool = Field(default=True, description="Активен ли регламент")
    priority: int = Field(default=10, description="Приоритет отображения")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
