from typing import Optional, Any, Dict
from datetime import datetime
from sqlmodel import Field, SQLModel, JSON, Column
from app.core.datetime_utils import utc_now

class VkMessage(SQLModel, table=True):
    """Модель для хранения истории сообщений ВК (входящих и исходящих)"""
    __tablename__ = "vk_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    vk_message_id: int = Field(index=True, description="ID сообщения в VK API")
    peer_id: int = Field(index=True, description="ID собеседника (пользователя или чата)")
    from_id: int = Field(index=True, description="ID отправителя (может быть ID группы)")
    text: str = Field(description="Текст сообщения")
    direction: str = Field(index=True, description="Направление: inbound (входящее) или outbound (исходящее)")
    payload: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON), description="Полный JSON сообщения")
    created_at: datetime = Field(
        default_factory=utc_now, 
        index=True,
        description="Дата и время сообщения"
    )
