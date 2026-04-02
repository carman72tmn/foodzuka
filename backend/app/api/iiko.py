"""
API эндпоинты для синхронизации с iiko и управления настройками
"""
from typing import List, Optional
from datetime import datetime
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.iiko_settings import IikoSettings
from app.models.sync_log import SyncLog
from app.schemas import (
    IikoSyncResponse,
    IikoSettingsCreate,
    IikoSettingsResponse,
    IikoConnectionTestResponse,
    SyncLogResponse,
    IikoWebhookEventResponse
)
from app.models.iiko_webhook_event import IikoWebhookEvent
from app.services.iiko_service import iiko_service
from app.services.iiko_sync_service import iiko_sync_service
from app.core.config import settings as global_settings

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
    session: Session = Depends(get_session)
):
    """Сохранить / обновить настройки iiko"""
    existing = session.exec(select(IikoSettings)).first()

    if existing:
        for key, value in data.model_dump().items():
            setattr(existing, key, value)
        existing.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(existing)
        return existing
    else:
        new_settings = IikoSettings(**data.model_dump())
        session.add(new_settings)
        session.commit()
        session.refresh(new_settings)
        return new_settings


# =============================================================================
# Проверка подключения
# =============================================================================

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
        # Calculate SHA-1 hash of the password
        password_sha1 = hashlib.sha1(password.encode()).hexdigest()
        
        async with httpx.AsyncClient(verify=False) as client:
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
                    
                return {"success": False, "error": f"Ошибка авторизации: HTTP {response.status_code} - {response.text}"}
    except Exception as e:
        return {"success": False, "error": f"Ошибка соединения: {str(e)}"}


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
    """Получить типы оплаты"""
    settings = session.exec(select(IikoSettings)).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    try:
        return await iiko_service.get_payment_types(
            api_login=settings.api_login,
            organization_id=settings.organization_id
        )
    except Exception as e:
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


@router.post("/sync-stop-lists", response_model=IikoSyncResponse)
async def sync_stop_lists(session: Session = Depends(get_session)):
    """Синхронизация стоп-листов (недоступные позиции)"""
    try:
        result = await iiko_sync_service.sync_stop_lists(session)
        return IikoSyncResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stop-list sync error: {str(e)}")


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
            settings_db.webhook_url = result["webhook_url"]
            settings_db.webhook_auth_token = result["auth_token"]
            session.add(settings_db)
            session.commit()
            
            return result
        else:
            # Ручная регистрация (существующая логика)
            settings_db.webhook_url = webhook_url
            settings_db.webhook_auth_token = auth_token
            session.add(settings_db)
            session.commit()
            
            iiko_resp = await iiko_service.update_webhook_settings(
                webhook_url, 
                auth_token,
                api_login=settings_db.api_login,
                organization_id=settings_db.organization_id
            )
            return {"success": True, "iiko_response": iiko_resp}
            
    except Exception as e:
        print(f"DEBUG: Webhook registration error: {e}")
        raise HTTPException(status_code=400, detail=f"iiko API error: {str(e)}")


@router.get("/webhooks/logs", response_model=List[IikoWebhookEventResponse])
async def get_webhook_logs(
    limit: int = 50,
    session: Session = Depends(get_session)
):
    """Получить лог вебхуков"""
    query = select(IikoWebhookEvent).order_by(IikoWebhookEvent.created_at.desc()).limit(limit)
    return session.exec(query).all()
