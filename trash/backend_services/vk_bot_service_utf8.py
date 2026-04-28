import httpx
import random
import logging
from typing import Optional, Dict, List, Any, Union
from sqlmodel import Session, select
from app.core.database import engine
from app.models.vk_settings import VkSettings
from app.models.vk_bot import VkBotAccount, VkBotMessageLog, MessageStatus

logger = logging.getLogger(__name__)

class VkBotService:
    """Сервис для работы с VK Bot API (уведомления сотрудников)"""

    def __init__(self):
        self.api_url = "https://api.vk.com/method/"
        self.api_version = "5.131"

    def _get_settings(self) -> Optional[VkSettings]:
        """Получение настроек VK из БД"""
        with Session(engine) as session:
            statement = select(VkSettings)
            return session.exec(statement).first()

    async def _request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Универсальный метод для запросов к VK API"""
        settings = self._get_settings()
        if not settings or not settings.vk_bot_token:
            logger.error("VK Bot Token не настроен в БД")
            return {"error": {"error_code": 0, "error_msg": "Token not configured"}}

        params["access_token"] = settings.vk_bot_token
        params["v"] = self.api_version

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.api_url}{method}", data=params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Ошибка при запросе к VK API ({method}): {e}")
                return {"error": {"error_code": -1, "error_msg": str(e)}}

    async def resolve_screen_name(self, screen_name: str) -> Optional[int]:
        """
        Превращает ссылку или screen_name в цифровой ID пользователя.
        Пример: 'https://vk.com/id1' -> 1, 'durov' -> 1
        """
        name = screen_name.split("/")[-1].replace("id", "")
        
        # Если это уже число, возвращаем его
        if name.isdigit():
            return int(name)

        params = {"user_ids": name}
        result = await self._request("users.get", params)
        
        if "response" in result and len(result["response"]) > 0:
            return result["response"][0]["id"]
        
        return None

    async def send_message(
        self, 
        user_id: int, 
        message: str, 
        account_id: Optional[int] = None,
        event_type: Optional[str] = None,
        keyboard: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Отправка сообщения пользователю.
        Если передан account_id, создается запись в логах.
        """
        params = {
            "user_id": user_id,
            "message": message,
            "random_id": random.randint(1, 2147483647)
        }
        
        if keyboard:
            params["keyboard"] = keyboard
        
        result = await self._request("messages.send", params)
        
        success = "response" in result
        vk_message_id = result.get("response") if success else None
        error_msg = result.get("error", {}).get("error_msg") if not success else None
        error_code = result.get("error", {}).get("error_code") if not success else None

        # Логирование в БД если нужно
        if account_id:
            with Session(engine) as session:
                from datetime import datetime
                log_entry = VkBotMessageLog(
                    account_id=account_id,
                    text=message,
                    event_type=event_type,
                    vk_message_id=vk_message_id,
                    status=MessageStatus.SENT if success else MessageStatus.FAILED,
                    error_text=error_msg,
                    sent_at=datetime.utcnow() if success else None
                )
                session.add(log_entry)
                
                # Если ошибка 901 (User denied), помечаем аккаунт как неверифицированный
                if error_code == 901:
                    account = session.get(VkBotAccount, account_id)
                    if account:
                        account.is_verified = False
                        session.add(account)
                
                session.commit()

        return {
            "success": success,
            "vk_message_id": vk_message_id,
            "error": error_msg,
            "error_code": error_code
        }

    async def get_message_history(self, user_id: int, count: int = 20) -> List[Dict[str, Any]]:
        """Получение истории сообщений (для отладки)"""
        params = {
            "user_id": user_id,
            "count": count
        }
        result = await self._request("messages.getHistory", params)
        return result.get("response", {}).get("items", [])

vk_bot_service = VkBotService()
