"""
Модели настроек интеграции с сервисом MAX
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel, Relationship

class MaxBot(SQLModel, table=True):
    """Настройки конкретного бота в системе MAX"""
    __tablename__ = "max_bots"

    id: Optional[int] = Field(default=None, primary_key=True)
    max_settings_id: int = Field(foreign_key="max_settings.id")
    
    bot_type: str = Field(description="Тип бота (Telegram, VK, etc)")
    bot_name: str = Field(description="Название бота для идентификации")
    bot_token: str = Field(description="Токен доступа")
    bot_external_id: Optional[str] = Field(default=None, description="ID в системе MAX")
    is_active: bool = Field(default=True, description="Статус активации")

    # Связь с основными настройками
    settings: "MaxSettings" = Relationship(back_populates="bots")

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

class MaxSettings(SQLModel, table=True):
    """Общие настройки подключения к сервису MAX"""
    __tablename__ = "max_settings"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Настройки API
    api_key: Optional[str] = Field(default=None, description="API Ключ MAX")
    api_secret: Optional[str] = Field(default=None, description="API Secret MAX")
    base_url: str = Field(default="https://api.max-service.ru/v1", description="Базовый URL API")
    
    # Настройки рассылок
    sender_name: Optional[str] = Field(default=None, description="Имя отправителя")
    default_template: Optional[str] = Field(default=None, description="Шаблон по умолчанию")
    
    is_active: bool = Field(default=False, description="Глобальный флаг активации")

    # Список ботов
    bots: List[MaxBot] = Relationship(back_populates="settings")

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
