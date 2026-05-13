import redis.asyncio as redis
from app.core.config import settings

# Инициализация клиента Redis для асинхронного использования (кеширование, зоны доставки и т.д.)
# Использует REDIS_URL из настроек или значение по умолчанию для Docker-окружения
redis_client = redis.from_url(
    settings.REDIS_URL or "redis://redis:6379/0", 
    decode_responses=True
)
