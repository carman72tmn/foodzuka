"""
Модель для хранения OLAP-данных по выручке из iiko
"""
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class OlapRevenueRecord(SQLModel, table=True):
    """
    Хранит агрегированные данные по выручке для каждого торгового предприятия
    за определённый период.
    """
    __tablename__ = "olap_revenue_records"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Идентификация
    organization_id: str = Field(max_length=100, index=True, description="UUID организации/группы терминалов из iiko")
    organization_name: str = Field(default="", max_length=255, description="Название торгового предприятия")

    # Период
    date_from: datetime = Field(index=True, description="Начало периода")
    date_to: datetime = Field(index=True, description="Конец периода")
    business_date: Optional[str] = Field(default=None, index=True, description="Бизнес-день (для ежедневной разбивки)")
    period_type: str = Field(max_length=20, index=True, description="Тип периода: day/yesterday/week/month/year/custom")

    # Данные выручки (из iiko OLAP)
    average_check: float = Field(default=0.0, description="Средний чек")
    markup: float = Field(default=0.0, description="Наценка (сумма)")
    markup_percent: float = Field(default=0.0, description="Наценка (%)")
    cost_price: float = Field(default=0.0, description="Себестоимость (сумма)")
    cost_price_percent: float = Field(default=0.0, description="Себестоимость (%)")
    discount_sum: float = Field(default=0.0, description="Сумма скидки")
    revenue: float = Field(default=0.0, description="Сумма со скидкой / выручка")
    orders_count: int = Field(default=0, description="Количество заказов")

    # Фильтры применявшиеся при запросе
    include_deleted: bool = Field(default=False, description="Включать ли удалённые заказы")

    # Мета-информация
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
