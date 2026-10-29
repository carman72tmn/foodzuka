"""
Модели для интеграции с сервисом рассылок Senler
"""
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel

class SenlerSettings(SQLModel, table=True):
    """Настройки интеграции с сервисом Senler"""
    __tablename__ = "senler_settings"

    id: Optional[int] = Field(default=None, primary_key=True)
    access_token: Optional[str] = Field(default=None, description="API access_token Senler")
    group_id: Optional[int] = Field(default=None, description="Идентификатор сообщества в Senler (group_id)")
    vk_group_id: Optional[int] = Field(default=None, description="ID группы ВКонтакте")
    secret_key: Optional[str] = Field(default=None, description="Секретный ключ для верификации Webhook")
    is_active: bool = Field(default=True, description="Статус активности интеграции")
    
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

class SenlerSubscriber(SQLModel, table=True):
    """Подписчики из сервиса Senler"""
    __tablename__ = "senler_subscribers"

    id: Optional[int] = Field(default=None, primary_key=True)
    vk_user_id: int = Field(unique=True, index=True, description="ID пользователя ВКонтакте")
    first_name: Optional[str] = Field(default=None, description="Имя")
    last_name: Optional[str] = Field(default=None, description="Фамилия")
    is_subscribed: bool = Field(default=True, description="Подписан ли в данный момент")
    subscribe_date: Optional[datetime] = Field(default=None, description="Дата подписки")
    unsubscribe_date: Optional[datetime] = Field(default=None, description="Дата отписки")
    
    # JSONB поля для хранения списков, UTM меток и переменных
    group_ids: Optional[List[int]] = Field(default=None, sa_column=Column(JSONB), description="Идентификаторы групп подписок Senler")
    utm_tags: Optional[Dict[str, str]] = Field(default=None, sa_column=Column(JSONB), description="UTM метки подписчика")
    user_vars: Optional[Dict[str, str]] = Field(default=None, sa_column=Column(JSONB), description="Дополнительные переменные пользователя")

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
