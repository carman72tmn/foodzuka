"""
Модель Акций (Маркетинговые кампании / Подарки)
"""
from typing import Optional
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlmodel import Field, SQLModel
from sqlalchemy import Numeric


class Action(SQLModel, table=True):
    """
    Таблица для Акций и Маркетинговых Кампаний.
    Похожа на промокоды, но срабатывает автоматически при выполнении условий.
    Например: "При заказе от 1500р ролл в подарок"
    """
    __tablename__ = "actions"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Основная информация
    name: str = Field(max_length=255, description="Название акции")
    description: Optional[str] = Field(default=None, description="Описание (для клиентов)")
    is_active: bool = Field(default=True, description="Статус активности")
    priority: int = Field(default=0, description="Приоритет (в случае конфликта акций)")
    image_url: Optional[str] = Field(default=None, description="Картинка (баннер) акции")
    
    # Тип акции
    action_type: str = Field(
        max_length=50, default="gift_product",
        description="Тип: gift_product (подарок), cart_discount (скидка на корзину), delivery_discount (скидка на доставку)"
    )
    
    # Условия
    min_order_amount: Optional[Decimal] = Field(
        sa_type=Numeric(10, 2), default=None,
        description="Срабатывает от суммы корзины"
    )
    
    # Результирующее действие
    gift_product_ids: Optional[str] = Field(
        default=None,
        description="JSON массив ID товаров-подарков (для gift_product)"
    )
    discount_value: Decimal = Field(
        sa_type=Numeric(10, 2), default=0,
        description="Значение скидки (% или фикс сумма)"
    )
    
    # Ограничения
    first_order_only: bool = Field(default=False, description="Только для первого заказа")
    no_combine: bool = Field(default=False, description="Не суммировать с промокодами")
    
    # Временные рамки (Опционально)
    valid_from: Optional[date] = Field(default=None)
    valid_until: Optional[date] = Field(default=None)
    valid_days: Optional[str] = Field(
        default=None, max_length=50,
        description="Дни недели JSON: [1,2,3...]"
    )
    time_from: Optional[str] = Field(default=None, max_length=5)
    time_until: Optional[str] = Field(default=None, max_length=5)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
