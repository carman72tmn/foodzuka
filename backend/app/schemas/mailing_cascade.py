from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

# --- Схемы шагов каскада ---

class MailingCascadeStepBase(BaseModel):
    """Базовые поля шага каскада"""
    channel: str
    priority: int = 0
    delay_minutes: int = 0
    condition: str = "always"
    template: str
    image_path: Optional[str] = None
    buttons_json: Optional[str] = None
    max_bot_id: Optional[int] = None
    max_send_mode: Optional[str] = "cascade"

class MailingCascadeStepCreate(MailingCascadeStepBase):
    """Схема для создания/обновления шага (внутри каскада)"""
    pass

class MailingCascadeStepResponse(MailingCascadeStepBase):
    """Схема ответа для шага"""
    id: int
    cascade_id: int
    model_config = ConfigDict(from_attributes=True)


# --- Схемы каскадов ---

class MailingCascadeBase(BaseModel):
    """Базовые поля каскада"""
    name: str
    trigger_event: str
    is_active: bool = True
    order_type: Optional[str] = None
    is_system: bool = False

class MailingCascadeCreate(MailingCascadeBase):
    """Схема для создания каскада"""
    steps: List[MailingCascadeStepCreate] = []

class MailingCascadeUpdate(BaseModel):
    """Схема для обновления каскада"""
    name: Optional[str] = None
    trigger_event: Optional[str] = None
    is_active: Optional[bool] = None
    order_type: Optional[str] = None
    is_system: Optional[bool] = None
    steps: Optional[List[MailingCascadeStepCreate]] = None

class MailingCascadeResponse(MailingCascadeBase):
    """Схема ответа для каскада"""
    id: int
    created_at: datetime
    updated_at: datetime
    steps: List[MailingCascadeStepResponse] = []
    model_config = ConfigDict(from_attributes=True)


# --- Схемы отзывов ---

class OrderReviewResponse(BaseModel):
    """Схема ответа для отзыва"""
    id: int
    order_id: Optional[int] = None
    customer_id: Optional[int] = None
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    
    # Расширенные поля для UI
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    order_number: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# --- Схемы напоминаний ---

class CustomerReminderBase(BaseModel):
    name: str
    days_inactive: int
    template: str
    cascade_id: Optional[int] = None
    is_active: bool = True

class CustomerReminderCreate(CustomerReminderBase):
    pass

class CustomerReminderUpdate(BaseModel):
    name: Optional[str] = None
    days_inactive: Optional[int] = None
    template: Optional[str] = None
    cascade_id: Optional[int] = None
    is_active: Optional[bool] = None

class CustomerReminderResponse(CustomerReminderBase):
    id: int
    created_at: datetime
    updated_at: datetime
    cascade_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# --- Схемы рассылок ---

class CustomerBroadcastBase(BaseModel):
    title: str
    template_text: str
    cascade_id: Optional[int] = None
    audience_filters: Optional[dict] = None
    status: str = "draft"
    scheduled_at: Optional[datetime] = None

class CustomerBroadcastCreate(CustomerBroadcastBase):
    pass

class CustomerBroadcastUpdate(BaseModel):
    title: Optional[str] = None
    template_text: Optional[str] = None
    cascade_id: Optional[int] = None
    audience_filters: Optional[dict] = None
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None

class CustomerBroadcastResponse(CustomerBroadcastBase):
    id: int
    sent_count: int
    delivered_count: int
    read_count: int
    error_count: int
    created_at: datetime
    updated_at: datetime
    cascade_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# --- Схемы логов сообщений ---

class CustomerMessageLogResponse(BaseModel):
    id: int
    customer_id: Optional[int] = None
    order_id: Optional[int] = None
    broadcast_id: Optional[int] = None
    reminder_id: Optional[int] = None
    cascade_step_id: Optional[int] = None
    channel: str
    recipient_address: str
    text: str
    status: str
    message_id: Optional[str] = None
    error_text: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    # Дополнительно для UI
    customer_name: Optional[str] = None
    broadcast_title: Optional[str] = None
    reminder_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
