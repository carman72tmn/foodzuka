"""
API эндпоинты для модуля «Помощники ИИ» (AI Site Assistants)
Включает:
- Управление виртуальными помощниками (CRUD, привязка к страницам, скины, квоты)
- Быстрый опрос оперативной аналитики и подсказок (0 токенов LLM)
- Интерактивный диалог с персонажем-помощником
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Header
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from pydantic import BaseModel, ConfigDict
from jose import jwt

from app.core.database import get_session
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.user import User
from app.models.ai_assistant import AiSiteAssistant, AiAssistantMessage
from app.services.ai_assistant_service import ai_assistant_service

router = APIRouter(prefix="/ai-assistants", tags=["AI Assistants"])

oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    session: Session = Depends(get_session)
) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id:
            return session.get(User, int(user_id))
    except Exception:
        return None
    return None

class AssistantCreateUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    code: Optional[str] = None
    role_title: str
    avatar_skin: str = "chef_male"
    avatar_custom_url: Optional[str] = None
    avatar_animation_mode: str = "alive"
    character_tone: str = "professional"
    assigned_pages: List[str] = ["*"]
    zone_of_responsibility: str = "full_control"
    linked_agent_code: Optional[str] = "omni_assistant"
    connection_id: Optional[Any] = None
    model_override: Optional[str] = None
    is_active: bool = True
    allow_sound_alerts: bool = True
    allow_voice_tts: bool = False
    daily_token_limit: Any = 50000
    daily_requests_limit: Any = 100
    auto_check_interval_sec: Any = 30
    system_prompt_addon: Optional[str] = None
    allow_external_queries: bool = True
    allow_iiko_api_queries: bool = False
    allow_iiko_export: bool = False
    allowed_external_tools: List[str] = ["weather", "general_search", "consulting"]
    iiko_allowed_actions: List[str] = ["read_orders", "read_menu", "read_stop_list"]
    enable_analytics_learning: bool = True

class AssistantUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    code: Optional[str] = None
    role_title: Optional[str] = None
    avatar_skin: Optional[str] = None
    avatar_custom_url: Optional[str] = None
    avatar_animation_mode: Optional[str] = None
    character_tone: Optional[str] = None
    assigned_pages: Optional[List[str]] = None
    zone_of_responsibility: Optional[str] = None
    linked_agent_code: Optional[str] = None
    connection_id: Optional[Any] = None
    model_override: Optional[str] = None
    is_active: Optional[bool] = None
    allow_sound_alerts: Optional[bool] = None
    allow_voice_tts: Optional[bool] = None
    daily_token_limit: Optional[Any] = None
    daily_requests_limit: Optional[Any] = None
    auto_check_interval_sec: Optional[Any] = None
    system_prompt_addon: Optional[str] = None
    allow_external_queries: Optional[bool] = None
    allow_iiko_api_queries: Optional[bool] = None
    allow_iiko_export: Optional[bool] = None
    allowed_external_tools: Optional[List[str]] = None
    iiko_allowed_actions: Optional[List[str]] = None
    enable_analytics_learning: Optional[bool] = None

class AssistantToggleSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")
    is_active: Optional[bool] = None

class ChatWithAssistantSchema(BaseModel):
    message: str
    session_id: Optional[str] = None
    page_route: Optional[str] = None

@router.get("/", response_model=List[AiSiteAssistant])
def list_assistants(
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Список всех помощников"""
    # Гарантируем наличие базовых помощников
    ai_assistant_service.seed_default_assistants(session)
    return ai_assistant_service.get_all_assistants(session)

