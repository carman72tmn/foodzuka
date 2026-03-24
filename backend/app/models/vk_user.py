"""
Модель пользователя ВКонтакте
"""
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class VkUser(SQLModel, table=True):
    """Таблица привязанных пользователей ВКонтакте"""
    __tablename__ = "vk_users"

    vk_id: int = Field(primary_key=True, description="ID пользователя ВКонтакте")
    phone: Optional[str] = Field(default=None, unique=True, index=True, max_length=20, description="Телефон из iiko")
    iiko_customer_id: Optional[str] = Field(default=None, max_length=100, description="ID гостя в iiko")
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    vk_bonus_balance: int = Field(default=0, description="Локальный баланс баллов за VK активность")
    is_linked: bool = Field(default=False, description="Привязан ли телефон")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
