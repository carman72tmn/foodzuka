from typing import Optional, List
from datetime import datetime
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
    status: Optional[str] = Field(default=None, description="Статус (например, Active, Deleted)")
    rate: Optional[float] = Field(default=None, description="Ставка за час")
    document_info: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="Данные документов")
    address: Optional[str] = Field(default=None, description="Адрес проживания")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
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
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
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
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Реляции
    employee: Optional[Employee] = Relationship(back_populates="schedules")


class CourierOrder(SQLModel, table=True):
    __tablename__ = "courier_orders"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    iiko_id: str = Field(index=True, unique=True, description="ID заказа в iiko")
    employee_id: int = Field(foreign_key="employees.id", description="ID сотрудника (курьера)")
    shift_id: Optional[int] = Field(default=None, foreign_key="shifts.id", description="ID смены")
    
    address: Optional[str] = Field(default=None, description="Адрес доставки")
    items_summary: Optional[str] = Field(default=None, description="Состав заказа (текст)")
    delivery_zone: Optional[str] = Field(default=None, description="Зона доставки")
    
    # Временные метки iiko
    created_at_iiko: datetime = Field(description="Время создания заказа")
    cooking_completed_at: Optional[datetime] = Field(default=None, description="Время готовности")
    expected_delivery_time: Optional[datetime] = Field(default=None, description="Ожидаемое время доставки")
    actual_delivery_time: Optional[datetime] = Field(default=None, description="Фактическое время вручения")
    
    is_late: bool = Field(default=False, description="Опоздание курьера")
    cooking_late: bool = Field(default=False, description="Опоздание кухни")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Отношения
    employee: Optional[Employee] = Relationship(back_populates="courier_orders")
    shift: Optional[Shift] = Relationship(back_populates="courier_orders")
