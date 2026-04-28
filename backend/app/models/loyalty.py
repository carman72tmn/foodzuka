"""
Модели программы лояльности
"""
from typing import Optional
from datetime import datetime
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel
from sqlalchemy import Numeric
from decimal import Decimal


class LoyaltyStatus(SQLModel, table=True):
    """
    Статусы программы лояльности (Золотой, Серебряный, Бронзовый и т.д.)

    - Статусные баллы только копятся, не списываются
    - max_discount: % от суммы заказа (1 бонус = 1 руб)
    - min_status_points: минимум статусных баллов для получения статуса
    """
    __tablename__ = "loyalty_statuses"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, description="Название статуса (напр. Золотой)")
    max_discount: Decimal = Field(
        sa_type=Numeric(5, 2), default=0,
        description="Максимальная скидка в % от суммы заказа"
    )
    min_status_points: int = Field(
        default=0,
        description="Минимум статусных баллов для получения этого статуса"
    )
    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class LoyaltyRule(SQLModel, table=True):
    """
    Правила начисления бонусов

    - Привязаны к конкретному статусу
    - Кэшбек — % начисления за каждый заказ
    - Срок жизни бонусных / статусных баллов в днях
    """
    __tablename__ = "loyalty_rules"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=255, description="Заголовок (для CRM)")
    loyalty_status_id: int = Field(
        foreign_key="loyalty_statuses.id", index=True,
        description="Привязка к статусу"
    )
    rule_type: str = Field(
        default="cashback", max_length=50,
        description="Тип правила"
    )
    cashback_percent: Decimal = Field(
        sa_type=Numeric(5, 2), default=0,
        description="Процент кэшбека за заказ"
    )
    bonus_ttl_days: int = Field(
        default=0,
        description="Срок жизни бонусных баллов (дни, 0 = бессрочно)"
    )
    status_ttl_days: int = Field(
        default=0,
        description="Срок жизни статусных баллов (дни, 0 = бессрочно)"
    )
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class LoyaltyTransaction(SQLModel, table=True):
    """
    Транзакции бонусных баллов (зачисление / списание)
    """
    __tablename__ = "loyalty_transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_type: str = Field(
        max_length=20, index=True,
        description="Тип: credit (зачисление) / debit (списание)"
    )
    phone: str = Field(max_length=50, index=True, description="Телефон клиента")
    points: Decimal = Field(
        sa_type=Numeric(10, 2),
        description="Количество баллов"
    )
    ttl_days: int = Field(
        default=0,
        description="Срок жизни баллов (дни, 0 = бессрочно)"
    )
    comment: Optional[str] = Field(default=None, max_length=500)
    order_id: Optional[int] = Field(
        default=None, index=True,
        description="ID заказа (если транзакция привязана к заказу)"
    )
    created_at: datetime = Field(default_factory=utc_now)
