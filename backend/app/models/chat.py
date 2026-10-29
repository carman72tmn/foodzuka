"""
Модели для системы внутреннего чата сотрудников
"""
from typing import Optional, List, Any, Dict
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Relationship, JSON, Column


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


class MultichatMessage(SQLModel, table=True):
    """Таблица сообщений мультичата (VK, MAX, Telegram)"""
    __tablename__ = "multichat_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    channel: str = Field(index=True, description="vk, max_account, max_bot, telegram_bot")
    channel_id: Optional[str] = Field(default=None, index=True, description="ID группы/бота/аккаунта")
    peer_id: str = Field(index=True, description="ID собеседника (пользователя или чата)")
    peer_name: Optional[str] = Field(default=None, description="Имя собеседника")
    peer_avatar: Optional[str] = Field(default=None, description="Аватар собеседника")
    from_id: str = Field(index=True, description="ID отправителя")
    text: str = Field(description="Текст сообщения")
    direction: str = Field(index=True, description="inbound или outbound")
    external_id: Optional[str] = Field(default=None, index=True, description="Внешний ID сообщения")
    is_read: bool = Field(default=False, index=True, description="Статус прочтения")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
        description="Дата и время"
    )
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON), description="Сырые JSON данные")


class MultichatTag(SQLModel, table=True):
    """Таблица меток для мультичата"""
    __tablename__ = "multichat_tags"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, description="Название метки")
    color: str = Field(default="#757575", description="Цвет метки (hex)")


class MultichatDialogTag(SQLModel, table=True):
    """Связующая таблица диалогов с метками"""
    __tablename__ = "multichat_dialog_tags"

    id: Optional[int] = Field(default=None, primary_key=True)
    channel: str = Field(index=True, description="vk, max_account, max_bot, telegram_bot")
    peer_id: str = Field(index=True, description="ID собеседника")
    tag_id: int = Field(foreign_key="multichat_tags.id", index=True, description="ID метки")


class MultichatAccount(SQLModel, table=True):
    """Таблица подключенных личных аккаунтов (Telegram, VK, MAX)"""
    __tablename__ = "multichat_accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    channel: str = Field(index=True, description="telegram_user, vk_user, max_user")
    name: str = Field(description="Имя или название аккаунта")
    phone: Optional[str] = Field(default=None, index=True, description="Номер телефона")
    status: str = Field(default="pending", index=True, description="active, pending, disconnected")
    token: Optional[str] = Field(default=None, description="Токен доступа (для VK / MAX)")
    session_string: Optional[str] = Field(default=None, description="Строка сессии StringSession для Telethon")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )


class MultichatPinnedDialog(SQLModel, table=True):
    """Закрепленные диалоги мультичата"""
    __tablename__ = "multichat_pinned_dialogs"

    id: Optional[int] = Field(default=None, primary_key=True)
    channel: str = Field(index=True, description="vk, max_account, max_bot, telegram_bot, etc.")
    peer_id: str = Field(index=True, description="ID собеседника")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )


class MultichatHiddenDialog(SQLModel, table=True):
    """Скрытые диалоги мультичата (архивированные/скрытые из общего списка)"""
    __tablename__ = "multichat_hidden_dialogs"

    id: Optional[int] = Field(default=None, primary_key=True)
    channel: str = Field(index=True, description="vk, max_account, max_bot, telegram_bot, etc.")
    peer_id: str = Field(index=True, description="ID собеседника")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )





