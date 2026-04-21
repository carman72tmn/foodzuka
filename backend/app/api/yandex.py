from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from app.core.database import get_session
from app.models.yandex_settings import YandexSettings
from app.services.yandex_service import yandex_service
from pydantic import BaseModel

router = APIRouter(prefix="/yandex", tags=["yandex"])

class YandexSettingsUpdate(BaseModel):
    api_key_js: Optional[str] = None
    api_key_suggest: Optional[str] = None
    api_key_matrix: Optional[str] = None
    api_key_monitoring: Optional[str] = None
    api_key_static: Optional[str] = None
    is_active: bool = True

@router.get("/settings", response_model=YandexSettings)
async def get_yandex_settings(session: Session = Depends(get_session)):
    settings = session.exec(select(YandexSettings)).first()
    if not settings:
        # Создаем пустые настройки если их нет
        settings = YandexSettings()
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings

@router.post("/settings", response_model=YandexSettings)
async def update_yandex_settings(data: YandexSettingsUpdate, session: Session = Depends(get_session)):
    settings = session.exec(select(YandexSettings)).first()
    if not settings:
        settings = YandexSettings()
        session.add(settings)
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(settings, key, value)
    
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings

@router.post("/test-key")
async def test_yandex_key(key_type: str, api_key: str):
    """Проверка ключа Яндекса"""
    if key_type == "geocoder":
        success = await yandex_service.test_geocoder_key(api_key)
        if success:
            return {"status": "ok", "message": "Ключ успешно проверен"}
        else:
            raise HTTPException(status_code=400, detail="Неверный ключ или ошибка API")
    
    # Для остальных типов пока просто возвращаем успех (заглушка)
    return {"status": "ok", "message": f"Проверка для {key_type} будет реализована позже"}
