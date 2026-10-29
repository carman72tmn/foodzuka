"""
Сервис для интеграции с RedSMS API и валидации номеров телефонов
"""
import time
import hashlib
import logging
import httpx
from typing import Dict, Any, Optional
from sqlmodel import Session, select
from app.models.validation_settings import ValidationSettings

logger = logging.getLogger(__name__)

class ValidationService:
    BASE_URL = "https://cp.redsms.ru/api"

    def _get_headers(self, login: str, api_key: str) -> Dict[str, str]:
        """Генерация заголовков аутентификации RedSMS"""
        ts = str(int(time.time()))
        # Хэш md5(ts + api_key)
        secret = hashlib.md5((ts + api_key).encode("utf-8")).hexdigest()
        return {
            "login": login,
            "ts": ts,
            "secret": secret,
            "Content-Type": "application/json"
        }

    async def send_verification(
        self,
        db: Session,
        phone: str,
        code: str,
        custom_route: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Отправка сервисного сообщения/вызова для верификации телефона.
        
        :param db: сессия базы данных
        :param phone: номер телефона получателя (в международном формате, например +79991234567)
        :param code: код верификации (4-6 цифр)
        :param custom_route: принудительно заданный канал отправки (используется для тестов)
        """
        # 1. Загружаем настройки из БД
        settings = db.exec(select(ValidationSettings)).first()
        if not settings:
            raise ValueError("Настройки валидации не найдены в базе данных")

        if not settings.is_active and not custom_route:
            return {
                "success": False,
                "message": "Сервис валидации отключен в настройках системы"
            }

        if not settings.api_login or not settings.api_key:
            raise ValueError("Не заполнены параметры авторизации RedSMS (логин или API ключ)")

        # 2. Определяем канал отправки
        route = custom_route or settings.active_route
        if route == "cascade":
            route = settings.cascade_routes or "fcall,voice,sms"

        # Форматируем номер телефона (должен начинаться с + или быть просто цифрами)
        formatted_phone = phone.strip()
        if not formatted_phone.startswith("+"):
            # Если начинается с 7 или 8 и длина 11
            if len(formatted_phone) == 11 and formatted_phone.startswith("8"):
                formatted_phone = "+7" + formatted_phone[1:]
            elif len(formatted_phone) == 11 and formatted_phone.startswith("7"):
                formatted_phone = "+" + formatted_phone
            else:
                formatted_phone = "+" + formatted_phone

        # 3. Формируем тело запроса в зависимости от канала
        import os
        public_url = os.getenv("APP_PUBLIC_URL", "https://vezuroll.ru").rstrip('/')
        dlr_url = f"{public_url}/api/v1/validation/redsms-webhook"

        payload: Dict[str, Any] = {
            "to": formatted_phone,
            "dlrUrl": dlr_url
        }

        # Если это каскадная отправка (содержит запятую)
        if "," in route:
            payload.update({
                "route": route,
                # Если первым шагом идет wcall и включено без озвучивания, то основной text (для первого шага) делаем пустым
                "text": "" if (route.startswith("wcall") and settings.wait_call_no_voice) else code,
                "fcall_text": code,
                "voice_text": code,
                "sms_text": f"Код подтверждения: {code}",
                "sms_from": settings.sender_name or "REDSMS"
            })
        else:
            # Одиночные каналы
            payload["route"] = route
            if route == "sms":
                payload["text"] = f"Код подтверждения: {code}"
                payload["from"] = settings.sender_name or "REDSMS"
            elif route in ("fcall", "voice"):
                payload["text"] = code
            elif route == "wcall":
                # Wait Call: проговаривание кода или просто дозвон
                # Если включено "без озвучивания кода", не передаем текст вообще (будет сброшен сразу)
                if not settings.wait_call_no_voice:
                    payload["text"] = code

        # 4. Отправляем запрос к API RedSMS
        headers = self._get_headers(settings.api_login, settings.api_key)
        url = f"{self.BASE_URL}/message"

        logger.info(f"Отправка запроса валидации RedSMS на {formatted_phone} через {route}. Payload: {payload}")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code != 200:
                    logger.error(f"Ошибка API RedSMS: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": response.text,
                        "message": f"Не удалось отправить запрос через RedSMS. Код ответа: {response.status_code}"
                    }

                response_data = response.json()
                logger.info(f"Ответ API RedSMS: {response_data}")

                if not response_data.get("success", False):
                    errors = response_data.get("errors", [])
                    error_msg = errors[0] if errors else "Неизвестная ошибка API"
                    return {
                        "success": False,
                        "error": error_msg,
                        "message": f"API RedSMS вернул ошибку: {error_msg}",
                        "raw": response_data
                    }

                # Извлекаем важные данные из ответа
                items = response_data.get("items", [])
                result_info = {
                    "success": True,
                    "message": "Запрос на отправку успешно зарегистрирован",
                    "route": route,
                    "raw": response_data
                }

                if items:
                    item = items[0]
                    result_info["uuid"] = item.get("uuid")
                    result_info["status"] = item.get("status")
                    
                    # Для Wait Call возвращается номер телефона, на который должен позвонить клиент
                    if route == "wcall" and "replacedFrom" in item:
                        result_info["phone_to_call"] = item.get("replacedFrom")
                        result_info["message"] = f"Для подтверждения номера позвоните на {item.get('replacedFrom')}"
                    
                    # Если в каскаде первым идет wcall, то тоже может вернуться replacedFrom
                    elif "replacedFrom" in item:
                        result_info["phone_to_call"] = item.get("replacedFrom")

                return result_info

        except httpx.RequestError as exc:
            logger.error(f"Сбой сети при запросе к RedSMS: {exc}")
            return {
                "success": False,
                "error": str(exc),
                "message": "Ошибка подключения к сервису RedSMS"
            }
        except Exception as e:
            logger.error(f"Непредвиденная ошибка в ValidationService: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Внутренняя ошибка сервиса: {str(e)}"
            }

validation_service = ValidationService()
