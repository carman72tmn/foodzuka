"""
API эндпоинты для синхронизации с iiko и управления настройками
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, File, UploadFile
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.iiko_settings import IikoSettings
from app.models.sync_log import SyncLog
from pydantic import BaseModel
from app.models.payment_type import PaymentType

from app.schemas import (
    IikoSyncResponse,
    IikoSettingsCreate,
    IikoSettingsResponse,
    IikoConnectionTestResponse,
    SyncLogResponse,
    IikoWebhookEventResponse
)

class MapSyncRequest(BaseModel):
    url: Optional[str] = None

from app.models.iiko_webhook_event import IikoWebhookEvent
from app.services.iiko_service import iiko_service
from app.services.iiko_sync_service import iiko_sync_service
from app.models.payment_type import PaymentType
from app.core.logging_utils import log_audit
from app.models.company import DeliveryZone
import logging
from app.core.config import settings as global_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/iiko", tags=["iiko Integration"])


# =============================================================================
# Настройки
# =============================================================================

@router.get("/settings", response_model=IikoSettingsResponse)
async def get_settings(session: Session = Depends(get_session)):
    """Получить текущие настройки iiko"""
    settings = session.exec(select(IikoSettings)).first()
    if not settings:
        raise HTTPException(status_code=404, detail="iiko settings not configured")
    return settings


@router.post("/settings", response_model=IikoSettingsResponse)
async def save_settings(
    data: IikoSettingsCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """Сохранить / обновить настройки iiko"""
    existing = session.exec(select(IikoSettings)).first()

    if existing:
        update_data = data.model_dump()

        # ИСПРАВЛЕНИЕ: защита от перезаписи реального API-ключа замаскированным значением.
        # Маска имеет вид "abcd...efgh" — если она пришла с фронтенда, не трогаем БД.
        incoming_api_login = update_data.get("api_login", "")
        if incoming_api_login and "..." in incoming_api_login:
            print(f"DEBUG save_settings: обнаружена маска api_login='{incoming_api_login}', сохраняем значение из БД")
            update_data["api_login"] = existing.api_login

        # ИСПРАВЛЕНИЕ: защита от перезаписи пароля Resto маской "********"
        incoming_password = update_data.get("resto_password", "")
        if incoming_password == "********":
            print(f"DEBUG save_settings: обнаружена маска resto_password, сохраняем значение из БД")
            update_data["resto_password"] = existing.resto_password

        for key, value in update_data.items():
            setattr(existing, key, value)
        existing.updated_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(existing)
        # Логируем изменение настроек
        log_audit(
            action="UPDATE",
            resource_type="IikoSettings",
            resource_id=str(existing.id),
            message="Настройки iiko обновлены пользователем"
        )
        # Запускаем синхронизацию сотрудников в фоне сразу после обновления настроек
        background_tasks.add_task(iiko_sync_service.sync_employees_full, session)
        return existing
    else:
        new_settings = IikoSettings(**data.model_dump())
        session.add(new_settings)
        session.commit()
        session.refresh(new_settings)
        # Логируем создание настроек
        log_audit(
            action="CREATE",
            resource_type="IikoSettings",
            resource_id=str(new_settings.id),
            message="Настройки iiko созданы"
        )
        # Запускаем синхронизацию сотрудников в фоне сразу после сохранения
        background_tasks.add_task(iiko_sync_service.sync_employees_full, session)
        return new_settings


# =============================================================================
# Проверка подключения
# =============================================================================

@router.post("/settings/resto")
async def save_resto_settings(
    data: Dict[str, Any],
    session: Session = Depends(get_session)
):
    """
    Сохранить настройки iiko Resto отдельно (включая пароль).
    Это позволяет избежать проблемы перезаписи реального пароля маской '********'.
    """
    existing = session.exec(select(IikoSettings)).first()
    if not existing:
        raise HTTPException(status_code=404, detail="iiko settings not found")
    
    # Обновляем URL и логин
    if "resto_url" in data and data["resto_url"]:
        existing.resto_url = data["resto_url"].strip()
    if "resto_login" in data and data["resto_login"]:
        existing.resto_login = data["resto_login"].strip()
    
    # Сохраняем пароль только если он передан и не является маской
    password = data.get("resto_password")
    if password and password != "********":
        existing.resto_password = password.strip()
        logger.info(f"Resto password updated for login: {existing.resto_login}")
    
    existing.updated_at = datetime.now(timezone.utc)
    session.add(existing)
    session.commit()
    session.refresh(existing)
    
    # Логируем действие
    log_audit(
        action="UPDATE",
        resource_type="IikoSettings",
        resource_id=str(existing.id),
        message=f"Настройки iiko Resto обновлены для {existing.resto_login}"
    )
    
    return {"success": True, "message": "Настройки Resto успешно сохранены"}


@router.post("/test-connection", response_model=IikoConnectionTestResponse)
async def test_connection(
    data: Optional[IikoSettingsCreate] = None,
    session: Session = Depends(get_session)
):
    """Проверить подключение к iiko Cloud API"""
    print(f"DEBUG: test_connection called with data: {data}")
    if data:
        # Очищаем данные от пробелов
        api_login = data.api_login.strip() if data.api_login else ""
        org_id = data.organization_id.strip() if data.organization_id else ""
        
        print(f"DEBUG: Testing with provided login: {api_login}")
        # Тестируем с переданными данными (без сохранения в БД)
        try:
            result = await iiko_service.test_connection(
                api_login=api_login,
                organization_id=org_id
            )
            return IikoConnectionTestResponse(**result)
        except Exception as e:
            print(f"DEBUG: Exception in test_connection: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    else:
        # Тестируем с данными из БД
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            raise HTTPException(status_code=404, detail="Settings not found")
        print(f"DEBUG: Testing with DB login: {settings.api_login}")
        try:
            result = await iiko_service.test_connection(
                api_login=settings.api_login,
                organization_id=settings.organization_id
            )
            return IikoConnectionTestResponse(**result)
        except Exception as e:
            print(f"DEBUG: Exception in test_connection (DB): {e}")
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/test-resto-connection")
async def test_resto_connection(
    data: Optional[IikoSettingsCreate] = None,
    session: Session = Depends(get_session)
):
    """Проверить подключение к iiko Resto (Direct Office API)"""
    
    if data:
        url = data.resto_url.strip() if data.resto_url else ""
        login = data.resto_login.strip() if data.resto_login else ""
        password = data.resto_password.strip() if data.resto_password else ""
        
        # If masked password is sent, try to get the real one from DB
        if password == "********" or (data.api_login and "..." in data.api_login):
            existing = session.exec(select(IikoSettings)).first()
            if existing:
                if password == "********":
                    password = existing.resto_password
                if data.api_login and "..." in data.api_login:
                    # Note: we are not using api_login for resto test, but good to be careful
                    pass
    else:
        existing = session.exec(select(IikoSettings)).first()
        if not existing:
            raise HTTPException(status_code=404, detail="Settings not found")
        url = existing.resto_url
        login = existing.resto_login
        password = existing.resto_password

    if not all([url, login, password]):
        raise HTTPException(status_code=400, detail="Resto URL, login, and password are required")

    try:
        import hashlib
        import httpx
        # Calculate SHA-1 hash of the password
        password_sha1 = hashlib.sha1(password.encode()).hexdigest()
        
        async with httpx.AsyncClient(verify=False, timeout=20.0) as client:
            # Attempt to login to get a token.
            # The URL usually ends with /resto/api, so we ensure it's correct
            base_url = url.rstrip('/')
            if not base_url.endswith('/api'):
                if base_url.endswith('/resto'):
                    base_url = f"{base_url}/api"
                else:
                    base_url = f"{base_url}/resto/api"
            
            auth_url = f"{base_url}/auth"
            params = {"login": login, "pass": password_sha1}
            
            print(f"DEBUG: Testing Resto connection to {auth_url} with login {login}")
            response = await client.get(auth_url, params=params)
            
            if response.status_code == 200:
                token = response.text.strip().replace('"', '')
                return {"success": True, "message": "Подключение успешно", "token": token}
            else:
                # Try fallback without hashing just in case (some versions might differ or it's already hashed)
                params_plain = {"login": login, "pass": password}
                response_plain = await client.get(auth_url, params=params_plain)
                if response_plain.status_code == 200:
                    token = response_plain.text.strip().replace('"', '')
                    return {"success": True, "message": "Подключение успешно (plain)", "token": token}
                else:
                    return {"success": False, "error": f"Ошибка авторизации: HTTP {response.status_code} - {response.text}"}
    except Exception as e:
        return {"success": False, "error": f"Ошибка соединения: {str(e)}"}

@router.post("/test-loyalty-connection")
async def test_loyalty_connection(
    data: Optional[IikoSettingsCreate] = None,
    session: Session = Depends(get_session)
):
    """Проверить подключение к iiko Loyalty"""
    if data:
        api_login = data.api_login
        organization_id = data.organization_id
        pos_loyalty_name = data.pos_loyalty_name
    else:
        existing = session.exec(select(IikoSettings)).first()
        if not existing:
            raise HTTPException(status_code=404, detail="Settings not found")
        api_login = existing.api_login
        organization_id = existing.organization_id
        pos_loyalty_name = existing.pos_loyalty_name

    try:
        return await iiko_service.test_loyalty_connection(
            api_login=api_login,
            organization_id=organization_id,
            pos_loyalty_name=pos_loyalty_name
        )
    except Exception as e:
        return {"success": False, "error": str(e)}



# =============================================================================
# Справочники (организации, терминалы, типы оплаты)
# =============================================================================

@router.get("/organizations")
async def get_organizations(session: Session = Depends(get_session)):
    """Получить список организаций из iiko"""
    settings = session.exec(select(IikoSettings)).first()
    api_login = settings.api_login if settings else None
    try:
        return await iiko_service.get_organizations(api_login=api_login)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/terminal-groups")
async def get_terminal_groups(session: Session = Depends(get_session)):
    """Получить список терминальных групп"""
    settings = session.exec(select(IikoSettings)).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    try:
        return await iiko_service.get_terminal_groups(
            api_login=settings.api_login,
            organization_id=settings.organization_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payment-types")
async def get_payment_types(session: Session = Depends(get_session)):
    """Получить типы оплаты из локальной БД"""
    types = session.exec(select(PaymentType).where(PaymentType.is_active == True)).all()
    return [{
        "id": t.iiko_id, 
        "name": t.name, 
        "paymentTypeKind": t.kind,
        "mapping_type": t.mapping_type,
        "is_processed_externally": t.is_processed_externally
    } for t in types]


@router.post("/save-payment-types-mapping")
async def save_payment_types_mapping(data: List[Dict[str, Any]], session: Session = Depends(get_session)):
    """Сохранить сопоставление типов оплаты"""
    try:
        logger.info(f"Получен запрос на сохранение маппинга для {len(data)} типов оплаты")
        for item in data:
            iiko_id = item.get("id")
            if not iiko_id: continue
            
            pt = session.exec(select(PaymentType).where(PaymentType.iiko_id == iiko_id)).first()
            if pt:
                logger.info(f"Обновление маппинга для {pt.name} ({iiko_id}): mapping_type={item.get('mapping_type')}")
                pt.mapping_type = item.get("mapping_type")
                pt.is_processed_externally = item.get("is_processed_externally", False)
                pt.updated_at = datetime.now(timezone.utc)
                session.add(pt)
            else:
                logger.warning(f"Тип оплаты с iiko_id {iiko_id} не найден в БД")
        
        session.commit()
        logger.info("Маппинг типов оплаты успешно сохранен")
        return {"status": "success"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/order-types")
async def get_order_types(session: Session = Depends(get_session)):
    """Получить типы заказов"""
    settings = session.exec(select(IikoSettings)).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    try:
        return await iiko_service.get_order_types(
            api_login=settings.api_login,
            organization_id=settings.organization_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discount-types")
async def get_discount_types(session: Session = Depends(get_session)):
    """Получить доступные типы скидок"""
    settings = session.exec(select(IikoSettings)).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    try:
        return await iiko_service.get_discount_types(
            api_login=settings.api_login,
            organization_id=settings.organization_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/external-menus")
async def get_external_menus(session: Session = Depends(get_session)):
    """Получить список внешних меню"""
    settings = session.exec(select(IikoSettings)).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    try:
        # Note: get_external_menus also needs update in service if dynamic
        return await iiko_service.get_external_menus(
            api_login=settings.api_login,
            organization_id=settings.organization_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/price-categories")
async def get_price_categories(session: Session = Depends(get_session)):
    """Получить список ценовых категорий из iiko Cloud"""
    settings = session.exec(select(IikoSettings)).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    try:
        return await iiko_service.get_price_categories(
            api_login=settings.api_login,
            organization_id=settings.organization_id
        )
    except Exception as e:
        logger.warning(f"Failed to fetch price categories: {e}")
        return []


# =============================================================================
# Синхронизация
# =============================================================================

@router.post("/sync-menu", response_model=IikoSyncResponse)
async def sync_menu(session: Session = Depends(get_session)):
    """Полная синхронизация меню (категории + товары) из iiko"""
    try:
        result = await iiko_sync_service.sync_menu(session)
        return IikoSyncResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Menu sync error: {str(e)}")


@router.post("/sync-prices", response_model=IikoSyncResponse)
async def sync_prices(session: Session = Depends(get_session)):
    """Синхронизация только цен из iiko"""
    try:
        result = await iiko_sync_service.sync_prices(session)
        return IikoSyncResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price sync error: {str(e)}")


@router.post("/sync-stop-list", response_model=IikoSyncResponse)
@router.post("/sync-stop-lists", response_model=IikoSyncResponse)
async def sync_stop_lists(session: Session = Depends(get_session)):
    """Синхронизация стоп-листов (недоступные позиции)"""
    try:
        result = await iiko_sync_service.sync_stop_lists(session)
        return IikoSyncResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stop-list sync error: {str(e)}")


@router.post("/sync-payment-types")
async def sync_payment_types(session: Session = Depends(get_session)):
    """Синхронизация типов оплаты из iiko в локальную БД"""
    try:
        result = await iiko_sync_service.sync_payment_types(session)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка синхронизации типов оплаты: {str(e)}")


@router.post("/save-delivery-zones")
async def save_delivery_zones(data: List[Dict[str, Any]], session: Session = Depends(get_session)):
    """Сохранить параметры зон доставки"""
    logger.info(f"Получен запрос на сохранение {len(data)} зон доставки")
    try:
        for item in data:
            zone_id = item.get("id")
            if not zone_id: 
                logger.warning(f"Пропуск зоны без ID: {item.get('name')}")
                continue
            
            # Строгое приведение к int для обхода ошибки типизации JSON -> DB
            try:
                numeric_id = int(zone_id)
            except (ValueError, TypeError):
                continue

            zone = session.exec(select(DeliveryZone).where(DeliveryZone.id == numeric_id)).first()
            if not zone and item.get("iiko_id"):
                # Запасной вариант: ищем по iiko_id
                zone = session.exec(select(DeliveryZone).where(DeliveryZone.iiko_id == item.get("iiko_id"))).first()
                if zone:
                    logger.info(f"Зона найдена по iiko_id: {zone.name} (iiko_id: {item.get('iiko_id')})")

            if zone:
                logger.info(f"Обновление зоны {zone.name} (ID: {numeric_id})")
                # Безопасное приведение к числу (обрабатываем пустые строки)
                def to_float(val, default=0.0):
                    if val is None or val == "": return default
                    try: return float(val)
                    except: return default

                def to_int(val, default=0):
                    if val is None or val == "": return default
                    try: return int(val)
                    except: return default

                zone.min_order_amount = to_float(item.get("min_order_amount"), 0.0)
                zone.delivery_cost = to_float(item.get("delivery_cost"), 0.0)
                zone.iiko_id = item.get("iiko_id")
                zone.name = item.get("name", zone.name)
                
                fs = item.get("free_delivery_sum")
                zone.free_delivery_sum = to_float(fs, None) if fs is not None and fs != "" else None
                
                zone.min_delivery_time = to_int(item.get("min_delivery_time"), None)
                zone.max_delivery_time = to_int(item.get("max_delivery_time"), None)
                zone.priority = to_int(item.get("priority"), 0)
                
                zone.is_default = bool(item.get("is_default"))
                zone.is_active = bool(item.get("is_active", True))
                zone.is_manual_override = True  # Помечаем что изменено вручную
                zone.updated_at = datetime.now(timezone.utc)
                session.add(zone)
            else:
                logger.warning(f"Зона с ID {numeric_id} не найдена в БД")
        
        session.commit()
        logger.info("Параметры зон доставки успешно сохранены в БД")
        return {"status": "success", "message": "Параметры зон доставки сохранены"}
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при сохранении зон: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения зон доставки: {str(e)}")


@router.post("/sync-delivery-zones")
async def sync_delivery_zones(session: Session = Depends(get_session)):
    """Синхронизация зон доставки из iiko в локальную БД"""
    try:
        result = await iiko_sync_service.sync_delivery_restrictions(session)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка синхронизации зон доставки: {str(e)}")


@router.post("/sync-zones-from-map")
async def sync_zones_from_map(request: MapSyncRequest, session: Session = Depends(get_session)):
    """Синхронизация геометрии зон доставки из внешней ссылки (Google Maps)"""
    try:
        result = await iiko_sync_service.sync_zones_from_external_map(session, url=request.url)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка синхронизации геометрии из карт: {str(e)}")


@router.post("/upload-kml")
async def upload_kml(file: UploadFile = File(...), session: Session = Depends(get_session)):
    """Загрузка KML файла для обновления геометрии зон доставки"""
    try:
        content = await file.read()
        kml_text = _decode_kml(content)
        
        result = await iiko_sync_service.sync_zones_from_kml_file(session, kml_text)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Ошибка обработки файла"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка загрузки KML файла: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка обработки файла: {str(e)}")


@router.post("/clear-delivery-zones")
async def clear_delivery_zones(session: Session = Depends(get_session)):
    """Полная очистка всех зон доставки в локальной БД"""
    try:
        from sqlalchemy import delete
        session.execute(delete(DeliveryZone))
        session.commit()
        
        # Очищаем кэш
        try:
            from app.core.redis import redis_client
            await redis_client.delete("delivery_zones_all")
        except:
            pass
            
        logger.info("Все зоны доставки успешно удалены из БД")
        return {"status": "success", "message": "Все зоны доставки успешно удалены"}
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при очистке зон доставки: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка очистки зон: {str(e)}")


def _decode_kml(content: bytes) -> str:
    """Вспомогательная функция для декодирования KML контента с поддержкой UTF-8 и других кодировок"""
    for encoding in ['utf-8', 'utf-8-sig', 'windows-1251', 'latin-1']:
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise HTTPException(status_code=400, detail="Не удалось определить кодировку файла. Используйте UTF-8.")


@router.get("/delivery-zones")
async def get_delivery_zones(session: Session = Depends(get_session)):
    """Получить список зон доставки из локальной БД"""
    zones = session.exec(select(DeliveryZone)).all()
    return [
        {
            "id": z.id,
            "iiko_id": z.iiko_id,
            "name": z.name,
            "min_order_amount": z.min_order_amount,
            "delivery_cost": z.delivery_cost,
            "free_delivery_sum": z.free_delivery_sum,
            "min_delivery_time": z.min_delivery_time,
            "max_delivery_time": z.max_delivery_time,
            "priority": z.priority,
            "is_default": z.is_default,
            "is_active": z.is_active,
            "is_manual_override": z.is_manual_override,
            "polygon_coordinates": z.polygon_coordinates,
        }
        for z in zones
    ]


@router.get("/iiko-zones-list")
async def get_iiko_zones_list(session: Session = Depends(get_session)):
    """Получить список всех зон, доступных в iiko Cloud"""
    try:
        return await iiko_sync_service.get_available_iiko_zones(session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-vk-loyalty", response_model=IikoSyncResponse)
async def sync_vk_loyalty(session: Session = Depends(get_session)):
    """Синхронизация баллов VK активности в iikoCard"""
    try:
        result = await iiko_sync_service.sync_vk_loyalty(session)
        return IikoSyncResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VK Loyalty sync error: {str(e)}")


# =============================================================================
# Логи синхронизации
# =============================================================================

@router.get("/sync-logs", response_model=List[SyncLogResponse])
async def get_sync_logs(
    limit: int = 50,
    sync_type: str = None,
    session: Session = Depends(get_session)
):
    """Получить историю синхронизаций"""
    query = select(SyncLog).order_by(SyncLog.created_at.desc()).limit(limit)
    if sync_type:
        query = query.where(SyncLog.sync_type == sync_type)
    logs = session.exec(query).all()
    return logs


# =============================================================================
# Лояльность
# =============================================================================

@router.get("/loyalty/importable-data")
async def get_loyalty_importable_data(session: Session = Depends(get_session)):
    """Получить список программ и категорий лояльности для импорта"""
    settings_db = session.exec(select(IikoSettings)).first()
    if not settings_db:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    try:
        programs = await iiko_service.get_loyalty_programs(
            api_login=settings_db.api_login,
            organization_id=settings_db.organization_id
        )
        categories = await iiko_service.get_loyalty_categories(
            api_login=settings_db.api_login,
            organization_id=settings_db.organization_id
        )
        return {
            "success": True,
            "programs": programs,
            "categories": categories
        }
    except Exception as e:
        logger.error(f"Error fetching loyalty importable data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customer/{phone}")
async def get_customer_info(phone: str):
    """Получить информацию о клиенте по номеру телефона"""
    try:
        return await iiko_service.get_customer_info(phone)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customer/{phone}/balance")
async def get_customer_balance(phone: str):
    """Получить баланс бонусов клиента"""
    try:
        return await iiko_service.get_customer_balance(phone)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Отчеты и аналитика
# =============================================================================

@router.get("/companies/report")
async def get_organization_report(
    organization_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """Получить отчет по компании (Dashboard)"""
    try:
        return await iiko_service.get_organization_report(
            organization_id=organization_id,
            date_from=date_from,
            date_to=date_to
        )
    except Exception as e:
        logger.error(f"Error in get_organization_report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Управление вебхуками
# =============================================================================

@router.post("/webhooks/register")
async def register_webhook(
    request: Request,
    webhook_url: Optional[str] = None,
    auth_token: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Регистрация вебхука в iiko и сохранение настроек.
    Если webhook_url не передан, используется автоматическая регистрация.
    """
    settings_db = session.exec(select(IikoSettings)).first()
    if not settings_db:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    try:
        if not webhook_url:
            # Пытаемся определить базовый URL (приоритет у настройки APP_PUBLIC_URL из конфига)
            base_url = global_settings.APP_PUBLIC_URL or str(request.base_url)
            
            # Автоматическая регистрация
            result = await iiko_service.auto_register_webhook(
                request_url=base_url,
                api_login=settings_db.api_login,
                organization_id=settings_db.organization_id
            )
            
            # Сохраняем сгенерированные данные в БД
            new_url = result.get("webhook_url")
            new_token = result.get("auth_token")
            
            logger.info(f"Auto-registering webhook: URL={new_url}, Token={new_token}")
            
            settings_db.webhook_url = new_url
            settings_db.webhook_auth_token = new_token
            session.add(settings_db)
            session.commit()
            
            return {
                "success": True, 
                "webhook_url": new_url, 
                "auth_token": new_token,
                "iiko_response": result
            }
        else:
            # Ручная регистрация (ИСПРАВЛЕНО: сначала iiko, потом БД)
            logger.info(f"Manually registering webhook: URL={webhook_url}, Token={auth_token}")
            
            # Пробуем зарегистрировать в iiko Cloud
            iiko_resp = await iiko_service.update_webhook_settings(
                webhook_url, 
                auth_token,
                api_login=settings_db.api_login,
                organization_id=settings_db.organization_id
            )
            
            # Если не упало с исключением - сохраняем в БД
            settings_db.webhook_url = webhook_url
            settings_db.webhook_auth_token = auth_token
            session.add(settings_db)
            session.commit()
            
            return {
                "success": True, 
                "webhook_url": webhook_url,
                "auth_token": auth_token,
                "iiko_response": iiko_resp
            }
            
    except Exception as e:
        logger.error(f"Webhook registration error: {e}")
        raise HTTPException(status_code=400, detail=f"iiko API error: {str(e)}")


