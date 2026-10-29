import redis
import redis.asyncio as aioredis
from app.core.config import settings

REDIS_URL = settings.REDIS_URL or "redis://redis:6379/0"

# Пул асинхронных соединений для предотвращения OSError: [Errno 99]
async_pool = aioredis.ConnectionPool.from_url(
    REDIS_URL,
    max_connections=50,
    decode_responses=True
)

redis_client = aioredis.Redis(connection_pool=async_pool)

# Синхронный клиент для фоновых воркеров Celery и синхронных потоков
sync_pool = redis.ConnectionPool.from_url(
    REDIS_URL,
    max_connections=50,
    decode_responses=True
)

sync_redis_client = redis.Redis(connection_pool=sync_pool)

