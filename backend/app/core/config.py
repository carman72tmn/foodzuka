"""
Конфигурация приложения FastAPI
Использует pydantic-settings для загрузки переменных окружения
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения из .env файла"""

    # Настройки базы данных
    DATABASE_URL: str

    # Настройки API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = False
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    APP_PUBLIC_URL: Optional[str] = None

    # Настройки iiko Cloud API
    IIKO_API_URL: str = "https://api-ru.iiko.services"
    IIKO_API_LOGIN: str
    IIKO_ORGANIZATION_ID: str

    # Настройки VK Bot
    VK_BOT_TOKEN: Optional[str] = None
    VK_CONFIRMATION_CODE: Optional[str] = None
    VK_SECRET_KEY: Optional[str] = None

    # Настройки Redis
    REDIS_URL: Optional[str] = None
    CACHE_ENABLED: bool = False
    CACHE_TTL: int = 3600

    # Режим отладки
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Глобальный экземпляр настроек
settings = Settings()
