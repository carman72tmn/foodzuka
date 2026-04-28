"""
Модель промокодов

Типы промокодов (из документации Result.Rest):
1. Скидка в % 
2. Скидка фиксированная сумма
3. Подарки (подарочные товары)
4. Бесплатные товары
5. Воронки (сложные цепочки)

Условия:
- Многоразовый / одноразовый / одноразовый для клиента
- Не суммировать с другими скидками
- Только первый заказ
- Ограничения по товарам, сумме, времени, дням, платформам, филиалам
"""
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel
from sqlalchemy import Numeric


class PromoCode(SQLModel, table=True):
    """Промокод"""
    __tablename__ = "promo_codes"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Основные поля
    name: str = Field(max_length=255, description="Название промокода")
    code: str = Field(max_length=100, unique=True, index=True, description="Код")
    description: Optional[str] = Field(default=None, description="Описание")
    is_active: bool = Field(default=True, description="Активен")

    # Тип: percent, fixed, gift, free_items, funnel
    promo_type: str = Field(
        max_length=20, index=True,
        description="Тип: percent, fixed, gift, free_items, funnel"
    )

    # Значение скидки (для percent и fixed)
    discount_value: Decimal = Field(
        sa_type=Numeric(10, 2), default=0,
        description="Значение скидки (% или сумма)"
    )

    # Подарочные товары (для gift и free_items) — JSON массив product_id
    gift_product_ids: Optional[str] = Field(
        default=None,
        description="JSON массив ID подарочных товаров"
    )

    # Условия использования
    usage_type: str = Field(
        default="multi", max_length=20,
        description="multi (многоразовый), single (одноразовый), single_per_user (раз для клиента)"
    )
    max_uses: Optional[int] = Field(
        default=None,
        description="Максимальное количество использований (null = без лимита)"
    )
    current_uses: int = Field(default=0, description="Текущее количество использований")
    no_combine: bool = Field(
        default=False,
        description="Не суммировать с другими скидками"
    )
    first_order_only: bool = Field(
        default=False,
        description="Только для первого заказа"
    )

    # Ограничения по заказу
    min_order_amount: Optional[Decimal] = Field(
        sa_type=Numeric(10, 2), default=None,
        description="Минимальная сумма заказа"
    )
    min_items_count: Optional[int] = Field(
        default=None,
        description="Минимальное количество товаров в заказе"
    )

    # Обязательные товары (JSON массив product_id)
    required_product_ids: Optional[str] = Field(
        default=None,
        description="JSON массив ID обязательных товаров в заказе"
    )

    # Временные ограничения
    valid_from: Optional[date] = Field(default=None, description="Действует с")
    valid_until: Optional[date] = Field(default=None, description="Действует до")
    time_from: Optional[str] = Field(
        default=None, max_length=5,
        description="Время начала действия (HH:MM)"
    )
    time_until: Optional[str] = Field(
        default=None, max_length=5,
        description="Время окончания действия (HH:MM)"
    )
    valid_days: Optional[str] = Field(
        default=None, max_length=50,
        description="Дни недели (JSON: [1,2,3,4,5,6,7])"
    )

    # Ограничения по платформе и способу получения
    platforms: Optional[str] = Field(
        default=None, max_length=100,
        description="Платформы (JSON: ['web', 'telegram', 'app'])"
    )
    delivery_types: Optional[str] = Field(
        default=None, max_length=50,
        description="Способ получения (JSON: ['delivery', 'pickup'])"
    )

    # Привязка к филиалу
    branch_ids: Optional[str] = Field(
        default=None,
        description="JSON массив ID филиалов (null = все)"
    )

    # Метаданные
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
