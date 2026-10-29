from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel

class PushSubscription(SQLModel, table=True):
    """Таблица подписок на пуш-уведомления"""
    __tablename__ = "push_subscriptions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    endpoint: str = Field(unique=True, index=True, max_length=1000)
    p256dh: str = Field(max_length=500)
    auth: str = Field(max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
