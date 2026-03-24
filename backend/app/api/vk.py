from fastapi import APIRouter, Request, Response, HTTPException, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.db.session import get_session
from app.models.vk_settings import VkSettings
from app.services.vk_service import process_vk_event
from pydantic import BaseModel

router = APIRouter()

class VkSettingsSchema(BaseModel):
    vk_bot_token: str | None = None
    vk_confirmation_code: str | None = None
    vk_secret_key: str | None = None

@router.get("/settings", response_model=VkSettingsSchema)
async def get_vk_settings(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(VkSettings))
    settings_db = result.scalars().first()
    if not settings_db:
        return VkSettingsSchema()
    return settings_db

@router.post("/settings", response_model=VkSettingsSchema)
async def save_vk_settings(data: VkSettingsSchema, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(VkSettings))
    settings_db = result.scalars().first()
    
    if settings_db:
        settings_db.vk_bot_token = data.vk_bot_token
        settings_db.vk_confirmation_code = data.vk_confirmation_code
        settings_db.vk_secret_key = data.vk_secret_key
    else:
        settings_db = VkSettings(**data.model_dump())
        db.add(settings_db)
        
    await db.commit()
    await db.refresh(settings_db)
    return settings_db

@router.post("/webhook")
async def vk_webhook(request: Request, db: AsyncSession = Depends(get_session)):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
        
    result = await db.execute(select(VkSettings))
    vk_settings = result.scalars().first()
    
    # Check secret key if configured
    if vk_settings and vk_settings.vk_secret_key and data.get("secret") != vk_settings.vk_secret_key:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    event_type = data.get("type")
    
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
        # Log error but return ok so VK doesn't retry infinitely
        print(f"Error processing VK event: {e}")
        
    return Response(content="ok", media_type="text/plain")
