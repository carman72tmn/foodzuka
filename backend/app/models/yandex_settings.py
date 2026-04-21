"""
Модель настроек интеграции с Яндекс Картами
"""
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel


class YandexSettings(SQLModel, table=True):
    """Настройки API ключей Яндекс"""
    __tablename__ = "yandex_settings"

    id: Optional[int] = Field(default=None, primary_key=True)

    # API Ключи
    api_key_js: Optional[str] = Field(
        default=None, max_length=500, 
        description="JavaScript API и HTTP Геокодер (для карт и поиска адресов)"
    )
    api_key_suggest: Optional[str] = Field(
        default=None, max_length=500, 
        description="API Геосаджеста (для подсказок адресов)"
    )
    api_key_matrix: Optional[str] = Field(
        default=None, max_length=500, 
        description="Матрица расстояний и Построение маршрутов"
    )
    api_key_monitoring: Optional[str] = Field(
        default=None, max_length=500, 
        description="Маршрутизация: Планирование и Мониторинг"
    )
    api_key_static: Optional[str] = Field(
        default=None, max_length=500, 
        description="Static API Яндекс.Карт"
    )

    is_active: bool = Field(default=True, description="Активна ли интеграция")

    # Метаданные
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
