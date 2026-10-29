from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

class AdminNotification(SQLModel, table=True):
    """Таблица для сохранения истории системных уведомлений и пушей администраторов"""
    __tablename__ = "admin_notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True, nullable=True) # None означает "для всех"
    title: str = Field(max_length=255)
    body: str = Field(max_length=1000)
    url: Optional[str] = Field(default=None, max_length=500)
    event_type: str = Field(max_length=100)
    category: Optional[str] = Field(default="system", max_length=32, index=True) # new_order, order_status, tbank_payment, vk_message, max_message
    subtitle: Optional[str] = Field(default=None, max_length=255)
    badge_text: Optional[str] = Field(default=None, max_length=64)
    badge_color: Optional[str] = Field(default="primary", max_length=32)
    amount: Optional[float] = Field(default=None)
    order_id: Optional[int] = Field(default=None)
    external_key: Optional[str] = Field(default=None, max_length=128, index=True)
    meta_json: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSONB))
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
