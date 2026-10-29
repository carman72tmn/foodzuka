"""
Модель для сбора отзывов гостей о заказах
"""
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel
from app.core.datetime_utils import utc_now

class OrderReview(SQLModel, table=True):
    """
    Отзывы гостей о заказах с оценкой (1-5) и текстовым комментарием.
    """
    __tablename__ = "order_reviews"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: Optional[int] = Field(default=None, foreign_key="orders.id", nullable=True, index=True)
    customer_id: Optional[int] = Field(default=None, foreign_key="customers.id", nullable=True, index=True)
    rating: int = Field(description="Оценка заказа от 1 до 5")
    comment: Optional[str] = Field(default=None, description="Текстовый отзыв гостя")
    
    created_at: datetime = Field(default_factory=utc_now)
