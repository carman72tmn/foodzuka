from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel, Relationship


class Employee(SQLModel, table=True):
    __tablename__ = "employees"

    id: Optional[int] = Field(default=None, primary_key=True)
    iiko_id: str = Field(index=True, unique=True, description="ID сотрудника в iiko")
    name: str = Field(description="Имя сотрудника")
    phone: Optional[str] = Field(default=None, description="Телефон")
    email: Optional[str] = Field(default=None, description="Email")
    role: Optional[str] = Field(default=None, description="Роль/должность в iiko")
    role_id: Optional[int] = Field(default=None, description="ID роли в локальной БД")
    status: Optional[str] = Field(default=None, description="Статус (например, Active, Deleted)")
    rate: Optional[float] = Field(default=None, description="Ставка за час")
    document_info: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="Данные документов")
    address: Optional[str] = Field(default=None, description="Адрес проживания")

    # Флаги типа сотрудника (вычисляются из role при синхронизации)
    is_courier: bool = Field(default=False, description="Является курьером")
    is_admin: bool = Field(default=False, description="Является администратором")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Отношения
    shifts: List["Shift"] = Relationship(back_populates="employee")
    schedules: List["Schedule"] = Relationship(back_populates="employee")
    courier_orders: List["CourierOrder"] = Relationship(back_populates="employee")


class Shift(SQLModel, table=True):
    __tablename__ = "shifts"

    id: Optional[int] = Field(default=None, primary_key=True)
    iiko_id: str = Field(index=True, unique=True, description="ID смены в iiko")
    employee_id: int = Field(foreign_key="employees.id", description="ID сотрудника в нашей БД")

    date_open: datetime = Field(description="Время открытия смены")
    date_close: Optional[datetime] = Field(default=None, description="Время закрытия смены")
    status: str = Field(default="OPEN", description="Статус: OPEN или CLOSED")
    work_hours: Optional[float] = Field(default=0.0, description="Отработанные часы")
    deliveries_count: int = Field(default=0, description="Количество доставок")
    deliveries_revenue: float = Field(default=0.0, description="Выручка за доставки")
    cancelled_orders_count: int = Field(default=0, description="Количество отмененных заказов за смену")
    revenue_at_close: Optional[float] = Field(default=None, description="Выручка на момент закрытия смены")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Реляции
    employee: Optional[Employee] = Relationship(back_populates="shifts")
    courier_orders: List["CourierOrder"] = Relationship(back_populates="shift")


class Schedule(SQLModel, table=True):
    __tablename__ = "schedules"

    id: Optional[int] = Field(default=None, primary_key=True)
    iiko_id: str = Field(index=True, unique=True, description="ID записи графика в iiko")
    employee_id: int = Field(foreign_key="employees.id", description="ID сотрудника в нашей БД")

    date_from: datetime = Field(description="Плановое время начала")
    date_to: datetime = Field(description="Плановое время окончания")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Реляции
    employee: Optional[Employee] = Relationship(back_populates="schedules")


class CourierOrder(SQLModel, table=True):
    __tablename__ = "courier_orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    iiko_id: str = Field(index=True, unique=True, description="ID заказа в iiko (UUID или номер)")
    order_num: Optional[str] = Field(default=None, index=True, description="Номер заказа (OrderNum из OLAP)")
    employee_id: int = Field(foreign_key="employees.id", description="ID сотрудника (курьера)")
    shift_id: Optional[int] = Field(default=None, foreign_key="shifts.id", description="ID смены")

    address: Optional[str] = Field(default=None, description="Адрес доставки")
    address_parts: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="Компоненты адреса (JSON)")
    items_summary: Optional[str] = Field(default=None, description="Состав заказа (текст)")
    delivery_zone: Optional[str] = Field(default=None, description="Зона доставки")
    amount: Optional[float] = Field(default=None, description="Сумма заказа")
    
    # Данные клиента из OLAP
    customer_name: Optional[str] = Field(default=None, description="Имя клиента")
    customer_phone: Optional[str] = Field(default=None, description="Телефон клиента")

    # Временные метки iiko
    created_at_iiko: Optional[datetime] = Field(default=None, description="Время создания заказа")
    cooking_completed_at: Optional[datetime] = Field(default=None, description="Время готовности кухни")
    departure_time: Optional[datetime] = Field(default=None, description="Время отправки курьера")
    expected_delivery_time: Optional[datetime] = Field(default=None, description="Ожидаемое время доставки")
    actual_delivery_time: Optional[datetime] = Field(default=None, description="Фактическое время вручения")
    close_time: Optional[datetime] = Field(default=None, description="Время закрытия заказа")

    delay_minutes: Optional[int] = Field(default=None, description="Опоздание в минутах (факт - план)")
    is_late: bool = Field(default=False, description="Курьер опоздал")
    cooking_late: bool = Field(default=False, description="Кухня опоздала")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Отношения
    employee: Optional[Employee] = Relationship(back_populates="courier_orders")
    shift: Optional[Shift] = Relationship(back_populates="courier_orders")
