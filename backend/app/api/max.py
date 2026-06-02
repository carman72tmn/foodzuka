from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.max_settings import MaxSettings, MaxBot
from pydantic import BaseModel
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Schemas ---

class MaxBotSchema(BaseModel):
    id: Optional[int] = None
    bot_type: str
    bot_name: str
    bot_token: str
    bot_external_id: Optional[str] = None
    is_active: bool = True

class MaxSettingsSchema(BaseModel):
    id: Optional[int] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: str = "https://api.max-service.ru/v1"
    sender_name: Optional[str] = None
    default_template: Optional[str] = None
    is_active: bool = False
    bots: List[MaxBotSchema] = []

# --- Endpoints ---

@router.get("/settings", response_model=MaxSettingsSchema)
def get_max_settings(db: Session = Depends(get_session)):
    """Получение настроек MAX и списка ботов"""
    settings = db.exec(select(MaxSettings)).first()
    if not settings:
        return MaxSettingsSchema()
    
    # SQLModelRelationship подгрузит ботов автоматически при обращении к свойству
    return settings

@router.post("/settings", response_model=MaxSettingsSchema)
def save_max_settings(data: MaxSettingsSchema, db: Session = Depends(get_session)):
    """Сохранение основных настроек MAX"""
    settings = db.exec(select(MaxSettings)).first()
    
    if settings:
        settings.api_key = data.api_key
        settings.api_secret = data.api_secret
        settings.base_url = data.base_url
        settings.sender_name = data.sender_name
        settings.default_template = data.default_template
        settings.is_active = data.is_active
    else:
        # Создаем новые настройки (без ботов, боты управляются отдельно)
        settings = MaxSettings(
            api_key=data.api_key,
            api_secret=data.api_secret,
            base_url=data.base_url,
            sender_name=data.sender_name,
            default_template=data.default_template,
            is_active=data.is_active
        )
        db.add(settings)
        
    db.commit()
    db.refresh(settings)
    return settings

@router.post("/bots", response_model=MaxBotSchema)
def add_max_bot(data: MaxBotSchema, db: Session = Depends(get_session)):
    """Добавление нового бота в MAX"""
    settings = db.exec(select(MaxSettings)).first()
    if not settings:
        # Создаем пустые настройки если их нет
        settings = MaxSettings(is_active=False)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    new_bot = MaxBot(
        max_settings_id=settings.id,
        bot_type=data.bot_type,
        bot_name=data.bot_name,
        bot_token=data.bot_token,
        bot_external_id=data.bot_external_id,
        is_active=data.is_active
    )
    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)
    return new_bot

@router.put("/bots/{bot_id}", response_model=MaxBotSchema)
def update_max_bot(bot_id: int, data: MaxBotSchema, db: Session = Depends(get_session)):
    """Обновление данных бота"""
    bot = db.get(MaxBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")
    
    bot.bot_type = data.bot_type
    bot.bot_name = data.bot_name
    bot.bot_token = data.bot_token
    bot.bot_external_id = data.bot_external_id
    bot.is_active = data.is_active
    
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot

@router.delete("/bots/{bot_id}")
def delete_max_bot(bot_id: int, db: Session = Depends(get_session)):
    """Удаление бота"""
    bot = db.get(MaxBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")
    
    db.delete(bot)
    db.commit()
    return {"status": "success", "message": "Бот удален"}
