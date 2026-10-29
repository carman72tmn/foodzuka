"""
Загрузчик и менеджер динамических модулей FoodTech
"""
import os
import importlib
import logging
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.database import engine, get_session
from app.models.system_module import SystemModule
from .base import BaseModule

logger = logging.getLogger(__name__)


class ModuleLoader:
    def __init__(self):
        self.modules: Dict[str, BaseModule] = {}
        self.app: Optional[FastAPI] = None

    def ensure_table(self):
        """Гарантирует существование таблицы system_modules в БД"""
        try:
            SystemModule.metadata.create_all(engine, tables=[SystemModule.__table__])
        except Exception as e:
            logger.warning(f"[ModuleLoader] Не удалось проверить/создать таблицу system_modules: {e}")

    def discover_and_load(self, app: FastAPI):
        """
        Сканирует директорию modules/, инициализирует модули
        и подключает активные роутеры к приложению.
        """
        self.app = app
        self.ensure_table()

        current_dir = os.path.dirname(__file__)
        logger.info(f"[ModuleLoader] Сканирование модулей в: {current_dir}")

        # Получаем список поддиректорий
        items = os.listdir(current_dir)
        for item in items:
            item_path = os.path.join(current_dir, item)
            # Игнорируем служебные файлы и папки
            if item.startswith(("_", ".")) or item in ("base.py", "loader.py"):
                continue

            # Поддерживаем как пакеты-директории с __init__.py / module.py, так и отдельные .py файлы
            module_name = None
            if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "__init__.py")):
                module_name = f"app.modules.{item}"
            elif item.endswith(".py"):
                module_name = f"app.modules.{item[:-3]}"

            if module_name:
                self._load_module(module_name)

        # Синхронизируем состояние с БД и подключаем роутеры
        self._sync_and_mount()

    def _load_module(self, module_import_path: str):
        """Загрузка одного модуля по имени пакета"""
        try:
            mod = importlib.import_module(module_import_path)
            # Ищем экземпляр или класс-наследник BaseModule
            module_instance = None

            # 1. Проверяем, экспортирован ли готовый экземпляр 'module'
            if hasattr(mod, "module") and isinstance(mod.module, BaseModule):
                module_instance = mod.module
            else:
                # 2. Ищем класс, унаследованный от BaseModule
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BaseModule) and attr is not BaseModule:
                        module_instance = attr()
                        break

            if module_instance:
                self.modules[module_instance.slug] = module_instance
                logger.info(f"[ModuleLoader] Обнаружен модуль: {module_instance.name} ({module_instance.slug}) v{module_instance.version}")
            else:
                logger.debug(f"[ModuleLoader] В {module_import_path} не найдено наследников BaseModule")
        except Exception as e:
            logger.error(f"[ModuleLoader] Ошибка при загрузке {module_import_path}: {e}", exc_info=True)

    def _sync_and_mount(self):
        """Сверка списка модулей с БД и подключение роутеров активных модулей"""
        try:
            with Session(engine) as session:
                db_modules = {m.slug: m for m in session.exec(select(SystemModule)).all()}

                for slug, mod in self.modules.items():
                    db_record = db_modules.get(slug)
                    if not db_record:
                        # Новый модуль - регистрируем в БД
                        db_record = SystemModule(
                            slug=slug,
                            name=mod.name,
                            description=mod.description,
                            version=mod.version,
                            author=mod.author,
                            is_enabled=True,
                            is_system=mod.is_system,
                            icon=mod.icon,
                            route_path=mod.route_path,
                            category=mod.category
                        )
                        session.add(db_record)
                        session.commit()
                        session.refresh(db_record)
                        logger.info(f"[ModuleLoader] Зарегистрирован новый модуль в БД: {slug}")

                    # Если модуль активен - подключаем его к FastAPI
                    if db_record.is_enabled and not mod.is_loaded:
                        try:
                            mod.on_startup()
                            if mod.router and self.app:
                                self.app.include_router(mod.router, prefix=mod.prefix, tags=mod.tags)
                            mod.is_loaded = True
                            mod.error = None
                            logger.info(f"[ModuleLoader] Модуль '{mod.name}' успешно активирован и подключен.")
                        except Exception as err:
                            mod.is_loaded = False
                            mod.error = str(err)
                            logger.error(f"[ModuleLoader] Сбой при активации модуля '{slug}': {err}")
                    elif not db_record.is_enabled:
                        mod.is_loaded = False
                        logger.info(f"[ModuleLoader] Модуль '{slug}' отключен в настройках БД.")
        except Exception as e:
            logger.error(f"[ModuleLoader] Ошибка при синхронизации модулей с БД: {e}")

    def get_modules_list(self, session: Session) -> List[Dict]:
        """Возвращает актуальный список модулей для фронтенда"""
        self.ensure_table()
        db_records = {m.slug: m for m in session.exec(select(SystemModule)).all()}
        result = []

        # Объединяем физические модули и записи из БД
        all_slugs = set(self.modules.keys()) | set(db_records.keys())

        for slug in sorted(all_slugs):
            mod = self.modules.get(slug)
            rec = db_records.get(slug)

            result.append({
                "slug": slug,
                "name": rec.name if rec else (mod.name if mod else slug),
                "description": rec.description if rec else (mod.description if mod else ""),
                "version": rec.version if rec else (mod.version if mod else "1.0.0"),
                "author": rec.author if rec else (mod.author if mod else "FoodTech"),
                "is_enabled": rec.is_enabled if rec else False,
                "is_system": rec.is_system if rec else (mod.is_system if mod else False),
                "icon": rec.icon if rec else (mod.icon if mod else "ri-puzzle-line"),
                "route_path": rec.route_path if rec else (mod.route_path if mod else None),
                "category": rec.category if rec else (mod.category if mod else "general"),
                "is_loaded": mod.is_loaded if mod else False,
                "error": mod.error if mod else None,
                "created_at": rec.created_at.isoformat() if rec and rec.created_at else None,
                "updated_at": rec.updated_at.isoformat() if rec and rec.updated_at else None,
            })
        return result

    def toggle_module(self, slug: str, enable: Optional[bool], session: Session) -> Dict:
        """Переключение активности модуля"""
        self.ensure_table()
        rec = session.exec(select(SystemModule).where(SystemModule.slug == slug)).first()
        if not rec:
            raise HTTPException(status_code=404, detail="Модуль не найден в базе данных")

        if rec.is_system and enable is False:
            raise HTTPException(status_code=400, detail="Системный модуль нельзя отключить")

        if enable is None:
            rec.is_enabled = not rec.is_enabled
        else:
            rec.is_enabled = enable

        rec.updated_at = datetime.utcnow()
        session.add(rec)
        session.commit()
        session.refresh(rec)

        mod = self.modules.get(slug)
        if mod:
            if rec.is_enabled and not mod.is_loaded:
                try:
                    mod.on_startup()
                    mod.is_loaded = True
                    mod.error = None
                except Exception as e:
                    mod.error = str(e)
            elif not rec.is_enabled and mod.is_loaded:
                try:
                    mod.on_shutdown()
                except Exception:
                    pass
                mod.is_loaded = False

        return {
            "status": "success",
            "slug": rec.slug,
            "is_enabled": rec.is_enabled,
            "message": f"Модуль '{rec.name}' {'активирован' if rec.is_enabled else 'отключен'}."
        }


# Глобальный синглтон загрузчика
module_loader = ModuleLoader()

# Роутер API для управления модулями
modules_router = APIRouter(prefix="/system/modules", tags=["System Modules"])


@modules_router.get("/")
def get_system_modules(session: Session = Depends(get_session)):
    """Получить список всех установленных модулей"""
    return module_loader.get_modules_list(session)


@modules_router.post("/{slug}/toggle")
def toggle_system_module(slug: str, session: Session = Depends(get_session)):
    """Включить/выключить модуль"""
    return module_loader.toggle_module(slug, None, session)
