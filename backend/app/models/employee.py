from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship

class Employee(SQLModel, table=True):
    __tablename__ = "employees"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    iiko_id: str = Field(index=True, unique=True, description="ID сотрудника в iiko")
    name: str = Field(description="Имя сотрудника")
    phone: Optional[str] = Field(default=None, description="Телефон")
    role: Optional[str] = Field(default=None, description="Роль/должность в iiko")
    status: Optional[str] = Field(default=None, description="Статус (например, Active, Deleted)")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Отношения
    shifts: List["Shift"] = Relationship(back_populates="employee")
    schedules: List["Schedule"] = Relationship(back_populates="employee")


class Shift(SQLModel, table=True):
    __tablename__ = "shifts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    iiko_id: str = Field(index=True, unique=True, description="ID смены в iiko")
    employee_id: int = Field(foreign_key="employees.id", description="ID сотрудника в нашей БД")
    
    date_open: datetime = Field(description="Время открытия смены")
    date_close: Optional[datetime] = Field(default=None, description="Время закрытия смены")
    status: str = Field(default="OPEN", description="Статус: OPEN или CLOSED")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Реляции
    employee: Optional[Employee] = Relationship(back_populates="shifts")


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
