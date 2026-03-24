"""
Модель активности пользователя ВКонтакте
"""
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class VkActivity(SQLModel, table=True):
    """Таблица накопления баллов за активность ВКонтакте"""
    __tablename__ = "vk_activities"

    id: Optional[int] = Field(default=None, primary_key=True)
    vk_id: int = Field(index=True, description="ID пользователя ВКонтакте")
    action_type: str = Field(max_length=50, description="Тип активности (например, like_add, wall_reply_new)")
    item_id: Optional[str] = Field(default=None, max_length=100, description="ID поста или комментария, чтобы избежать повторов")
    points: int = Field(default=0, description="Начисленные баллы")
    is_synced: bool = Field(default=False, description="Синхронизировано ли с iikoCard")
    created_at: datetime = Field(default_factory=datetime.utcnow)
