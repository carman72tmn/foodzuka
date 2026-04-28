"""
Главное приложение FastAPI для FoodTech
Точка входа для backend API
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.core.config import settings
import asyncio
import logging
from app.core.logging_utils import DatabaseLogHandler, global_exception_handler
from app.services.iiko_sync_service import iiko_sync_service
from app.core.database import Session, engine, get_session
from app.api import (
    categories, products, orders, companies, branches, iiko,
    loyalty, promo_codes, actions, nps, customers, mailings,
    stories, funnels, reports, employees, webhooks, vk, vk_bot_admin, bot_settings,
    logs, yandex, auth, users, system
)

from app.services.revenue_sync import revenue_sync_service
from app.core.scheduler import start_scheduler

logger = logging.getLogger(__name__)

# Создание приложения FastAPI
app = FastAPI(
    title="FoodTech API",
    description="API для системы доставки еды с интеграцией iiko Cloud",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# Настройка логирования в БД
db_handler = DatabaseLogHandler()
db_handler.setLevel(logging.WARNING) # Логируем WARNING и выше
logging.getLogger().addHandler(db_handler)

# Глобальный обработчик исключений (500 и прочие)
@app.exception_handler(Exception)
async def unified_exception_handler(request, exc):
    return await global_exception_handler(request, exc)

# Обработчик HTTP исключений (4xx) для логирования ошибок API
from fastapi.exceptions import HTTPException
from fastapi.exception_handlers import http_exception_handler
@app.exception_handler(HTTPException)
async def http_exception_db_handler(request, exc):
    # Логируем ошибки API (кроме 404, если их слишком много)
    if exc.status_code >= 400:
        logger.warning(f"API Error {exc.status_code}: {exc.detail} at {request.url.path}")
    return await http_exception_handler(request, exc)

@app.on_event("startup")
async def startup_event():
    # Запуск планировщика задач (управляет всеми задачами из БД)
    start_scheduler()
    
    # Инициализация ролей и супер-админа
    try:
        with Session(engine) as session:
            await iiko_sync_service.ensure_super_admin(session)
            logger.info("Системные роли и супер-админ проверены.")
    except Exception as e:
        logger.error(f"Ошибка при инициализации супер-админа: {e}")

# Настройка CORS для работы с фронтендом и Telegram Bot
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173", 
        "https://72roll.ru",
        "http://72roll.ru",
        "*"
    ],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Поддержка заголовков прокси (X-Forwarded-Proto и т.д.)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Подключение роутеров
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(branches.router, prefix="/api/v1")
app.include_router(iiko.router, prefix="/api/v1")
app.include_router(loyalty.router, prefix="/api/v1")
app.include_router(promo_codes.router, prefix="/api/v1")
app.include_router(actions.router, prefix="/api/v1")
app.include_router(nps.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(mailings.router, prefix="/api/v1")
app.include_router(stories.router, prefix="/api/v1")
app.include_router(funnels.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1/employees", tags=["Employees"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])
app.include_router(vk.router, prefix="/api/v1/vk", tags=["VK"])
app.include_router(vk_bot_admin.router, prefix="/api/v1/vk-bot", tags=["VK Bot Admin"])
app.include_router(bot_settings.router, prefix="/api/v1")
app.include_router(logs.router, prefix="/api/v1")
app.include_router(yandex.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")


# Алиас для настроек iiko (совместимость с фронтендом)
@app.get("/api/v1/settings/iiko")
async def get_iiko_settings_legacy(session: Session = Depends(get_session)):
    """Алиас для /api/v1/iiko/settings"""
    from app.api.iiko import get_settings
    return await get_settings(session)



@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "сообщение": "FoodTech API",
        "версия": "1.0.0",
        "документация": "/docs",
        "статус": "работает"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {
        "статус": "здоров",
        "база_данных": "подключено"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
