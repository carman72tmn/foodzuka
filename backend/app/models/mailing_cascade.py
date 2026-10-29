"""
Модели для каскадных рассылок (настройка очередности каналов)
"""
from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from app.core.datetime_utils import utc_now

class MailingCascade(SQLModel, table=True):
    """
    Основная модель каскада уведомлений.
    Связывает триггер (событие) с набором последовательных шагов.
    """
    __tablename__ = "mailing_cascades"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, description="Название каскада (напр. Уведомления по заказам)")
    trigger_event: str = Field(index=True, description="Событие-триггер (например, order_confirmed, order_delivered)")
    is_active: bool = Field(default=True, description="Активен ли каскад")
    order_type: Optional[str] = Field(default=None, max_length=50, description="Тип заказа (delivery, pickup, any)")
    is_system: bool = Field(default=False, description="Системный каскад статусов заказа")
    
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # Отношение к шагам
    steps: List["MailingCascadeStep"] = Relationship(
        back_populates="cascade", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "order_by": "MailingCascadeStep.priority"}
    )

class MailingCascadeStep(SQLModel, table=True):
    """
    Шаг в каскаде рассылки.
    Определяет канал, шаблон сообщения и условия перехода.
    """
    __tablename__ = "mailing_cascade_steps"

    id: Optional[int] = Field(default=None, primary_key=True)
    cascade_id: int = Field(foreign_key="mailing_cascades.id", index=True)
    
    channel: str = Field(max_length=50, description="Канал: vk, max, telegram")
    priority: int = Field(default=0, description="Порядок выполнения (0 - первый)")
    delay_minutes: int = Field(default=0, description="Задержка перед отправкой этого шага (в минутах)")
    
    # Условия: 
    # always - отправлять всегда
    # if_previous_failed - если предыдущий шаг завершился ошибкой
    # if_not_read_previous - если предыдущее сообщение не прочитано (для каналов с поддержкой статуса)
    condition: str = Field(default="always", max_length=50, description="Условие выполнения шага")
    
    template: str = Field(description="Шаблон сообщения с поддержкой переменных {order_number}, {status} и т.д.")
    image_path: Optional[str] = Field(default=None, max_length=255, description="Путь к прикрепленному изображению")
    buttons_json: Optional[str] = Field(default=None, description="JSON кнопок клавиатуры (VK, TG, MAX)")
    max_bot_id: Optional[int] = Field(default=None, foreign_key="max_bots.id", nullable=True, description="ID бота MAX для шага каскада")
    max_send_mode: Optional[str] = Field(default="cascade", max_length=50, description="Режим отправки MAX: cascade, bot_only, bridge_only")
    
    # Обратная связь с каскадом
    cascade: MailingCascade = Relationship(back_populates="steps")
