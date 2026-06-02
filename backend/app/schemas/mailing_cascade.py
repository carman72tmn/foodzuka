from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class MailingCascadeStepBase(BaseModel):
    """Базовые поля шага каскада"""
    channel: str
    priority: int = 0
    delay_minutes: int = 0
    condition: str = "always"
    template: str

class MailingCascadeStepCreate(MailingCascadeStepBase):
    """Схема для создания/обновления шага (внутри каскада)"""
    pass

class MailingCascadeStepResponse(MailingCascadeStepBase):
    """Схема ответа для шага"""
    id: int
    cascade_id: int
    model_config = ConfigDict(from_attributes=True)

class MailingCascadeBase(BaseModel):
    """Базовые поля каскада"""
    name: str
    trigger_event: str
    is_active: bool = True

class MailingCascadeCreate(MailingCascadeBase):
    """Схема для создания каскада"""
    steps: List[MailingCascadeStepCreate] = []

class MailingCascadeUpdate(BaseModel):
    """Схема для обновления каскада"""
    name: Optional[str] = None
    trigger_event: Optional[str] = None
    is_active: Optional[bool] = None
    steps: Optional[List[MailingCascadeStepCreate]] = None

class MailingCascadeResponse(MailingCascadeBase):
    """Схема ответа для каскада"""
    id: int
    created_at: datetime
    updated_at: datetime
    steps: List[MailingCascadeStepResponse] = []
    model_config = ConfigDict(from_attributes=True)
