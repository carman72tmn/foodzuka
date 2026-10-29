from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class VkPostScheduler(SQLModel, table=True):
    __tablename__ = "vk_post_scheduler"

    id: Optional[int] = Field(default=None, primary_key=True)
    vk_bot_connection_id: int = Field(foreign_key="vk_bot_connections.id")
    type: str = Field(default="post")  # "post" или "story"
    content_text: Optional[str] = Field(default=None)
    media_url: Optional[str] = Field(default=None)  # Путь к картинке/видео
    publish_at: datetime  # Запланированное время публикации (naive/UTC в БД)
    status: str = Field(default="pending")  # "pending", "published", "failed"
    error_message: Optional[str] = Field(default=None)
    link_url: Optional[str] = Field(default=None)  # Ссылка для кнопки/стикера
    button_text: Optional[str] = Field(default=None)  # Текст на кнопке/стикере
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
