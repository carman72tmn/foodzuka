"""
Сервис для работы с ИИ-агентами, провайдерами, пулом прокси и интерактивным чатом.
"""

import time
import uuid
import json
import logging
import asyncio
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, date, timedelta
import httpx
from sqlmodel import Session, select

from app.models.ai_agent import AiProxy, AiProviderConnection, AiSiteAgent, AiChatSession, AiChatMessage
from app.models.order import Order
from app.models.olap_revenue import OlapRevenueRecord
from app.models.nps import NpsReview
from app.models.product import Product

try:
    from app.models.customer import Customer
except ImportError:
    Customer = None

try:
    from app.models.promo_code import PromoCode
except ImportError:
    PromoCode = None

try:
    from app.models.category import Category
except ImportError:
    Category = None

logger = logging.getLogger(__name__)

# ==========================================
# РЕЕСТР ДОСТУПНЫХ ДАННЫХ САЙТА ДЛЯ АГЕНТОВ
# ==========================================
AVAILABLE_DATA_SOURCES = [
    {
        "id": "olap_stats",
        "name": "Финансовая и OLAP-аналитика (iiko Resto)",
        "icon": "bx-line-chart",
        "badge_color": "primary",
        "description": "Выручка по дням, средний чек, количество гостей и чеков, сумма скидок, безнал и наличные оплаты.",
        "sample_fields": ["business_date", "revenue", "average_check", "orders_count", "discount_sum", "card_sum", "cash_sum"]
    },
    {
        "id": "orders",
        "name": "Заказы и Чеки в реальном времени",
        "icon": "bx-receipt",
        "badge_color": "info",
        "description": "Поток заказов сайта: номера, статусы (доставка, закрыт и т.д.), суммы, примененные скидки и состав позиций.",
        "sample_fields": ["id", "status", "total_amount", "total_discount", "total_paid", "delivery_type", "created_at"]
    },
    {
        "id": "customers",
        "name": "База клиентов и Программа лояльности",
        "icon": "bx-group",
        "badge_color": "success",
        "description": "Анкеты гостей, бонусный баланс iikoCard, частота визитов, новые гости и категории лояльности.",
        "sample_fields": ["name", "phone", "bonus_balance", "is_new_guest", "created_at"]
    },
    {
        "id": "nps_reviews",
        "name": "Отзывы клиентов и Оценки качества NPS",
        "icon": "bx-star",
        "badge_color": "warning",
        "description": "Оценки блюд и сервиса от 1 до 5 звезд, текстовые комментарии гостей, оценки качества и скорости.",
        "sample_fields": ["rating", "comment", "order_id", "created_at"]
    },
    {
        "id": "menu_catalog",
        "name": "Каталог меню, Категории и Стоп-листы",
        "icon": "bx-food-menu",
        "badge_color": "secondary",
        "description": "Категории (роллы, сеты, пицца и др.), блюда, актуальные цены и статус доступности (стоп-лист).",
        "sample_fields": ["name", "category", "price", "is_available"]
    },
    {
        "id": "promo_codes",
        "name": "Промокоды, Маркетинг и Скидки",
        "icon": "bx-gift",
        "badge_color": "error",
        "description": "Действующие промокоды, скидки в %, подарочные позиции и статус активности.",
        "sample_fields": ["code", "discount_percent", "discount_amount", "is_active"]
    }
]

