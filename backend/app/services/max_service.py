import logging
import httpx
from typing import Optional
from app.models.max_settings import MaxSettings, MaxBot
from sqlmodel import Session, select

logger = logging.getLogger(__name__)

async def send_max_message(phone: str, text: str, settings: MaxSettings) -> bool:
    """
    Отправка сообщения через сервис MAX.
    Если есть активный бот типа 'MAX', используем его токен.
    Иначе используем общий API ключ.
    """
    if not settings.is_active or not settings.api_key:
        logger.warning("MAX integration is not active or API key is missing")
        return False

    # Очищаем номер телефона
    clean_phone = "".join(filter(str.isdigit, phone))
    if not clean_phone.startswith("7") and len(clean_phone) == 10:
        clean_phone = "7" + clean_phone
    
    url = f"{settings.base_url.rstrip('/')}/messages/send"
    
    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "phone": clean_phone,
        "text": text,
        "sender": settings.sender_name
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") == "success" or result.get("ok"):
                logger.info(f"Message sent to {clean_phone} via MAX")
                return True
            else:
                logger.error(f"MAX API error: {result}")
                return False
    except Exception as e:
        logger.error(f"Failed to send message via MAX: {e}")
        return False
