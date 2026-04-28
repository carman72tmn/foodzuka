"""
Модель событий вебхуков iiko
"""
from typing import Optional, Dict
from datetime import datetime
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel, Column, JSON


class IikoWebhookEvent(SQLModel, table=True):
    """
    Лог входящих вебхуков от iiko
    """
    __tablename__ = "iiko_webhook_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    event_type: str = Field(index=True, description="Тип события (DeliveryOrderUpdate, StopListUpdate...)")
    event_id: str = Field(index=True, description="correlationId или eventId из пакета")
    
    payload: Dict = Field(
        sa_column=Column(JSON),
        default={},
        description="Полный JSON тела запроса"
    )
    
    processed: bool = Field(default=False, description="Обработано ли успешно")
    error: Optional[str] = Field(default=None, description="Текст ошибки при обработке")
    
    created_at: datetime = Field(default_factory=utc_now)
