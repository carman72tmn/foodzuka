"""
Модели для управления VK Ботом (уведомления сотрудников)
"""
from typing import Optional, List
from datetime import datetime
import enum
from sqlmodel import Field, SQLModel, Relationship, Column
from sqlalchemy import JSON
from app.core.datetime_utils import utc_now
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.employee import Employee

class DeliveryMode(str, enum.Enum):
    REALTIME = "realtime"
    INTERVAL = "interval"

class MessageStatus(str, enum.Enum):
    PENDING = "pending"       # В очереди на отправку (дайджест)
    SENT = "sent"             # Отправлено в VK
    DELIVERED = "delivered"   # Доставлено пользователю
    READ = "read"             # Прочитано пользователем
    FAILED = "failed"         # Ошибка отправки

class VkBotAccountGroupLink(SQLModel, table=True):
    """Связь аккаунтов и групп (Many-to-Many)"""
    __tablename__ = "vk_bot_account_group_links"
    
    account_id: Optional[int] = Field(
        default=None, foreign_key="vk_bot_accounts.id", primary_key=True
    )
    group_id: Optional[int] = Field(
        default=None, foreign_key="vk_bot_groups.id", primary_key=True
    )

class VkBotGroup(SQLModel, table=True):
    """Группы аккаунтов (напр. Курьеры, Менеджеры)"""
    __tablename__ = "vk_bot_groups"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, description="Название группы")
    
    # Связи
    accounts: List["VkBotAccount"] = Relationship(
        back_populates="groups", link_model=VkBotAccountGroupLink
    )

class VkBotAccount(SQLModel, table=True):
    """Аккаунты получателей уведомлений"""
    __tablename__ = "vk_bot_accounts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    vk_user_id: int = Field(unique=True, index=True, description="Цифровой ID VK")
    name: str = Field(max_length=255, description="Имя/Должность получателя")
    phone: Optional[str] = Field(default=None, max_length=20, description="Телефон для связи с клиентами")
    is_active: bool = Field(default=True, description="Активен ли аккаунт")
    is_verified: bool = Field(default=False, description="Прошел ли проверку связи")
    
    # Связи
    groups: List[VkBotGroup] = Relationship(
        back_populates="accounts", link_model=VkBotAccountGroupLink
    )
    subscriptions: List["VkBotSubscription"] = Relationship(back_populates="account")
    logs: List["VkBotMessageLog"] = Relationship(back_populates="account")
    
    employee_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    employee: Optional["Employee"] = Relationship()
    
    enabled_events: list = Field(default_factory=list, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

class VkTemplate(SQLModel, table=True):
    """Шаблоны сообщений для рассылок"""
    __tablename__ = "vk_templates"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, description="Название шаблона")
    text: str = Field(description="Текст шаблона с переменными")
    keyboard_json: Optional[str] = Field(default=None, description="JSON клавиатуры VK")
    
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

class VkMailing(SQLModel, table=True):
    """Кампании рассылок"""
    __tablename__ = "vk_mailings"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    template_id: int = Field(foreign_key="vk_templates.id")
    title: str = Field(max_length=255, description="Заголовок рассылки")
    audience_filters: Optional[str] = Field(default=None, description="JSON фильтров аудитории")
    
    status: str = Field(default="draft", max_length=20, index=True)
    target_count: int = Field(default=0)
    sent_count: int = Field(default=0)
    error_count: int = Field(default=0)
    
    scheduled_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

class VkBotSubscription(SQLModel, table=True):
    """Подписки аккаунтов на события"""

    __tablename__ = "vk_bot_subscriptions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="vk_bot_accounts.id")
    event_type: str = Field(max_length=100, description="Тип события (new_order, shift_close, etc.)")
    delivery_mode: DeliveryMode = Field(default=DeliveryMode.REALTIME, description="Режим доставки")
    interval_minutes: int = Field(default=0, description="Интервал в минутах для дайджестов")
    last_digest_at: Optional[datetime] = Field(default=None, description="Время последней отправки дайджеста")
    
    active_start_hour: int = Field(default=0, ge=0, le=23, description="Час начала активности (0-23)")
    active_end_hour: int = Field(default=23, ge=0, le=23, description="Час окончания активности (0-23)")
    
    # Связи
    account: VkBotAccount = Relationship(back_populates="subscriptions")

class VkBotMessageLog(SQLModel, table=True):
    """Логи сообщений и статистика"""
    __tablename__ = "vk_bot_message_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="vk_bot_accounts.id")
    vk_message_id: Optional[int] = Field(default=None, description="ID сообщения в VK")
    event_type: Optional[str] = Field(default=None, max_length=100)
    text: str = Field(description="Текст сообщения")
    
    status: MessageStatus = Field(default=MessageStatus.PENDING)
    error_text: Optional[str] = Field(default=None, description="Текст ошибки при отправке")
    
    created_at: datetime = Field(default_factory=utc_now)
    sent_at: Optional[datetime] = Field(default=None, description="Время фактической отправки")
    
    # Связи
    account: VkBotAccount = Relationship(back_populates="logs")
