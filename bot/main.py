import asyncio
import logging
import httpx
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.token import validate_token
from aiogram.exceptions import TelegramUnauthorizedError
from config import settings
from handlers import router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def get_bot_settings():
    """Получение настроек бота из бэкенда"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{settings.API_URL}/bot/settings", timeout=10.0)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"❌ Ошибка при получении настроек бота: {e}")
    return None


async def main():
    """Запуск бота"""
    bot = None
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    logger.info("📡 Ожидание корректных настроек бота из БД...")
    
    while True:
        bot_settings = await get_bot_settings()
        token = None
        
        if bot_settings and bot_settings.get("token"):
            token = bot_settings["token"]
            try:
                validate_token(token)
                logger.info("✅ Токен валиден, инициализация бота...")
                break
            except Exception:
                logger.warning("⚠️ Токен в БД невалиден. Проверьте настройки в админ-панели.")
        else:
            logger.warning("⏳ Токен не найден в БД или бэкенд недоступен. Ожидание...")
        
        await asyncio.sleep(10)  # Проверяем каждые 10 секунд

    # Инициализация бота
    bot = Bot(token=token)

    # Запуск polling
    logger.info("🤖 Бот запущен!")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except TelegramUnauthorizedError:
        logger.error("❌ Ошибка авторизации: Токен недействителен!")
    finally:
        if bot:
            await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
