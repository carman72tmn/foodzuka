from fastapi import APIRouter, Request, Response, HTTPException, Depends
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.vk_settings import VkSettings
from app.models.vk_webhook_log import VkWebhookLog
from app.services.vk_service import process_vk_event
from pydantic import BaseModel
import httpx
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter()

class VkSettingsSchema(BaseModel):
    vk_bot_token: str | None = None
    vk_confirmation_code: str | None = None
    vk_group_id: str | None = None
    vk_secret_key: str | None = None

class VkLogResponse(BaseModel):
    id: int
    event_type: str
    payload: Dict[str, Any]
    created_at: Any

@router.get("/settings", response_model=VkSettingsSchema)
async def get_vk_settings(db: Session = Depends(get_session)):
    result = db.execute(select(VkSettings))
    settings_db = result.scalars().first()
    if not settings_db:
        return VkSettingsSchema()
    return settings_db

@router.post("/settings", response_model=VkSettingsSchema)
async def save_vk_settings(data: VkSettingsSchema, db: Session = Depends(get_session)):
    result = db.execute(select(VkSettings))
    settings_db = result.scalars().first()
    
    if settings_db:
        settings_db.vk_bot_token = data.vk_bot_token
        settings_db.vk_confirmation_code = data.vk_confirmation_code
        settings_db.vk_group_id = data.vk_group_id
        settings_db.vk_secret_key = data.vk_secret_key
    else:
        settings_db = VkSettings(**data.model_dump())
        db.add(settings_db)
        
    db.commit()
    db.refresh(settings_db)
    return settings_db

@router.get("/test-connection")
async def test_vk_connection(db: Session = Depends(get_session)):
    """Проверка валидности токена бота"""
    result = db.execute(select(VkSettings))
    vk_settings = result.scalars().first()
    
    if not vk_settings or not vk_settings.vk_bot_token:
        raise HTTPException(status_code=400, detail="Токен бота не настроен")
        
    async with httpx.AsyncClient() as client:
        try:
            # Простейший запрос к API VK для проверки токена
            response = await client.get(
                "https://api.vk.com/method/groups.getById",
                params={
                    "access_token": vk_settings.vk_bot_token,
                    "v": "5.131"
                }
            )
            data = response.json()
            if "error" in data:
                return {"status": "error", "message": data["error"].get("error_msg", "Ошибка API VK")}
            return {"status": "success", "message": "Соединение с VK успешно установлено", "data": data.get("response")}
        except Exception as e:
            return {"status": "error", "message": str(e)}

@router.post("/webhook")
async def vk_webhook(request: Request, db: Session = Depends(get_session)):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
        
    event_type = data.get("type")
    
    # Логируем входящее событие
    try:
        log_entry = VkWebhookLog(event_type=event_type or "unknown", payload=data)
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Ошибка при сохранении лога VK: {e}")

    result = db.execute(select(VkSettings))
    vk_settings = result.scalars().first()
    
    # Check secret key if configured
    if vk_settings and vk_settings.vk_secret_key and data.get("secret") != vk_settings.vk_secret_key:
        # Если это не подтверждение адреса, проверяем секрет
        if event_type != "confirmation":
            raise HTTPException(status_code=403, detail="Invalid secret key")
    
    # Confirmation event
    if event_type == "confirmation":
        if not vk_settings or not vk_settings.vk_confirmation_code:
            return Response(content="ok", media_type="text/plain")
        return Response(content=vk_settings.vk_confirmation_code, media_type="text/plain")
    
    # Process other events
    bot_token = vk_settings.vk_bot_token if vk_settings else None
    try:
        await process_vk_event(data, db, bot_token)
    except Exception as e:
        logger.error(f"Error processing VK event: {e}")
        
    return Response(content="ok", media_type="text/plain")

@router.get("/logs", response_model=List[VkLogResponse])
async def get_vk_logs(limit: int = 50, db: Session = Depends(get_session)):
    """Получение последних событий VK"""
    result = db.execute(
        select(VkWebhookLog).order_by(VkWebhookLog.created_at.desc()).limit(limit)
    )
    return result.scalars().all()
