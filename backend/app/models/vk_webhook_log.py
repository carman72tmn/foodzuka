from typing import Optional, Any, Dict
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, JSON, Column


class VkWebhookLog(SQLModel, table=True):
    """Модель для логов входящих событий от VK Callback API"""
    __tablename__ = "vk_webhook_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_type: str = Field(index=True, description="Тип события VK (например, message_new, confirmation)")
    payload: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON), description="Полный JSON события")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        index=True,
        description="Дата и время получения события"
    )
