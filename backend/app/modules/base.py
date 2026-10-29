"""
Базовый класс для модулей и плагинов FoodTech (Modular Monolith)
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, FastAPI


class BaseModule:
    """
    Базовый класс динамического модуля админ-панели.
    Любой модуль, унаследованный от BaseModule, автоматически регистрируется в ModuleManager.
    """
    slug: str = "base_module"
    name: str = "Базовый модуль"
    description: str = "Описание модуля отсутствует"
    version: str = "1.0.0"
    author: str = "FoodTech Core"
    icon: str = "bx-extension"
    category: str = "general"
    is_system: bool = False
    is_enabled: bool = True
    route_path: Optional[str] = None
    
    # Роутер FastAPI, обслуживающий эндпоинты модуля
    router: Optional[APIRouter] = None

    def __init__(self):
        pass

    def get_router(self) -> Optional[APIRouter]:
        """Возвращает APIRouter модуля или None."""
        return self.router

    def on_load(self, app: FastAPI):
        """
        Хук инициализации при подключении модуля к FastAPI.
        """
        pass

    def on_unload(self, app: FastAPI):
        """
        Хук при отключении модуля.
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """
        Получение метаданных модуля для UI и реестра.
        """
        return {
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "icon": self.icon,
            "category": self.category,
            "is_system": self.is_system,
            "is_enabled": self.is_enabled,
            "route_path": self.route_path,
            "has_router": self.router is not None
        }
