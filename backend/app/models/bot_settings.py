"""
Модель настроек интеграции с Telegram
Поддержка официального Telegram Bot API и Telegram User Client (отправка с личного номера)
"""
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel


class BotSettings(SQLModel, table=True):
    """Настройки подключения и рассылок Telegram"""
    __tablename__ = "bot_settings"

    id: Optional[int] = Field(default=None, primary_key=True)

    # --- Официальный Telegram Bot ---
    is_bot_active: bool = Field(default=False, description="Активен ли Telegram бот")
    telegram_bot_token: Optional[str] = Field(
        default=None, max_length=500, description="Токен Telegram бота от @BotFather"
    )
    bot_username: Optional[str] = Field(default=None, max_length=255, description="Юзернейм бота")
    
    # --- Системный канал / чат рассылок ---
    system_channel_id: Optional[str] = Field(
        default=None, max_length=255, description="ID канала/группы для системных уведомлений (напр. @channel или -100...)"
    )
    is_system_notifications_active: bool = Field(
        default=False, description="Отправлять ли системные уведомления в канал Telegram"
    )
    is_client_broadcast_active: bool = Field(
        default=False, description="Разрешены ли рассылки клиентам в Telegram"
    )

    # --- Личный аккаунт Telegram (Отправка с номера) ---
    is_user_client_active: bool = Field(
        default=False, description="Активна ли рассылка с номера личного Telegram аккаунта"
    )
    user_phone: Optional[str] = Field(default=None, max_length=50, description="Номер телефона аккаунта (+7...)")
    user_api_id: Optional[str] = Field(default=None, max_length=100, description="Telegram API ID от my.telegram.org")
    user_api_hash: Optional[str] = Field(default=None, max_length=255, description="Telegram API Hash")
    user_session_string: Optional[str] = Field(default=None, description="Строка авторизованной сессии")
    user_account_status: Optional[str] = Field(
        default="not_connected", max_length=50, description="Статус подключения: connected / not_connected / code_required"
    )

    welcome_message: Optional[str] = Field(
        default="Добро пожаловать в нашего бота!", 
        description="Приветственное сообщение"
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
