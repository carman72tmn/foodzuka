"""
Модели данных для модуля «Агенты ИИ» (AI Agents)
Включает:
- AiProxy: Пул прокси-серверов (HTTPS / SOCKS5) для обхода региональных ограничений
- AiProviderConnection: Настройки подключений к провайдерам (Google Gemini, OpenAI, Claude, DeepSeek, GigaChat, YandexGPT и др.)
- AiSiteAgent: Функциональные роли ИИ на сайте (аналитика, обратная связь, управление)
- AiChatSession & AiChatMessage: Сессии и сообщения чата с ИИ Агентами
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, date
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

class AiProxy(SQLModel, table=True):
    """Пул прокси-серверов для мировых ИИ"""
    __tablename__ = "ai_proxies"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(..., max_length=100, description="Название / метка прокси")
    protocol: str = Field(default="http", max_length=20, description="http, https, socks5")
    host: str = Field(..., max_length=255, description="IP или домен")
    port: int = Field(..., description="Порт прокси")
    username: Optional[str] = Field(default=None, max_length=255, description="Логин")
    password: Optional[str] = Field(default=None, max_length=255, description="Пароль")
    priority: int = Field(default=10, description="Приоритет (меньше = выше)")
    is_enabled: bool = Field(default=True, description="Включен ли прокси")
    is_active_current: bool = Field(default=False, description="Текущий активный прокси")
    status: str = Field(default="untested", max_length=30, description="working, failed, timeout, untested")
    latency_ms: Optional[int] = Field(default=None, description="Задержка в мс")
    detected_ip: Optional[str] = Field(default=None, max_length=64, description="Внешний IP адрес")
    detected_country: Optional[str] = Field(default=None, max_length=64, description="Страна прокси")
    last_checked_at: Optional[datetime] = Field(default=None, description="Время последней проверки")
    last_error: Optional[str] = Field(default=None, description="Текст последней ошибки")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    def build_url(self) -> str:
        """Формирует полный URL прокси"""
        proto = self.protocol.lower()
        if proto == "https":
            proto = "http"
        elif proto.startswith("socks"):
            proto = "socks5"
        else:
            proto = "http"
            
        if self.username and self.password:
            return f"{proto}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{proto}://{self.host}:{self.port}"


class AiProviderConnection(SQLModel, table=True):
    """Подключение к ИИ провайдеру (Google Gemini, OpenAI, Claude, DeepSeek, GigaChat, YandexGPT)"""
    __tablename__ = "ai_provider_connections"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(..., max_length=120, description="Название подключения")
    provider_group: str = Field(..., max_length=20, description="global (через прокси) или ru (напрямую)")
    provider_type: str = Field(..., max_length=50, description="gemini, openai, anthropic, deepseek, openrouter, gigachat, yandexgpt, tbank_ai, custom")
    api_key: Optional[str] = Field(default=None, description="API Key / Secret Key")
    client_id: Optional[str] = Field(default=None, max_length=255, description="Client ID / Folder ID / Org ID")
    auth_scope: Optional[str] = Field(default=None, max_length=100, description="Scope для GigaChat или тип ключа Yandex")
    base_url: Optional[str] = Field(default=None, max_length=500, description="Кастомный Endpoint URL")
    default_model: str = Field(..., max_length=120, description="Модель по умолчанию")
    use_proxy: bool = Field(default=True, description="Использовать ли прокси (для ru всегда false)")
    pinned_proxy_id: Optional[int] = Field(default=None, foreign_key="ai_proxies.id", description="Привязка конкретного прокси")
    verify_ssl: bool = Field(default=True, description="Проверка SSL (актуально для сертификатов Минцифры)")
    rotation_weight: int = 1
    rpm_limit: int = 60
    daily_requests_limit: int = 1000
    daily_tokens_limit: int = 1000000
    today_requests: int = 0
    today_tokens: int = 0
    last_reset_date: Optional[date] = None
    is_enabled: bool = True
    status: str = Field(default="untested", max_length=30, description="connected, error, quota_exceeded, untested")
    last_tested_at: Optional[datetime] = None
    last_error: Optional[str] = None
    total_requests: int = 0
    total_tokens: int = 0
    extra_config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class AiSiteAgent(SQLModel, table=True):
    """Функциональные агенты сайта FoodTech"""
    __tablename__ = "ai_site_agents"

    id: Optional[int] = Field(default=None, primary_key=True)
    agent_code: str = Field(..., max_length=50, unique=True, index=True, description="stats_analyst, feedback_nps, site_manager, general_assistant")
    title: str = Field(..., max_length=150, description="Название агента")
    description: Optional[str] = Field(default=None, description="Описание ответственности")
    is_active: bool = Field(default=False, description="Включен ли агент на сайте")
    primary_connection_id: Optional[int] = Field(default=None, foreign_key="ai_provider_connections.id")
    fallback_connection_id: Optional[int] = Field(default=None, foreign_key="ai_provider_connections.id")
    use_gemini_pool: bool = Field(default=False, description="Использовать пул активных ключей Gemini")
    model_override: Optional[str] = Field(default=None, max_length=120)
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=2048)
    system_prompt: Optional[str] = None
    permissions_config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class AiChatSession(SQLModel, table=True):
    """Сессия диалога с ИИ Агентом"""
    __tablename__ = "ai_chat_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(default="Новый диалог", max_length=200)
    agent_code: str = Field(default="stats_analyst", max_length=50)
    user_id: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class AiChatMessage(SQLModel, table=True):
    """Сообщение в сессии чата"""
    __tablename__ = "ai_chat_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="ai_chat_sessions.id", index=True)
    role: str = Field(..., max_length=20, description="user, assistant, system")
    content: str
    model: Optional[str] = Field(default=None, max_length=100)
    tokens_used: int = 0
    latency_ms: int = 0
    provider_name: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
