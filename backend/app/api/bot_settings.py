import httpx
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.bot_settings import BotSettings
from app.api import deps
from app.models.user import User
from pydantic import BaseModel
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bot", tags=["Telegram Settings"])

class BotSettingsSchema(BaseModel):
    is_bot_active: bool = False
    telegram_bot_token: Optional[str] = None
    bot_username: Optional[str] = None
    system_channel_id: Optional[str] = None
    is_system_notifications_active: bool = False
    is_client_broadcast_active: bool = False
    is_user_client_active: bool = False
    user_phone: Optional[str] = None
    user_api_id: Optional[str] = None
    user_api_hash: Optional[str] = None
    user_account_status: Optional[str] = "not_connected"
    welcome_message: Optional[str] = None

class ToggleChannelSchema(BaseModel):
    field: str
    value: bool

class TestMessageSchema(BaseModel):
    chat_id: Optional[str] = None
    message: Optional[str] = "🔔 Тестовое уведомление из панели управления Vezuroll"


@router.get("/settings", response_model=BotSettingsSchema)
async def get_bot_settings(
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("settings_bot_view"))
):
    """Получить текущие настройки Telegram интеграции"""
    result = db.execute(select(BotSettings))
    settings_db = result.scalars().first()
    if not settings_db:
        return BotSettingsSchema()
    return settings_db


@router.post("/settings", response_model=BotSettingsSchema)
async def save_bot_settings(
    data: BotSettingsSchema, 
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("settings_bot_view"))
):
    """Сохранить настройки Telegram интеграции"""
    result = db.execute(select(BotSettings))
    settings_db = result.scalars().first()
    
    if settings_db:
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(settings_db, k, v)
        settings_db.updated_at = datetime.now(timezone.utc)
    else:
        settings_db = BotSettings(**data.model_dump())
        db.add(settings_db)
        
    db.commit()
    db.refresh(settings_db)
    return settings_db


@router.post("/test-connection")
async def test_bot_connection(
    data: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("settings_bot_view"))
):
    """Проверка подключения Telegram Бота через getMe"""
    token = None
    if data and data.get("token"):
        token = data.get("token").strip()
    else:
        result = db.execute(select(BotSettings))
        settings_db = result.scalars().first()
        if settings_db and settings_db.telegram_bot_token:
            token = settings_db.telegram_bot_token.strip()

    if not token:
        raise HTTPException(status_code=400, detail="Токен бота не указан")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"https://api.telegram.org/bot{token}/getMe")
            res_json = resp.json()

            if not res_json.get("ok"):
                desc = res_json.get("description", "Неизвестная ошибка Telegram API")
                raise HTTPException(status_code=400, detail=f"Ошибка Telegram API: {desc}")

            bot_info = res_json.get("result", {})
            username = bot_info.get("username")
            first_name = bot_info.get("first_name", "")

            # Обновляем username в настройках если запись существует
            result = db.execute(select(BotSettings))
            settings_db = result.scalars().first()
            if settings_db:
                settings_db.bot_username = username
                settings_db.updated_at = datetime.now(timezone.utc)
                db.commit()

            return {
                "status": "success",
                "message": f"Бот успешно подключен: @{username} ({first_name})",
                "bot": bot_info
            }
    except httpx.RequestError as e:
        logger.error(f"Network error testing Telegram bot: {e}")
        raise HTTPException(status_code=502, detail=f"Сетевая ошибка подключения к Telegram API: {str(e)}")


@router.post("/test-channel")
async def test_channel_notification(
    data: TestMessageSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("settings_bot_view"))
):
    """Отправка тестового сообщения в канал Telegram"""
    result = db.execute(select(BotSettings))
    settings_db = result.scalars().first()

    if not settings_db or not settings_db.telegram_bot_token:
        raise HTTPException(status_code=400, detail="Токен Telegram бота не настроен")

    target_chat = data.chat_id or settings_db.system_channel_id
    if not target_chat:
        raise HTTPException(status_code=400, detail="ID канала или чата не указан")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{settings_db.telegram_bot_token}/sendMessage",
                json={
                    "chat_id": target_chat,
                    "text": data.message or "🔔 Тестовое уведомление из панели управления Vezuroll",
                    "parse_mode": "HTML"
                }
            )
            res_json = resp.json()
            if not res_json.get("ok"):
                desc = res_json.get("description", "Ошибка отправки в канал")
                raise HTTPException(status_code=400, detail=f"Ошибка Telegram: {desc}. Убедитесь, что бот добавлен в канал администратором.")

            return {
                "status": "success",
                "message": f"Тестовое сообщение успешно отправлено в {target_chat}!"
            }
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Сетевая ошибка: {str(e)}")


@router.patch("/toggle-channel")
async def toggle_channel(
    data: ToggleChannelSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("settings_bot_view"))
):
    """Быстрое включение/отключение канала или функции рассылки"""
    allowed_fields = [
        "is_bot_active", 
        "is_system_notifications_active", 
        "is_client_broadcast_active", 
        "is_user_client_active"
    ]
    if data.field not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"Недопустимое поле. Допустимо: {allowed_fields}")

    result = db.execute(select(BotSettings))
    settings_db = result.scalars().first()
    if not settings_db:
        settings_db = BotSettings()
        db.add(settings_db)

    setattr(settings_db, data.field, data.value)
    settings_db.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(settings_db)

    return {
        "status": "success",
        "field": data.field,
        "value": data.value,
        "message": f"Состояние {data.field} изменено на {data.value}"
    }