# ==========================================
# ОФИЦИАЛЬНЫЕ СИСТЕМНЫЕ ТАРИФЫ И ЛИМИТЫ ИИ
# ==========================================
SYSTEM_QUOTA_PRESETS = {
    "gemini": {
        "google_one_pro": {
            "tier_key": "google_one_pro",
            "tier_name": "Google One AI Premium (Gemini Pro)",
            "rpm_limit": 360,
            "daily_requests_limit": 10000,
            "daily_tokens_limit": 4000000,
            "tpm_limit": 4000000,
            "reset_interval": "daily_utc",
            "default_model": "gemini-pro-latest",
            "models": ["gemini-pro-latest", "gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-flash-latest"],
            "description": "Подписка Google One AI Premium (Gemini Advanced/Pro): расширенные квоты и доступ к линейкам Pro и Flash. Сброс в 00:00 UTC."
        },
        "pay_as_you_go": {
            "tier_key": "pay_as_you_go",
            "tier_name": "Google Gemini (Платный биллинг Pay-As-You-Go / Tier 1)",
            "rpm_limit": 1000,
            "daily_requests_limit": 50000,
            "daily_tokens_limit": 4000000,
            "tpm_limit": 4000000,
            "reset_interval": "rpm_minute",
            "default_model": "gemini-3.1-flash-lite",
            "models": ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-flash-latest", "gemini-pro-latest"],
            "description": "Официальные лимиты Google Cloud Project с привязанным биллингом: 1 000 RPM, 4 000 000 TPM без жесткого дневного лимита."
        },
        "free": {
            "tier_key": "free",
            "tier_name": "Google Gemini (Бесплатный тариф Free Tier)",
            "rpm_limit": 15,
            "daily_requests_limit": 1500,
            "daily_tokens_limit": 1000000,
            "tpm_limit": 1000000,
            "reset_interval": "daily_utc",
            "default_model": "gemini-3.1-flash-lite",
            "models": ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-flash-latest", "gemini-pro-latest"],
            "description": "Официальные лимиты Google Gemini Free: 15 запросов в минуту (RPM), 1 500 запросов в день (RPD), сброс каждые сутки в 00:00 UTC."
        }
    },
    "groq": {
        "free": {
            "tier_key": "free",
            "tier_name": "Groq LPU (Бесплатный Free Tier)",
            "rpm_limit": 30,
            "daily_requests_limit": 14400,
            "daily_tokens_limit": 500000,
            "tpm_limit": 6000,
            "reset_interval": "daily_utc",
            "default_model": "llama-3.3-70b-versatile",
            "models": [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "deepseek-r1-distill-llama-70b",
                "mixtral-8x7b-32768",
                "gemma2-9b-it",
                "qwen-2.5-32b"
            ],
            "description": "Ультрабыстрый LPU инференс Groq: 30 RPM, 6 000 TPM, до 14 400 запросов/день. Суточный сброс в 00:00 UTC."
        },
        "payg": {
            "tier_key": "payg",
            "tier_name": "Groq On-Demand (Платный биллинг)",
            "rpm_limit": 1000,
            "daily_requests_limit": 100000,
            "daily_tokens_limit": 10000000,
            "tpm_limit": 300000,
            "reset_interval": "rpm_minute",
            "default_model": "llama-3.3-70b-versatile",
            "models": [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "deepseek-r1-distill-llama-70b",
                "mixtral-8x7b-32768",
                "gemma2-9b-it",
                "qwen-2.5-32b"
            ],
            "description": "Коммерческий On-Demand тариф Groq: 1 000 RPM, 300 000 TPM без дневных ограничений."
        }
    },
    "cerebras": {
        "free": {
            "tier_key": "free",
            "tier_name": "Cerebras (Developer Free Tier)",
            "rpm_limit": 30,
            "daily_requests_limit": 14400,
            "daily_tokens_limit": 1000000,
            "tpm_limit": 60000,
            "reset_interval": "daily_utc",
            "default_model": "llama3.3-70b",
            "models": [
                "llama3.3-70b",
                "llama3.1-70b",
                "llama3.1-8b",
                "deepseek-r1-distill-llama-70b"
            ],
            "description": "Сверхбыстрый чип CS-3 Cerebras: 30 RPM, 60 000 TPM, 14 400 запросов в день. Сброс в 00:00 UTC."
        },
        "enterprise": {
            "tier_key": "enterprise",
            "tier_name": "Cerebras (Dedicated / Pro)",
            "rpm_limit": 300,
            "daily_requests_limit": 50000,
            "daily_tokens_limit": 10000000,
            "tpm_limit": 500000,
            "reset_interval": "rpm_minute",
            "default_model": "llama3.3-70b",
            "models": [
                "llama3.3-70b",
                "llama3.1-70b",
                "llama3.1-8b",
                "deepseek-r1-distill-llama-70b"
            ],
            "description": "Выделенный инференс Cerebras с лимитами до 500 000 TPM."
        }
    },
    "nvidia": {
        "eval": {
            "tier_key": "eval",
            "tier_name": "NVIDIA NIM (Free 1000 Credits / Starter)",
            "rpm_limit": 40,
            "daily_requests_limit": 1000,
            "daily_tokens_limit": 500000,
            "tpm_limit": 100000,
            "reset_interval": "none",
            "default_model": "meta/llama-3.3-70b-instruct",
            "models": [
                "meta/llama-3.3-70b-instruct",
                "meta/llama-3.1-405b-instruct",
                "deepseek-ai/deepseek-r1",
                "mistralai/mistral-large-2-instruct",
                "nvidia/llama-3.1-nemotron-70b-instruct"
            ],
            "description": "1 000 бесплатных кредитов NVIDIA Cloud / NIM. Кредиты фиксированные, автоматического обновления нет (n/a)."
        },
        "cloud": {
            "tier_key": "cloud",
            "tier_name": "NVIDIA Cloud Functions / Enterprise",
            "rpm_limit": 120,
            "daily_requests_limit": 10000,
            "daily_tokens_limit": 2000000,
            "tpm_limit": 300000,
            "reset_interval": "monthly",
            "default_model": "meta/llama-3.3-70b-instruct",
            "models": [
                "meta/llama-3.3-70b-instruct",
                "meta/llama-3.1-405b-instruct",
                "deepseek-ai/deepseek-r1",
                "mistralai/mistral-large-2-instruct",
                "nvidia/llama-3.1-nemotron-70b-instruct"
            ],
            "description": "Платный корпоративный доступ к микросервисам NVIDIA NIM."
        }
    },
    "github_models": {
        "free": {
            "tier_key": "free",
            "tier_name": "GitHub Models (Free Tier PAT)",
            "rpm_limit": 15,
            "daily_requests_limit": 150,
            "daily_tokens_limit": 200000,
            "tpm_limit": 8000,
            "reset_interval": "daily_utc",
            "default_model": "gpt-4o-mini",
            "models": [
                "gpt-4o-mini",
                "gpt-4o",
                "o1-preview",
                "o1-mini",
                "Meta-Llama-3.1-70B-Instruct",
                "Phi-3.5-mini-instruct",
                "Mistral-large-2407",
                "DeepSeek-R1"
            ],
            "description": "Бесплатный GitHub Models Playground через Personal Access Token (PAT). Лимиты: 15 RPM, 150 RPD, сброс в 00:00 UTC."
        },
        "copilot": {
            "tier_key": "copilot",
            "tier_name": "GitHub Copilot Pro / Enterprise",
            "rpm_limit": 60,
            "daily_requests_limit": 1000,
            "daily_tokens_limit": 1000000,
            "tpm_limit": 50000,
            "reset_interval": "daily_utc",
            "default_model": "gpt-4o",
            "models": [
                "gpt-4o-mini",
                "gpt-4o",
                "o1-preview",
                "o1-mini",
                "Meta-Llama-3.1-70B-Instruct",
                "Phi-3.5-mini-instruct",
                "Mistral-large-2407",
                "DeepSeek-R1"
            ],
            "description": "Расширенные квоты GitHub Models для подписчиков Copilot Enterprise."
        }
    },
    "openai": {
        "free": {
            "tier_key": "free",
            "tier_name": "OpenAI (Free Tier / Пробный)",
            "rpm_limit": 3,
            "daily_requests_limit": 200,
            "daily_tokens_limit": 40000,
            "tpm_limit": 40000,
            "reset_interval": "none",
            "default_model": "gpt-4o-mini",
            "models": ["gpt-4o-mini", "gpt-4o"],
            "description": "3 RPM, 200 запросов в день, 40 000 TPM."
        },
        "tier1": {
            "tier_key": "tier1",
            "tier_name": "OpenAI (Tier 1 / Pay-as-you-go)",
            "rpm_limit": 500,
            "daily_requests_limit": 10000,
            "daily_tokens_limit": 200000,
            "tpm_limit": 200000,
            "reset_interval": "rpm_minute",
            "default_model": "gpt-4o-mini",
            "models": ["gpt-4o-mini", "gpt-4o"],
            "description": "500 RPM, 10 000 запросов в день, 200 000 TPM."
        }
    },
    "gigachat": {
        "pers": {
            "tier_key": "pers",
            "tier_name": "Сбер GigaChat (Физлица / GIGACHAT_API_PERS)",
            "rpm_limit": 60,
            "daily_requests_limit": 3000,
            "daily_tokens_limit": 1000000,
            "tpm_limit": 1000000,
            "reset_interval": "none",
            "default_model": "GigaChat",
            "models": ["GigaChat", "GigaChat-Pro", "GigaChat-Max"],
            "description": "Бесплатный стартовый пакет 1 000 000 токенов (60 RPM) для физических лиц (n/a)."
        },
        "corp": {
            "tier_key": "corp",
            "tier_name": "Сбер GigaChat (Бизнес / B2B / CORP)",
            "rpm_limit": 300,
            "daily_requests_limit": 50000,
            "daily_tokens_limit": 10000000,
            "tpm_limit": 5000000,
            "reset_interval": "monthly",
            "default_model": "GigaChat-Pro",
            "models": ["GigaChat", "GigaChat-Pro", "GigaChat-Max"],
            "description": "Корпоративный тариф Сбера для юридических лиц с высокими лимитами."
        }
    },
    "yandexgpt": {
        "standard": {
            "tier_key": "standard",
            "tier_name": "YandexGPT (Yandex Cloud API)",
            "rpm_limit": 600,
            "daily_requests_limit": 20000,
            "daily_tokens_limit": 2000000,
            "tpm_limit": 1000000,
            "reset_interval": "rpm_minute",
            "default_model": "yandexgpt/latest",
            "models": ["yandexgpt/latest", "yandexgpt-lite/latest"],
            "description": "Квоты каталога Yandex Cloud: 10 RPS (600 RPM) с расчетом по балансу облака."
        }
    },
    "custom": {
        "default": {
            "tier_key": "default",
            "tier_name": "Пользовательский тариф (Custom)",
            "rpm_limit": 60,
            "daily_requests_limit": 1000,
            "daily_tokens_limit": 1000000,
            "tpm_limit": 1000000,
            "reset_interval": "none",
            "default_model": "default",
            "models": [],
            "description": "Ручные настройки лимитов и тарифа."
        }
    }
}

DEFAULT_BASE_URLS = {
    "groq": "https://api.groq.com/openai/v1",
    "cerebras": "https://api.cerebras.ai/v1",
    "nvidia": "https://integrate.api.nvidia.com/v1",
    "github_models": "https://models.inference.ai.azure.com",
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com",
    "openrouter": "https://openrouter.ai/api/v1",
}

