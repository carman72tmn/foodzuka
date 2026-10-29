"""
Модели данных для ИИ-Помощников сайта FoodTech (AI Site Assistants)
Включает:
- AiSiteAssistant: Настройки виртуального помощника (скин, аватар, характер, зоны ответственности, привязка к страницам, лимиты)
- AiAssistantMessage: История диалогов и автоматических серверных подсказок
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, date
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

class AiSiteAssistant(SQLModel, table=True):
    """Интерактивный виртуальный помощник для сотрудников сайта/админки"""
    __tablename__ = "ai_site_assistants"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(..., max_length=120, description="Имя помощника (например: Шеф Марк, Анна)")
    code: str = Field(..., max_length=50, unique=True, index=True, description="Уникальный slug (kitchen_chef, admin_anna, etc.)")
    role_title: str = Field(..., max_length=150, description="Роль: Шеф-Повар / Контроль кухни, Старший администратор и т.д.")
    avatar_skin: str = Field(default="chef_male", max_length=50, description="chef_male, admin_female, courier_male, cyber_bot, fox_mascot, custom")
    avatar_custom_url: Optional[str] = Field(default=None, max_length=500, description="URL пользовательского аватара")
    avatar_animation_mode: str = Field(default="alive", max_length=30, description="alive, float, pulse, static")
    character_tone: str = Field(default="professional", max_length=50, description="professional, strict_supervisor, caring_mentor, friendly, humorous")
    assigned_pages: List[str] = Field(default_factory=lambda: ["*"], sa_column=Column(JSONB), description="Список маршрутов: ['*'] для всех, ['/orders'], ['/dashboard'], etc.")
    zone_of_responsibility: str = Field(default="full_control", max_length=50, description="kitchen_control, delivery_control, admin_cashier, full_control")
    
    # Связка с ИИ-моделью / Агентом
    linked_agent_code: Optional[str] = Field(default="omni_assistant", max_length=50, description="Код связанного AiSiteAgent")
    connection_id: Optional[int] = Field(default=None, foreign_key="ai_provider_connections.id")
    model_override: Optional[str] = Field(default=None, max_length=120)
    
    # Флаги активности и поведения
    is_active: bool = Field(default=True, description="Активен ли помощник")
    allow_sound_alerts: bool = Field(default=True, description="Звуковые сигналы при задержках")
    allow_voice_tts: bool = Field(default=False, description="Голосовое озвучивание подсказок")
    
    # Квоты и жесткая оптимизация токенов
    daily_token_limit: int = Field(default=50000, description="Дневной лимит токенов")
    daily_requests_limit: int = Field(default=100, description="Дневной лимит сообщений к LLM")
    used_tokens_today: int = Field(default=0)
    used_requests_today: int = Field(default=0)
    last_reset_date: Optional[date] = None
    
    # Серверный модуль мониторинга
    auto_check_interval_sec: int = Field(default=30, description="Интервал проверки ситуаций (сек)")
    system_prompt_addon: Optional[str] = Field(default=None, description="Дополнительные инструкции к поведению")
    
    # Ограничения и интеграции (сторонние ресурсы, iiko API, обучение и статистика)
    allow_external_queries: bool = Field(default=True, description="Разрешить запросы к сторонним ресурсам (погода, внешние вопросы)")
    allow_iiko_api_queries: bool = Field(default=False, description="Разрешить самостоятельные запросы к iiko API")
    allow_iiko_export: bool = Field(default=False, description="Разрешить выгрузку данных iiko")
    allowed_external_tools: List[str] = Field(default_factory=lambda: ["weather", "general_search", "consulting"], sa_column=Column(JSONB), description="Разрешенные внешние инструменты")
    iiko_allowed_actions: List[str] = Field(default_factory=lambda: ["read_orders", "read_menu", "read_stop_list"], sa_column=Column(JSONB), description="Разрешенные действия iiko")
    enable_analytics_learning: bool = Field(default=True, description="Вести наблюдения и изучать статистику (Zero-Token mode)")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class AiAssistantMessage(SQLModel, table=True):
    """История сообщений и серверных подсказок помощника"""
    __tablename__ = "ai_assistant_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    assistant_id: int = Field(foreign_key="ai_site_assistants.id", index=True)
    user_id: Optional[int] = None
    session_id: Optional[str] = Field(default=None, max_length=100, index=True)
    page_route: Optional[str] = Field(default=None, max_length=255)
    role: str = Field(..., max_length=20, description="user, assistant, system_tip")
    content: str
    is_auto_tip: bool = Field(default=False, description="Сгенерировано ли быстрым скриптом без LLM")
    tip_category: Optional[str] = Field(default=None, max_length=50, description="cooking_delay, delivery_delay, new_order_stuck, shift_alert, general")
    tokens_used: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
