"""
Модель Рассылок (Уведомлений для клиентов)
"""
from typing import Optional
from datetime import datetime
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel


class Mailing(SQLModel, table=True):
    """
    Таблица для управления массовыми рассылками (Telegram, СМС, Push)
    Содержит текст, фильтры аудитории и статусы выполнения
    """
    __tablename__ = "mailings"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Основная информация
    title: str = Field(max_length=255, description="Название рассылки (для админки)")
    message_text: str = Field(description="Текст сообщения")
    image_url: Optional[str] = Field(default=None, description="Картинка (URL) для сообщения")
    
    # Канал отправки
    channel: str = Field(
        default="telegram", max_length=50,
        description="telegram, sms, push"
    )
    
    # Фильтры аудитории (хранятся в JSON)
    audience_filters: Optional[str] = Field(
        default=None,
        description="JSON правила (напр. {'min_orders': 1, 'max_orders': 5, 'last_order_days_ago': 30})"
    )
    
    # Рассчитанная аудитория
    target_count: int = Field(default=0, description="Сколько клиентов попало в фильтр")
    sent_count: int = Field(default=0, description="Скольким успешно отправлено")
    error_count: int = Field(default=0, description="Количество ошибок отправки")
    
    # Планирование
    scheduled_at: Optional[datetime] = Field(default=None, description="Запланированное время отправки")
    
    # Статус: draft, scheduled, running, completed, cancelled
    status: str = Field(default="draft", max_length=20, index=True)
    
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
