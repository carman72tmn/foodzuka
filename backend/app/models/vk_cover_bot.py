"""
Модели для бота динамических обложек ВКонтакте
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON

class VkCoverBot(SQLModel, table=True):
    """Настройки динамической обложки ВК"""
    __tablename__ = "vk_cover_bots"

    id: Optional[int] = Field(default=None, primary_key=True)
    vk_bot_connection_id: int = Field(
        foreign_key="vk_bot_connections.id", 
        index=True, 
        description="Ссылка на подключение бота ВК"
    )
    name: str = Field(default="Основная обложка", description="Пользовательское название обложки")
    is_active: bool = Field(default=True, description="Активна ли обложка")
    is_rotation_enabled: bool = Field(default=True, description="Участвует ли в авто-ротации")
    
    # Настройки расписания ротации
    schedule_type: str = Field(default="always", description="Тип расписания: always, time_range, interval")
    schedule_start_time: Optional[str] = Field(default=None, description="Время начала работы (HH:MM)")
    schedule_end_time: Optional[str] = Field(default=None, description="Время окончания работы (HH:MM)")
    rotation_order: int = Field(default=0, description="Порядок при ротации")
    
    # Изображения для фона и слайд-шоу
    background_image_url: Optional[str] = Field(default=None, description="Путь или URL фонового изображения")
    slideshow_images: List[str] = Field(
        default=[],
        sa_column=Column(JSON),
        description="Список изображений для слайд-шоу фона"
    )
    slideshow_interval_minutes: int = Field(default=5, description="Интервал смены фона в слайд-шоу (минуты)")
    slideshow_mode: str = Field(default="sequence", description="Режим слайд-шоу: sequence, random")

    city_weather: str = Field(default="Москва", description="Город для виджета погоды")
    update_interval: str = Field(default="1m", description="Интервал обновления обложки (1m, 2m, 3m, 5m, 15m, 30m, 1h, 6h, 12h, morning, day, evening, callback)")
    use_custom_callback: bool = Field(default=False, description="Использовать отдельный Callback API для обложки")
    callback_confirmation_code: Optional[str] = Field(default=None, description="Код подтверждения для собственного Callback API")
    callback_secret_key: Optional[str] = Field(default=None, description="Секретный ключ для собственного Callback API")
    
    # Список виджетов: [{"type": "clock", "x": 100, "y": 100, "font_size": 24, "color": "#ffffff"}, ...]
    widgets: List[Dict[str, Any]] = Field(
        default=[],
        sa_column=Column(JSON),
        description="JSON-список виджетов и их настроек"
    )

    last_published_at: Optional[datetime] = Field(default=None, description="Время последнего обновления обложки в ВК")
    vk_bot_token: Optional[str] = Field(default=None, description="Индивидуальный ключ сообщества для бота")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class VkCoverSubscriberActivity(SQLModel, table=True):
    """Кэш таблицы активности подписчиков для вывода топ-пользователей на обложке"""
    __tablename__ = "vk_cover_subscriber_activities"

    id: Optional[int] = Field(default=None, primary_key=True)
    vk_group_id: int = Field(index=True, description="ID группы ВКонтакте")
    vk_user_id: int = Field(index=True, description="ID пользователя ВКонтакте")
    first_name: str = Field(description="Имя")
    last_name: str = Field(description="Фамилия")
    avatar_url: Optional[str] = Field(default=None, description="URL аватара")
    score: int = Field(default=0, description="Набранные баллы активности")
    updated_at: datetime = Field(default_factory=utc_now, description="Время расчета")
