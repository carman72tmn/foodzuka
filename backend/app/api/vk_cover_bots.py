import os
import shutil
import base64
from io import BytesIO
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlmodel import Session, select
from pydantic import BaseModel

from app.api.deps import get_db, require_permission
from app.models.vk_cover_bot import VkCoverBot
from app.models.vk_bot_connection import VkBotConnection
from app.services.vk_cover_service import vk_cover_service
from app.core.datetime_utils import utc_now

router = APIRouter()

# --- Схемы данных Pydantic ---

class VkCoverBotCreateSchema(BaseModel):
    vk_bot_connection_id: int
    name: str = "Основная обложка"
    is_active: bool = True
    is_rotation_enabled: bool = True
    schedule_type: str = "always"
    schedule_start_time: Optional[str] = None
    schedule_end_time: Optional[str] = None
    rotation_order: int = 0
    background_image_url: Optional[str] = None
    slideshow_images: List[str] = []
    slideshow_interval_minutes: int = 5
    slideshow_mode: str = "sequence"
    city_weather: str = "Москва"
    widgets: List[Dict[str, Any]] = []
    update_interval: str = "1m"
    use_custom_callback: bool = False
    callback_confirmation_code: Optional[str] = None
    callback_secret_key: Optional[str] = None
    vk_bot_token: Optional[str] = None

class VkCoverBotUpdateSchema(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    is_rotation_enabled: Optional[bool] = None
    schedule_type: Optional[str] = None
    schedule_start_time: Optional[str] = None
    schedule_end_time: Optional[str] = None
    rotation_order: Optional[int] = None
    background_image_url: Optional[str] = None
    slideshow_images: Optional[List[str]] = None
    slideshow_interval_minutes: Optional[int] = None
    slideshow_mode: Optional[str] = None
    city_weather: Optional[str] = None
    widgets: Optional[List[Dict[str, Any]]] = None
    update_interval: Optional[str] = None
    use_custom_callback: Optional[bool] = None
    callback_confirmation_code: Optional[str] = None
    callback_secret_key: Optional[str] = None
    vk_bot_token: Optional[str] = None


# --- Эндпоинты ---

@router.get("/", response_model=List[VkCoverBot], dependencies=[Depends(require_permission("marketing_vk_bots_view"))])
def get_cover_bots(db: Session = Depends(get_db)):
    """Получить список всех ботов динамических обложек"""
    return db.exec(select(VkCoverBot)).all()


@router.post("/", response_model=VkCoverBot, dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
def create_cover_bot(data: VkCoverBotCreateSchema, db: Session = Depends(get_db)):
    """Создать новые настройки динамической обложки"""
    conn = db.get(VkBotConnection, data.vk_bot_connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Подключение ВК не найдено")

    new_bot = VkCoverBot(**data.model_dump())
    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)
    return new_bot


@router.patch("/{bot_id}", response_model=VkCoverBot, dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
def update_cover_bot(bot_id: int, data: VkCoverBotUpdateSchema, db: Session = Depends(get_db)):
    """Обновить настройки динамической обложки"""
    bot = db.get(VkCoverBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Настройки бота не найдены")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(bot, key, value)

    bot.updated_at = utc_now()
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot


@router.delete("/{bot_id}", dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
def delete_cover_bot(bot_id: int, db: Session = Depends(get_db)):
    """Удалить настройки динамической обложки"""
    bot = db.get(VkCoverBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Настройки бота не найдены")

    db.delete(bot)
    db.commit()
    return {"status": "success", "message": "Бот динамических обложек успешно удален"}


@router.post("/preview", dependencies=[Depends(require_permission("marketing_vk_bots_view"))])
async def get_cover_preview(data: VkCoverBotCreateSchema, db: Session = Depends(get_db)):
    """Генерация и возврат обложки в виде base64 для предпросмотра на фронтенде"""
    try:
        # Создаем временный объект бота без сохранения в БД для рендеринга
        temp_bot = VkCoverBot(**data.model_dump())
        
        # Генерируем картинку
        img = await vk_cover_service.generate_cover_image(db, temp_bot)
        
        # Сохраняем в байты и кодируем в base64
        buf = BytesIO()
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()
        base64_str = base64.b64encode(img_bytes).decode("utf-8")
        
        return {"status": "success", "image": f"data:image/png;base64,{base64_str}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации превью обложки: {str(e)}")


@router.post("/{bot_id}/publish-now", dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
async def publish_cover_now(bot_id: int, db: Session = Depends(get_db)):
    """Принудительно обновить обложку в группе ВК прямо сейчас"""
    bot = db.get(VkCoverBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Настройки бота не найдены")

    success = await vk_cover_service.publish_cover(db, bot)
    if success:
        return {"status": "success", "message": "Обложка успешно обновлена в сообществе ВК"}
    else:
        raise HTTPException(status_code=500, detail="Не удалось обновить обложку в сообществе. Проверьте логи сервера и токен ВК.")


@router.post("/upload-background", dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
async def upload_cover_background(file: UploadFile = File(...)):
    """Загрузка фонового изображения для динамической обложки"""
    try:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ('.png', '.jpg', '.jpeg', '.webp'):
            raise HTTPException(status_code=400, detail="Разрешены только файлы изображений (png, jpg, jpeg, webp)")

        # Создаем папку для обложек, если ее нет
        media_dir = "/app/media/img/vk_covers"
        os.makedirs(media_dir, exist_ok=True)

        # Формируем имя файла
        filename = f"cover_{int(datetime.now().timestamp())}{ext}"
        file_path = os.path.join(media_dir, filename)

        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Возвращаем относительный путь
        relative_url = f"/media/img/vk_covers/{filename}"
        return {"status": "success", "image_url": relative_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении изображения на сервере: {str(e)}")


@router.post("/webhook/{bot_id}")
async def vk_cover_webhook(bot_id: int, request: Request, db: Session = Depends(get_db)):
    """Вебхук для выделенного Callback API конкретной обложки"""
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"VK Cover Webhook JSON error for bot {bot_id}: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    bot = db.get(VkCoverBot, bot_id)
    if not bot or not bot.is_active:
        raise HTTPException(status_code=404, detail="Active Cover Bot not found")

    event_type = data.get("type")
    
    # 1. Confirmation event
    if event_type == "confirmation":
        conf_code = bot.callback_confirmation_code
        if not conf_code:
            conn = db.get(VkBotConnection, bot.vk_bot_connection_id)
            if conn:
                conf_code = conn.vk_confirmation_code
        
        return PlainTextResponse(content=conf_code or "ok")

    # 2. Проверка секретного ключа (если он задан)
    secret_key = bot.callback_secret_key
    if secret_key and data.get("secret") != secret_key:
        raise HTTPException(status_code=403, detail="Invalid secret key")

    # 3. Обрабатываем событие
    conn = db.get(VkBotConnection, bot.vk_bot_connection_id)
    if conn and conn.is_active:
        from app.services.vk_service import process_vk_event
        try:
            await process_vk_event(data, db, conn.vk_bot_token, conn.vk_group_id)
        except Exception as e:
            logger.error(f"Error processing VK event inside cover webhook for bot {bot_id}: {e}")

        # Сразу перерисовываем и обновляем обложку
        try:
            await vk_cover_service.publish_cover(db, bot)
        except Exception as e:
            logger.error(f"Error updating cover on webhook trigger for bot {bot_id}: {e}")

    return PlainTextResponse(content="ok")
