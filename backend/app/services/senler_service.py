import logging
import httpx
from typing import Optional, List, Dict, Any
from sqlmodel import Session, select
from app.models.senler import SenlerSettings, SenlerSubscriber
from app.core.database import engine

logger = logging.getLogger(__name__)

class SenlerService:
    """Сервис для интеграции с API Senler v2"""
    
    BASE_URL = "https://senler.ru/api"

    def _get_settings(self, db: Session) -> Optional[SenlerSettings]:
        """Получить активные настройки Senler"""
        statement = select(SenlerSettings).where(SenlerSettings.is_active == True)
        return db.exec(statement).first()

    async def _make_request(self, method_name: str, data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Выполнить запрос к API Senler"""
        settings = self._get_settings(db)
        if not settings or not settings.access_token or not settings.group_id:
            raise ValueError("Интеграция с Senler не настроена или неактивна")

        url = f"{self.BASE_URL}/{method_name}"
        
        # Подготовка параметров запроса
        payload = {
            "access_token": settings.access_token,
            "group_id": settings.group_id,
            "v": "2"
        }
        
        # Добавляем специфичные данные, преобразуя списки в формат Senler (например, массивы как [value1, value2])
        for k, v in data.items():
            if isinstance(v, list):
                # Senler API ожидает массивы в формате query string: key[]=val1&key[]=val2
                # Но httpx при передаче словаря в data=[] поддерживает списки как кортежи
                pass
            payload[k] = v

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                # Отправляем POST-запрос с payload (form-urlencoded)
                response = await client.post(url, data=payload)
                response.raise_for_status()
                result = response.json()
                
                if "error" in result:
                    error_msg = result["error"].get("message", "Неизвестная ошибка")
                    error_code = result["error"].get("code", 0)
                    logger.error(f"Senler API error ({error_code}): {error_msg}")
                    raise Exception(f"Senler API error ({error_code}): {error_msg}")
                    
                return result
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during Senler request to {method_name}: {e}")
            raise Exception(f"Ошибка сети при запросе к Senler: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during Senler request to {method_name}: {e}")
            raise e

    async def test_connection(self, access_token: str, group_id: int) -> bool:
        """Проверить подключение с тестовыми ключами"""
        url = f"{self.BASE_URL}/groups/get"
        payload = {
            "access_token": access_token,
            "group_id": group_id,
            "v": "2"
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, data=payload)
                response.raise_for_status()
                result = response.json()
                if "error" in result:
                    logger.warning(f"Test connection failed: {result['error']}")
                    return False
                return True
        except Exception as e:
            logger.error(f"Test connection failed with exception: {e}")
            return False

    async def get_subscribers(self, offset_id: Optional[str] = None, count: int = 100, db: Session = None) -> Dict[str, Any]:
        """Получить список подписчиков из Senler"""
        data = {"count": count}
        if offset_id:
            data["offset_id"] = offset_id
        
        # Получаем данные через наш запрос
        return await self._make_request("subscribers/get", data, db)

    async def get_groups(self, db: Session) -> List[Dict[str, Any]]:
        """Получить список групп подписчиков из Senler"""
        result = await self._make_request("groups/get", {}, db)
        return result.get("items", [])

    async def get_deliveries(self, db: Session) -> List[Dict[str, Any]]:
        """Получить список рассылок из Senler"""
        result = await self._make_request("deliveries/get", {}, db)
        return result.get("items", [])

    async def get_delivery_stats(self, delivery_ids: List[int], db: Session) -> Dict[str, Any]:
        """Получить количественную статистику по рассылкам"""
        # Senler API deliveries/statCount принимает массив delivery_id
        # В HTTP POST передаем список ID
        data = {}
        for idx, d_id in enumerate(delivery_ids):
            data[f"delivery_id[{idx}]"] = d_id
            
        return await self._make_request("deliveries/statCount", data, db)

    async def create_delivery(
        self, 
        name: str, 
        message: str, 
        subscription_id: int, 
        is_now: bool = True, 
        scheduled_time: Optional[int] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Создать рассылку (очередь доставки) в Senler"""
        data = {
            "name": name,
            "message": message,
            "subscription_id": subscription_id,
            "is_now": 1 if is_now else 0
        }
        if not is_now and scheduled_time:
            data["date"] = scheduled_time
            
        return await self._make_request("deliveries/add", data, db)

    async def send_message(self, user_id: int, message: str, db: Session) -> Dict[str, Any]:
        """Отправить личное сообщение пользователю через Senler"""
        import random
        data = {
            "user_id": user_id,
            "message": message,
            "random_id": random.randint(1, 2147483647)
        }
        return await self._make_request("messages/send", data, db)

senler_service = SenlerService()
