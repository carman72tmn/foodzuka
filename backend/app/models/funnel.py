"""
Модель Воронок (Автоматические каскадные цепочки сообщений/действий)
"""
from typing import Optional
from datetime import datetime
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel


class Funnel(SQLModel, table=True):
    """
    Таблица для управления маркетинговыми Воронками
    Например: Если клиент не заказывал 30 дней -> Отправить СМС с промокодом.
    Если код не применен 3 дня -> Позвонить.
    """
    __tablename__ = "funnels"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Контент
    name: str = Field(max_length=255, description="Название воронки")
    description: Optional[str] = Field(default=None, description="Описание или цель")
    
    # Статус
    is_active: bool = Field(default=True, description="Работает ли воронка")
    
    # Триггер (Событие старта воронки)
    trigger_type: str = Field(
        max_length=50, default="no_orders_n_days",
        description="no_orders_n_days (нет заказов N дней), first_order (первый заказ), registration (регистрация)"
    )
    trigger_value: Optional[int] = Field(
        default=None,
        description="Значение триггера (например кол-во дней для no_orders_n_days)"
    )
    
    # Шаги воронки хранятся в формате JSON
    # Примерно так: [{"step": 1, "delay_hours": 0, "action": "send_tg", "message": "Привет!", "promo_code_id": 5}, ...]
    steps: str = Field(
        default="[]", 
        description="JSON массив шагов и действий воронки"
    )
    
    # Статистика
    clients_entered: int = Field(default=0, description="Сколько клиентов попало в воронку")
    clients_converted: int = Field(default=0, description="Сколько совершили целевое действие (обычно заказ)")
    
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
