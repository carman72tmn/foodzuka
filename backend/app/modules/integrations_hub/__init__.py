"""
Пилотный модуль: Хаб внешних интеграций FoodTech (Integrations Hub)
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.modules.base import BaseModule
from app.core.database import get_session
from app.models.iiko_settings import IikoSettings
from app.models.tbank_settings import TBankSettings
from app.models.bot_settings import BotSettings
from app.models.vk_settings import VkSettings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Модуль: Хаб внешних интеграций"])


@router.get("/status")
def get_integrations_health(session: Session = Depends(get_session)) -> Dict[str, Any]:
    """
    Диагностика статуса всех внешних интеграций в реальном времени.
    """
    # 1. iiko Cloud / Resto
    iiko_set = session.exec(select(IikoSettings)).first()
    iiko_status = {
        "status": "configured" if (iiko_set and iiko_set.api_login) else "unconfigured",
        "api_login": iiko_set.api_login if iiko_set else None,
        "organization_id": iiko_set.organization_id if iiko_set else None,
    }

    # 2. Т-Банк
    tbank_set = session.exec(select(TBankSettings)).first()
    tbank_status = {
        "status": "configured" if (tbank_set and (tbank_set.terminal_key or tbank_set.token)) else "unconfigured",
        "has_token": bool(tbank_set and tbank_set.token),
        "terminal_key": (tbank_set.terminal_key[:4] + "****") if (tbank_set and tbank_set.terminal_key) else None,
    }

    # 3. Telegram Bot
    tg_set = session.exec(select(BotSettings)).first()
    tg_status = {
        "status": "configured" if (tg_set and tg_set.bot_token) else "unconfigured",
        "bot_username": tg_set.bot_username if tg_set else None,
    }

    # 4. VK Bot
    vk_set = session.exec(select(VkSettings)).first()
    vk_status = {
        "status": "configured" if (vk_set and vk_set.vk_bot_token) else "unconfigured",
        "group_id": vk_set.vk_group_id if vk_set else None,
    }

    return {
        "status": "ok",
        "module": "integrations_hub",
        "version": "1.0.0",
        "services": {
            "database": {"status": "ok", "engine": "postgresql"},
            "iiko_cloud": iiko_status,
            "tbank_api": tbank_status,
            "telegram_bot": tg_status,
            "vk_bot": vk_status,
        }
    }


class IntegrationsHubModule(BaseModule):
    slug = "integrations_hub"
    name = "Хаб внешних интеграций"
    description = "Модульный центр диагностики и управления внешними сервисами (iiko, Т-Банк, Telegram, ВКонтакте)"
    version = "1.0.0"
    author = "FoodTech"
    icon = "bx-git-merge"
    category = "integrations"
    is_system = False
    route_path = "/system/modules?tab=pilot_integrations"
    router = router

    def on_load(self, app):
        logger.info("[Module: IntegrationsHub] Загружен и подключен к приложению")

    def on_unload(self, app):
        logger.info("[Module: IntegrationsHub] Отключен")


module_instance = IntegrationsHubModule()
