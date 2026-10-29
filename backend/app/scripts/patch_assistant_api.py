file_path = "backend/app/api/ai_assistants.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Ensure ConfigDict and Any are imported
if "from pydantic import BaseModel, ConfigDict" not in content:
    content = content.replace("from pydantic import BaseModel", "from pydantic import BaseModel, ConfigDict")

old_schema_and_put = '''class AssistantCreateUpdateSchema(BaseModel):
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
    connection_id: Optional[int] = None
    model_override: Optional[str] = None
    is_active: bool = True
    allow_sound_alerts: bool = True
    allow_voice_tts: bool = False
    daily_token_limit: int = 50000
    daily_requests_limit: int = 100
    auto_check_interval_sec: int = 30
    system_prompt_addon: Optional[str] = None'''

new_schema_and_put = '''class AssistantCreateUpdateSchema(BaseModel):
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
    is_active: Optional[bool] = None'''

content_norm = content.replace("\r\n", "\n")
old_norm = old_schema_and_put.replace("\r\n", "\n")
new_norm = new_schema_and_put.replace("\r\n", "\n")

if old_norm in content_norm:
    content_norm = content_norm.replace(old_norm, new_norm)
    print("Replaced schema block!")

# Replace update_assistant definition to accept AssistantUpdateSchema
old_update_ep = '''@router.put("/{assistant_id}", response_model=AiSiteAssistant)
def update_assistant(
    assistant_id: int,
    payload: AssistantCreateUpdateSchema,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Обновление помощника"""
    res = ai_assistant_service.update_assistant(session, assistant_id, payload.dict())
    if not res:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return res'''

new_update_ep = '''@router.patch("/{assistant_id}/toggle", response_model=AiSiteAssistant)
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
    return res'''

old_update_ep_norm = old_update_ep.replace("\r\n", "\n")
new_update_ep_norm = new_update_ep.replace("\r\n", "\n")

if old_update_ep_norm in content_norm:
    content_norm = content_norm.replace(old_update_ep_norm, new_update_ep_norm)
    print("Replaced update_assistant endpoint!")

# Add all-active, observations and summary endpoints
new_endpoints = '''
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
'''

# Add before @router.post("/{assistant_id}/chat")
if '@router.post("/{assistant_id}/chat")' in content_norm:
    content_norm = content_norm.replace('@router.post("/{assistant_id}/chat")', new_endpoints + '\n@router.post("/{assistant_id}/chat")')
    print("Added analytics & all-active endpoints!")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content_norm)

print("Patch applied to ai_assistants.py successfully!")
