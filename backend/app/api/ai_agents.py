"""
API эндпоинты для управления Агентами ИИ, пулом прокси, подключениями и интерактивным чатом.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.ai_agent import AiProxy, AiProviderConnection, AiSiteAgent, AiChatSession, AiChatMessage
from app.services.ai_agent_service import ai_agent_service

router = APIRouter(prefix="/ai-agents", tags=["AI Agents"])

# ==========================================
# СХЕМЫ ЗАПРОСОВ И ОТВЕТОВ
# ==========================================

class ProxyCreate(BaseModel):
    name: str
    protocol: str = "http"
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    priority: int = 10
    is_enabled: bool = True

class ProxyBulkCreate(BaseModel):
    raw_lines: str

class ConnectionCreate(BaseModel):
    name: str
    provider_group: str
    provider_type: str
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    auth_scope: Optional[str] = None
    base_url: Optional[str] = None
    default_model: str
    use_proxy: bool = True
    pinned_proxy_id: Optional[int] = None
    verify_ssl: bool = True
    rotation_weight: int = 1
    rpm_limit: int = 60
    daily_requests_limit: int = 1500
    daily_tokens_limit: int = 1000000
    is_enabled: bool = True
    extra_config: Optional[Dict[str, Any]] = None

class ConnectionUpdate(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    auth_scope: Optional[str] = None
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    use_proxy: Optional[bool] = None
    pinned_proxy_id: Optional[int] = None
    verify_ssl: Optional[bool] = None
    rotation_weight: Optional[int] = None
    rpm_limit: Optional[int] = None
    daily_requests_limit: Optional[int] = None
    daily_tokens_limit: Optional[int] = None
    is_enabled: Optional[bool] = None
    extra_config: Optional[Dict[str, Any]] = None

class SiteAgentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    primary_connection_id: Optional[int] = None
    fallback_connection_id: Optional[int] = None
    use_gemini_pool: Optional[bool] = None
    model_override: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    permissions_config: Optional[Dict[str, Any]] = None

class SiteAgentCreate(BaseModel):
    agent_code: Optional[str] = None
    title: str
    description: Optional[str] = None
    is_active: bool = True
    primary_connection_id: Optional[int] = None
    fallback_connection_id: Optional[int] = None
    use_gemini_pool: bool = False
    model_override: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    system_prompt: Optional[str] = None
    permissions_config: Optional[Dict[str, Any]] = None

class GeneratePromptRequest(BaseModel):
    goal: str
    title: Optional[str] = None
    selected_data_sources: Optional[List[str]] = None
    connection_id: Optional[int] = None
    current_prompt: Optional[str] = None
    custom_instructions: Optional[str] = None

class ExecuteAgentRequest(BaseModel):
    agent_code: str
    query: str
    connection_id_override: Optional[int] = None
    model_override: Optional[str] = None
    use_live_data: bool = True
    custom_data_sources: Optional[List[str]] = None

class ChatSendMessageRequest(BaseModel):
    agent_code: str
    message: str
    session_id: Optional[int] = None
    connection_id: Optional[int] = None
    model: Optional[str] = None

class FetchModelsRequest(BaseModel):
    provider_type: str = "gemini"
    provider_group: str = "global"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    pinned_proxy_id: Optional[int] = None


def mask_key(key: Optional[str]) -> Optional[str]:
    if not key:
        return ""
    if len(key) <= 8:
        return "********"
    return f"{key[:4]}...{key[-4:]}"


# ==========================================
# 1. ПРОКСИ-СЕРВЕРЫ
# ==========================================

@router.get("/proxies", response_model=List[AiProxy])
def list_proxies(session: Session = Depends(get_session)):
    return session.exec(select(AiProxy).order_by(AiProxy.priority.asc(), AiProxy.id.asc())).all()

@router.get("/proxies/export")
def export_proxies_txt(session: Session = Depends(get_session)):
    """
    Экспорт всех настроек прокси в формате txt (ip:port:user:pass)
    """
    proxies = session.exec(select(AiProxy).order_by(AiProxy.priority.asc(), AiProxy.id.asc())).all()
    lines = []
    for p in proxies:
        if p.username and p.password:
            lines.append(f"{p.host}:{p.port}:{p.username}:{p.password}")
        elif p.username:
            lines.append(f"{p.host}:{p.port}:{p.username}")
        else:
            lines.append(f"{p.host}:{p.port}")
    content = "\n".join(lines)
    from fastapi.responses import Response
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=proxies_export.txt"}
    )

@router.post("/proxies", response_model=AiProxy)
def create_proxy(data: ProxyCreate, session: Session = Depends(get_session)):
    proxy = AiProxy(**data.dict())
    session.add(proxy)
    session.commit()
    session.refresh(proxy)
    return proxy

@router.post("/proxies/bulk", response_model=Dict[str, Any])
def create_proxies_bulk(data: ProxyBulkCreate, session: Session = Depends(get_session)):
    added = 0
    lines = [line.strip() for line in data.raw_lines.strip().splitlines() if line.strip()]
    
    for idx, line in enumerate(lines, 1):
        try:
            if "://" in line:
                proto, rest = line.split("://", 1)
                proto = proto.lower()
                user = None
                password = None
                if "@" in rest:
                    auth_part, host_port = rest.split("@", 1)
                    if ":" in auth_part:
                        user, password = auth_part.split(":", 1)
                    else:
                        user = auth_part
                else:
                    host_port = rest
                host, port_str = host_port.split(":", 1)
                port = int(port_str.split("/")[0])
            elif line.count(":") == 3:
                parts = line.split(":")
                host, port_str, user, password = parts[0], parts[1], parts[2], parts[3]
                port = int(port_str)
                proto = "http"
            elif line.count(":") == 1:
                parts = line.split(":")
                host, port_str = parts[0], parts[1]
                port = int(port_str)
                user = None
                password = None
                proto = "http"
            else:
                continue

            proxy = AiProxy(
                name=f"Импорт #{idx} ({host})",
                protocol=proto,
                host=host,
                port=port,
                username=user,
                password=password,
                priority=10
            )
            session.add(proxy)
            added += 1
        except Exception:
            continue

    session.commit()
    return {"status": "success", "added_count": added}

@router.put("/proxies/{proxy_id}", response_model=AiProxy)
def update_proxy(proxy_id: int, data: ProxyCreate, session: Session = Depends(get_session)):
    proxy = session.get(AiProxy, proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")

    for k, v in data.dict().items():
        setattr(proxy, k, v)
    proxy.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.add(proxy)
    session.commit()
    session.refresh(proxy)
    return proxy

@router.delete("/proxies/{proxy_id}")
def delete_proxy(proxy_id: int, session: Session = Depends(get_session)):
    proxy = session.get(AiProxy, proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")

    session.delete(proxy)
    session.commit()
    return {"status": "success", "deleted_id": proxy_id}

@router.post("/proxies/{proxy_id}/test", response_model=Dict[str, Any])
async def test_single_proxy_endpoint(proxy_id: int, session: Session = Depends(get_session)):
    proxy = session.get(AiProxy, proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")

    updated = await ai_agent_service.check_and_update_proxy(session, proxy)
    return {
        "status": updated.status,
        "latency_ms": updated.latency_ms,
        "detected_ip": updated.detected_ip,
        "detected_country": updated.detected_country,
        "last_error": updated.last_error
    }

@router.post("/proxies/test-all", response_model=Dict[str, Any])
async def test_all_proxies_endpoint(session: Session = Depends(get_session)):
    best_proxy = await ai_agent_service.auto_select_best_proxy(session)
    if best_proxy:
        return {
            "status": "success",
            "message": f"Выбран активный прокси: {best_proxy.name} ({best_proxy.host}:{best_proxy.port})",
            "best_proxy_id": best_proxy.id,
            "detected_ip": best_proxy.detected_ip,
            "detected_country": best_proxy.detected_country,
            "latency_ms": best_proxy.latency_ms
        }
    else:
        return {
            "status": "warning",
            "message": "Не найдено ни одного рабочего прокси в списке включенных",
            "best_proxy_id": None
        }

@router.post("/proxies/{proxy_id}/set-active")
def set_active_proxy(proxy_id: int, session: Session = Depends(get_session)):
    proxy = session.get(AiProxy, proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")

    all_proxies = session.exec(select(AiProxy)).all()
    for p in all_proxies:
        p.is_active_current = (p.id == proxy_id)
        session.add(p)

    session.commit()
    return {"status": "success", "active_proxy_id": proxy_id}


# ==========================================
# 2. ПОДКЛЮЧЕНИЯ ИИ И КВОТЫ
# ==========================================

@router.get("/connections")
def list_connections(group: Optional[str] = None, session: Session = Depends(get_session)):
    from app.services.ai_agent_service import calculate_limits_reset

    query = select(AiProviderConnection)
    if group:
        query = query.where(AiProviderConnection.provider_group == group)
    conns = session.exec(query.order_by(AiProviderConnection.id.asc())).all()

    results = []
    for c in conns:
        ai_agent_service._check_and_reset_daily_limits(c)
        d = c.dict()
        d["api_key_masked"] = mask_key(c.api_key)
        d["has_api_key"] = bool(c.api_key and len(c.api_key) > 5)
        d["api_key"] = ""
        # Вычисляем остатки квот
        d_req_lim = c.daily_requests_limit or 1000
        t_req = c.today_requests or 0
        d["remaining_requests"] = max(0, d_req_lim - t_req)
        d["requests_percent"] = min(100, int((t_req / d_req_lim) * 100))

        d_tok_lim = c.daily_tokens_limit or 1000000
        t_tok = c.today_tokens or 0
        d["remaining_tokens"] = max(0, d_tok_lim - t_tok)
        d["tokens_percent"] = min(100, int((t_tok / d_tok_lim) * 100))

        # Вычисление времени обновления лимитов и данных Rate Limit
        reset_display, is_renewable = calculate_limits_reset(c)
        d["limits_reset_display"] = reset_display
        d["is_reset_renewable"] = is_renewable
        d["live_rate_limits"] = (c.extra_config or {}).get("live_rate_limits") or {}

        results.append(d)
        session.add(c)

    session.commit()
    return results

@router.get("/quota-presets")
def get_quota_presets():
    """Справочник официальных системных лимитов и тарифов провайдеров"""
    from app.services.ai_agent_service import SYSTEM_QUOTA_PRESETS
    return SYSTEM_QUOTA_PRESETS

@router.get("/quota-summary")
def get_quota_summary(session: Session = Depends(get_session)):
    """Возвращает сводную статистику по доступным токенам и запросам"""
    return ai_agent_service.get_quota_summary(session)

@router.post("/connections", response_model=Dict[str, Any])
def create_connection(data: ConnectionCreate, session: Session = Depends(get_session)):
    from app.services.ai_agent_service import DEFAULT_BASE_URLS

    d = data.dict()
    ptype = d.get("provider_type", "").lower()

    if d.get("provider_group") == "ru":
        d["use_proxy"] = False

    # Авто-подстановка базового URL если не указан
    if not d.get("base_url") and ptype in DEFAULT_BASE_URLS:
        d["base_url"] = DEFAULT_BASE_URLS[ptype]

    extra = d.get("extra_config") or {}
    if ptype == "yandexgpt":
        if not d.get("client_id") and extra.get("folder_id"):
            d["client_id"] = str(extra["folder_id"]).strip()
        # Автокоррекция если перепутан secret key и key id
        key_id = str(extra.get("key_id", "")).strip()
        api_key = str(d.get("api_key", "")).strip()
        if api_key.startswith("aje") and key_id and (key_id.startswith("AQVN") or len(key_id) > 35):
            d["api_key"] = key_id
            extra["key_id"] = api_key
            d["extra_config"] = extra

    conn = AiProviderConnection(**d)
    session.add(conn)
    session.commit()
    session.refresh(conn)
    return {"status": "success", "id": conn.id, "name": conn.name}

@router.put("/connections/{conn_id}", response_model=Dict[str, Any])
def update_connection(conn_id: int, data: ConnectionUpdate, session: Session = Depends(get_session)):
    conn = session.get(AiProviderConnection, conn_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    extra = dict(conn.extra_config or {})
    if data.extra_config:
        extra.update(data.extra_config)

    for k, v in data.dict(exclude_unset=True).items():
        if k == "api_key" and (not v or str(v).strip() == ""):
            continue
        if k == "extra_config":
            continue
        setattr(conn, k, v)

    conn.extra_config = extra

    if conn.provider_type == "yandexgpt":
        if not conn.client_id and extra.get("folder_id"):
            conn.client_id = str(extra["folder_id"]).strip()
        key_id = str(extra.get("key_id", "")).strip()
        api_key = str(conn.api_key or "").strip()
        if api_key.startswith("aje") and key_id and (key_id.startswith("AQVN") or len(key_id) > 35):
            conn.api_key = key_id
            extra["key_id"] = api_key
            conn.extra_config = extra

    from app.services.ai_agent_service import DEFAULT_BASE_URLS

    if not conn.base_url and conn.provider_type in DEFAULT_BASE_URLS:
        conn.base_url = DEFAULT_BASE_URLS[conn.provider_type]

    if conn.provider_group == "ru":
        conn.use_proxy = False

    conn.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.add(conn)
    session.commit()
    return {"status": "success", "id": conn.id}

@router.delete("/connections/{conn_id}")
def delete_connection(conn_id: int, session: Session = Depends(get_session)):
    conn = session.get(AiProviderConnection, conn_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    session.delete(conn)
    session.commit()
    return {"status": "success", "deleted_id": conn_id}

@router.post("/connections/{conn_id}/test", response_model=Dict[str, Any])
async def test_connection_endpoint(conn_id: int, session: Session = Depends(get_session)):
    conn = session.get(AiProviderConnection, conn_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    success, latency, message = await ai_agent_service.test_connection(session, conn)
    return {
        "success": success,
        "latency_ms": latency,
        "message": message,
        "status": conn.status
    }

@router.get("/connections/{conn_id}/models", response_model=List[str])
async def get_connection_models(conn_id: int, session: Session = Depends(get_session)):
    """Получить список доступных моделей для конкретного подключения (через его API)"""
    conn = session.get(AiProviderConnection, conn_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    return await ai_agent_service.fetch_available_models(session, connection=conn)

@router.post("/models/fetch", response_model=List[str])
async def fetch_models_preview(data: FetchModelsRequest, session: Session = Depends(get_session)):
    """Запросить список моделей из API провайдера до сохранения подключения"""
    return await ai_agent_service.fetch_available_models(
        session=session,
        provider_type=data.provider_type,
        api_key=data.api_key,
        base_url=data.base_url,
        pinned_proxy_id=data.pinned_proxy_id,
        provider_group=data.provider_group
    )

@router.get("/models/defaults", response_model=Dict[str, List[str]])
def get_default_models():
    """Справочник проверенных моделей по умолчанию по каждому провайдеру"""
    return {
        "gemini": [
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash-lite",
            "gemini-3.8-flash",
            "gemini-flash-latest",
            "gemini-pro-latest"
        ],
        "openai": [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4-turbo",
            "o1-mini",
            "o3-mini"
        ],
        "gigachat": [
            "GigaChat",
            "GigaChat-Pro",
            "GigaChat-Max",
            "GigaChat-Plus"
        ],
        "yandexgpt": [
            "yandexgpt/latest",
            "yandexgpt-lite/latest",
            "yandexgpt/rc",
            "yandexgpt-lite/rc",
            "summarization/latest"
        ],
        "anthropic": [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229"
        ],
        "deepseek": [
            "deepseek-chat",
            "deepseek-reasoner"
        ]
    }


# ==========================================
# 3. РОЛИ АГЕНТОВ САЙТА И ПЕСОЧНИЦА
# ==========================================

@router.get("/data-catalog")
def get_data_catalog():
    """Справочник доступных источников данных системы для агентов"""
    return ai_agent_service.get_available_data_sources()

@router.post("/generate-prompt")
async def generate_agent_prompt(data: GeneratePromptRequest, session: Session = Depends(get_session)):
    """Генерация или улучшение системного промпта агента с помощью подключенных ИИ без ограничений"""
    try:
        res = await ai_agent_service.generate_agent_prompt(
            session=session,
            goal=data.goal,
            title=data.title,
            selected_data_sources=data.selected_data_sources,
            connection_id=data.connection_id,
            current_prompt=data.current_prompt,
            custom_instructions=data.custom_instructions
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/site-agents")
def list_site_agents(session: Session = Depends(get_session)):
    return session.exec(select(AiSiteAgent).order_by(AiSiteAgent.id.asc())).all()

@router.post("/site-agents", response_model=Dict[str, Any])
def create_site_agent(data: SiteAgentCreate, session: Session = Depends(get_session)):
    """Создание новой роли агента сайта"""
    agent_code = (data.agent_code or "").strip()
    if not agent_code:
        import re
        translit_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
        }
        raw = data.title.lower().strip()
        slug = "".join(translit_map.get(ch, ch) for ch in raw)
        slug = re.sub(r'[^a-z0-9_]+', '_', slug).strip('_')
        agent_code = (slug[:30] or "custom") + "_agent"

    existing = session.exec(select(AiSiteAgent).where(AiSiteAgent.agent_code == agent_code)).first()
    if existing:
        agent_code = f"{agent_code}_{int(time.time()) % 10000}"

    perms = data.permissions_config or {}
    if "data_sources" not in perms:
        perms["data_sources"] = ["olap_stats", "orders"]
    perms["is_custom"] = True

    agent = AiSiteAgent(
        agent_code=agent_code,
        title=data.title,
        description=data.description,
        is_active=data.is_active,
        primary_connection_id=data.primary_connection_id,
        fallback_connection_id=data.fallback_connection_id,
        use_gemini_pool=data.use_gemini_pool,
        model_override=data.model_override,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
        system_prompt=data.system_prompt,
        permissions_config=perms
    )
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return {"status": "success", "agent_code": agent.agent_code, "id": agent.id, "title": agent.title}

@router.put("/site-agents/{agent_code}", response_model=Dict[str, Any])
def update_site_agent(agent_code: str, data: SiteAgentUpdate, session: Session = Depends(get_session)):
    agent = session.exec(select(AiSiteAgent).where(AiSiteAgent.agent_code == agent_code)).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Site agent not found")

    for k, v in data.dict(exclude_unset=True).items():
        setattr(agent, k, v)

    agent.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return {"status": "success", "agent_code": agent.agent_code}

@router.delete("/site-agents/{agent_code}")
def delete_site_agent(agent_code: str, session: Session = Depends(get_session)):
    """Удаление кастомного агента сайта"""
    agent = session.exec(select(AiSiteAgent).where(AiSiteAgent.agent_code == agent_code)).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Агент не найден")

    if agent_code in ["stats_analyst", "feedback_nps", "site_manager"]:
        raise HTTPException(status_code=400, detail="Базовых системных агентов нельзя удалять (можно отключить переключателем активности).")

    session.delete(agent)
    session.commit()
    return {"status": "success", "message": f"Агент «{agent.title}» удален"}

@router.post("/execute")
async def execute_agent_query(data: ExecuteAgentRequest, session: Session = Depends(get_session)):
    """Исполнение тестового запроса к агенту в песочнице с реальными данными БД"""
    try:
        res = await ai_agent_service.execute_agent_query(
            session=session,
            agent_code=data.agent_code,
            query=data.query,
            connection_id_override=data.connection_id_override,
            model_override=data.model_override,
            use_live_data=data.use_live_data,
            custom_data_sources=data.custom_data_sources
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 4. ИНТЕРАКТИВНЫЙ ЧАТ С ИИ АГЕНТАМИ
# ==========================================

@router.get("/chat/sessions")
def list_chat_sessions(session: Session = Depends(get_session)):
    """Список сохраненных диалогов чата"""
    return session.exec(
        select(AiChatSession).order_by(AiChatSession.updated_at.desc()).limit(30)
    ).all()

@router.post("/chat/sessions")
def create_chat_session(title: str = "Новый диалог", agent_code: str = "stats_analyst", session: Session = Depends(get_session)):
    """Создать новую сессию диалога"""
    sess = AiChatSession(title=title, agent_code=agent_code)
    session.add(sess)
    session.commit()
    session.refresh(sess)
    return sess

@router.delete("/chat/sessions/{session_id}")
def delete_chat_session(session_id: int, session: Session = Depends(get_session)):
    """Удалить сессию диалога"""
    sess = session.get(AiChatSession, session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    session.delete(sess)
    session.commit()
    return {"status": "success"}

@router.get("/chat/sessions/{session_id}/messages")
def get_session_messages(session_id: int, session: Session = Depends(get_session)):
    """Получить сообщения выбранной сессии"""
    return session.exec(
        select(AiChatMessage).where(AiChatMessage.session_id == session_id).order_by(AiChatMessage.id.asc())
    ).all()

@router.post("/chat/send")
async def send_chat_message(req: ChatSendMessageRequest, session: Session = Depends(get_session)):
    """Отправить сообщение агенту в чате"""
    try:
        res = await ai_agent_service.chat_with_agent(
            session=session,
            agent_code=req.agent_code,
            user_message=req.message,
            session_id=req.session_id,
            connection_id_override=req.connection_id,
            model_override=req.model
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
