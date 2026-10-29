"""
Модели базы данных для постинга в группах ВКонтакте от имени личного аккаунта
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel


class VkGroupPreset(SQLModel, table=True):
    """Готовые блоки (списки) групп для постинга"""
    __tablename__ = "vk_group_presets"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=150, description="Название списка групп (например, Барахолки Самары)")
    description: Optional[str] = Field(default=None, description="Описание или заметки по списку")
    
    # Список проверенных групп в JSONB:
    # [{"id": 123, "name": "...", "screen_name": "...", "type": "group", "can_post": 1, "photo": "...", "members_count": 500, "url": "..."}]
    groups_data: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
        description="Структурированный список сообществ"
    )

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class VkGroupPostCampaign(SQLModel, table=True):
    """Кампания / запуск рассылки постов по группам"""
    __tablename__ = "vk_group_post_campaigns"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200, description="Название или тема рассылки")
    text: str = Field(description="Текст публикации")
    media_urls: Optional[List[str]] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
        description="Ссылки на прикрепленные изображения"
    )
    
    account_id: int = Field(index=True, description="ID аккаунта из MultichatAccount")
    account_name: Optional[str] = Field(default=None, description="Имя аккаунта ВКонтакте")
    preset_id: Optional[int] = Field(default=None, index=True, description="ID использованного пресета (если был)")
    
    status: str = Field(default="completed", index=True, description="in_progress, completed, failed, stopped")
    delay_seconds: int = Field(default=20, description="Задержка между публикациями (сек)")
    
    total_count: int = Field(default=0, description="Всего целевых групп")
    success_count: int = Field(default=0, description="Успешно опубликовано")
    failed_count: int = Field(default=0, description="Ошибок при публикации")

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class VkGroupPostHistory(SQLModel, table=True):
    """История публикаций записей на стенах групп ВКонтакте и их аналитика"""
    __tablename__ = "vk_group_post_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: Optional[int] = Field(default=None, index=True, description="ID кампании рассылки")
    
    account_id: int = Field(index=True, description="ID аккаунта из MultichatAccount")
    account_name: Optional[str] = Field(default=None, description="Имя личного аккаунта ВК")
    
    group_id: int = Field(index=True, description="ID группы ВК (положительное число)")
    group_name: Optional[str] = Field(default=None, description="Название группы")
    group_screen_name: Optional[str] = Field(default=None, description="Короткий адрес группы (domain/screen_name)")
    group_photo: Optional[str] = Field(default=None, description="Аватарка сообщества")
    
    post_id: Optional[int] = Field(default=None, index=True, description="ID созданного поста в группе")
    post_url: Optional[str] = Field(default=None, description="Прямая ссылка на пост: https://vk.com/wall-{group_id}_{post_id}")
    
    text: Optional[str] = Field(default=None, description="Текст поста")
    media_urls: Optional[List[str]] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
        description="Прикрепленные медиафайлы"
    )
    
    status: str = Field(default="published", index=True, description="published, failed, deleted, forbidden")
    error_message: Optional[str] = Field(default=None, description="Текст ошибки, если публикация не удалась")
    
    # Метрики из wall.getById
    views_count: int = Field(default=0, description="Количество просмотров")
    likes_count: int = Field(default=0, description="Количество лайков")
    reposts_count: int = Field(default=0, description="Количество репостов")
    comments_count: int = Field(default=0, description="Количество комментариев")
    
    published_at: Optional[datetime] = Field(default=None, description="Время успешной публикации")
    last_checked_at: Optional[datetime] = Field(default=None, description="Время последней проверки метрик")
    
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# Алиас для совместимости
VkGroupPostingHistory = VkGroupPostHistory
