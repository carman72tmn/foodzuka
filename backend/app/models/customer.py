"""
Модели Клиентов (Покупателей) для системы Лояльности
"""
from typing import Optional, List, TYPE_CHECKING

from datetime import datetime, date, timezone
from enum import Enum
from decimal import Decimal
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Numeric
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from .order import Order



class Customer(SQLModel, table=True):
    """
    Таблица клиентов для профилей, истории заказов и программы лояльности
    """
    __tablename__ = "customers"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Основные данные
    phone: str = Field(max_length=20, unique=True, index=True, description="Телефон (основной идентификатор)")
    telegram_id: Optional[int] = Field(default=None, index=True, description="ID в Telegram если авторизован через бота")
    vk_user_id: Optional[int] = Field(default=None, index=True, description="ID в VK если аккаунт связан")
    name: Optional[str] = Field(default=None, max_length=255)
    surname: Optional[str] = Field(default=None, max_length=255)
    first_name: Optional[str] = Field(default=None, max_length=255, description="Имя (для совместимости)")
    last_name: Optional[str] = Field(default=None, max_length=255, description="Фамилия (для совместимости)")
    email: Optional[str] = Field(default=None, max_length=255)
    birthday: Optional[date] = Field(default=None, description="Дата рождения")
    
    # Данные лояльности
    loyalty_status_id: Optional[int] = Field(
        default=None, foreign_key="loyalty_statuses.id",
        description="Текущий статус лояльности (если есть)"
    )
    bonus_points: Decimal = Field(
        sa_type=Numeric(10, 2), default=0,
        description="Текущий баланс бонусных баллов (для оплаты)"
    )
    status_points: int = Field(
        default=0,
        description="Статусные баллы (для достижения уровней)"
    )
    
    # Данные из iiko (при необходимости)
    iiko_customer_id: Optional[str] = Field(default=None, max_length=100, index=True)
    uid: Optional[str] = Field(default=None, max_length=100, description="UID гостя в iiko")
    iiko_id: Optional[str] = Field(default=None, max_length=100, description="ID гостя в iiko")
    iiko_categories: Optional[List[str]] = Field(sa_type=JSONB, default=[], description="Категории гостя iiko (Laravel)")
    additional_phones: Optional[List[str]] = Field(sa_type=JSONB, default=[], description="Доп. телефоны гостя iiko (Laravel)")
    
    # Расширенные данные гостя
    city: Optional[str] = Field(default=None, max_length=255, description="Город гостя")
    addresses: Optional[str] = Field(default=None, description="Список адресов в формате JSON")
    notes: Optional[str] = Field(default=None, description="Заметки о госте")
    card_number: Optional[str] = Field(default=None, max_length=50, description="Номер карты лояльности (основной)")
    iiko_card_numbers: Optional[List[str]] = Field(sa_type=JSONB, default=[], description="Все номера карт гостя из iiko")
    gender: Optional[str] = Field(default="Не указан", max_length=50, description="Пол (Не указан / Мужской / Женский)")
    middle_name: Optional[str] = Field(default=None, max_length=255, description="Отчество")
    referrer: Optional[str] = Field(default=None, max_length=255, description="Рекомендатель")
    
    is_marketing_consented: bool = Field(default=True, description="Согласие на рекламную рассылку")
    is_system_notifications_consented: bool = Field(default=True, description="Согласие на системные уведомления")
    is_loyalty_messages_consented: bool = Field(default=True, description="Согласие на сообщения системы лояльности")
    is_synced_to_iiko_cards: bool = Field(default=False, description="Синхронизирован с iiko.cards")
    consent_status: Optional[str] = Field(default=None, max_length=50, description="Статус согласия (NotGiven, Given, Revoked)")
    marketing_consents: Optional[List[dict]] = Field(sa_type=JSONB, default=[], description="Детальные маркетинговые согласия iiko")
    
    # Расширенные данные гостя (дополнения по ТЗ)
    registration_date: Optional[datetime] = Field(default=None, description="Дата регистрации в IIKO")
    registration_source: Optional[str] = Field(default=None, max_length=255, description="Источник регистрации")
    registered_organization: Optional[str] = Field(default=None, max_length=255, description="Зарегистрировавшая организация")
    
    last_order_date: Optional[datetime] = Field(default=None, description="Дата последнего заказа")
    first_order_date: Optional[datetime] = Field(default=None, description="Дата самого первого заказа")
    last_olap_sync_at: Optional[datetime] = Field(default=None, description="Время последней OLAP синхронизации аналитики")
    
    # [NEW] Поля расширенной аналитики OLAP
    total_orders_count: int = Field(default=0, description="Общее количество заказов")
    total_orders_amount: Decimal = Field(sa_type=Numeric(12, 2), default=0, description="Общая сумма выкупленных заказов (LTV)")
    total_discount: Decimal = Field(sa_type=Numeric(12, 2), default=0, description="Общая сумма скидок")
    total_items: float = Field(default=0, description="Общее количество товаров в заказах")
    
    average_check: Decimal = Field(sa_type=Numeric(12, 2), default=0, description="Средний чек")
    frequency_days: float = Field(default=0, description="Средняя частота заказов в днях")
    days_since_last_order: Optional[int] = Field(default=None, description="Количество дней с последнего заказа")
    
    total_purchases_sum: Decimal = Field(sa_type=Numeric(12, 2), default=0, description="Общая сумма выкупа (Laravel)")
    
    # Новые поля для синхронизации с Laravel (по ТЗ пользователя)
    is_high_risk: bool = Field(default=False, description="Статус высокого риска (Laravel)")
    risk_reason: Optional[str] = Field(default=None, description="Причина высокого риска (Laravel)")
    iiko_notes: Optional[str] = Field(default=None, description="Заметки iiko (Laravel)")
    last_iiko_order_id: Optional[str] = Field(default=None, description="ID последнего заказа в iiko (Laravel)")
    last_order_id_iiko: Optional[str] = Field(default=None, description="ID последнего заказа в iiko (Cloud)")
    wallet_balances: Optional[List[dict]] = Field(sa_type=JSONB, default=[], description="Балансы кошельков гостя iiko")

    # Старые поля для обратной совместимости
    is_new_guest: bool = Field(default=True, description="Статус 'Новый гость'")
    iiko_comment: Optional[str] = Field(default=None, description="Комментарий из iiko")
    loyalty_categories: Optional[str] = Field(default=None, description="Категории гостя в формате JSON")
    
    # Флаги риска (дублирующие, но оставлены для совместимости, если используются в коде)
    high_risk_status: bool = Field(default=False, description="Статус высокого риска (legacy)")
    high_risk_reason: Optional[str] = Field(default=None, description="Причина высокого риска (legacy)")
    is_risk: bool = Field(default=False, description="Флаг риска (legacy)")
    # risk_reason уже определен выше
    
    is_blocked: bool = Field(default=False, description="Заблокирован ли клиент")
    
    orders_history: Optional[List] = Field(sa_type=JSONB, default=[], description="История заказов из iiko в формате JSON")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Отношения
    guest_addresses: List["GuestAddress"] = Relationship(back_populates="customer")
    guest_phones: List["GuestPhone"] = Relationship(back_populates="customer")
    bonus_transactions: List["BonusTransaction"] = Relationship(back_populates="customer")
    
    # Новые отношения для Laravel-совместимых таблиц
    addresses_history: List["ClientAddressHistory"] = Relationship(back_populates="client")
    bonuses_history: List["ClientBonusHistory"] = Relationship(back_populates="client")


