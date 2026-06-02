"""
Модели для системы внутреннего чата сотрудников
"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Relationship

class ChatMessage(SQLModel, table=True):
    """Таблица сообщений чата"""
    __tablename__ = "chat_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    sender_id: int = Field(foreign_key="users.id", index=True)
    receiver_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    is_group: bool = Field(default=False, index=True) # True для общего чата
    content: str = Field(max_length=4000)
    type: str = Field(default="text", max_length=50)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )
    read_at: Optional[datetime] = Field(default=None)

class ChatReadState(SQLModel, table=True):
    """Таблица состояния прочтения общего чата для каждого пользователя"""
    __tablename__ = "chat_read_states"

    user_id: int = Field(primary_key=True, foreign_key="users.id")
    last_read_group_msg_id: int = Field(default=0)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
