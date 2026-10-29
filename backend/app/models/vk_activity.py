"""
Модель активности пользователя ВКонтакте
"""
from typing import Optional
from datetime import datetime
from app.core.datetime_utils import utc_now
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
    created_at: datetime = Field(default_factory=utc_now)


class VkActivityPenaltyTimer(SQLModel, table=True):
    """Таблица штрафных таймеров для повторных действий ВК"""
    __tablename__ = "vk_activity_penalty_timers"

    id: Optional[int] = Field(default=None, primary_key=True)
    vk_id: int = Field(index=True, description="ID пользователя ВКонтакте")
    vk_bot_connection_id: int = Field(index=True, description="ID подключения бота VK")
    target_type: str = Field(max_length=50, description="Тип цели (post или group)")
    target_id: str = Field(max_length=100, description="Идентификатор цели (например, ID поста или group)")
    expires_at: datetime = Field(description="Время окончания действия штрафа")
    created_at: datetime = Field(default_factory=utc_now)