class GuestPhone(SQLModel, table=True):
    """
    Таблица дополнительных телефонов гостя
    """
    __tablename__ = "guest_phones"

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id", index=True)
    phone: str = Field(max_length=20, index=True, description="Номер телефона")
    comment: Optional[str] = Field(default=None, description="Комментарий к номеру (напр. 'Рабочий')")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    customer: Customer = Relationship(back_populates="guest_phones")


class GuestAddress(SQLModel, table=True):
    """
    Таблица дополнительных адресов гостя (Legacy)
    """
    __tablename__ = "guest_addresses"

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id", index=True)
    address: str = Field(description="Полный адрес")
    is_main: bool = Field(default=False, description="Основной ли это адрес")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    customer: Customer = Relationship(back_populates="guest_addresses")


class ClientAddressHistory(SQLModel, table=True):
    """
    История адресов (Laravel-совместимая)
    """
    __tablename__ = "client_addresses_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="customers.id", index=True)
    city: str = Field(default="Тюмень", sa_column_kwargs={"server_default": "Тюмень"}, nullable=False, max_length=255)
    settlement: Optional[str] = Field(default="", max_length=255, description="Населенный пункт")
    street: str = Field(default="", sa_column_kwargs={"server_default": ""}, nullable=False, max_length=255)
    house: str = Field(default="-", sa_column_kwargs={"server_default": "-"}, nullable=False, max_length=50)
    entrance: Optional[str] = Field(default="", max_length=50)
    floor: Optional[str] = Field(default="", max_length=50)
    apartment: Optional[str] = Field(default="", max_length=50)
    doorphone: Optional[str] = Field(default="", max_length=50)
    address: str = Field(default="", description="Полный собранный адрес")
    last_used_at: Optional[datetime] = Field(default=None)
    orders_count: int = Field(default=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    client: Customer = Relationship(back_populates="addresses_history")


class BonusTransactionType(str, Enum):
    ACCRUAL = "accrual"   # Начисление
    DEDUCTION = "deduction" # Списание


class BonusTransaction(SQLModel, table=True):
    """
    История бонусных транзакций (Legacy)
    """
    __tablename__ = "bonus_transactions_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id", index=True)
    transaction_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    type: BonusTransactionType = Field(description="Тип транзакции (начисление/списание)")
    amount: Decimal = Field(sa_type=Numeric(10, 2), description="Сумма")
    order_id: Optional[str] = Field(default=None, description="ID заказа (если связано)")
    balance_after: Optional[Decimal] = Field(sa_type=Numeric(10, 2), default=None, description="Баланс после операции")
    comment: Optional[str] = Field(default=None, description="Комментарий к операции")
    external_id: Optional[str] = Field(default=None, unique=True, index=True, description="ID транзакции в iiko")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    customer: Customer = Relationship(back_populates="bonus_transactions")


class ClientBonusHistory(SQLModel, table=True):
    """
    История бонусов (Laravel-совместимая)
    """
    __tablename__ = "client_bonus_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="customers.id", index=True)
    type: str = Field(description="accrual/deduction")
    amount: Decimal = Field(sa_type=Numeric(10, 2))
    transaction_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    comment: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    client: Customer = Relationship(back_populates="bonuses_history")