@router.post("/webhooks/test")
async def test_webhook_connection(
    session: Session = Depends(get_session)
):
    """РџСЂРѕРІРµСЂРёС‚СЊ С‚РµРєСѓС‰РёРµ РЅР°СЃС‚СЂРѕР№РєРё РІРµР±С…СѓРєРѕРІ РІ iiko Cloud Рё СЃРІРµСЂРёС‚СЊ СЃ Р‘Р”"""
    settings_db = session.exec(select(IikoSettings)).first()
    if not settings_db:
        raise HTTPException(status_code=404, detail="Settings not found")
        
    try:
        # Запрашиваем настройки из iiko
        iiko_settings = await iiko_service.get_webhook_settings(
            api_login=settings_db.api_login,
            organization_id=settings_db.organization_id
        )
        
        iiko_uri = iiko_settings.get("webHooksUri")
        iiko_token = iiko_settings.get("authToken")
        
        url_match = (iiko_uri == settings_db.webhook_url)
        token_match = (iiko_token == settings_db.webhook_auth_token)
        
        return {
            "success": url_match and token_match,
            "local_url": settings_db.webhook_url,
            "iiko_url": iiko_uri,
            "local_token": "***" if settings_db.webhook_auth_token else None,
            "iiko_token": "***" if iiko_token else None,
            "url_match": url_match,
            "token_match": token_match,
            "iiko_full_response": iiko_settings
        }
    except Exception as e:
        logger.error(f"Error testing webhook connection: {e}")
        raise HTTPException(status_code=400, detail=f"iiko API error: {str(e)}")


