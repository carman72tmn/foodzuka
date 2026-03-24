"""
Модель настроек интеграции с VK
"""
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel

class VkSettings(SQLModel, table=True):
    """Настройки подключения к VK Bot API"""
    __tablename__ = "vk_settings"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Основные настройки подключения
    vk_bot_token: Optional[str] = Field(
        default=None, max_length=500, description="Токен сообщества VK"
    )
    vk_confirmation_code: Optional[str] = Field(
        default=None, max_length=100, description="Код подтверждения Callback API"
    )
    vk_secret_key: Optional[str] = Field(
        default=None, max_length=255, description="Секретный ключ"
    )

    # Метаданные
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
