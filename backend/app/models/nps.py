"""
Модель NPS (Индекс потребительской лояльности / Отзывы)
"""
from typing import Optional
from datetime import datetime
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel


class NpsReview(SQLModel, table=True):
    """
    Таблица отзывов об заказах (NPS - Net Promoter Score)
    Отправляется пользователю через час после доставки
    """
    __tablename__ = "nps_reviews"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    order_id: int = Field(foreign_key="orders.id", index=True, description="ID заказа")
    customer_id: Optional[int] = Field(
        default=None, foreign_key="customers.id", index=True,
        description="ID клиента (если провязан)"
    )
    
    # Оценки (от 1 до 5)
    score: int = Field(ge=1, le=5, description="Общая оценка")
    kitchen_score: Optional[int] = Field(default=None, ge=1, le=5, description="Вкус еды")
    delivery_score: Optional[int] = Field(default=None, ge=1, le=5, description="Качество доставки")
    
    # Текст отзыва
    comment: Optional[str] = Field(default=None, description="Текстовый комментарий клиента")
    
    # Статус обработки
    is_processed: bool = Field(default=False, description="Обработан ли отзыв менеджером")
    manager_comment: Optional[str] = Field(default=None, description="Комментарий менеджера (результат решения)")
    
    created_at: datetime = Field(default_factory=utc_now)
    processed_at: Optional[datetime] = Field(default=None, description="Дата обработки")
