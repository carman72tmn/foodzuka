"""
Модели заказа и позиций заказа
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Numeric, Column, JSON


class OrderStatus(str, Enum):
    """Статусы заказа"""
    NEW = "new"  # Новый заказ
    CONFIRMED = "confirmed"  # Подтвержден
    PREPARING = "preparing"  # В подготовке
    COOKING = "cooking"  # Готовится
    READY = "ready"  # Готов
    DELIVERING = "delivering"  # Доставляется
    DELIVERED = "delivered"  # Доставлен
    CANCELLED = "cancelled"  # Отменен


class Order(SQLModel, table=True):
    """Таблица заказов"""
    __tablename__ = "orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_user_id: Optional[int] = Field(default=None, index=True)
    telegram_username: Optional[str] = Field(default=None, max_length=255)
    customer_name: Optional[str] = Field(default=None, max_length=255)
    customer_phone: Optional[str] = Field(default=None, max_length=20)
    delivery_address: Optional[str] = Field(default=None, max_length=500)
    total_amount: Decimal = Field(sa_type=Numeric(10, 2))
    status: OrderStatus = Field(default=OrderStatus.NEW)
    branch_id: int = Field(foreign_key="branches.id", index=True)
    customer_id: Optional[int] = Field(default=None, foreign_key="customers.id", index=True)
    bonus_spent: Decimal = Field(sa_type=Numeric(10, 2), default=Decimal("0.00"), description="Списанные бонусы")
    total_discount: Decimal = Field(sa_type=Numeric(10, 2), default=Decimal("0.00"), description="Сумма скидки")
    promo_code_id: Optional[int] = Field(default=None, foreign_key="promo_codes.id", index=True)
    iiko_order_id: Optional[str] = Field(default=None, unique=True, index=True, max_length=255)
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
    admin_name: Optional[str] = Field(default=None, description="Администратор")
    delivery_zone: Optional[str] = Field(default=None, description="Зона доставки")
    
    # JSON-поля для хранения детализированных данных, если они нужны
    order_items_details: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="Полный состав заказа из iiko")
    discounts_details: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="Детали скидок")
    customer_info_details: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="Полные данные заказчика")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    items: List["OrderItem"] = Relationship(back_populates="order", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

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
    
    product_id: int = Field(foreign_key="products.id")
    product_name: str = Field(max_length=255)  # Сохраняем название на момент заказа
    quantity: int = Field(default=1, ge=1)
    price: Decimal = Field(sa_type=Numeric(10, 2))  # Цена на момент заказа
    total: Decimal = Field(sa_type=Numeric(10, 2))  # quantity * price

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