@router.get("/active-for-page")
def get_active_assistant_for_page(
    route: str = Query("/", description="Текущий маршрут страницы"),
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Возвращает активного помощника для страницы и свежие подсказки"""
    ai_assistant_service.seed_default_assistants(session)
    assistant = ai_assistant_service.get_active_assistant_for_page(session, route)
    if not assistant:
        return {"active": False, "assistant": None, "tips": [], "metrics": {}}

    ops = ai_assistant_service.get_operational_metrics_and_tips(session, assistant)
    return {
        "active": True,
        "assistant": assistant,
        "tips": ops.get("tips", []),
        "metrics": ops.get("metrics", {}),
        "status": ops.get("status", "ok")
    }

@router.get("/operational-tips")
def get_operational_tips(
    assistant_id: Optional[int] = None,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Быстрый опрос подсказок и метрик (0 токенов LLM)"""
    assistant = None
    if assistant_id:
        assistant = ai_assistant_service.get_assistant_by_id(session, assistant_id)
    return ai_assistant_service.get_operational_metrics_and_tips(session, assistant)

@router.post("/", response_model=AiSiteAssistant)
def create_assistant(
    payload: AssistantCreateUpdateSchema,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Создание нового помощника"""
    return ai_assistant_service.create_assistant(session, payload.dict())

@router.patch("/{assistant_id}/toggle", response_model=AiSiteAssistant)
@router.put("/{assistant_id}/toggle", response_model=AiSiteAssistant)
def toggle_assistant_endpoint(
    assistant_id: int,
    payload: Optional[AssistantToggleSchema] = None,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Быстрое переключение активности помощника (вкл/выкл)"""
    is_active = payload.is_active if payload else None
    res = ai_assistant_service.toggle_assistant_active(session, assistant_id, is_active)
    if not res:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return res

@router.put("/{assistant_id}", response_model=AiSiteAssistant)
def update_assistant(
    assistant_id: int,
    payload: AssistantUpdateSchema,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Обновление помощника (поддерживает частичные обновления и новые настройки)"""
    res = ai_assistant_service.update_assistant(session, assistant_id, payload.dict(exclude_unset=True))
    if not res:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return res

@router.delete("/{assistant_id}")
def delete_assistant(
    assistant_id: int,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Удаление помощника"""
    ok = ai_assistant_service.delete_assistant(session, assistant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return {"status": "success", "deleted_id": assistant_id}


@router.get("/all-active")
def get_all_active_assistants(
    session: Session = Depends(get_session)
):
    """Список всех активных помощников для селектора в плавающем окне"""
    from sqlmodel import select
    return session.exec(select(AiSiteAssistant).where(AiSiteAssistant.is_active == True).order_by(AiSiteAssistant.id.asc())).all()

@router.get("/analytics/observations")
def get_analytics_observations_endpoint(
    days: int = Query(7, ge=1, le=90),
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Наблюдения и аналитика работы админки (Zero-Token mode)"""
    return ai_assistant_service.get_analytics_observations(session, days=days)

@router.post("/analytics/generate-ai-summary")
async def generate_ai_summary_endpoint(
    days: int = Query(7, ge=1, le=90),
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Генерация компактного стратегического ИИ-резюме (~150 токенов)"""
    return await ai_assistant_service.generate_ai_analytics_summary(session, days=days)

@router.post("/{assistant_id}/chat")
async def chat_with_assistant(
    assistant_id: int,
    payload: ChatWithAssistantSchema,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Диалог с виртуальным помощником"""
    try:
        user_id = current_user.id if current_user else None
        res = await ai_assistant_service.chat_with_assistant(
            session=session,
            assistant_id=assistant_id,
            user_message=payload.message,
            session_id=payload.session_id,
            page_route=payload.page_route,
            user_id=user_id
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{assistant_id}/history")
def get_assistant_history(
    assistant_id: int,
    session_id: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Получение истории сообщений помощника"""
    return ai_assistant_service.get_messages_history(session, assistant_id, session_id, limit)

@router.delete("/{assistant_id}/history")
def clear_assistant_history(
    assistant_id: int,
    session_id: Optional[str] = Query(None),
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Очистка истории сообщений"""
    ai_assistant_service.clear_messages_history(session, assistant_id, session_id)
    return {"status": "success", "cleared": True}
