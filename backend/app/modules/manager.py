import os
import importlib
import inspect
import logging
from typing import Dict, List, Optional, Type
from fastapi import FastAPI
from sqlmodel import Session, select
from app.core.database import engine
from app.models.system_module import SystemModule
from app.modules.base import BaseModule

logger = logging.getLogger("modules.manager")

class ModuleManager:
    """
    Центральный менеджер динамических модулей админ-панели.
    Отвечает за:
    1. Автообнаружение модулей в каталоге app/modules/
    2. Синхронизацию метаданных модулей с таблицей system_modules в БД
    3. Динамическую регистрацию роутеров включенных модулей в FastAPI
    4. Управление жизненным циклом (on_load, on_unload, toggle)
    """

    def __init__(self):
        self._modules: Dict[str, BaseModule] = {}
        self._app: Optional[FastAPI] = None
        self._base_dir = os.path.dirname(os.path.abspath(__file__))

    def register(self, module_instance: BaseModule) -> None:
        """Регистрирует экземпляр модуля в памяти менеджера."""
        self._modules[module_instance.slug] = module_instance
        logger.info(f"Модуль '{module_instance.slug}' ({module_instance.name}) зарегистрирован в памяти.")

    def get_module(self, slug: str) -> Optional[BaseModule]:
        return self._modules.get(slug)

    def get_all_modules(self) -> List[BaseModule]:
        return list(self._modules.values())

    def discover_modules(self) -> None:
        """
        Сканирует директорию app/modules на наличие поддиректорий с классами-наследниками BaseModule.
        """
        print(f"[ModuleManager] Scanning directory: {self._base_dir}")
        for item in os.listdir(self._base_dir):
            item_path = os.path.join(self._base_dir, item)
            if not os.path.isdir(item_path) or item.startswith("_"):
                continue

            init_file = os.path.join(item_path, "__init__.py")
            if not os.path.exists(init_file):
                continue

            module_import_path = f"app.modules.{item}"
            try:
                mod = importlib.import_module(module_import_path)
                # Поиск экземпляров или подклассов BaseModule
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if isinstance(attr, BaseModule):
                        if attr.slug not in self._modules:
                            self.register(attr)
                    elif (
                        inspect.isclass(attr)
                        and issubclass(attr, BaseModule)
                        and attr is not BaseModule
                    ):
                        try:
                            instance = attr()
                            if instance.slug not in self._modules:
                                self.register(instance)
                        except Exception as inst_err:
                            print(f"[ModuleManager] Could not instantiate class {attr}: {inst_err}")
            except Exception as e:
                print(f"[ModuleManager] Error loading {module_import_path}: {e}")
                logger.error(f"Ошибка при загрузке модуля из {module_import_path}: {e}", exc_info=True)
        print(f"[ModuleManager] Active registered modules: {list(self._modules.keys())}")

    def sync_with_db(self) -> None:
        """
        Сверяет зарегистрированные в памяти модули с таблицей system_modules в БД.
        Создает записи для новых модулей и сохраняет их статус is_enabled.
        """
        if not engine:
            logger.warning("БД engine не инициализирован, пропуск синхронизации модулей с БД.")
            return

        try:
            with Session(engine) as session:
                existing_records = session.exec(select(SystemModule)).all()
                db_map = {rec.slug: rec for rec in existing_records}

                for slug, mod in self._modules.items():
                    info = mod.get_info()
                    if slug in db_map:
                        rec = db_map[slug]
                        # Обновляем версию и имя если изменились
                        rec.name = info.get("name", rec.name)
                        rec.description = info.get("description", rec.description)
                        rec.version = info.get("version", rec.version)
                        rec.author = info.get("author", rec.author)
                        rec.category = info.get("category", rec.category)
                        rec.icon = info.get("icon", rec.icon)
                        rec.route_path = info.get("route_path", rec.route_path)
                        session.add(rec)
                        mod.is_enabled = rec.is_enabled
                    else:
                        # Добавляем новый модуль в БД
                        new_rec = SystemModule(
                            slug=slug,
                            name=info.get("name", slug),
                            description=info.get("description"),
                            version=info.get("version", "1.0.0"),
                            author=info.get("author", "Team VezuRoll"),
                            is_enabled=mod.is_enabled,
                            is_system=info.get("is_system", False),
                            icon=info.get("icon", "bx-cube"),
                            route_path=info.get("route_path"),
                            category=info.get("category", "general"),
                        )
                        session.add(new_rec)
                        db_map[slug] = new_rec
                session.commit()
                logger.info(f"Синхронизация модулей с БД успешно завершена. Всего модулей: {len(self._modules)}")
        except Exception as e:
            logger.error(f"Ошибка при синхронизации модулей с БД: {e}", exc_info=True)

    def mount_routes(self, app: FastAPI) -> None:
        """
        Подключает роутеры всех включенных модулей к FastAPI под префиксом /api/v1/modules/{slug}
        """
        self._app = app
        for slug, mod in self._modules.items():
            if mod.is_enabled:
                router = mod.get_router()
                if router:
                    prefix = f"/api/v1/modules/{slug.replace('_', '-')}"
                    app.include_router(router, prefix=prefix, tags=[f"Модуль: {mod.name}"])
                    logger.info(f"Роутер модуля '{slug}' подключен по префиксу '{prefix}'.")
                try:
                    mod.on_load(app)
                except Exception as e:
                    logger.error(f"Ошибка при вызове on_load для модуля '{slug}': {e}", exc_info=True)

    def toggle_module(self, slug: str, enable: bool) -> bool:
        """
        Включает или выключает модуль в БД и в памяти.
        """
        mod = self.get_module(slug)
        if not mod:
            logger.warning(f"Попытка переключить несуществующий модуль '{slug}'")
            return False

        if not engine:
            return False

        try:
            with Session(engine) as session:
                rec = session.exec(select(SystemModule).where(SystemModule.slug == slug)).first()
                if not rec:
                    return False
                rec.is_enabled = enable
                session.add(rec)
                session.commit()

            mod.is_enabled = enable
            if enable and self._app:
                router = mod.get_router()
                if router:
                    prefix = f"/api/v1/modules/{slug.replace('_', '-')}"
                    self._app.include_router(router, prefix=prefix, tags=[f"Модуль: {mod.name}"])
                mod.on_load(self._app)
            elif not enable and self._app:
                mod.on_unload(self._app)

            return True
        except Exception as e:
            logger.error(f"Ошибка при переключении статуса модуля '{slug}': {e}", exc_info=True)
            return False

    def init_app(self, app: FastAPI) -> None:
        """Инициализация модульной подсистемы при старте приложения FastAPI."""
        self._app = app
        self.discover_modules()
        self.sync_with_db()
        self.mount_routes(app)


# Синглтон менеджера модулей
module_manager = ModuleManager()
