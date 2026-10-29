import base64
import logging
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from pywebpush import webpush, WebPushException

logger = logging.getLogger(__name__)

def generate_vapid_keys():
    """Генерирует пару ключей VAPID (public/private) в формате base64 url-safe"""
    try:
        private_key = ec.generate_private_key(ec.SECP256R1())
        
        # Получаем приватный ключ как 32-байтовое число
        private_value = private_key.private_numbers().private_value
        private_bytes = private_value.to_bytes(32, byteorder='big')
        private_b64 = base64.urlsafe_b64encode(private_bytes).decode('utf-8').rstrip('=')
        
        # Получаем несжатую форму публичного ключа (65 байт: 0x04 + X + Y)
        public_key = private_key.public_key()
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        public_b64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')
        
        return public_b64, private_b64
    except Exception as e:
        logger.error(f"Failed to generate VAPID keys: {e}")
        raise

def send_web_push(subscription_data: dict, payload: str, private_key_b64: str) -> str:
    """
    Отправляет push-уведомление через протокол Web Push.
    Возвращает:
      - "success" при успешной отправке
      - "remove" если подписка недействительна (ошибка 410 или 404)
      - "failed" при прочих ошибках
    """
    try:
        # Формат subscription_data: {"endpoint": "...", "keys": {"p256dh": "...", "auth": "..."}}
        webpush(
            subscription_info=subscription_data,
            data=payload,
            vapid_private_key=private_key_b64,
            vapid_claims={
                "sub": "mailto:admin@vezuroll.ru"
            }
        )
        return "success"
    except WebPushException as ex:
        status_code = ex.response.status_code if ex.response is not None else 0
        body = ex.response.text if ex.response is not None else ""
        # 400 (несовпадение VAPID ключей), 401 (неавторизован), 404 и 410 означают недействительную подписку
        if status_code in (400, 401, 404, 410):
            logger.info(f"Push subscription invalid or expired (status {status_code}), marking for removal: {subscription_data.get('endpoint')}. Body: {body}")
            return "remove"
        logger.error(f"WebPushException during push send (status {status_code}): {ex}. Response body: {body}")
        return "failed"
    except Exception as e:
        logger.error(f"Unexpected error during push send: {e}")
        return "failed"
