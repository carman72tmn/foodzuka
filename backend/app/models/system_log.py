from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel


class SystemLog(SQLModel, table=True):
    """Модель для хранения системных ошибок и сбоев"""
    __tablename__ = "system_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    level: str = Field(index=True, description="Уровень лога: INFO, WARNING, ERROR, CRITICAL")
    module: str = Field(index=True, description="Модуль, где возникла ошибка")
    message: str = Field(description="Сообщение об ошибке")
    stack_trace: Optional[str] = Field(default=None, description="Стек вызовов для исключений")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
