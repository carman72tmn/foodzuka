import logging
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.system_module import SystemModule
from app.modules.manager import module_manager

logger = logging.getLogger("api.system_modules")
router = APIRouter(prefix="/system/modules", tags=["Системные модули"])

class ModuleResponse(BaseModel):
    id: int | None = None
    slug: str
    name: str
    description: str | None = None
    version: str | None = "1.0.0"
    author: str | None = "VezuRoll Core"
    is_enabled: bool = True
    is_system: bool = False
    icon: str | None = "bx-cube"
    route_path: str | None = None
    category: str | None = "general"
    is_loaded: bool = False
    has_router: bool = False

class ToggleModuleRequest(BaseModel):
    is_enabled: bool

@router.get("", response_model=List[ModuleResponse])
def get_system_modules(
    session: Session = Depends(get_session)
):
    """
    Возвращает список всех модулей системы (из БД и памяти менеджера).
    """
    try:
        db_modules = session.exec(select(SystemModule)).all()
        db_map = {m.slug: m for m in db_modules}

        # Все найденные в файловой системе модули
        all_code_modules = module_manager.get_all_modules()
        result = []

        seen_slugs = set()

        for code_mod in all_code_modules:
            info = code_mod.get_info()
            slug = code_mod.slug
            seen_slugs.add(slug)
            db_record = db_map.get(slug)

            result.append(
                ModuleResponse(
                    id=db_record.id if db_record else None,
                    slug=slug,
                    name=db_record.name if db_record else info.get("name", slug),
                    description=db_record.description if db_record else info.get("description"),
                    version=db_record.version if db_record else info.get("version", "1.0.0"),
                    author=db_record.author if db_record else info.get("author", "Team VezuRoll"),
                    is_enabled=db_record.is_enabled if db_record else code_mod.is_enabled,
                    is_system=db_record.is_system if db_record else info.get("is_system", False),
                    icon=db_record.icon if db_record else info.get("icon", "bx-cube"),
                    route_path=db_record.route_path if db_record else info.get("route_path"),
                    category=db_record.category if db_record else info.get("category", "general"),
                    is_loaded=True,
                    has_router=code_mod.get_router() is not None,
                )
            )

        # Модули, которые есть в БД, но их файлов нет на диске (например, удаленные или внешние)
        for slug, db_mod in db_map.items():
            if slug not in seen_slugs:
                result.append(
                    ModuleResponse(
                        id=db_mod.id,
                        slug=db_mod.slug,
                        name=db_mod.name,
                        description=db_mod.description,
                        version=db_mod.version,
                        author=db_mod.author,
                        is_enabled=db_mod.is_enabled,
                        is_system=db_mod.is_system,
                        icon=db_mod.icon,
                        route_path=db_mod.route_path,
                        category=db_mod.category,
                        is_loaded=False,
                        has_router=False,
                    )
                )

        return result
    except Exception as e:
        logger.error(f"Ошибка при получении списка системных модулей: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")

@router.post("/{slug}/toggle")
def toggle_system_module(
    slug: str,
    payload: ToggleModuleRequest,
    session: Session = Depends(get_session)
):
    """
    Включает или выключает модуль.
    """
    db_mod = session.exec(select(SystemModule).where(SystemModule.slug == slug)).first()
    if not db_mod:
        raise HTTPException(status_code=404, detail=f"Модуль '{slug}' не найден в БД")

    if db_mod.is_system and not payload.is_enabled:
        raise HTTPException(status_code=400, detail="Системный модуль не может быть отключен")

    success = module_manager.toggle_module(slug, payload.is_enabled)
    if not success:
        # Обновим хотя бы в БД
        db_mod.is_enabled = payload.is_enabled
        session.add(db_mod)
        session.commit()

    return {"status": "ok", "slug": slug, "is_enabled": payload.is_enabled}

@router.post("/rescan")
def rescan_modules():
    """
    Повторно сканирует каталог модулей и синхронизирует с БД.
    """
    try:
        module_manager.discover_modules()
        module_manager.sync_with_db()
        return {"status": "ok", "total_modules": len(module_manager.get_all_modules())}
    except Exception as e:
        logger.error(f"Ошибка при повторном сканировании модулей: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
