"""
Модель Историй (Информационные блоки в стиле Instagram/VK)
"""
from typing import Optional
from datetime import datetime
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel


class Story(SQLModel, table=True):
    """
    Таблица визуальных "историй" (Stories), которые показываются на главном экране сайта/приложения.
    Используются для уведомлений об акциях, новинках или просто как контент.
    """
    __tablename__ = "stories"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Контент
    title: str = Field(max_length=255, description="Внутреннее название")
    image_url: str = Field(max_length=500, description="URL обложки истории")
    video_url: Optional[str] = Field(default=None, max_length=500, description="URL видео (опционально)")
    
    # Действие по клику (например переход на страницу товара или категории)
    action_type: Optional[str] = Field(
        default=None, max_length=50,
        description="open_product, open_category, open_promo, external_link"
    )
    action_target: Optional[str] = Field(
        default=None, max_length=255,
        description="ID товара, ID категории или URL"
    )
    action_button_text: Optional[str] = Field(default="Подробнее", max_length=50)
    
    # Статус и тайминг
    is_active: bool = Field(default=True, description="Показывать ли историю")
    sort_order: int = Field(default=0, description="Порядок сортировки (меньше - левее)")
    
    valid_from: Optional[datetime] = Field(default=None, description="Показывать с")
    valid_until: Optional[datetime] = Field(default=None, description="Показывать до")
    
    # Статистика (просмотры/клики)
    views_count: int = Field(default=0)
    clicks_count: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
