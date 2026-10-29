import httpx

import random

import logging

from typing import Optional, Dict, List, Any, Union

from sqlmodel import Session, select

from app.core.database import engine

from app.models.vk_settings import VkSettings
from app.models.vk_bot_connection import VkBotConnection
from app.models.vk_bot import VkBotAccount, VkBotMessageLog, MessageStatus



logger = logging.getLogger(__name__)



class VkBotService:

    """Сервис для работы с VK Bot API (уведомления сотрудников)"""



    def __init__(self):

        self.api_url = "https://api.vk.com/method/"

        self.api_version = "5.199"



    def _get_bot_token(self) -> Optional[str]:
        """Получение токена основного активного VK-бота из БД с фолбэком на настройки"""
        with Session(engine) as session:
            main_bot = session.exec(select(VkBotConnection).where(VkBotConnection.is_main == True, VkBotConnection.is_active == True)).first()
            if main_bot and main_bot.vk_bot_token:
                return main_bot.vk_bot_token
            settings = session.exec(select(VkSettings)).first()
            return settings.vk_bot_token if settings else None

    async def _request(self, method: str, params: Dict[str, Any], bot_token_override: Optional[str] = None) -> Dict[str, Any]:
        """Универсальный метод для запросов к VK API"""
        bot_token = bot_token_override or self._get_bot_token()
        if not bot_token:
            logger.error("VK Bot Token не настроен в БД")
            return {"error": {"error_code": 0, "error_msg": "Token not configured"}}

        params["access_token"] = bot_token
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
        keyboard: Optional[Union[str, Dict[str, Any], List[Any]]] = None,
        image_path: Optional[str] = None,
        bot_token_override: Optional[str] = None
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

        target_token = bot_token_override or self._get_bot_token()
        attachment_str = None
        if image_path and target_token:
            try:
                from app.services.vk_service import upload_vk_photo_detailed
                attachment, effective_token = await upload_vk_photo_detailed(target_token, image_path, user_id)
                if attachment:
                    params["attachment"] = attachment
                    attachment_str = attachment
                    if effective_token and not bot_token_override:
                        target_token = effective_token
                else:
                    logger.warning(f"VK photo could not be uploaded for send_message (empty attachment returned)")
            except Exception as e:
                logger.error(f"Failed to upload VK photo for send_message: {e}")
        if keyboard:
            import json
            if isinstance(keyboard, (dict, list)):
                params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
            elif isinstance(keyboard, str):
                if keyboard.strip():
                    params["keyboard"] = keyboard

        result = await self._request("messages.send", params, target_token)

        # RETRY FALLBACK FOR KEYBOARD / BOT CAPABILITIES ERROR:
        # ???? ? ?????? ?? ?? ???????? "??????????? ?????" (?????? 912) ??? ???????? ?????? ?????????? (?????? 911),
        # ????????????? ????????? ???????? ????????? ??? ??????????, ????? ??????/????????? ?????????????? ??????? ???????????!
        if "error" in result and result["error"].get("error_code") in (911, 912) and "keyboard" in params:
            err_code = result["error"].get("error_code")
            logger.warning(
                f"VK API error {err_code} ({result['error'].get('error_msg')}) with keyboard for user {user_id}. "
                f"Retrying send without keyboard..."
            )
            params_no_kb = {k: v for k, v in params.items() if k != "keyboard"}
            params_no_kb["random_id"] = random.randint(1, 2147483647)
            result = await self._request("messages.send", params_no_kb, target_token)

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
            "attachment": attachment_str,
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

    async def is_messages_allowed(self, group_id: int, user_id: int, bot_token_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Проверка разрешения сообщений от группы для конкретного пользователя через VK API.
        Метод: messages.isMessagesFromGroupAllowed
        """
        params = {
            "group_id": group_id,
            "user_id": user_id
        }
        res = await self._request("messages.isMessagesFromGroupAllowed", params, bot_token_override=bot_token_override)
        if "response" in res and isinstance(res["response"], dict):
            is_allowed = bool(res["response"].get("is_allowed") == 1)
            return {"success": True, "is_allowed": is_allowed, "error": None}
        err = res.get("error", {})
        err_msg = err.get("error_msg", "Неизвестная ошибка VK API")
        return {"success": False, "is_allowed": False, "error": err_msg}

    async def check_group_connection(self, group_id: int, bot_token_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Проверка соединения с группой ВКонтакте и валидности токена через VK API.
        Метод: groups.getById
        """
        params = {
            "group_id": group_id
        }
        res = await self._request("groups.getById", params, bot_token_override=bot_token_override)
        if "response" in res and isinstance(res["response"], list) and len(res["response"]) > 0:
            grp = res["response"][0]
            return {
                "success": True, 
                "name": grp.get("name"), 
                "screen_name": grp.get("screen_name"),
                "photo": grp.get("photo_100") or grp.get("photo_50"),
                "error": None
            }
        err = res.get("error", {})
        err_msg = err.get("error_msg", "Не удалось связаться с сообществом")
        return {"success": False, "name": None, "error": err_msg}



    async def edit_message(
        self,
        peer_id: int,
        message_id: int,
        message: str,
        attachment: Optional[str] = "",
        keyboard: Optional[Union[str, Dict[str, Any]]] = None,
        bot_token_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Редактирование ранее отправленного сообщения в VK (messages.edit).
        Если attachment="" — удаляет прикрепленный QR-код из сообщения!
        Если keyboard={"buttons": []} — убирает кнопки!
        """
        import json
        params: Dict[str, Any] = {
            "peer_id": int(peer_id),
            "message_id": int(message_id),
            "message": message,
            "keep_forward_messages": 1,
            "keep_snippets": 1
        }
        params["attachment"] = attachment if attachment is not None else ""
        
        if keyboard is not None:
            if isinstance(keyboard, (dict, list)):
                params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
            elif isinstance(keyboard, str):
                params["keyboard"] = keyboard
        else:
            params["keyboard"] = json.dumps({"buttons": [], "inline": True}, ensure_ascii=False)

        target_token = bot_token_override or self._get_bot_token()
        result = await self._request("messages.edit", params, target_token)
        if "error" in result and result["error"].get("error_code") in (911, 912) and "keyboard" in params:
            logger.warning(f"VK API error {result['error'].get('error_code')} on edit_message with keyboard, retrying without keyboard...")
            params_no_kb = {k: v for k, v in params.items() if k != "keyboard"}
            result = await self._request("messages.edit", params_no_kb, target_token)
        success = result.get("response") == 1
        err_msg = result.get("error", {}).get("error_msg") if not success else None
        return {
            "success": success,
            "error": err_msg
        }


vk_bot_service = VkBotService()