def calculate_limits_reset(connection: AiProviderConnection) -> Tuple[str, bool]:
    """
    Рассчитывает отображение времени обновления лимитов:
    - Если обновляются: 'через 4 ч 35 мин (00:00 UTC)' или 'через 45 сек' (True)
    - Если НЕ обновляются: строго 'n/a' (False)
    """
    extra = dict(connection.extra_config or {})
    live_rl = extra.get("live_rate_limits") or {}
    tier_key = extra.get("tier_key") or "default"
    ptype = (connection.provider_type or "").lower()

    # 1. Живой заголовок сброса из последнего ответа API
    reset_val = (
        live_rl.get("x-ratelimit-reset-requests")
        or live_rl.get("x-ratelimit-reset-requests-minute")
        or live_rl.get("x-ratelimit-reset-tokens")
    )
    if reset_val:
        val_str = str(reset_val).strip()
        if val_str.endswith("ms"):
            return "через < 1 сек", True
        elif val_str.endswith("s") or "m" in val_str:
            val_clean = val_str.replace("m", "м ").replace("s", "с")
            return f"через {val_clean}", True
        elif val_str.isdigit():
            sec = int(val_str)
            if sec < 60:
                return f"через {sec}с", True
            return f"через {sec // 60}м {sec % 60}с", True

    # 2. Определение по типу тарифа
    tier_info = SYSTEM_QUOTA_PRESETS.get(ptype, {}).get(tier_key, {})
    reset_type = tier_info.get("reset_interval") or extra.get("reset_interval")

    # Если сброса нет -> строго n/a
    if reset_type == "none" or (ptype == "nvidia" and tier_key == "eval"):
        return "n/a", False

    if ptype in ["deepseek", "openrouter", "custom"] and not reset_type:
        return "n/a", False

    # Суточный сброс в полночь 00:00 UTC (Gemini, Groq RPD, Cerebras RPD, GitHub Models)
    if reset_type in ["daily_utc", "rpm_minute_rpd_daily", "daily"]:
        now_utc = datetime.now(timezone.utc)
        midnight_utc = (now_utc + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        diff_sec = int((midnight_utc - now_utc).total_seconds())
        hours = diff_sec // 3600
        mins = (diff_sec % 3600) // 60
        return f"через {hours}ч {mins}м (00:00 UTC)", True

    if reset_type == "rpm_minute":
        return "каждые 60 сек (RPM)", True

    if reset_type == "monthly":
        return "1-го числа месяца", True

    return "n/a", False

class AiAgentService:
    def __init__(self):
        pass

    # ==========================================
    # 1. РАБОТА С ПУЛОМ ПРОКСИ-СЕРВЕРОВ
    # ==========================================

    async def test_proxy(self, proxy: AiProxy) -> Tuple[bool, Optional[int], Optional[str], Optional[str], Optional[str]]:
        proxy_url = proxy.build_url()
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(
                proxy=proxy_url,
                timeout=12.0,
                trust_env=False
            ) as client:
                res = await client.get("http://ip-api.com/json/?fields=status,message,country,query")
                latency_ms = int((time.time() - start_time) * 1000)
                
                if res.status_code == 200:
                    data = res.json()
                    if data.get("status") == "success":
                        detected_ip = data.get("query")
                        detected_country = data.get("country")
                        return True, latency_ms, detected_ip, detected_country, None
                    else:
                        return False, latency_ms, None, None, f"IP lookup error: {data.get('message')}"
                else:
                    res_fb = await client.get("https://ifconfig.me/ip", timeout=8.0)
                    if res_fb.status_code == 200:
                        ip_text = res_fb.text.strip()
                        return True, latency_ms, ip_text, "Unknown", None
                    return False, latency_ms, None, None, f"HTTP status: {res.status_code}"

        except httpx.ProxyError as e:
            return False, None, None, None, f"Proxy connection error: {str(e)}"
        except httpx.ConnectTimeout:
            return False, None, None, None, "Connection timeout (12s)"
        except Exception as e:
            logger.warning(f"Error testing proxy {proxy.host}:{proxy.port}: {e}")
            return False, None, None, None, str(e)

    async def check_and_update_proxy(self, session: Session, proxy: AiProxy) -> AiProxy:
        is_working, latency_ms, detected_ip, detected_country, err = await self.test_proxy(proxy)
        
        proxy.status = "working" if is_working else "failed"
        proxy.latency_ms = latency_ms
        proxy.detected_ip = detected_ip
        proxy.detected_country = detected_country
        proxy.last_error = err
        proxy.last_checked_at = datetime.now(timezone.utc).replace(tzinfo=None)
        proxy.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        session.add(proxy)
        session.commit()
        session.refresh(proxy)
        return proxy

    async def auto_select_best_proxy(self, session: Session) -> Optional[AiProxy]:
        proxies = session.exec(
            select(AiProxy).where(AiProxy.is_enabled == True).order_by(AiProxy.priority.asc(), AiProxy.id.asc())
        ).all()

        if not proxies:
            return None

        for p in proxies:
            is_working, latency_ms, detected_ip, detected_country, err = await self.test_proxy(p)
            p.status = "working" if is_working else "failed"
            p.latency_ms = latency_ms
            p.detected_ip = detected_ip
            p.detected_country = detected_country
            p.last_error = err
            p.last_checked_at = datetime.now(timezone.utc).replace(tzinfo=None)
            p.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
            if is_working:
                for other in proxies:
                    other.is_active_current = (other.id == p.id)
                    session.add(other)
                session.commit()
                session.refresh(p)
                return p
            else:
                p.is_active_current = False
                session.add(p)
                session.commit()

        return None

    def get_active_proxy(self, session: Session, pinned_proxy_id: Optional[int] = None) -> Optional[AiProxy]:
        if pinned_proxy_id:
            pinned = session.get(AiProxy, pinned_proxy_id)
            if pinned and pinned.is_enabled:
                return pinned

        active = session.exec(
            select(AiProxy).where(AiProxy.is_active_current == True, AiProxy.is_enabled == True)
        ).first()

        if not active:
            active = session.exec(
                select(AiProxy).where(AiProxy.is_enabled == True, AiProxy.status == "working")
                .order_by(AiProxy.priority.asc(), AiProxy.latency_ms.asc())
            ).first()

        return active

    # ==========================================
    # 2. АВТОРИЗАЦИЯ РОССИЙСКИХ ИИ
    # ==========================================

    async def get_gigachat_access_token(self, connection: AiProviderConnection, session: Session) -> str:
        extra = dict(connection.extra_config or {})
        cached_token = extra.get("access_token")
        expires_at = extra.get("expires_at", 0)

        if cached_token and time.time() < (expires_at - 60):
            return cached_token

        auth_key = connection.api_key.strip() if connection.api_key else ""
        scope = connection.auth_scope or "GIGACHAT_API_PERS"
        rquid = str(uuid.uuid4())

        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        headers = {
            "Authorization": f"Basic {auth_key}",
            "RqUID": rquid,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"scope": scope}

        async with httpx.AsyncClient(
            verify=connection.verify_ssl,
            trust_env=False,
            timeout=15.0
        ) as client:
            res = await client.post(url, headers=headers, data=data)
            if res.status_code != 200:
                raise Exception(f"GigaChat OAuth Error ({res.status_code}): {res.text}")

            token_data = res.json()
            access_token = token_data.get("access_token")
            exp_ts = token_data.get("expires_at", int((time.time() + 1800) * 1000)) / 1000.0

            extra["access_token"] = access_token
            extra["expires_at"] = exp_ts
            connection.extra_config = extra
            session.add(connection)
            session.commit()

            return access_token

    # ==========================================
    # 3. ТЕСТИРОВАНИЕ И ВЫЗОВ ПРОВАЙДЕРОВ
    # ==========================================

    def _check_and_reset_daily_limits(self, connection: AiProviderConnection):
        """Проверяет и сбрасывает счетчики дня при смене календарной даты"""
        today = date.today()
        if connection.last_reset_date != today:
            connection.last_reset_date = today
            connection.today_requests = 0
            connection.today_tokens = 0

    async def test_connection(self, session: Session, connection: AiProviderConnection) -> Tuple[bool, int, str]:
        start = time.time()
        test_prompt = "Напиши ровно одно слово: ОК"

        try:
            resp_text, tokens = await self.generate_completion(
                session=session,
                connection=connection,
                prompt=test_prompt,
                system_prompt="Отвечай кратко.",
                max_tokens=20,
                temperature=0.1
            )
            latency = int((time.time() - start) * 1000)
            
            self._check_and_reset_daily_limits(connection)
            connection.status = "connected"
            connection.last_tested_at = datetime.now(timezone.utc).replace(tzinfo=None)
            connection.last_error = None
            connection.total_requests = (connection.total_requests or 0) + 1
            connection.total_tokens = (connection.total_tokens or 0) + (tokens or 1)
            connection.today_requests = (connection.today_requests or 0) + 1
            connection.today_tokens = (connection.today_tokens or 0) + (tokens or 1)
            session.add(connection)
            session.commit()
            return True, latency, resp_text.strip()

        except Exception as e:
            latency = int((time.time() - start) * 1000)
            err_msg = str(e)
            connection.status = "error"
            connection.last_tested_at = datetime.now(timezone.utc).replace(tzinfo=None)
            connection.last_error = err_msg
            session.add(connection)
            session.commit()
            return False, latency, err_msg

    async def fetch_available_models(
        self,
        session: Session,
        connection: Optional[AiProviderConnection] = None,
        provider_type: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        pinned_proxy_id: Optional[int] = None,
        provider_group: Optional[str] = None
    ) -> List[str]:
        """Динамически запрашивает список доступных моделей у провайдера ИИ с фоллбэком на встроенный справочник"""
        ptype = (connection.provider_type if connection else (provider_type or "gemini")).lower()
        pgroup = (connection.provider_group if connection else (provider_group or "global")).lower()
        key = ((connection.api_key if connection else api_key) or "").strip()
        b_url = (connection.base_url if connection else base_url) or ""
        proxy_id = connection.pinned_proxy_id if connection else pinned_proxy_id
        use_proxy = connection.use_proxy if connection else (pgroup == "global")

        proxy_url = None
        if pgroup == "global" and use_proxy:
            active_p = self.get_active_proxy(session, proxy_id)
            if active_p:
                proxy_url = active_p.build_url()

        # 1. Google Gemini
        if ptype == "gemini":
            default_gemini = [
                "gemini-3.1-flash-lite",
                "gemini-3.5-flash-lite",
                "gemini-3.8-flash",
                "gemini-flash-latest",
                "gemini-pro-latest",
                "gemini-2.5-flash-lite",
                "gemini-2.5-pro"
            ]
            if not key:
                return default_gemini

            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
            try:
                async with httpx.AsyncClient(proxy=proxy_url, timeout=12.0, trust_env=False) as client:
                    res = await client.get(url)
                    if res.status_code == 200:
                        data = res.json()
                        raw_models = data.get("models", [])
                        valid_models = []
                        for m in raw_models:
                            methods = m.get("supportedGenerationMethods", [])
                            name = m.get("name", "").replace("models/", "")
                            if "generateContent" in methods and "gemini" in name:
                                valid_models.append(name)

                        # Приоритетная сортировка: сначала популярные/рекомендуемые
                        priority_order = [
                            "gemini-3.1-flash-lite",
                            "gemini-3.5-flash-lite",
                            "gemini-3.8-flash",
                            "gemini-flash-latest",
                            "gemini-pro-latest"
                        ]
                        sorted_models = [m for m in priority_order if m in valid_models]
                        for m in sorted(valid_models):
                            if m not in sorted_models:
                                sorted_models.append(m)

                        return sorted_models if sorted_models else default_gemini
            except Exception as e:
                logger.warning(f"Error fetching dynamic Gemini models: {e}")
            return default_gemini

        # 2. OpenAI / DeepSeek / OpenRouter / Groq / Cerebras / Nvidia / GitHub Models
        elif ptype in ["openai", "deepseek", "openrouter", "custom", "tbank_ai", "groq", "cerebras", "nvidia", "github_models"]:
            default_map = {
                "groq": [
                    "llama-3.3-70b-versatile",
                    "llama-3.1-8b-instant",
                    "deepseek-r1-distill-llama-70b",
                    "mixtral-8x7b-32768",
                    "gemma2-9b-it",
                    "qwen-2.5-32b"
                ],
                "cerebras": [
                    "llama3.3-70b",
                    "llama3.1-70b",
                    "llama3.1-8b",
                    "deepseek-r1-distill-llama-70b"
                ],
                "nvidia": [
                    "meta/llama-3.3-70b-instruct",
                    "meta/llama-3.1-405b-instruct",
                    "deepseek-ai/deepseek-r1",
                    "mistralai/mistral-large-2-instruct",
                    "nvidia/llama-3.1-nemotron-70b-instruct"
                ],
                "github_models": [
                    "gpt-4o-mini",
                    "gpt-4o",
                    "o1-preview",
                    "o1-mini",
                    "Meta-Llama-3.1-70B-Instruct",
                    "Phi-3.5-mini-instruct",
                    "Mistral-large-2407",
                    "DeepSeek-R1"
                ],
                "deepseek": ["deepseek-chat", "deepseek-reasoner"],
                "openai": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "o1-mini", "o3-mini"]
            }
            default_models = default_map.get(ptype, ["default"])

            if not key:
                return default_models

            base = b_url or DEFAULT_BASE_URLS.get(ptype, "https://api.openai.com/v1")
            if base.endswith("/"):
                base = base[:-1]
            url = f"{base}/models"

            try:
                headers = {"Authorization": f"Bearer {key}"}
                async with httpx.AsyncClient(proxy=proxy_url, timeout=12.0, trust_env=False) as client:
                    res = await client.get(url, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        raw_list = data.get("data", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                        model_ids = []
                        for m in raw_list:
                            if isinstance(m, dict):
                                m_id = m.get("id") or m.get("name")
                                if m_id:
                                    model_ids.append(m_id)
                            elif isinstance(m, str):
                                model_ids.append(m)

                        if ptype == "openai":
                            # Фильтруем основные чат-модели
                            chat_models = [mid for mid in model_ids if any(pref in mid for pref in ["gpt-4", "gpt-3.5", "o1", "o3", "chatgpt"])]
                            return sorted(chat_models) if chat_models else default_models
                        elif ptype == "groq":
                            # Приоритетно новые модели
                            priority_groq = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "deepseek-r1-distill-llama-70b"]
                            ordered = [m for m in priority_groq if m in model_ids]
                            for m in sorted(model_ids):
                                if m not in ordered:
                                    ordered.append(m)
                            return ordered if ordered else default_models
                        return sorted(model_ids) if model_ids else default_models
            except Exception as e:
                logger.warning(f"Error fetching dynamic models for {ptype}: {e}")
            return default_models

        # 3. Anthropic Claude
        elif ptype == "anthropic":
            return [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229"
            ]

        # 4. Сбер GigaChat
        elif ptype == "gigachat":
            default_giga = ["GigaChat", "GigaChat-Pro", "GigaChat-Max", "GigaChat-Plus"]
            if not connection and not key:
                return default_giga

            try:
                # Если передан connection, можем запросить токен
                token = None
                if connection:
                    token = await self.get_gigachat_access_token(connection, session)
                if token:
                    url = "https://gigachat.devices.sberbank.ru/api/v1/models"
                    verify_val = connection.verify_ssl if connection else True
                    async with httpx.AsyncClient(verify=verify_val, timeout=10.0, trust_env=False) as client:
                        res = await client.get(url, headers={"Authorization": f"Bearer {token}"})
                        if res.status_code == 200:
                            data = res.json()
                            models = [m.get("id") for m in data.get("data", []) if m.get("id")]
                            return models if models else default_giga
            except Exception as e:
                logger.warning(f"Error fetching dynamic GigaChat models: {e}")
            return default_giga

        # 5. YandexGPT
        elif ptype == "yandexgpt":
            return [
                "yandexgpt/latest",
                "yandexgpt-lite/latest",
                "yandexgpt/rc",
                "yandexgpt-lite/rc",
                "summarization/latest"
            ]

        return ["default"]

    async def generate_completion(
        self,
        session: Session,
        connection: AiProviderConnection,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        return_details: bool = False
    ) -> Any:
        ptype = connection.provider_type.lower()
        pgroup = connection.provider_group.lower()

        # Прокси для мировых моделей
        proxy_url = None
        if pgroup == "global" and connection.use_proxy:
            active_proxy = self.get_active_proxy(session, connection.pinned_proxy_id)
            if active_proxy:
                proxy_url = active_proxy.build_url()

        # 1. Google Gemini (с автоповторами и fallback)
        if ptype == "gemini":
            target_model = connection.default_model or "gemini-3.1-flash-lite"
            api_key = (connection.api_key or "").strip()

            # Формируем цепочку моделей для проверки при 503 / 404 / 429
            fallback_models = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-flash-latest"]
            models_to_try = [target_model]
            for fb in fallback_models:
                if fb not in models_to_try:
                    models_to_try.append(fb)

            contents = []
            if conversation_history:
                for msg in conversation_history:
                    role_str = "user" if msg.get("role") == "user" else "model"
                    contents.append({
                        "role": role_str,
                        "parts": [{"text": msg.get("content", "")}]
                    })
            contents.append({
                "role": "user",
                "parts": [{"text": prompt}]
            })

            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens
                }
            }
            if system_prompt:
                payload["systemInstruction"] = {
                    "parts": [{"text": system_prompt}]
                }

            last_error_text = ""
            for model_attempt in models_to_try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_attempt}:generateContent?key={api_key}"
                
                # До 2 попыток на модель с задержкой при 503 / 429
                for retry in range(2):
                    try:
                        async with httpx.AsyncClient(proxy=proxy_url, timeout=30.0, trust_env=False) as client:
                            res = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                            
                            if res.status_code == 200:
                                data = res.json()
                                candidates = data.get("candidates", [])
                                if not candidates:
                                    raise Exception("Gemini вернул пустой список кандидатов")
                                
                                parts = candidates[0].get("content", {}).get("parts", [])
                                text = "".join([p.get("text", "") for p in parts])
                                tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
                                
                                fallback_note = None
                                if model_attempt != target_model:
                                    fallback_note = f"Модель {target_model} временно перегружена (503 High Demand). Запрос успешно выполнен резервной моделью {model_attempt}."
                                
                                if return_details:
                                    return text, tokens, model_attempt, fallback_note
                                return text, tokens

                            elif res.status_code in [503, 429]:
                                last_error_text = f"HTTP {res.status_code}: {res.text}"
                                logger.warning(f"Gemini {model_attempt} returned {res.status_code} (attempt {retry+1}/2). Backing off...")
                                await asyncio.sleep(1.2 * (retry + 1))
                                continue

                            elif res.status_code == 404:
                                last_error_text = f"HTTP 404: Модель {model_attempt} не найдена или устарела."
                                logger.warning(f"Gemini model {model_attempt} returned 404, switching to fallback.")
                                break

                            else:
                                last_error_text = f"Gemini API Error ({res.status_code}): {res.text}"
                                break

                    except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                        last_error_text = f"Timeout при обращении к {model_attempt}: {e}"
                        logger.warning(last_error_text)
                        await asyncio.sleep(1.0)
                        continue
                    except Exception as e:
                        last_error_text = str(e)
                        break

            # Если все попытки и фоллбэки исчерпаны
            raise Exception(f"Все попытки вызова Gemini исчерпаны. Последняя ошибка: {last_error_text}")

        # 2. OpenAI / DeepSeek / OpenRouter / Custom / T-Bank / Groq / Cerebras / Nvidia / GitHub Models
        elif ptype in ["openai", "deepseek", "openrouter", "custom", "tbank_ai", "groq", "cerebras", "nvidia", "github_models"]:
            base_url = connection.base_url or DEFAULT_BASE_URLS.get(ptype, "https://api.openai.com/v1")
            if base_url.endswith("/"):
                base_url = base_url[:-1]
            url = f"{base_url}/chat/completions"

            default_model_map = {
                "groq": "llama-3.3-70b-versatile",
                "cerebras": "llama3.3-70b",
                "nvidia": "meta/llama-3.3-70b-instruct",
                "github_models": "gpt-4o-mini",
                "deepseek": "deepseek-chat",
                "openai": "gpt-4o-mini"
            }
            model = connection.default_model or default_model_map.get(ptype, "gpt-4o-mini")
            api_key = (connection.api_key or "").strip()

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if conversation_history:
                messages.extend(conversation_history)
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            if connection.client_id and ptype == "openai":
                headers["OpenAI-Organization"] = connection.client_id

            effective_proxy = proxy_url if pgroup == "global" and connection.use_proxy else None

            async with httpx.AsyncClient(
                proxy=effective_proxy,
                verify=connection.verify_ssl,
                timeout=45.0,
                trust_env=False
            ) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code != 200:
                    raise Exception(f"{ptype.upper()} Error ({res.status_code}): {res.text}")

                # Захват заголовков Rate Limit от провайдера
                rl_data = {}
                for h_name in [
                    "x-ratelimit-limit-requests",
                    "x-ratelimit-remaining-requests",
                    "x-ratelimit-reset-requests",
                    "x-ratelimit-limit-tokens",
                    "x-ratelimit-remaining-tokens",
                    "x-ratelimit-reset-tokens",
                    "x-ratelimit-limit-requests-minute",
                    "x-ratelimit-remaining-requests-minute",
                    "x-ratelimit-reset-requests-minute",
                    "x-ratelimit-limit-tokens-minute",
                    "x-ratelimit-remaining-tokens-minute",
                    "x-ratelimit-reset-tokens-minute",
                    "x-ratelimit-limit-requests-day",
                    "x-ratelimit-remaining-requests-day"
                ]:
                    h_val = res.headers.get(h_name)
                    if h_val is not None:
                        rl_data[h_name] = h_val

                if rl_data:
                    extra = dict(connection.extra_config or {})
                    extra["live_rate_limits"] = rl_data
                    connection.extra_config = extra
                    if "x-ratelimit-limit-requests" in rl_data and str(rl_data["x-ratelimit-limit-requests"]).isdigit():
                        connection.rpm_limit = int(rl_data["x-ratelimit-limit-requests"])
                    elif "x-ratelimit-limit-requests-minute" in rl_data and str(rl_data["x-ratelimit-limit-requests-minute"]).isdigit():
                        connection.rpm_limit = int(rl_data["x-ratelimit-limit-requests-minute"])
                    session.add(connection)
                    session.commit()

                data = res.json()
                choices = data.get("choices", [])
                if not choices:
                    raise Exception("No choices returned from model")

                text = choices[0].get("message", {}).get("content", "")
                tokens = data.get("usage", {}).get("total_tokens", 0)
                if return_details:
                    return text, tokens, model, None
                return text, tokens

        # 3. Anthropic Claude
        elif ptype == "anthropic":
            url = "https://api.anthropic.com/v1/messages"
            model = connection.default_model or "claude-3-5-haiku-20241022"
            api_key = (connection.api_key or "").strip()

            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }

            messages = []
            if conversation_history:
                messages.extend(conversation_history)
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            if system_prompt:
                payload["system"] = system_prompt

            async with httpx.AsyncClient(proxy=proxy_url, timeout=45.0, trust_env=False) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code != 200:
                    raise Exception(f"Anthropic Claude Error ({res.status_code}): {res.text}")

                data = res.json()
                content_blocks = data.get("content", [])
                text = "".join([b.get("text", "") for b in content_blocks if b.get("type") == "text"])
                usage = data.get("usage", {})
                tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                if return_details:
                    return text, tokens, model, None
                return text, tokens

        # 4. Сбер GigaChat (Прямой канал в РФ)
        elif ptype == "gigachat":
            access_token = await self.get_gigachat_access_token(connection, session)
            url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
            model = connection.default_model or "GigaChat"

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if conversation_history:
                messages.extend(conversation_history)
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(
                verify=connection.verify_ssl,
                timeout=45.0,
                trust_env=False
            ) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code != 200:
                    raise Exception(f"GigaChat Error ({res.status_code}): {res.text}")

                data = res.json()
                choices = data.get("choices", [])
                if not choices:
                    raise Exception("GigaChat returned no choices")

                text = choices[0].get("message", {}).get("content", "")
                tokens = data.get("usage", {}).get("total_tokens", 0)
                if return_details:
                    return text, tokens, model, None
                return text, tokens

        # 5. Яндекс YandexGPT (Прямой канал в РФ)
        elif ptype == "yandexgpt":
            extra_cfg = dict(connection.extra_config or {})
            folder_id = (connection.client_id or "").strip()
            if not folder_id and extra_cfg.get("folder_id"):
                folder_id = str(extra_cfg.get("folder_id", "")).strip()

            api_key = (connection.api_key or "").strip()
            if not api_key and (extra_cfg.get("secret_key") or extra_cfg.get("api_key")):
                api_key = str(extra_cfg.get("secret_key") or extra_cfg.get("api_key") or "").strip()

            key_id = str(extra_cfg.get("key_id", "")).strip()

            # Интеллектуальная коррекция, если перепутаны Секретный ключ и Идентификатор ключа
            if api_key.startswith("aje") and key_id and (key_id.startswith("AQVN") or len(key_id) > 35):
                api_key, key_id = key_id, api_key

            if not folder_id:
                raise Exception(
                    "Не указан 'Идентификатор каталога' (Folder ID, например: b1g...) из консоли Yandex Cloud. "
                    "Без него обращение к модели YandexGPT невозможно (modelUri: gpt://<folder_id>/<модель>). "
                    "Пожалуйста, укажите Folder ID в настройках подключения."
                )

            if not api_key:
                raise Exception(
                    "Не указан 'Секретный ключ' (Secret Key, обычно начинается с AQVN...) сервисного аккаунта Yandex Cloud. "
                    "Пожалуйста, укажите его в настройках подключения."
                )

            if api_key.startswith("aje") and len(api_key) <= 30 and not api_key.startswith("AQVN"):
                raise Exception(
                    f"Значение в поле ключа ('{api_key[:8]}...') является 'Идентификатором API-ключа' (Key ID), "
                    "а не 'Секретным ключом'. Для авторизации в Yandex Cloud требуется именно Секретный ключ (Secret Key, обычно начинается с AQVN...). "
                    "Скопируйте Секретный ключ, показанный при создании ключа в консоли Yandex Cloud."
                )

            auth_type = connection.auth_scope or "api_key"
            model_name = connection.default_model or "yandexgpt/latest"

            model_uri = f"gpt://{folder_id}/{model_name}"
            url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

            auth_header = f"Api-Key {api_key}" if auth_type == "api_key" else f"Bearer {api_key}"
            headers = {
                "Authorization": auth_header,
                "x-folder-id": folder_id,
                "Content-Type": "application/json"
            }

            messages = []
            if system_prompt:
                messages.append({"role": "system", "text": system_prompt})
            if conversation_history:
                for h in conversation_history:
                    messages.append({"role": h.get("role", "user"), "text": h.get("content", "")})
            messages.append({"role": "user", "text": prompt})

            payload = {
                "modelUri": model_uri,
                "completionOptions": {
                    "stream": False,
                    "temperature": temperature,
                    "maxTokens": str(max_tokens)
                },
                "messages": messages
            }

            async with httpx.AsyncClient(
                verify=connection.verify_ssl,
                timeout=45.0,
                trust_env=False
            ) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code != 200:
                    err_text = res.text
                    if res.status_code in [401, 403]:
                        raise Exception(
                            f"Ошибка авторизации Yandex Cloud ({res.status_code}): проверьте правильность Секретного ключа (начинается на AQVN...) "
                            f"и убедитесь, что сервисному аккаунту выдана роль 'ai.languageModels.user' на каталог '{folder_id}'. Ответ: {err_text}"
                        )
                    elif res.status_code == 400 and "model_uri" in err_text:
                        raise Exception(
                            f"Ошибка Yandex Cloud ({res.status_code}): неверный адрес модели (modelUri: {model_uri}). "
                            f"Проверьте Folder ID каталога ('{folder_id}') и имя модели ('{model_name}'). Ответ: {err_text}"
                        )
                    else:
                        raise Exception(f"YandexGPT Error ({res.status_code}): {err_text}")

                data = res.json()
                result = data.get("result", {})
                alternatives = result.get("alternatives", [])
                if not alternatives:
                    raise Exception("YandexGPT вернул пустой список вариантов ответа")

                text = alternatives[0].get("message", {}).get("text", "")
                usage = result.get("usage", {})
                tokens = int(usage.get("totalTokens", 0))
                if return_details:
                    return text, tokens, model_name, None
                return text, tokens

        else:
            raise Exception(f"Unsupported provider type: {ptype}")

    def get_gemini_pool_connection(self, session: Session) -> Optional[AiProviderConnection]:
        gemini_conns = session.exec(
            select(AiProviderConnection)
            .where(
                AiProviderConnection.provider_type == "gemini",
                AiProviderConnection.is_enabled == True
            )
            .order_by(AiProviderConnection.total_requests.asc(), AiProviderConnection.rotation_weight.desc())
        ).all()

        return gemini_conns[0] if gemini_conns else None

    def get_available_data_sources(self) -> List[Dict[str, Any]]:
        """Возвращает каталог доступных источников данных системы для агентов"""
        return AVAILABLE_DATA_SOURCES

    # ==========================================
    # 4. СБОР КОНТЕКСТА САЙТА
    # ==========================================

    def gather_site_context(self, session: Session, agent_code: str, custom_sources: Optional[List[str]] = None) -> str:
        """Динамически собирает актуальный контекст сайта из БД на основе подключенных к агенту источников данных"""
        context_parts = []

        # Определяем источники данных
        sources = custom_sources
        if sources is None:
            agent = session.exec(select(AiSiteAgent).where(AiSiteAgent.agent_code == agent_code)).first()
            if agent and agent.permissions_config and isinstance(agent.permissions_config, dict):
                sources = agent.permissions_config.get("data_sources", [])

        if not sources:
            if agent_code == "stats_analyst":
                sources = ["olap_stats", "orders"]
            elif agent_code == "feedback_nps":
                sources = ["nps_reviews", "orders"]
            elif agent_code == "site_manager":
                sources = ["menu_catalog", "orders"]
            else:
                sources = ["olap_stats", "orders", "customers", "menu_catalog"]

        try:
            # 1. OLAP Выручка
            if "olap_stats" in sources:
                recent_revs = session.exec(
                    select(OlapRevenueRecord).order_by(OlapRevenueRecord.id.desc()).limit(7)
                ).all()
                if recent_revs:
                    context_parts.append("📊 ПОСЛЕДНИЕ ДАННЫЕ ВЫРУЧКИ И ПРОДАЖ (OLAP iiko Resto):")
                    for r in recent_revs:
                        context_parts.append(
                            f"- Дата: {r.business_date}, Выручка: {r.revenue} ₽, Заказов: {r.orders_count}, "
                            f"Ср. чек: {r.average_check} ₽, Скидки: {r.discount_sum} ₽, Наличные: {r.cash_sum} ₽, Карты/Безнал: {r.card_sum} ₽"
                        )

            # 2. Заказы
            if "orders" in sources:
                recent_orders = session.exec(
                    select(Order).order_by(Order.id.desc()).limit(12)
                ).all()
                if recent_orders:
                    context_parts.append(f"\n📦 ПОСЛЕДНИЕ {len(recent_orders)} ЗАКАЗОВ САЙТА:")
                    for o in recent_orders:
                        dt_str = o.created_at.strftime('%d.%m %H:%M') if getattr(o, 'created_at', None) else '–'
                        deliv = getattr(o, 'delivery_type', 'стандарт')
                        context_parts.append(
                            f"- Заказ #{o.id} ({dt_str}): Сумма: {o.total_amount} ₽, Скидка: {o.total_discount} ₽, "
                            f"Оплачено: {o.total_paid} ₽, Статус: {o.status}, Доставка: {deliv}"
                        )

            # 3. Клиенты и лояльность
            if "customers" in sources and Customer:
                recent_customers = session.exec(
                    select(Customer).order_by(Customer.id.desc()).limit(8)
                ).all()
                if recent_customers:
                    context_parts.append(f"\n👥 КЛИЕНТСКАЯ БАЗА И ЛОЯЛЬНОСТЬ (ПОСЛЕДНИЕ ГОСТИ):")
                    for c in recent_customers:
                        b_bal = getattr(c, 'bonus_balance', 0)
                        is_new = 'Да' if getattr(c, 'is_new_guest', False) else 'Постоянный'
                        context_parts.append(
                            f"- Гость: {c.name or 'Без имени'} ({c.phone}), Бонусный баланс: {b_bal} баллов, Новый гость: {is_new}"
                        )

            # 4. Отзывы NPS
            if "nps_reviews" in sources:
                reviews = session.exec(
                    select(NpsReview).order_by(NpsReview.id.desc()).limit(8)
                ).all()
                if reviews:
                    context_parts.append("\n⭐ ПОСЛЕДНИЕ ОТЗЫВЫ И ОЦЕНКИ ГОСТЕЙ (NPS):")
                    for rev in reviews:
                        rating = getattr(rev, "rating", None) or getattr(rev, "score", "–")
                        comment = getattr(rev, "comment", "") or getattr(rev, "text", "")
                        context_parts.append(f"- Оценка {rating}/5: \"{comment}\"")

            # 5. Каталог меню
            if "menu_catalog" in sources:
                products = session.exec(
                    select(Product).order_by(Product.id.desc()).limit(15)
                ).all()
                if products:
                    context_parts.append("\n🍣 ПОЗИЦИИ МЕНЮ И СТОП-ЛИСТ:")
                    for p in products:
                        avail = 'Да' if p.is_available else 'НЕТ (в стоп-листе)'
                        context_parts.append(f"- {p.name} | Цена: {p.price} ₽ | Доступен: {avail}")

            # 6. Промокоды
            if "promo_codes" in sources and PromoCode:
                promos = session.exec(
                    select(PromoCode).order_by(PromoCode.id.desc()).limit(6)
                ).all()
                if promos:
                    context_parts.append("\n🎁 ДЕЙСТВУЮЩИЕ ПРОМОКОДЫ И АКЦИИ:")
                    for pr in promos:
                        context_parts.append(
                            f"- Промокод '{pr.code}': скидка {getattr(pr, 'discount_percent', 0)}% / {getattr(pr, 'discount_amount', 0)} ₽, Активен: {pr.is_active}"
                        )

        except Exception as e:
            logger.warning(f"Error gathering dynamic site context for {agent_code}: {e}")

        return "\n".join(context_parts) if context_parts else "Данные сайта на текущий момент обновляются."

    # ==========================================
    # 5. ГЕНЕРАТОР СИСТЕМНЫХ ПРОМПТОВ ЧЕРЕЗ ИИ
    # ==========================================

    async def generate_agent_prompt(
        self,
        session: Session,
        goal: str,
        title: Optional[str] = None,
        selected_data_sources: Optional[List[str]] = None,
        connection_id: Optional[int] = None,
        current_prompt: Optional[str] = None,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Генерирует развернутый профессиональный системный промпт для ИИ-агента с использованием подключенных ИИ без ограничений"""
        # 1. Подбираем подключение ИИ
        conn = None
        if connection_id:
            conn = session.get(AiProviderConnection, connection_id)
        if not conn:
            conn = self.get_gemini_pool_connection(session)
        if not conn:
            conn = session.exec(
                select(AiProviderConnection)
                .where(AiProviderConnection.is_enabled == True)
                .order_by(AiProviderConnection.id.asc())
            ).first()

        if not conn:
            raise Exception("Нет активных подключений ИИ для генерации промпта. Подключите Gemini, GigaChat, YandexGPT или OpenAI.")

        # 2. Описание выбранных источников данных
        sources_info = []
        sources_list = selected_data_sources or ["olap_stats", "orders", "customers", "menu_catalog"]
        for src_id in sources_list:
            for s in AVAILABLE_DATA_SOURCES:
                if s["id"] == src_id:
                    sources_info.append(f"- {s['name']}: {s['description']} (Поля: {', '.join(s['sample_fields'])})")

        sources_text = "\n".join(sources_info) if sources_info else "Общие данные сайта (выручка, заказы, меню)."

        # 3. Meta-prompt
        engineer_system = (
            "Ты главный эксперт по Prompt Engineering и системный архитектор ИИ-агентов в сфере FoodTech (сеть доставки еды VezuRoll).\n"
            "Твоя задача — составить развернутый, глубокий, высокоэффективный SYSTEM PROMPT для ИИ-агента платформы без каких-либо искусственных ограничений по длине и детализации.\n\n"
            "Требования к промпту агента:\n"
            "1. Четкая ролевая идентичность, сфера ответственности и экспертные цели.\n"
            "2. Подробная инструкция, как читать и анализировать поступающие данные из БД сайта.\n"
            "3. Структура и формат ответа (Markdown, списки, выделение ключевых цифр, таблицы при необходимости, конкретные выводы и призывы к действию).\n"
            "4. Ограничения: опираться на факты из базы данных, не фантазировать отсутствующие цифры, четко разделять подтвержденные данные и гипотезы.\n"
            "5. Деловой, конструктивный, профессиональный тон.\n\n"
            "ОТВЕТ ДОЛЖЕН БЫТЬ СТРОГО В ФОРМАТЕ JSON:\n"
            "{\n"
            '  "title": "Рекомендуемое название агента",\n'
            '  "agent_code": "rekomenduemyi_kod_agenta",\n'
            '  "description": "Краткое понятное описание роли агента (1-2 предложения)",\n'
            '  "recommended_data_sources": ["olap_stats", "orders"],\n'
            '  "system_prompt": "ПОЛНЫЙ РАЗВЕРНУТЫЙ ТЕКСТ СИСТЕМНОГО ПРОМПТА..."\n'
            "}"
        )

        user_req = (
            f"Создай системный промпт для агента сайта FoodTech:\n"
            f"Желаемое название: {title or 'Умный ассистент'}\n"
            f"Задача и цель агента: {goal}\n"
            f"Источники данных сайта, к которым агент имеет доступ:\n{sources_text}\n"
        )
        if current_prompt:
            user_req += f"\nТекущий базовый промпт для улучшения/расширения:\n{current_prompt}\n"
        if custom_instructions:
            user_req += f"\nДополнительные пожелания заказчика:\n{custom_instructions}\n"

        resp_text, tokens = await self.generate_completion(
            session=session,
            connection=conn,
            prompt=user_req,
            system_prompt=engineer_system,
            max_tokens=4000,
            temperature=0.6
        )

        # 4. Парсинг ответа
        parsed = None
        cleaned = resp_text.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

        try:
            parsed = json.loads(cleaned)
        except Exception as e:
            logger.warning(f"Failed to parse prompt json: {e}")
            parsed = {
                "title": title or "ИИ Агент сайта",
                "agent_code": (title or "custom_agent").lower().replace(" ", "_"),
                "description": goal[:150],
                "recommended_data_sources": sources_list,
                "system_prompt": resp_text
            }

        parsed["generated_by_model"] = conn.default_model
        parsed["generated_by_provider"] = conn.name
        parsed["tokens_used"] = tokens
        return parsed

    # ==========================================
    # 6. ТЕСТОВОЕ ИСПОЛНЕНИЕ В ПЕСОЧНИЦЕ
    # ==========================================

    async def execute_agent_query(
        self,
        session: Session,
        agent_code: str,
        query: str,
        connection_id_override: Optional[int] = None,
        model_override: Optional[str] = None,
        use_live_data: bool = True,
        custom_data_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Исполняет запрос к агенту в тестовой песочнице с передачей данных из БД сайта"""
        start = time.time()
        agent = session.exec(select(AiSiteAgent).where(AiSiteAgent.agent_code == agent_code)).first()
        if not agent:
            raise Exception(f"Агент с кодом '{agent_code}' не найден в системе")

        # Подбираем подключение
        conn = None
        if connection_id_override:
            conn = session.get(AiProviderConnection, connection_id_override)
        if not conn and agent.use_gemini_pool:
            conn = self.get_gemini_pool_connection(session)
        if not conn and agent.primary_connection_id:
            conn = session.get(AiProviderConnection, agent.primary_connection_id)
        if not conn and agent.fallback_connection_id:
            conn = session.get(AiProviderConnection, agent.fallback_connection_id)
        if not conn:
            conn = session.exec(select(AiProviderConnection).where(AiProviderConnection.is_enabled == True)).first()

        if not conn:
            raise Exception("Нет активных подключений ИИ для выполнения запроса.")

        # Модель
        original_model = conn.default_model
        if model_override:
            conn.default_model = model_override
        elif agent.model_override:
            conn.default_model = agent.model_override

        # Контекст данных
        full_system_prompt = agent.system_prompt or ""
        sources_used = []
        if use_live_data:
            sources_used = custom_data_sources
            if sources_used is None and agent.permissions_config and isinstance(agent.permissions_config, dict):
                sources_used = agent.permissions_config.get("data_sources", [])
            site_ctx = self.gather_site_context(session, agent_code, custom_sources=sources_used)
            full_system_prompt += f"\n\nАКТУАЛЬНЫЕ ДАННЫЕ САЙТА ИЗ БАЗЫ ДАННЫХ:\n{site_ctx}"

        try:
            resp_text, tokens, used_model, fallback_note = await self.generate_completion(
                session=session,
                connection=conn,
                prompt=query,
                system_prompt=full_system_prompt,
                max_tokens=agent.max_tokens or 2048,
                temperature=float(agent.temperature or 0.7),
                return_details=True
            )
            latency_ms = int((time.time() - start) * 1000)

            conn.default_model = original_model
            session.add(conn)
            session.commit()

            return {
                "status": "success",
                "agent_title": agent.title,
                "agent_code": agent.agent_code,
                "response": resp_text,
                "model": used_model,
                "fallback_note": fallback_note,
                "provider_name": conn.name,
                "used_proxy": conn.provider_group == "global" and conn.use_proxy,
                "latency_ms": latency_ms,
                "tokens": tokens,
                "data_sources_used": sources_used or []
            }
        except Exception as e:
            conn.default_model = original_model
            session.add(conn)
            session.commit()
            raise e

    # ==========================================
    # 7. ИНТЕРАКТИВНЫЙ ЧАТ С АГЕНТОМ
    # ==========================================

    async def chat_with_agent(
        self,
        session: Session,
        agent_code: str,
        user_message: str,
        session_id: Optional[int] = None,
        connection_id_override: Optional[int] = None,
        model_override: Optional[str] = None
    ) -> Dict[str, Any]:
        start = time.time()
        agent = session.exec(select(AiSiteAgent).where(AiSiteAgent.agent_code == agent_code)).first()
        if not agent:
            raise Exception(f"Agent '{agent_code}' not found")

        # 1. Определяем сессию диалога
        chat_sess = None
        if session_id:
            chat_sess = session.get(AiChatSession, session_id)
        if not chat_sess:
            title_preview = user_message[:40] + ("..." if len(user_message) > 40 else "")
            chat_sess = AiChatSession(title=title_preview, agent_code=agent_code)
            session.add(chat_sess)
            session.commit()
            session.refresh(chat_sess)

        # 2. Сохраняем сообщение пользователя
        user_msg_db = AiChatMessage(
            session_id=chat_sess.id,
            role="user",
            content=user_message
        )
        session.add(user_msg_db)
        session.commit()

        # 3. Достаем историю последних 10 сообщений сессии
        prev_messages = session.exec(
            select(AiChatMessage)
            .where(AiChatMessage.session_id == chat_sess.id)
            .order_by(AiChatMessage.id.asc())
        ).all()
        
        history = []
        for m in prev_messages[:-1]:  # без текущего только что добавленного
            history.append({"role": m.role, "content": m.content})

        # 4. Выбор подключения
        conn = None
        if connection_id_override:
            conn = session.get(AiProviderConnection, connection_id_override)
        if not conn and agent.use_gemini_pool:
            conn = self.get_gemini_pool_connection(session)
        if not conn and agent.primary_connection_id:
            conn = session.get(AiProviderConnection, agent.primary_connection_id)
        if not conn and agent.fallback_connection_id:
            conn = session.get(AiProviderConnection, agent.fallback_connection_id)
        if not conn:
            conn = session.exec(select(AiProviderConnection).where(AiProviderConnection.is_enabled == True)).first()

        if not conn:
            raise Exception("Нет активных подключений ИИ. Пожалуйста, добавьте API ключ в разделе Система -> Агенты ИИ.")

        # Модель
        original_model = conn.default_model
        if model_override:
            conn.default_model = model_override
        elif agent.model_override:
            conn.default_model = agent.model_override

        # Собираем контекст БД
        site_context = self.gather_site_context(session, agent_code)
        full_system_prompt = f"{agent.system_prompt or ''}\n\nАКТУАЛЬНЫЕ ДАННЫЕ САЙТА ИЗ БАЗЫ ДАННЫХ:\n{site_context}"

        fallback_note = None
        actual_model = conn.default_model
        try:
            res_comp = await self.generate_completion(
                session=session,
                connection=conn,
                prompt=user_message,
                system_prompt=full_system_prompt,
                max_tokens=agent.max_tokens or 2048,
                temperature=float(agent.temperature or 0.7),
                conversation_history=history,
                return_details=True
            )
            response_text, tokens, actual_model, fallback_note = res_comp
            latency_ms = int((time.time() - start) * 1000)

            # Восстанавливаем модель если переопределяли
            used_model = actual_model or conn.default_model
            conn.default_model = original_model

            # Обновляем счетчики и квоты
            self._check_and_reset_daily_limits(conn)
            conn.total_requests = (conn.total_requests or 0) + 1
            conn.total_tokens = (conn.total_tokens or 0) + (tokens or 1)
            conn.today_requests = (conn.today_requests or 0) + 1
            conn.today_tokens = (conn.today_tokens or 0) + (tokens or 1)
            session.add(conn)

            # Сохраняем ответ ассистента
            ai_msg_db = AiChatMessage(
                session_id=chat_sess.id,
                role="assistant",
                content=response_text,
                model=used_model,
                tokens_used=tokens,
                latency_ms=latency_ms,
                provider_name=conn.name
            )
            session.add(ai_msg_db)
            chat_sess.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            session.add(chat_sess)
            session.commit()
            session.refresh(ai_msg_db)

            # Расчет остатка лимитов
            extra = dict(conn.extra_config or {})
            tier_info = extra.get("tier_name") or f"{conn.provider_type.upper()} Тариф"
            daily_req_limit = conn.daily_requests_limit or 1500
            today_req = conn.today_requests or 0
            remaining_requests = max(0, daily_req_limit - today_req)
            req_percentage = min(100, int((today_req / max(1, daily_req_limit)) * 100))

            daily_tok_limit = conn.daily_tokens_limit or 1000000
            today_tok = conn.today_tokens or 0
            remaining_tokens = max(0, daily_tok_limit - today_tok)
            tok_percentage = min(100, int((today_tok / max(1, daily_tok_limit)) * 100))

            return {
                "status": "success",
                "session_id": chat_sess.id,
                "message_id": ai_msg_db.id,
                "response": response_text,
                "model": used_model,
                "fallback_note": fallback_note,
                "provider_name": conn.name,
                "provider_group": conn.provider_group,
                "latency_ms": latency_ms,
                "tokens_used": tokens,
                "quota": {
                    "connection_id": conn.id,
                    "connection_name": conn.name,
                    "provider_type": conn.provider_type,
                    "tier_title": tier_info,
                    "rpm_limit": conn.rpm_limit or 15,
                    "daily_requests_limit": daily_req_limit,
                    "today_requests": today_req,
                    "remaining_requests": remaining_requests,
                    "requests_used_percent": req_percentage,
                    "daily_tokens_limit": daily_tok_limit,
                    "today_tokens": today_tok,
                    "remaining_tokens": remaining_tokens,
                    "tokens_used_percent": tok_percentage
                }
            }

        except Exception as e:
            conn.default_model = original_model
            session.add(conn)
            session.commit()
            latency_ms = int((time.time() - start) * 1000)
            err_str = str(e)
            logger.error(f"Error during AI completion: {err_str}")

            # Человекопонятное сообщение об ошибке для чата
            helpful_msg = (
                f"⚠️ **Временная ошибка провайдера ИИ**\n\n"
                f"{err_str}\n\n"
                f"*Рекомендация:* Если вы видите ошибку `503 High demand` от Google Gemini — "
                f"это означает временный пик мировой нагрузки на сервера Google. "
                f"Переключите модель на **gemini-3.1-flash-lite** в выпадающем меню слева или выберите другого провайдера (GigaChat)."
            )

            # Сохраняем уведомление в чат чтобы диалог не зависал
            ai_msg_err = AiChatMessage(
                session_id=chat_sess.id,
                role="assistant",
                content=helpful_msg,
                model=conn.default_model,
                tokens_used=0,
                latency_ms=latency_ms,
                provider_name=conn.name
            )
            session.add(ai_msg_err)
            chat_sess.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            session.add(chat_sess)
            session.commit()
            session.refresh(ai_msg_err)

            return {
                "status": "error_handled",
                "session_id": chat_sess.id,
                "message_id": ai_msg_err.id,
                "response": helpful_msg,
                "model": conn.default_model,
                "fallback_note": None,
                "provider_name": conn.name,
                "provider_group": conn.provider_group,
                "latency_ms": latency_ms,
                "tokens_used": 0,
                "error_detail": err_str,
                "quota": {
                    "connection_id": conn.id,
                    "connection_name": conn.name,
                    "provider_type": conn.provider_type,
                    "tier_title": (conn.extra_config or {}).get("tier_name", "Лимит провайдера"),
                    "rpm_limit": conn.rpm_limit or 15,
                    "daily_requests_limit": conn.daily_requests_limit or 1500,
                    "today_requests": conn.today_requests or 0,
                    "remaining_requests": max(0, (conn.daily_requests_limit or 1500) - (conn.today_requests or 0)),
                    "requests_used_percent": 0,
                    "daily_tokens_limit": conn.daily_tokens_limit or 1000000,
                    "today_tokens": conn.today_tokens or 0,
                    "remaining_tokens": max(0, (conn.daily_tokens_limit or 1000000) - (conn.today_tokens or 0)),
                    "tokens_used_percent": 0
                }
            }

    def get_quota_summary(self, session: Session) -> Dict[str, Any]:
        """Возвращает общую статистику лимитов и токенов по активным подключениям с привязкой к тарифам"""
        conns = session.exec(
            select(AiProviderConnection).where(AiProviderConnection.is_enabled == True)
        ).all()

        total_daily_req = sum(c.daily_requests_limit or 1500 for c in conns) or 1500
        total_today_req = sum(c.today_requests or 0 for c in conns)
        total_daily_tok = sum(c.daily_tokens_limit or 1000000 for c in conns) or 1000000
        total_today_tok = sum(c.today_tokens or 0 for c in conns)

        conns_data = []
        for c in conns:
            self._check_and_reset_daily_limits(c)
            extra = dict(c.extra_config or {})
            tier_title = extra.get("tier_name") or f"{c.provider_type.upper()} ({c.rpm_limit} RPM)"
            
            d_req_lim = c.daily_requests_limit or 1500
            t_req = c.today_requests or 0
            d_tok_lim = c.daily_tokens_limit or 1000000
            t_tok = c.today_tokens or 0

            conns_data.append({
                "id": c.id,
                "name": c.name,
                "provider_type": c.provider_type,
                "provider_group": c.provider_group,
                "default_model": c.default_model,
                "tier_key": extra.get("tier_key", "free"),
                "tier_title": tier_title,
                "rpm_limit": c.rpm_limit or 15,
                "daily_requests_limit": d_req_lim,
                "today_requests": t_req,
                "remaining_requests": max(0, d_req_lim - t_req),
                "requests_percent": min(100, int((t_req / max(1, d_req_lim)) * 100)),
                "daily_tokens_limit": d_tok_lim,
                "today_tokens": t_tok,
                "remaining_tokens": max(0, d_tok_lim - t_tok),
                "tokens_percent": min(100, int((t_tok / max(1, d_tok_lim)) * 100)),
                "status": c.status
            })

        session.commit()

        return {
            "total_today_requests": total_today_req,
            "total_daily_requests_limit": total_daily_req,
            "total_requests_percent": min(100, int((total_today_req / max(1, total_daily_req)) * 100)),
            "total_today_tokens": total_today_tok,
            "total_daily_tokens_limit": total_daily_tok,
            "total_tokens_percent": min(100, int((total_today_tok / max(1, total_daily_tok)) * 100)),
            "connections": conns_data
        }


ai_agent_service = AiAgentService()
