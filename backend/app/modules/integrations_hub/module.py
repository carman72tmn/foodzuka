"""
Модуль 'Хаб внешних интеграций' (Integrations Hub)
"""
from app.modules.base import BaseModule
from .router import router


class IntegrationsHubModule(BaseModule):
    slug: str = "integrations_hub"
    name: str = "Хаб внешних интеграций"
    description: str = "Диагностика и мониторинг подключений iiko Cloud, iiko Resto, Redis, VK и MAX Messenger в режиме реального времени."
    version: str = "1.0.0"
    author: str = "FoodTech Core Team"
    icon: str = "ri-cloud-line"
    category: str = "integrations"
    route_path: str = "/settings/integrations-hub"
    is_system: bool = False

    # Роутер FastAPI
    router = router
    prefix: str = "/api/v1"
    tags: list = ["Integrations Hub Module"]

    def on_startup(self):
        """Логика при включении плагина"""
        pass

    def on_shutdown(self):
        """Логика при отключении плагина"""
        pass


# Экспортируем экземпляр плагина
module = IntegrationsHubModule()
