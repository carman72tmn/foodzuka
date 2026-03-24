"""
Конфигурация Telegram бота
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки бота из .env файла"""

    # Токен Telegram бота
    BOT_TOKEN: str

    # URL Backend API
    API_URL: str = "http://backend:8000/api/v1"

    # Режим отладки
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Глобальный экземпляр настроек
settings = Settings()
