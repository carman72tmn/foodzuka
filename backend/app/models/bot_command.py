"""
Модели для команд ботов и состояний пользователей
"""
from typing import Optional, List
from datetime import datetime
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, Integer, Sequence
from sqlalchemy.dialects.postgresql import JSONB

class BotCommand(SQLModel, table=True):
    """Таблица команд ботов с ручной настройкой"""
    __tablename__ = "bot_commands"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer,
            Sequence("bot_commands_id_seq", start=100),
            primary_key=True,
            autoincrement=True
        ),
        description="ID команды, начиная со 100"
    )
    name: str = Field(max_length=255, description="Название команды")
    trigger_phrase: str = Field(max_length=255, index=True, description="Триггерная фраза")
    action_type: str = Field(default="get_balance", max_length=50, description="Тип действия (get_balance, custom_text, unlink_phone)")
    channels: List[str] = Field(default=[], sa_column=Column(JSONB), description="Выбранные каналы соцсетей")
    is_active: bool = Field(default=True, description="Активна ли команда")
    response_text: Optional[str] = Field(default=None, description="Ответ для custom_text")
    request_phone_text: Optional[str] = Field(default=None, description="Текст запроса телефона")
    phone_not_found_text: Optional[str] = Field(default=None, description="Текст если телефон не найден")
    register_confirm_text: Optional[str] = Field(default=None, description="Текст подтверждения регистрации")
    register_success_text: Optional[str] = Field(default=None, description="Текст успешной регистрации")
    balance_text: Optional[str] = Field(default=None, description="Текст с балансом бонусов")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class BotUserState(SQLModel, table=True):
    """Таблица состояний пользователей (FSM)"""
    __tablename__ = "bot_user_states"

    id: Optional[int] = Field(default=None, primary_key=True)
    messenger: str = Field(max_length=50, index=True, description="Мессенджер (vk, telegram, whatsapp, max)")
    peer_id: str = Field(max_length=100, index=True, description="ID диалога/пользователя")
    state: str = Field(max_length=100, description="Имя состояния FSM")
    command_id: Optional[int] = Field(default=None, description="ID текущей команды")
    context_data: dict = Field(sa_column=Column(JSONB), default={}, description="Контекст диалога (телефон, имя и т.д.)")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
