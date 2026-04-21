from typing import Optional, List, TYPE_CHECKING

from datetime import datetime
from app.core.datetime_utils import utc_now
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from .order import Order


class CompanyBase(SQLModel):
    name: str
    description: Optional[str] = None
    inn: Optional[str] = None
    is_active: bool = True

    # iiko connection settings
    iiko_api_login: Optional[str] = None
    iiko_organization_id: Optional[str] = None


class Company(CompanyBase, table=True):
    __tablename__ = "companies"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Relationships
    branches: List["Branch"] = Relationship(back_populates="company", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class BranchBase(SQLModel):
    name: str
    address: str
    phone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool = True
    company_id: int = Field(foreign_key="companies.id")
    
    # Управление приемом заказов
    is_accepting_orders: bool = Field(default=True, description="Принимает ли филиал заказы вообще")
    is_accepting_delivery: bool = Field(default=True, description="Принимает ли заказы на доставку")
    is_accepting_pickup: bool = Field(default=True, description="Принимает ли заказы на самовывоз")
    
    # Расширенные настройки (CRM Фаза 1)
    min_order_amount: float = Field(default=0.0, description="Минимальная сумма заказа")
    free_delivery_threshold: float = Field(default=0.0, description="Сумма для бесплатной доставки")
    working_hours: Optional[str] = Field(default=None, description="Часы работы (напр. '10:00-22:00')")
    
    # iiko sync correlation
    iiko_terminal_id: Optional[str] = None


class Branch(BranchBase, table=True):
    __tablename__ = "branches"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Relationships
    company: Company = Relationship(back_populates="branches")
    delivery_zones: List["DeliveryZone"] = Relationship(back_populates="branch", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    custom_polygons: List["CustomPolygon"] = Relationship(back_populates="branch", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class DeliveryZoneBase(SQLModel):
    iiko_id: Optional[str] = Field(default=None, index=True, description="UUID зоны из iiko")
    name: str
    branch_id: int = Field(foreign_key="branches.id")
    
    # Coordinates for polygon (GeoJSON or simple list of points stringified for MVP)
    polygon_coordinates: Optional[str] = Field(default=None, description="JSON string of lat/lng coordinate pairs")
    
    min_order_amount: float = Field(default=0.0)
    delivery_cost: float = Field(default=0.0)
    min_delivery_time: Optional[int] = Field(default=None, description="Мин. время доставки (мин)")
    max_delivery_time: Optional[int] = Field(default=None, description="Макс. время доставки (мин)")
    free_delivery_sum: Optional[float] = Field(default=None, description="Сумма для бесплатной доставки")
    priority: int = Field(default=0, description="Приоритет зоны")
    is_default: bool = Field(default=False, description="Является ли зоной по умолчанию")
    is_manual_override: bool = Field(default=False, description="Запретить автоматическое обновление параметров из iiko")

    # Дополнительно из iiko Resto (Office)
    description: Optional[str] = Field(default=None, description="Текстовое описание зоны")
    additional_info: Optional[List] = Field(default=None, sa_column=Column(JSONB), description="Все остальные параметры из Resto")
    
    is_active: bool = True


class DeliveryZone(DeliveryZoneBase, table=True):
    __tablename__ = "delivery_zones"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Relationships
    branch: Branch = Relationship(back_populates="delivery_zones")
    custom_polygons: List["CustomPolygon"] = Relationship(back_populates="delivery_zone")


class CustomPolygonBase(SQLModel):
    name: str
    description: Optional[str] = None
    branch_id: int = Field(foreign_key="branches.id")
    delivery_zone_id: Optional[int] = Field(default=None, foreign_key="delivery_zones.id")

    # Параметры доставки
    min_delivery_time: Optional[int] = Field(default=None, description="Мин. время доставки (мин)")
    max_delivery_time: Optional[int] = Field(default=None, description="Макс. время доставки (мин)")
    min_order_amount: float = Field(default=0.0, description="Минимальная сумма заказа")
    delivery_cost: float = Field(default=0.0, description="Стоимость доставки")
    free_delivery_threshold: float = Field(default=0.0, description="Сумма для бесплатной доставки")

    # Визуальные настройки
    fill_color: str = Field(default="#4caf50", description="Цвет заливки полигона (HEX)")
    priority: int = Field(default=0, description="Приоритет полигона (чем выше, тем главнее)")
    
    # Coordinates as a list of [lat, lng]
    coordinates: List[List[float]] = Field(default_factory=list, sa_column=Column(JSONB))
    is_active: bool = True


class CustomPolygon(CustomPolygonBase, table=True):
    __tablename__ = "custom_polygons"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    
    # Relationships
    branch: Branch = Relationship(back_populates="custom_polygons")
    delivery_zone: Optional[DeliveryZone] = Relationship(back_populates="custom_polygons")
