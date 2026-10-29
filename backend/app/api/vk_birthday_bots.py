import os
import shutil
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status
from sqlmodel import Session, select
from pydantic import BaseModel

from app.api.deps import get_db, require_permission
from app.models.vk_birthday_bot import VkBirthdayBot, VkBirthdayPost
from app.models.vk_bot_connection import VkBotConnection
from app.services.vk_birthday_service import vk_birthday_service
from app.core.datetime_utils import utc_now

router = APIRouter()

# --- Схемы данных Pydantic ---

class VkBirthdayBotCreateSchema(BaseModel):
    vk_bot_connection_id: int
    is_active: bool = True
    message_template: str
    image_url: Optional[str] = None
    include_names: bool = True
    name_format: str = "fullname"
    make_links: bool = True
    publish_time: str = "10:00"
    delete_mode: str = "interval"
    delete_interval_minutes: int = 720
    delete_time: Optional[str] = "22:00"
    vk_bot_token: Optional[str] = None

class VkBirthdayBotUpdateSchema(BaseModel):
    is_active: Optional[bool] = None
    message_template: Optional[str] = None
    image_url: Optional[str] = None
    include_names: Optional[bool] = None
    name_format: Optional[str] = None
    make_links: Optional[bool] = None
    publish_time: Optional[str] = None
    delete_mode: Optional[str] = None
    delete_interval_minutes: Optional[int] = None
    delete_time: Optional[str] = None
    vk_bot_token: Optional[str] = None


# --- Эндпоинты ---

@router.get("/", response_model=List[VkBirthdayBot], dependencies=[Depends(require_permission("marketing_vk_bots_view"))])
def get_birthday_bots(db: Session = Depends(get_db)):
    """Получить список всех настроенных ботов именинников"""
    return db.exec(select(VkBirthdayBot)).all()


@router.post("/", response_model=VkBirthdayBot, dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
def create_birthday_bot(data: VkBirthdayBotCreateSchema, db: Session = Depends(get_db)):
    """Создать новые настройки бота именинников"""
    # Проверим, существует ли такое подключение ВК
    conn = db.get(VkBotConnection, data.vk_bot_connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Подключение ВК не найдено")

    # Проверим, нет ли уже настроек бота для этого подключения
    existing = db.exec(
        select(VkBirthdayBot).where(VkBirthdayBot.vk_bot_connection_id == data.vk_bot_connection_id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Для этого подключения ВК уже настроен бот именинников")

    new_bot = VkBirthdayBot(**data.model_dump())
    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)
    return new_bot


@router.patch("/{bot_id}", response_model=VkBirthdayBot, dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
def update_birthday_bot(bot_id: int, data: VkBirthdayBotUpdateSchema, db: Session = Depends(get_db)):
    """Обновить настройки бота именинников"""
    bot = db.get(VkBirthdayBot, bot_id)
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
def delete_birthday_bot(bot_id: int, db: Session = Depends(get_db)):
    """Удалить настройки бота именинников"""
    bot = db.get(VkBirthdayBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Настройки бота не найдены")

    db.delete(bot)
    db.commit()
    return {"status": "success", "message": "Бот поздравлений успешно удален"}


@router.post("/{bot_id}/test-publish", dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
async def test_publish_birthday(bot_id: int, db: Session = Depends(get_db)):
    """Запустить проверку именинников и публикацию поздравления прямо сейчас (вручную)"""
    bot = db.get(VkBirthdayBot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Настройки бота не найдены")

    # Сбрасываем last_run_date, чтобы разрешить принудительный ручной запуск
    bot.last_run_date = None
    db.add(bot)
    db.commit()

    post_id = await vk_birthday_service.publish_birthday_post(db, bot)
    if post_id:
        return {"status": "success", "message": f"Поздравление успешно опубликовано. ID поста: {post_id}", "post_id": post_id}
    else:
        return {"status": "info", "message": "Сегодня нет именинников среди подписчиков сообщества или возникла ошибка публикации"}


@router.post("/upload-image", dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
async def upload_birthday_image(file: UploadFile = File(...)):
    """Загрузка поздравительного изображения на сервер"""
    try:
        # Проверка расширения файла
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ('.png', '.jpg', '.jpeg', '.gif', '.webp'):
            raise HTTPException(status_code=400, detail="Разрешены только файлы изображений (png, jpg, jpeg, gif, webp)")

        # Создаем папку, если ее нет
        media_dir = "/app/media/img/vk_bots"
        os.makedirs(media_dir, exist_ok=True)

        # Формируем имя файла
        filename = f"birthday_{int(datetime.now().timestamp())}{ext}"
        file_path = os.path.join(media_dir, filename)

        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Возвращаем относительный путь для сохранения в БД и вывода на фронтенде
        relative_url = f"/media/img/vk_bots/{filename}"
        return {"status": "success", "image_url": relative_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении изображения на сервере: {str(e)}")