@router.post("/webhooks/sync-token")
async def sync_webhook_token(
    session: Session = Depends(get_session)
):
    """
    РЎРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°С‚СЊ С‚РѕРєРµРЅ РёР· iiko Cloud РІ Р»РѕРєР°Р»СЊРЅСѓСЋ Р‘Р”.
    РџРѕРјРѕРіР°РµС‚ РёСЃРїСЂР°РІРёС‚СЊ 'Token mismatch' Р±РµР· РІС‹Р·РѕРІР° update_settings (Р·Р°С‰РёС‚Р° РѕС‚ 429).
    """
    settings_db = session.exec(select(IikoSettings)).first()
    if not settings_db:
        raise HTTPException(status_code=404, detail="Settings not found")
        
    try:
        # 1. Р—Р°РїСЂР°С€РёРІР°РµРј С‚РµРєСѓС‰РёРµ РЅР°СЃС‚СЂРѕР№РєРё РёР· iiko (СЌС‚Рѕ Р±РµР·РѕРїР°СЃРЅС‹Р№ Р·Р°РїСЂРѕСЃ)
        iiko_settings = await iiko_service.get_webhook_settings(
            api_login=settings_db.api_login,
            organization_id=settings_db.organization_id
        )
        
        iiko_token = iiko_settings.get("authToken")
        iiko_uri = iiko_settings.get("webHooksUri")
        
        if not iiko_token:
            raise HTTPException(status_code=400, detail="iiko Cloud does not have a webhook token set. Please use 'Register Webhook' first.")

        # 2. РћР±РЅРѕРІР»СЏРµРј Р»РѕРєР°Р»СЊРЅСѓСЋ Р‘Р”
        settings_db.webhook_auth_token = iiko_token
        if iiko_uri:
            settings_db.webhook_url = iiko_uri
            
        session.add(settings_db)
        session.commit()
        
        return {
            "success": True,
            "message": "Token successfully synchronized from iiko Cloud",
            "webhook_url": settings_db.webhook_url,
            "auth_token": settings_db.webhook_auth_token
        }
    except Exception as e:
        logger.error(f"Error syncing webhook token: {e}")
        raise HTTPException(status_code=400, detail=f"iiko API error: {str(e)}")


@router.get("/webhooks/logs", response_model=List[IikoWebhookEventResponse])
async def get_webhook_logs(
    limit: int = 50,
    session: Session = Depends(get_session)
):
    """Получить лог вебхуков с расширенной информацией"""
    query = select(IikoWebhookEvent).order_by(IikoWebhookEvent.created_at.desc()).limit(limit)
    events = session.exec(query).all()
    
    result = []
    for event in events:
        # Извлекаем ID заказа из payload если это событие по заказу
        order_id = None
        payload = event.payload or {}
        
        # Для iiko Cloud DeliveryOrderUpdate
        if "eventInfo" in payload:
            order_id = payload["eventInfo"].get("orderId") or payload["eventInfo"].get("id")
        # Для iiko Cloud v2
        elif "orderId" in payload:
            order_id = payload["orderId"]
        elif "id" in payload and event.event_type == "DeliveryOrderUpdate":
            order_id = payload["id"]
            
        result.append({
            "id": event.id,
            "event_type": event.event_type,
            "event_id": event.event_id,
            "payload": event.payload,
            "processed": event.processed,
            "status": "Успешно" if event.processed else "Ошибка",
            "order_id": order_id,
            "error": event.error,
            "created_at": event.created_at
        })
        
    return result
