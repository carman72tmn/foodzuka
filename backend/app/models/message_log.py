"""
Модели логов сообщений клиентам и сокращателя ссылок для отслеживания кликов (трекер переходов)
"""
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field, SQLModel, Relationship
from app.core.datetime_utils import utc_now

class CustomerMessageLog(SQLModel, table=True):
    """
    Журнал всех отправленных клиентам сообщений по всем каналам каскадов
    с отслеживанием статусов: отправлено, доставлено, прочитано, кликнуто, ошибка.
    """
    __tablename__ = "customer_message_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: Optional[int] = Field(default=None, foreign_key="customers.id", nullable=True, index=True)
    order_id: Optional[int] = Field(default=None, foreign_key="orders.id", nullable=True, index=True)
    broadcast_id: Optional[int] = Field(default=None, foreign_key="customer_broadcasts.id", nullable=True, index=True)
    reminder_id: Optional[int] = Field(default=None, foreign_key="customer_reminders.id", nullable=True, index=True)
    cascade_step_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("mailing_cascade_steps.id", ondelete="SET NULL"),
            nullable=True,
            index=True
        )
    )
    
    channel: str = Field(max_length=20, index=True, description="Канал: vk, telegram, max, sms")
    recipient_address: str = Field(max_length=100, description="Получатель (ID соцсети или номер телефона)")
    text: str = Field(description="Фактически отправленный текст сообщения")
    
    status: str = Field(default="pending", max_length=20, index=True, description="Статус: pending, sent, delivered, read, clicked, failed")
    message_id: Optional[str] = Field(default=None, max_length=100, index=True, description="Идентификатор сообщения от API соцсети")
    error_text: Optional[str] = Field(default=None, description="Текст ошибки при сбое")
    
    sent_at: Optional[datetime] = Field(default=None, description="Время фактической отправки бэкендом")
    delivered_at: Optional[datetime] = Field(default=None, description="Время получения уведомления о доставке")
    read_at: Optional[datetime] = Field(default=None, description="Время получения уведомления о прочтении")
    clicked_at: Optional[datetime] = Field(default=None, description="Время перехода по ссылке в сообщении")

class ShortLink(SQLModel, table=True):
    """
    Уникальные короткие ссылки для отслеживания переходов (кликов) гостей.
    """
    __tablename__ = "short_links"

    code: str = Field(primary_key=True, max_length=10, description="Короткий уникальный код ссылки")
    message_log_id: int = Field(foreign_key="customer_message_logs.id", index=True, description="Связь с логом отправки сообщения")
    original_url: str = Field(description="Оригинальный длинный URL")
    created_at: datetime = Field(default_factory=utc_now)
