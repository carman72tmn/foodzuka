"""
Модели для автоматических напоминаний неактивным клиентам
"""
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from app.core.datetime_utils import utc_now
from app.models.mailing_cascade import MailingCascade

class CustomerReminder(SQLModel, table=True):
    """
    Настройки автоматического напоминания на основе неактивности клиента (в днях).
    """
    __tablename__ = "customer_reminders"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, description="Название напоминания (для админки)")
    days_inactive: int = Field(index=True, description="Количество дней с момента последнего заказа для триггера")
    template: str = Field(description="Шаблон сообщения (с поддержкой шорткодов)")
    is_active: bool = Field(default=True, description="Активно ли напоминание")
    cascade_id: Optional[int] = Field(default=None, foreign_key="mailing_cascades.id", nullable=True)
    
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Связь с каскадом
    cascade: Optional[MailingCascade] = Relationship()

class SentReminder(SQLModel, table=True):
    """
    Журнал отправленных напоминаний клиентам, во избежание дублирования отправки по правилу.
    """
    __tablename__ = "sent_reminders"

    id: Optional[int] = Field(default=None, primary_key=True)
    reminder_id: int = Field(foreign_key="customer_reminders.id", index=True)
    customer_id: int = Field(foreign_key="customers.id", index=True)
    sent_at: datetime = Field(default_factory=utc_now)
