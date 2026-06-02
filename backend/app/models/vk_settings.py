"""
Модель настроек интеграции с VK
"""
from typing import Optional
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel

class VkSettings(SQLModel, table=True):
    """Настройки подключения к VK Bot API"""
    __tablename__ = "vk_settings"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Основные настройки подключения
    vk_bot_token: Optional[str] = Field(
        default=None, description="Токен доступа для VK Bot API"
    )
    vk_group_id: Optional[int] = Field(
        default=None, description="ID группы VK"
    )
    vk_confirmation_code: Optional[str] = Field(
        default=None, description="Код подтверждения для Callback API"
    )
    vk_secret_key: Optional[str] = Field(
        default=None, description="Секретный ключ Callback API"
    )

    # Настройки парсера
    vk_parser_enabled: bool = Field(
        default=False, description="Включить автоматический парсинг сообщений для привязки клиентов"
    )
    vk_parser_phrase: Optional[str] = Field(
        default="здравствуйте! Ваш заказ {order_id} принят и мы приступили к его приготовлению",
        description="Шаблон фразы для поиска номера заказа"
    )
    vk_parser_last_scan_at: Optional[datetime] = Field(
        default=None, description="Дата последнего полного сканирования истории"
    )
    vk_parser_scan_status: Optional[dict] = Field(
        default=None, sa_column=Column(JSONB), description="Статус текущего/последнего сканирования (progress, total, matches)"
    )

    # Настройки уведомлений для клиентов
    vk_notification_settings: Optional[dict] = Field(
        default=None, sa_column=Column(JSONB), description="Настройки уведомлений для клиентов (статусы, шаблоны)"
    )

    # Метаданные
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
