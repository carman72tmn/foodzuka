"""
Пилотный модуль: Хаб внешних интеграций
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session
from sqlalchemy import text
from app.core.database import get_session, engine
from app.core.config import settings
from app.models.iiko_settings import IikoSettings
from app.models.max_settings import MaxSettings
from app.models.vk_settings import VkSettings
import time

router = APIRouter(prefix="/modules/integrations", tags=["Integrations Hub Module"])


@router.get("/status")
async def get_integrations_status(session: Session = Depends(get_session)):
    """Проверка и статус всех внешних интеграций"""
    results = {}

    # 1. База данных PostgreSQL
    try:
        t0 = time.time()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_latency = round((time.time() - t0) * 1000, 1)
        results["database"] = {
            "name": "PostgreSQL (foodtech_db)",
            "status": "online",
            "latency_ms": db_latency,
            "details": "Подключение активно"
        }
    except Exception as e:
        results["database"] = {
            "name": "PostgreSQL (foodtech_db)",
            "status": "error",
            "latency_ms": None,
            "details": str(e)
        }

    # 2. Redis брокер
    try:
        t0 = time.time()
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=2)
        r.ping()
        redis_latency = round((time.time() - t0) * 1000, 1)
        results["redis"] = {
            "name": "Redis (Broker & Cache)",
            "status": "online",
            "latency_ms": redis_latency,
            "details": "Брокер задач доступен"
        }
    except Exception as e:
        results["redis"] = {
            "name": "Redis (Broker & Cache)",
            "status": "error",
            "latency_ms": None,
            "details": str(e)
        }

    # 3. iiko Cloud API
    try:
        iiko_cfg = session.query(IikoSettings).first()
        if iiko_cfg and iiko_cfg.api_login:
            results["iiko_cloud"] = {
                "name": "iiko Cloud Transport API",
                "status": "online" if iiko_cfg.organization_id else "configured",
                "latency_ms": None,
                "details": f"Организация: {iiko_cfg.organization_id or 'Не указана'}"
            }
        else:
            results["iiko_cloud"] = {
                "name": "iiko Cloud Transport API",
                "status": "unconfigured",
                "latency_ms": None,
                "details": "API логин не настроен"
            }
    except Exception as e:
        results["iiko_cloud"] = {"name": "iiko Cloud Transport API", "status": "error", "details": str(e)}

    # 4. MAX Messenger
    try:
        max_cfg = session.query(MaxSettings).first()
        results["max_messenger"] = {
            "name": "MAX Messenger Gateway",
            "status": "online" if max_cfg and max_cfg.is_active else "disabled",
            "latency_ms": None,
            "details": "Канал активен" if max_cfg and max_cfg.is_active else "Шлюз отключен в настройках"
        }
    except Exception:
        results["max_messenger"] = {"name": "MAX Messenger Gateway", "status": "disabled", "latency_ms": None, "details": "Не настроен"}

    # 5. VK Community Bot
    try:
        vk_cfg = session.query(VkSettings).first()
        results["vk_bot"] = {
            "name": "VKontakte Bot & Community",
            "status": "online" if vk_cfg and vk_cfg.access_token else "unconfigured",
            "latency_ms": None,
            "details": f"Группа ID: {vk_cfg.group_id if vk_cfg else 'Не указана'}"
        }
    except Exception:
        results["vk_bot"] = {"name": "VKontakte Bot & Community", "status": "disabled", "latency_ms": None, "details": "Не настроен"}

    return {
        "status": "ok",
        "timestamp": time.time(),
        "services": results
    }
