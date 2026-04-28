"""
Модели заказа и позиций заказа
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Numeric, Column, JSON


class OrderStatus(str, Enum):
    """Статусы заказа"""
    new = "new"  # Новый заказ
    unconfirmed = "unconfirmed"  # Не подтвержден
    confirmed = "confirmed"  # Подтвержден
    preparing = "preparing"  # В подготовке
    cooking = "cooking"  # Готовится
    ready = "ready"  # Готов
    ready_for_pickup = "ready_for_pickup"  # Готов к выдаче
    delivering = "delivering"  # Доставляется
    delivered = "delivered"  # Доставлен
    closed = "closed"  # Закрыт
    cancelled = "cancelled"  # Отменен


class Order(SQLModel, table=True):
    """Таблица заказов"""
    __tablename__ = "orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_user_id: Optional[int] = Field(default=None, index=True)
    telegram_username: Optional[str] = Field(default=None, max_length=255)
    customer_name: Optional[str] = Field(default=None, max_length=255, nullable=True)
    customer_phone: Optional[str] = Field(default=None, max_length=20, nullable=True)
    delivery_address: Optional[str] = Field(default=None, max_length=500, nullable=True)
    total_amount: Decimal = Field(sa_type=Numeric(10, 2))
    status: OrderStatus = Field(default=OrderStatus.new)
    branch_id: int = Field(foreign_key="branches.id", index=True)
    customer_id: Optional[int] = Field(default=None, foreign_key="customers.id", index=True)
    bonus_spent: Decimal = Field(sa_type=Numeric(10, 2), default=Decimal("0.00"), description="Списанные бонусы")
    total_discount: Decimal = Field(sa_type=Numeric(10, 2), default=Decimal("0.00"), description="Сумма скидки")
    promo_code_id: Optional[int] = Field(default=None, foreign_key="promo_codes.id", index=True)
    iiko_order_id: Optional[str] = Field(default=None, unique=True, index=True, max_length=255)
    external_number: Optional[str] = Field(default=None, index=True, max_length=100, description="Читаемый номер заказа из iiko")
    terminal_group_id: Optional[str] = Field(default=None, index=True, max_length=255, description="ID терминальной группы iiko")
    terminal_group_name: Optional[str] = Field(default=None, index=True, max_length=255, description="Название терминальной группы")
    source: Optional[str] = Field(default=None, max_length=100, description="Источник заказа (например, сайт, приложение, агрегатор)")
    comment: Optional[str] = Field(default=None)
    
    # Расширенные данные из iiko
    bonus_accrued: Decimal = Field(sa_type=Numeric(10, 2), default=Decimal("0.00"), description="Начисленные бонусы")
    total_with_discount: Decimal = Field(sa_type=Numeric(10, 2), default=Decimal("0.00"), description="Итого к оплате")
    payment_method: Optional[str] = Field(default=None, description="Способ оплаты (из iiko)")
    order_type: Optional[str] = Field(default=None, description="Тип заказа: доставка/самовывоз/зал")
    courier_name: Optional[str] = Field(default=None, description="Имя курьера")
    iiko_creation_time: Optional[datetime] = Field(default=None, description="Время создания заказа в iiko")
    expected_time: Optional[datetime] = Field(default=None, description="Время готовности/ожидаемой доставки")
    actual_time: Optional[datetime] = Field(default=None, description="Фактическое время выдачи/доставки")
    delay_minutes: Optional[int] = Field(default=None, description="Опоздание в минутах")
    is_on_time: bool = Field(default=True, description="Заказ на время / вовремя")
    is_asap: bool = Field(default=True, description="Заказ на ближайшее время (ASAP)")
    admin_name: Optional[str] = Field(default=None, description="Администратор")
    city: Optional[str] = Field(default=None, description="Город")
    street: Optional[str] = Field(default=None, description="Улица")
    house: Optional[str] = Field(default=None, description="Дом")
    flat: Optional[str] = Field(default=None, description="Квартира")
    entrance: Optional[str] = Field(default=None, description="Подъезд")
    floor: Optional[str] = Field(default=None, description="Этаж")
    doorphone: Optional[str] = Field(default=None, description="Домофон")
    delivery_zone: Optional[str] = Field(default=None, description="Зона доставки (из iiko)")
    
    # Гео-данные (Яндекс)
    latitude: Optional[float] = Field(default=None, description="Широта (координаты Яндекса)")
    longitude: Optional[float] = Field(default=None, description="Долгота (координаты Яндекса)")
    resolved_delivery_zone_id: Optional[int] = Field(default=None, foreign_key="delivery_zones.id", description="ID локально определенной зоны доставки")
    
    is_paid: bool = Field(default=False, description="Заказ оплачен")

    discounts_details: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON), 
        description="Детали скидок (названия и суммы)"
    )
    
    # История событий заказа
    status_history: Optional[List[Dict[str, Any]]] = Field(
        default=None, sa_column=Column(JSON), 
        description="История изменения статусов (лента событий)"
    )
    
    # Данные антиспам проверки
    spam_score: Optional[int] = Field(default=None, description="Оценка спама (0-100)")
    spam_info: Optional[str] = Field(default=None, description="Информация о спаме")
    
    base_amount: Decimal = Field(sa_type=Numeric(10, 2), default=Decimal("0.00"), description="Сумма без скидок")
    left_to_pay: Decimal = Field(sa_type=Numeric(10, 2), default=Decimal("0.00"), description="Осталось доплатить")
    payments_details: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON), 
        description="Детали оплат (наличные, безнал, частичные оплаты)"
    )
    
    # JSON-поля для хранения детализированных данных, если они нужны
    order_items_details: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON), description="Полный состав заказа из iiko")
    customer_info_details: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="Полные данные заказчика")
    address_parts: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="Детальные компоненты адреса (JSON)")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Отношения
    branch: Optional["Branch"] = Relationship()
    items: List["OrderItem"] = Relationship(back_populates="order", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    customer: Optional["Customer"] = Relationship()
    resolved_zone: Optional["DeliveryZone"] = Relationship()


    @property
    def resolved_zone_name(self) -> Optional[str]:
        if self.order_type == "Самовывоз":
            return "Самовывоз"
        return self.resolved_zone.name if self.resolved_zone else None


    class Config:
        """Настройки модели"""
        json_schema_extra = {
            "example": {
                "telegram_user_id": 123456789,
                "customer_name": "Иван Иванов",
                "customer_phone": "+79991234567",
                "delivery_address": "ул. Пушкина, д. 10, кв. 5",
                "total_amount": 1250.00,
                "status": "new"
            }
        }


class OrderItem(SQLModel, table=True):
    """Таблица позиций заказа"""
    __tablename__ = "order_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    
    # Relationships
    order: Order = Relationship(back_populates="items")
    
    product_id: Optional[int] = Field(default=None, foreign_key="products.id")
    product_name: str = Field(max_length=255)  # Сохраняем название на момент заказа
    quantity: int = Field(default=1, ge=1)
    price: Decimal = Field(sa_type=Numeric(10, 2))  # Цена на момент заказа
    total: Decimal = Field(sa_type=Numeric(10, 2))  # quantity * price
    size_name: Optional[str] = Field(default=None, max_length=100)
    comment: Optional[str] = Field(default=None)
    modifiers: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))

    class Config:
        """Настройки модели"""
        json_schema_extra = {
            "example": {
                "order_id": 1,
                "product_id": 1,
                "product_name": "Маргарита",
                "quantity": 2,
                "price": 450.00,
                "total": 900.00
            }
        }
