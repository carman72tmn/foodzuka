import os
import shutil
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status
from sqlmodel import Session, select
from pydantic import BaseModel

from app.api.deps import get_db, require_permission
from app.models.vk_post_scheduler import VkPostScheduler
from app.models.vk_bot_connection import VkBotConnection
from app.services.vk_scheduler_service import vk_scheduler_service
from app.core.datetime_utils import utc_now

router = APIRouter()

# --- Схемы данных Pydantic ---

class VkPostSchedulerCreateSchema(BaseModel):
    vk_bot_connection_id: int
    type: str = "post" # "post" или "story"
    content_text: Optional[str] = None
    media_url: Optional[str] = None
    publish_at: datetime
    link_url: Optional[str] = None
    button_text: Optional[str] = None

class VkPostSchedulerUpdateSchema(BaseModel):
    type: Optional[str] = None
    content_text: Optional[str] = None
    media_url: Optional[str] = None
    publish_at: Optional[datetime] = None
    link_url: Optional[str] = None
    button_text: Optional[str] = None
    status: Optional[str] = None

# --- Эндпоинты ---

@router.get("/", response_model=List[VkPostScheduler], dependencies=[Depends(require_permission("marketing_vk_bots_view"))])
def get_scheduled_publications(vk_bot_connection_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Получить список всех отложенных публикаций (опционально по подключению ВК)"""
    query = select(VkPostScheduler)
    if vk_bot_connection_id is not None:
        query = query.where(VkPostScheduler.vk_bot_connection_id == vk_bot_connection_id)
    return db.exec(query.order_by(VkPostScheduler.publish_at.asc())).all()


@router.post("/", response_model=VkPostScheduler, dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
def create_scheduled_publication(data: VkPostSchedulerCreateSchema, db: Session = Depends(get_db)):
    """Создать новую отложенную публикацию (пост или сторис)"""
    conn = db.get(VkBotConnection, data.vk_bot_connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Подключение ВК не найдено")

    # Предотвращаем публикацию сторис без картинки
    if data.type == "story" and not data.media_url:
        raise HTTPException(status_code=400, detail="Для историй обязательно наличие изображения")

    new_job = VkPostScheduler(**data.model_dump())
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job


@router.patch("/{job_id}", response_model=VkPostScheduler, dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
def update_scheduled_publication(job_id: int, data: VkPostSchedulerUpdateSchema, db: Session = Depends(get_db)):
    """Обновить настройки отложенной публикации"""
    job = db.get(VkPostScheduler, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Публикация не найдена")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(job, key, value)

    job.updated_at = utc_now()
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}", dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
def delete_scheduled_publication(job_id: int, db: Session = Depends(get_db)):
    """Удалить запланированную публикацию"""
    job = db.get(VkPostScheduler, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Публикация не найдена")

    db.delete(job)
    db.commit()
    return {"status": "success", "message": "Запланированная публикация успешно удалена"}


@router.post("/{job_id}/publish", dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
async def trigger_manual_publish(job_id: int, db: Session = Depends(get_db)):
    """Опубликовать запись прямо сейчас (вручную)"""
    job = db.get(VkPostScheduler, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Публикация не найдена")

    success = await vk_scheduler_service.execute_publication(db, job)
    if success:
        return {"status": "success", "message": "Публикация успешно размещена во ВКонтакте"}
    else:
        raise HTTPException(status_code=500, detail=f"Ошибка публикации: {job.error_message}")


@router.post("/upload-media", dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
async def upload_scheduler_media(file: UploadFile = File(...)):
    """Загрузка изображения или видео на сервер для использования в отложенном постинке"""
    try:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.mp4', '.mov', '.avi'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Разрешены только файлы изображений (png, jpg, jpeg, gif, webp) или видео (mp4, mov, avi)"
            )

        media_dir = "/app/media/img/vk_bots"
        os.makedirs(media_dir, exist_ok=True)

        filename = f"sched_{int(datetime.now().timestamp())}{ext}"
        file_path = os.path.join(media_dir, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        relative_url = f"/media/img/vk_bots/{filename}"
        return {"status": "success", "media_url": relative_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении файла на сервере: {str(e)}")
