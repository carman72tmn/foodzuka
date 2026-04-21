from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, JSON


class AuditLog(SQLModel, table=True):
    """Модель для аудита изменений (кто, когда и что изменил)"""
    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, index=True, description="ID пользователя, совершившего действие")
    action: str = Field(index=True, description="Действие: CREATE, UPDATE, DELETE")
    resource_type: str = Field(index=True, description="Тип ресурса: IikoSettings, Product и т.д.")
    resource_id: Optional[str] = Field(None, index=True, description="ID измененного ресурса")
    changes: Dict[str, Any] = Field(default_factory=dict, sa_type=JSON, description="JSON с изменениями (old vs new)")
    message: Optional[str] = Field(None, description="Дополнительное описание")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
