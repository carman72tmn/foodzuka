"""
Модели настроек интеграции с сервисом MAX
Официальный Bot API (platform-api2.max.ru) и Web Instance Bridge (pymax)
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
    
    bot_type: str = Field(default="MAX", description="Тип бота (MAX, Telegram, etc)")
    bot_name: str = Field(description="Название бота для идентификации")
    bot_token: str = Field(description="Токен доступа бота")
    bot_external_id: Optional[str] = Field(default=None, description="ID в системе MAX")
    bot_username: Optional[str] = Field(default=None, description="Username бота в MAX")
    bot_avatar: Optional[str] = Field(default=None, description="URL аватара бота")
    
    is_default_for_notifications: bool = Field(default=False, description="Использовать по умолчанию для системных уведомлений")
    webhook_url: Optional[str] = Field(default=None, description="Зарегистрированный URL вебхука")
    webhook_set: bool = Field(default=False, description="Статус активности подписки Webhook")
    webhook_updated_at: Optional[datetime] = Field(default=None, description="Дата последнего обновления Webhook")
    
    commands_json: Optional[str] = Field(default=None, description="JSON-список команд бота")
    welcome_message: Optional[str] = Field(default="Здравствуйте! Я официальный бот для уведомлений о ваших заказах.", description="Приветственное сообщение")
    request_contact_on_start: bool = Field(default=True, description="Запрашивать контакт при старте")
    
    is_active: bool = Field(default=True, description="Статус активации")

    # Связь с основными настройками
    settings: Optional["MaxSettings"] = Relationship(back_populates="bots")

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class MaxSettings(SQLModel, table=True):
    """Общие настройки подключения к сервису MAX"""
    __tablename__ = "max_settings"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Настройки API
    api_key: Optional[str] = Field(default=None, description="API Ключ / Токен MAX по умолчанию")
    api_secret: Optional[str] = Field(default=None, description="Секретный ключ MAX")
    base_url: str = Field(default="https://platform-api2.max.ru", description="Базовый URL официального API")
    
    # Настройки рассылок
    sender_name: Optional[str] = Field(default=None, description="Имя отправителя")
    default_template: Optional[str] = Field(default=None, description="Шаблон по умолчанию")
    
    is_active: bool = Field(default=False, description="Глобальный флаг активации интеграции")
    send_priority: str = Field(default="bot_first", description="Приоритет отправки: bot_first / bridge_first / both")
    auto_search_phone: bool = Field(default=True, description="Автопоиск MAX ID по номеру телефона клиента")

    # Список ботов
    bots: List[MaxBot] = Relationship(back_populates="settings")

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class MaxMessageLog(SQLModel, table=True):
    """Журнал отправки сообщений и уведомлений через MAX"""
    __tablename__ = "max_message_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    recipient: str = Field(description="Получатель: user_id, chat_id или номер телефона")
    customer_id: Optional[int] = Field(default=None, index=True, description="ID связанного клиента в CRM")
    channel_type: str = Field(default="bot", description="Канал доставки: bot или bridge")
    bot_id: Optional[int] = Field(default=None, description="ID бота, через которого отправлено")
    
    text: str = Field(description="Текст отправленного сообщения")
    format: str = Field(default="markdown", description="Форматирование: markdown, html или text")
    notify: bool = Field(default=True, description="Флаг push-уведомления")
    buttons_json: Optional[str] = Field(default=None, description="JSON-структура прикрепленных кнопок")
    
    status: str = Field(default="sent", description="Статус: sent, failed, pending")
    error_text: Optional[str] = Field(default=None, description="Текст ошибки при отправке")
    max_message_id: Optional[str] = Field(default=None, description="ID созданного сообщения в MAX")
    
    created_at: datetime = Field(default_factory=utc_now, index=True)


class MaxWebhookEvent(SQLModel, table=True):
    """Журнал входящих событий Webhook от мессенджера MAX"""
    __tablename__ = "max_webhook_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    bot_id: Optional[int] = Field(default=None, index=True, description="ID бота-получателя вебхука")
    event_type: str = Field(description="Тип события: bot_started, message_created, message_callback, contact_received")
    user_id: Optional[str] = Field(default=None, index=True, description="ID пользователя MAX")
    chat_id: Optional[str] = Field(default=None, description="ID чата MAX")
    payload_json: Optional[str] = Field(default=None, description="Полный JSON входящего события")
    
    created_at: datetime = Field(default_factory=utc_now, index=True)
