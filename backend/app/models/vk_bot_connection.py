"""
Модель для подключений ботов ВКонтакте (разные группы)
"""
from typing import Optional
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel

class VkBotConnection(SQLModel, table=True):
    """Настройки подключения к конкретному VK Bot API (группе)"""
    __tablename__ = "vk_bot_connections"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, description="Название подключения (например, Основной, Бот доставки)")
    vk_bot_token: str = Field(description="Токен доступа для VK Bot API")
    vk_user_token: Optional[str] = Field(default=None, description="Токен пользователя ВК (для динамической обложки)")
    vk_group_id: int = Field(unique=True, index=True, description="ID группы VK")
    vk_confirmation_code: Optional[str] = Field(default=None, description="Код подтверждения Callback API")
    vk_secret_key: Optional[str] = Field(default=None, description="Секретный ключ Callback API")
    is_active: bool = Field(default=True, description="Активен ли бот")
    is_main: bool = Field(default=False, description="Основной ли бот")
    use_longpoll: bool = Field(default=False, description="Использовать Long Poll API вместо Callback API")
    
    # Статус сканирования истории
    scan_status: Optional[dict] = Field(
        default=None, sa_column=Column(JSONB), description="Статус текущего/последнего сканирования"
    )
    last_scan_at: Optional[datetime] = Field(
        default=None, description="Дата последнего полного сканирования истории"
    )

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
