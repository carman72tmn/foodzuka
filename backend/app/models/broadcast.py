"""
Модель для массовых рассылок сообщений гостям
"""
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Column
from sqlalchemy import JSON
from app.core.datetime_utils import utc_now
from app.models.mailing_cascade import MailingCascade

class CustomerBroadcast(SQLModel, table=True):
    """
    Массовые рассылки клиентам с использованием фильтров аудитории и каскадов.
    """
    __tablename__ = "customer_broadcasts"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=255, description="Тема/Название рассылки")
    template_text: str = Field(description="Текст рассылки с поддержкой переменных")
    cascade_id: Optional[int] = Field(default=None, foreign_key="mailing_cascades.id", nullable=True)
    
    # Фильтры в JSON формате, например:
    # {
    #   "days_inactive_min": 10,
    #   "days_inactive_max": 30,
    #   "orders_count_min": 1,
    #   "total_spent_min": 1000,
    #   "segment": "Loyal"
    # }
    audience_filters: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="Фильтры целевой аудитории")
    
    status: str = Field(default="draft", max_length=20, index=True, description="Статус: draft, scheduled, processing, completed, cancelled")
    scheduled_at: Optional[datetime] = Field(default=None, description="Планируемое время автоматической отправки")
    
    # Метрики
    sent_count: int = Field(default=0, description="Количество отправленных сообщений")
    delivered_count: int = Field(default=0, description="Количество доставленных сообщений")
    read_count: int = Field(default=0, description="Количество прочитанных сообщений")
    error_count: int = Field(default=0, description="Количество сообщений с ошибками отправки")
    
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Связь с каскадом
    cascade: Optional[MailingCascade] = Relationship()
