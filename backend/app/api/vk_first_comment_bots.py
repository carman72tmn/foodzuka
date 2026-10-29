from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel

from app.api.deps import get_db, require_permission
from app.models.vk_first_comment_settings import VkFirstCommentSettings
from app.models.vk_bot_connection import VkBotConnection
from app.core.datetime_utils import utc_now

router = APIRouter()

# --- Схемы данных Pydantic ---

class VkFirstCommentSettingsSchema(BaseModel):
    vk_bot_connection_id: int
    is_active: bool = False
    comments: List[str] = []
    post_type_filter: str = "all"
    include_keywords: Optional[str] = None
    exclude_keywords: Optional[str] = None
    delay_seconds: int = 0
    ignore_empty_text: bool = False
    exclude_reposts: bool = False
    delay_min: int = 0
    delay_max: int = 0
    vk_bot_token: Optional[str] = None


# --- Эндпоинты ---

@router.get("/connection/{connection_id}", response_model=Optional[VkFirstCommentSettings], dependencies=[Depends(require_permission("marketing_vk_bots_view"))])
def get_first_comment_settings(connection_id: int, db: Session = Depends(get_db)):
    """Получить настройки автокомментатора для подключения"""
    return db.exec(
        select(VkFirstCommentSettings).where(VkFirstCommentSettings.vk_bot_connection_id == connection_id)
    ).first()


@router.post("/", response_model=VkFirstCommentSettings, dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
def save_first_comment_settings(data: VkFirstCommentSettingsSchema, db: Session = Depends(get_db)):
    """Сохранить или обновить настройки автокомментатора"""
    # Проверяем, существует ли подключение ВК
    conn = db.get(VkBotConnection, data.vk_bot_connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Подключение ВК не найдено")

    # Валидируем количество вариантов комментариев (не более 15)
    if len(data.comments) > 15:
        raise HTTPException(status_code=400, detail="Максимальное количество вариантов комментариев - 15")

    # Очищаем пустые комментарии
    cleaned_comments = [c.strip() for c in data.comments if c and c.strip()]

    # Ищем существующие настройки
    settings = db.exec(
        select(VkFirstCommentSettings).where(VkFirstCommentSettings.vk_bot_connection_id == data.vk_bot_connection_id)
    ).first()

    if settings:
        settings.is_active = data.is_active
        settings.comments = cleaned_comments
        settings.post_type_filter = data.post_type_filter
        settings.include_keywords = data.include_keywords
        settings.exclude_keywords = data.exclude_keywords
        settings.delay_seconds = data.delay_seconds
        settings.ignore_empty_text = data.ignore_empty_text
        settings.exclude_reposts = data.exclude_reposts
        settings.delay_min = data.delay_min
        settings.delay_max = data.delay_max
        settings.vk_bot_token = data.vk_bot_token
        settings.updated_at = utc_now()
    else:
        settings = VkFirstCommentSettings(
            vk_bot_connection_id=data.vk_bot_connection_id,
            is_active=data.is_active,
            comments=cleaned_comments,
            post_type_filter=data.post_type_filter,
            include_keywords=data.include_keywords,
            exclude_keywords=data.exclude_keywords,
            delay_seconds=data.delay_seconds,
            ignore_empty_text=data.ignore_empty_text,
            exclude_reposts=data.exclude_reposts,
            delay_min=data.delay_min,
            delay_max=data.delay_max,
            vk_bot_token=data.vk_bot_token
        )
        
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings
