from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.bot_settings import BotSettings
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/bot", tags=["Bot Settings"])

class BotSettingsSchema(BaseModel):
    telegram_bot_token: str | None = None
    welcome_message: str | None = None

@router.get("/settings", response_model=BotSettingsSchema)
async def get_bot_settings(db: Session = Depends(get_session)):
    """Получить текущие настройки Telegram бота"""
    result = db.execute(select(BotSettings))
    settings_db = result.scalars().first()
    if not settings_db:
        return BotSettingsSchema()
    return settings_db

@router.post("/settings", response_model=BotSettingsSchema)
async def save_bot_settings(data: BotSettingsSchema, db: Session = Depends(get_session)):
    """Сохранить настройки Telegram бота"""
    result = db.execute(select(BotSettings))
    settings_db = result.scalars().first()
    
    if settings_db:
        settings_db.telegram_bot_token = data.telegram_bot_token
        if data.welcome_message:
            settings_db.welcome_message = data.welcome_message
        settings_db.updated_at = datetime.utcnow()
    else:
        settings_db = BotSettings(**data.model_dump())
        db.add(settings_db)
        
    db.commit()
    db.refresh(settings_db)
    return settings_db
