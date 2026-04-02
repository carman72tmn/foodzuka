"""
Модель настроек интеграции с Telegram
"""
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class BotSettings(SQLModel, table=True):
    """Настройки подключения к Telegram Bot API"""
    __tablename__ = "bot_settings"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Основные настройки подключения
    telegram_bot_token: Optional[str] = Field(
        default=None, max_length=500, description="Токен Telegram бота"
    )
    
    # Можно добавить другие настройки (например, ID админов, приветственное сообщение и т.д.)
    welcome_message: Optional[str] = Field(
        default="Добро пожаловать в нашего бота!", 
        description="Приветственное сообщение"
    )

    # Метаданные
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
