"""
API эндпоинты управления резервными копиями, дисковым пространством,
автоматизацией и системными ИИ-протоколами
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Body
from fastapi.responses import FileResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import os
from jose import jwt, JWTError
from sqlmodel import select

from app.core.database import Session, get_session
from app.services.backup_service import backup_service
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/system/backups", tags=["Система: Резервное копирование и ИИ"])


def get_current_user_auth(
    token_query: Optional[str] = Query(None, alias="token"),
    auth_header: Optional[str] = Header(None, alias="Authorization"),
    x_device_id: Optional[str] = Header(None, alias="X-Device-Id"),
    session: Session = Depends(get_session)
) -> User:
    """Универсальная аутентификация через заголовок Bearer или Query-параметр token"""
    raw_token = None
    if auth_header and auth_header.startswith("Bearer "):
        raw_token = auth_header[7:].strip()
    elif token_query:
        raw_token = token_query.strip()

    if not raw_token or raw_token in ("null", "undefined", "None", ""):
        raise HTTPException(status_code=401, detail="Не удалось валидировать учетные данные (токен отсутствует)")

    try:
        payload = jwt.decode(raw_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Не удалось валидировать учетные данные")
    except (JWTError, Exception):
        raise HTTPException(status_code=401, detail="Не удалось валидировать учетные данные")

    user = session.exec(select(User).where(User.id == int(user_id))).first()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user


class CreateBackupRequest(BaseModel):
    backup_type: str = "db_and_code"  # db_only, code_only, db_and_code, full_with_media


class UpdateSettingsRequest(BaseModel):
    auto_backup_enabled: bool = True
    schedule_interval: str = "daily_night"
    backup_type: str = "db_and_code"
    retention_days: int = 14
    max_backup_count: int = 10
    min_disk_free_gb: float = 3.0
    notify_admin_panel: bool = True


class UpdateAiPromptRequest(BaseModel):
    code: str
    title: str
    content: str
    is_active: bool = True
    priority: int = 10


class UpdateDocRequest(BaseModel):
    content: str


@router.get("")
@router.get("/")
@router.get("/dashboard")
def get_backups_dashboard(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_auth)
):
    """Сводная информация: список бэкапов, дисковое пространство и настройки"""
    backups = backup_service.list_backups()
    disk = backup_service.get_disk_info()
    settings_obj = backup_service.get_or_create_settings(session)
    return {
        "status": "success",
        "disk": disk,
        "backups": backups,
        "settings": settings_obj.dict()
    }


@router.post("/create")
def create_backup_endpoint(
    req: CreateBackupRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_auth)
):
    """Создание резервной копии вручную"""
    res = backup_service.create_backup(backup_type=req.backup_type)
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("message", "Ошибка создания бэкапа"))
    return res


@router.delete("/{filename}")
def delete_backup_endpoint(
    filename: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_auth)
):
    """Удаление указанного файла бэкапа"""
    res = backup_service.delete_backup(filename)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message", "Ошибка удаления"))
    return res


@router.get("/download/{filename}")
def download_backup_endpoint(
    filename: str,
    current_user: User = Depends(get_current_user_auth)
):
    """Скачивание файла бэкапа"""
    clean_name = os.path.basename(filename)
    filepath = os.path.join(backup_service.backup_dir, clean_name)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Файл бэкапа не найден")
    return FileResponse(filepath, filename=clean_name, media_type="application/octet-stream")


@router.get("/settings")
def get_backup_settings_endpoint(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_auth)
):
    """Получение настроек автоматизации и ротации"""
    st = backup_service.get_or_create_settings(session)
    return {"status": "success", "settings": st.dict()}


@router.put("/settings")
def update_backup_settings_endpoint(
    req: UpdateSettingsRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_auth)
):
    """Сохранение настроек автоматизации и ротации"""
    st = backup_service.get_or_create_settings(session)
    st.auto_backup_enabled = req.auto_backup_enabled
    st.schedule_interval = req.schedule_interval
    st.backup_type = req.backup_type
    st.retention_days = req.retention_days
    st.max_backup_count = req.max_backup_count
    st.min_disk_free_gb = req.min_disk_free_gb
    st.notify_admin_panel = req.notify_admin_panel
    session.add(st)
    session.commit()
    session.refresh(st)
    return {"status": "success", "settings": st.dict(), "message": "Настройки успешно сохранены"}


@router.post("/retention/run")
def run_retention_policy_endpoint(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_auth)
):
    """Запуск автоочистки устаревших бэкапов прямо сейчас"""
    res = backup_service.apply_retention_policy()
    return res


# ------------------ ИИ-протоколы и Документация ------------------

@router.get("/ai-prompts")
def get_ai_prompts_endpoint(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_auth)
):
    """Получение списка единых системных промптов и регламентов для ИИ"""
    prompts = backup_service.get_ai_instructions(session)
    return {"status": "success", "prompts": prompts}


@router.put("/ai-prompts")
def save_ai_prompt_endpoint(
    req: UpdateAiPromptRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_auth)
):
    """Сохранение или обновление ИИ-протокола"""
    res = backup_service.save_ai_instruction(session, req.dict())
    return {"status": "success", "prompt": res, "message": "Протокол успешно обновлен"}


@router.get("/docs/{doc_name}")
def get_doc_endpoint(
    doc_name: str,
    current_user: User = Depends(get_current_user_auth)
):
    """Чтение содержимого файла документации (system_faq, sitenav, sql_faq)"""
    res = backup_service.get_document(doc_name)
    if res.get("status") == "error":
        raise HTTPException(status_code=404, detail=res.get("message"))
    return res


@router.put("/docs/{doc_name}")
def save_doc_endpoint(
    doc_name: str,
    req: UpdateDocRequest,
    current_user: User = Depends(get_current_user_auth)
):
    """Сохранение файла документации"""
    res = backup_service.save_document(doc_name, req.content)
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("message"))
    return res
