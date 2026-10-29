"""
Модель настроек бота автокомментирования (первокоммент) ВКонтакте
"""
from typing import Optional, List
from datetime import datetime
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON

class VkFirstCommentSettings(SQLModel, table=True):
    """Настройки бота автокомментирования (первокоммент) ВК"""
    __tablename__ = "vk_first_comment_settings"

    id: Optional[int] = Field(default=None, primary_key=True)
    vk_bot_connection_id: int = Field(
        foreign_key="vk_bot_connections.id", 
        index=True, 
        unique=True,
        description="Ссылка на подключение бота ВК"
    )
    is_active: bool = Field(default=False, description="Активен ли бот")
    
    # Список вариантов комментариев
    comments: List[str] = Field(
        default=[],
        sa_column=Column(JSON),
        description="JSON-список вариантов комментариев"
    )

    # Детальные настройки и фильтры
    post_type_filter: str = Field(default="all", description="Фильтр постов: all, only_group, only_users")
    include_keywords: Optional[str] = Field(default=None, description="Ключевые слова, которые ДОЛЖНЫ быть в посте (через запятую)")
    exclude_keywords: Optional[str] = Field(default=None, description="Стоп-слова, которых НЕ ДОЛЖНО быть в посте (через запятую)")
    delay_seconds: int = Field(default=0, description="Задержка перед публикацией комментария в секундах")
    ignore_empty_text: bool = Field(default=False, description="Игнорировать посты без текста")
    exclude_reposts: bool = Field(default=False, description="Исключить репосты из комментирования")
    delay_min: int = Field(default=0, description="Минимальная задержка в секундах")
    delay_max: int = Field(default=0, description="Максимальная задержка в секундах")
    vk_bot_token: Optional[str] = Field(default=None, description="Индивидуальный ключ сообщества для бота")

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
