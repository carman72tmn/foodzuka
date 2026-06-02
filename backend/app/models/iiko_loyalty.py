"""
Модель для кэширования элементов лояльности из iiko Cloud
"""
from typing import Optional, Dict, Any
from datetime import datetime
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel, JSON, Column


class IikoLoyaltyItem(SQLModel, table=True):
    """
    Элемент лояльности iiko (программа, серия купонов, ручное условие, скидка)
    Используется для кэширования данных из iiko Cloud API для отображения в админке.
    """
    __tablename__ = "iiko_loyalty_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    iiko_id: str = Field(index=True, description="UUID элемента в iiko")
    name: str = Field(max_length=255, description="Название")
    type: str = Field(index=True, description="Тип: program, coupon_series, manual_condition, discount")
    description: Optional[str] = Field(default=None, sa_type=JSON, description="Описание или дополнительные текстовые поля")
    content: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON, description="Полный JSON ответа от iiko")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
