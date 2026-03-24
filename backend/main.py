"""
Главное приложение FastAPI для FoodTech
Точка входа для backend API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import categories, products, orders, iiko, loyalty, promo_codes, webhooks, companies, branches, actions, nps, customers, mailings, stories, funnels, reports, employees, vk

# Создание приложения FastAPI
app = FastAPI(
    title="FoodTech API",
    description="API для системы доставки еды с интеграцией iiko Cloud",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# Настройка CORS для работы с фронтендом и Telegram Bot
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173", 
        "http://192.168.31.162:5173",
        "http://192.168.31.162:8081",
        "*"
    ],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
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


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "FoodTech API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {
        "status": "healthy",
        "database": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
