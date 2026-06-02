"""
Сервис для интеграции с iiko Cloud API
Документация API: https://api-ru.iiko.services/
"""
import httpx
import asyncio
# -*- coding: utf-8 -*-
# Encoding: UTF-8 (Strictly required for FoodTech project)
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta, timezone
import secrets
import json
import hashlib
from sqlmodel import Session, select
from fastapi import HTTPException
from app.core.config import settings
from app.core.database import engine
from app.core.redis import redis_client
from app.models.iiko_settings import IikoSettings
from app.services.yandex_service import yandex_service
from app.utils.geo_utils import parse_kml

logger = logging.getLogger(__name__)


class IikoService:
    """Сервис для работы с iiko Cloud API"""

    def __init__(self):
        self.api_url = settings.IIKO_API_URL
        self.api_login = settings.IIKO_API_LOGIN
        self.organization_id = settings.IIKO_ORGANIZATION_ID
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        # Кеш токенов для разных логинов (api_login -> (token, expires_at))
        self._token_cache: Dict[str, tuple[str, datetime]] = {}
        
        # Оптимизация производительности: Пулинг соединений и блокировки
        self._client: Optional[httpx.AsyncClient] = None
        self._insecure_client: Optional[httpx.AsyncClient] = None
        self._token_lock = None # Инициализируется лениво через _get_token_lock()
        
        # Кэш настроек организаций (ID -> IikoSettings)
        # Снижает нагрузку на БД при каждом API запросе
        self._org_settings_cache: Dict[str, IikoSettings] = {}
        self._cache_ttl = 300  # 5 минут
        self._cache_updated_at: Dict[str, datetime] = {}
        
        # Cooling Period для предотвращения 429 (Endpoint -> Timestamp)
        self._cooling_endpoints: Dict[str, datetime] = {}
        self._cooling_duration = 120  # 2 минуты тишины при 429

        # Denied Period для предотвращения спама при отсутствии прав (403)
        self._denied_endpoints: Dict[str, datetime] = {}
        self._denied_duration = 3600  # 1 час тишины при отсутствии прав

        # Кеш токенов для Resto API (login -> (token, expires_at))
        self._resto_token_cache: Dict[str, tuple[str, datetime]] = {}
        self._resto_token_lock = None

    def _get_token_lock(self):
        """Ленивая инициализация Lock для предотвращения RuntimeError: no running event loop"""
        if self._token_lock is None:
            self._token_lock = asyncio.Lock()
        return self._token_lock

    def _get_resto_token_lock(self):
        """Лок для авторизации в Resto API"""
        if self._resto_token_lock is None:
            self._resto_token_lock = asyncio.Lock()
        return self._resto_token_lock

    @property
    def client(self) -> httpx.AsyncClient:
        """Ленивая инициализация асинхронного HTTP клиента"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
            )
        return self._client

    @property
    def insecure_client(self) -> httpx.AsyncClient:
        """Ленивая инициализация клиента без проверки SSL (для iiko Server/Resto)"""
        if self._insecure_client is None or self._insecure_client.is_closed:
            self._insecure_client = httpx.AsyncClient(
                verify=False,
                timeout=httpx.Timeout(60.0, connect=10.0),
                limits=httpx.Limits(max_connections=50, max_keepalive_connections=10)
            )
        return self._insecure_client

    async def aclose(self):
        """Закрытие клиентов при завершении работы приложения"""
        tasks = []
        if self._client and not self._client.is_closed:
            tasks.append(self._client.aclose())
        if self._insecure_client and not self._insecure_client.is_closed:
            tasks.append(self._insecure_client.aclose())
        if tasks:
            await asyncio.gather(*tasks)

    # =========================================================================
    # Настройки и БД
    # =========================================================================

    async def _get_settings_by_org_id(self, organization_id: str) -> Optional[IikoSettings]:
        """
        Получение настроек API из БД по organization_id с использованием кэширования.
        """
        if not organization_id:
            return None

        # Проверка кэша
        now = datetime.now(timezone.utc)
        if organization_id in self._org_settings_cache:
            updated_at = self._cache_updated_at.get(organization_id)
            if updated_at and (now - updated_at).total_seconds() < self._cache_ttl:
                return self._org_settings_cache[organization_id]

        try:
            # Импортируем get_session_sync здесь чтобы избежать циклических зависимостей в некоторых случаях
            from app.core.database import get_session_sync
            
            def _fetch():
                with get_session_sync() as session:
                    statement = select(IikoSettings).where(IikoSettings.organization_id == organization_id)
                    res = session.exec(statement).first()
                    if res:
                        # Создаем копию без привязки к сессии, чтобы избежать DetachedInstanceError
                        return IikoSettings.model_validate(res.model_dump())
                    return None

            # Выполняем синхронный запрос в отдельном потоке
            settings_obj = await asyncio.to_thread(_fetch)
            
            if settings_obj:
                self._org_settings_cache[organization_id] = settings_obj
                self._cache_updated_at[organization_id] = now
            
            return settings_obj
        except Exception as e:
            logger.error(f"Error getting settings for org {organization_id}: {e}")
            return None

    async def check_address_zone(
        self,
        organization_id: str,
        city: str,
        street: str,
        house: str,
        api_login: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Автоматическое определение зоны доставки по адресу.
        1. Геокодирует адрес через Яндекс.
        2. Ищет вхождение координат в полигоны зон доставки.
        """
        full_address = f"{city}, {street}, {house}"
        logger.info(f"Checking delivery zone for address: {full_address}")

        try:
            with Session(engine) as session:
                # 1. Получаем настройки Яндекса
                yandex_settings = await yandex_service.get_settings(session)
                if not yandex_settings or not yandex_settings.api_key_js:
                    logger.warning("Yandex API key not configured for zone checking")
                    return {"zone": None, "error": "Yandex API key missing"}

                # 2. Геокодируем адрес
                coords = await yandex_service.geocode_address(full_address, yandex_settings.api_key_js)
                if not coords:
                    logger.warning(f"Failed to geocode address: {full_address}")
                    return {"zone": None, "error": "Geocoding failed"}

                lat, lng = coords["lat"], coords["lng"]
                logger.debug(f"Coordinates for {full_address}: {lat}, {lng}")

                # 3. Определяем зону по координатам
                zone = await yandex_service.resolve_zone_for_point(lat, lng, session)
                
                if zone:
                    logger.info(f"Address {full_address} belongs to zone: {zone.name} (ID: {zone.id})")
                    return {
                        "zone": zone.name,
                        "zone_id": zone.id,
                        "iiko_id": zone.iiko_id,
                        "coordinates": {"lat": lat, "lng": lng}
                    }

                logger.info(f"No delivery zone found for address: {full_address}")
                return {"zone": None}

        except Exception as e:
            logger.error(f"Error in check_address_zone: {str(e)}")
            return {"zone": None, "error": str(e)}

    # =========================================================================
    # Аутентификация
    # =========================================================================

    async def _get_access_token(self, api_login: Optional[str] = None) -> str:
        """
        Получение токена доступа к iiko API с использованием блокировки для предотвращения race conditions.
        """
        login = api_login or self.api_login
        
        # Защита от плейсхолдеров и пустых значений
        if not login or login.startswith("your_") or "placeholder" in login.lower() or "client error" in login.lower():
            logger.error(f"Некорректный логин iiko API: {login}")
            raise ValueError("Логин iiko API не настроен или содержит ошибку. Пожалуйста, введите ключ заново.")

        login = login.strip()
        now = datetime.now(timezone.utc)

        # 1. Проверка in-memory кеша
        if login in self._token_cache:
            token, expires_at = self._token_cache[login]
            if now < expires_at:
                # Если это основной логин, также обновляем основные поля для совместимости
                if not api_login:
                    self.access_token = token
                    self.token_expires_at = expires_at
                return token

        # 2. Проверка БД (для синхронизации между процессами/воркерами)
        async with self._get_token_lock():
            # Повторная проверка кеша внутри блокировки
            if login in self._token_cache:
                token, expires_at = self._token_cache[login]
                if now < expires_at:
                    return token

            # Ищем настройки в БД по логину
            try:
                def _get_db_token():
                    with Session(engine) as session:
                        return session.exec(select(IikoSettings).where(IikoSettings.api_login == login)).first()
                
                settings_db = await asyncio.to_thread(_get_db_token)
                if settings_db and settings_db.access_token and settings_db.token_expires_at:
                    # Принудительно делаем expires_at aware если он naive
                    db_expires = settings_db.token_expires_at
                    if db_expires.tzinfo is None:
                        db_expires = db_expires.replace(tzinfo=timezone.utc)
                    
                    if now < db_expires:
                        # Обновляем in-memory кеш из БД
                        self._token_cache[login] = (settings_db.access_token, db_expires)
                        if not api_login:
                            self.access_token = settings_db.access_token
                            self.token_expires_at = db_expires
                        logger.debug(f"Токен для {login[:4]}... восстановлен из БД")
                        return settings_db.access_token
            except Exception as e:
                logger.error(f"Ошибка чтения токена из БД: {e}")

            # 3. Если в БД нет или просрочен — запрашиваем новый
            masked_login = f"{login[:4]}...{login[-4:]}" if login and len(login) > 8 else "НЕКОРРЕКТНО"
            logger.info(f"Запрос НОВОГО токена iiko для логина: {masked_login}")

            try:
                response = await self.client.post(
                    f"{self.api_url}/api/1/access_token",
                    json={"apiLogin": login}
                )
                response.raise_for_status()
                data = response.json()
                token = data["token"]
                expires_at = now + timedelta(minutes=14)
                
                # Сохраняем в кеш и БД
                self._token_cache[login] = (token, expires_at)
                
                try:
                    def _update_db_token(t, e):
                        with Session(engine) as session:
                            s = session.exec(select(IikoSettings).where(IikoSettings.api_login == login)).first()
                            if s:
                                s.access_token = t
                                s.token_expires_at = e
                                session.add(s)
                                session.commit()
                    await asyncio.to_thread(_update_db_token, token, expires_at)
                except Exception as db_err:
                    logger.error(f"Не удалось сохранить токен в БД: {db_err}")

                # Обновляем основные поля если это "глобальный" логин
                if not api_login:
                    self.access_token = token
                    self.token_expires_at = expires_at

                return token
            except httpx.HTTPStatusError as e:
                try:
                    err_text = e.response.text
                except:
                    err_text = str(e)
                logger.error(f"Не удалось получить токен доступа: {err_text}")
                raise
            except Exception as e:
                logger.error(f"Критическая ошибка при получении токена iiko: {e}")
                raise

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        timeout: float = 30.0,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None,
        _is_retry: bool = False,
        _retry_count: int = 0,
        log_error: bool = True
    ) -> Any:
        """Универсальный метод для запросов к iiko API с авторизацией"""
        # Пытаемся получить актуальный api_login из БД если передана организация
        current_api_login = api_login
        if organization_id and not current_api_login:
            db_settings = await self._get_settings_by_org_id(organization_id)
            if db_settings and db_settings.api_login:
                current_api_login = db_settings.api_login
                
        token = await self._get_access_token(api_login=current_api_login)
        org_id = organization_id or self.organization_id
        
        # Если это плейсхолдер - игнорируем его
        if org_id and (org_id.startswith("your_") or "placeholder" in org_id.lower()):
            org_id = None

        # Подготовка данных (копия чтобы не менять оригинал)
        payload = json_data.copy() if json_data else {}

        # Если в payload есть organizationId или organizationIds - подменяем если передали organization_id
        if org_id:
            # Всегда стараемся добавлять оба варианта для совместимости с разными версиями iiko Cloud
            if "organizationId" in payload or any(k in endpoint for k in ["/by_id", "/create", "/nomenclature", "/stop_lists"]):
                payload["organizationId"] = org_id
            
            if "organizationIds" in payload or any(k in endpoint for k in [
                "/organizations", "/terminal_groups", "/payment_types", "/deliveries/order_types", 
                "/discounts", "/menu", "/stop_lists", "/by_delivery_date_and_status", "/employees", 
                "/shift", "/schedule", "/reports/olap"
            ]):
                if "organizationIds" not in payload or not isinstance(payload["organizationIds"], list):
                    payload["organizationIds"] = [org_id]
                elif not payload["organizationIds"]:
                    payload["organizationIds"] = [org_id]

        logger.debug(f"iiko request: {method} {endpoint} | Payload keys: {list(payload.keys()) if payload else 'None'}")
        
        # Проверка Cooling Period (если мы недавно получали 429 на этот эндпоинт)
        now = datetime.now(timezone.utc)
        if endpoint in self._cooling_endpoints:
            cooling_until = self._cooling_endpoints[endpoint]
            if now < cooling_until:
                wait_left = int((cooling_until - now).total_seconds())
                logger.warning(f"Endpoint {endpoint} is in Cooling Period. Skipping request. Wait {wait_left}s.")
                return {"status": "error", "error": "TOO_MANY_REQUESTS_COOLING", "message": f"Пожалуйста, подождите {wait_left} сек. перед повторной попыткой."}
            else:
                del self._cooling_endpoints[endpoint]

        # Проверка прав (если мы недавно получали 403 на этот эндпоинт)
        if endpoint in self._denied_endpoints:
            denied_until = self._denied_endpoints[endpoint]
            if now < denied_until:
                logger.debug(f"Endpoint {endpoint} is in Denied Period. Skipping request.")
                return {"status": "error", "error": "IIKO_RIGHTS_ERROR", "message": "Доступ к этому ресурсу ограничен в iiko Cloud (кэшировано на 1 час)."}
            else:
                del self._denied_endpoints[endpoint]

        try:
            response = await self.client.request(
                method,
                f"{self.api_url}{endpoint}",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
                timeout=timeout
            )
            
            # Принудительная установка кодировки UTF-8 для корректной обработки кириллицы
            if response.encoding is None or response.encoding.lower() == 'iso-8859-1':
                response.encoding = 'utf-8'

            # Обработка 429 (Too Many Requests) - Экспоненциальный бэкхофф + Cooling Period
            if response.status_code == 429:
                # Устанавливаем период охлаждения для этого эндпоинта
                self._cooling_endpoints[endpoint] = datetime.now(timezone.utc) + timedelta(seconds=self._cooling_duration)
                
                if _retry_count < 2: # Уменьшаем кол-во повторов для 429
                    wait_time = (2 ** _retry_count) * 15 # 15, 30 секунд
                    logger.warning(f"iiko API 429 Too Many Requests for {endpoint}. Waiting {wait_time}s before retry {_retry_count + 1}/2...")
                    await asyncio.sleep(wait_time)
                    return await self._request(
                        method, endpoint, json_data, timeout, 
                        current_api_login, organization_id, _is_retry=True,
                        _retry_count=_retry_count + 1,
                        log_error=log_error
                    )
                else:
                    logger.error(f"iiko API 429: Max retries reached for {endpoint}. Cooling period started.")
                    try:
                        return response.json()
                    except:
                        return {"error": "TOO_MANY_REQUESTS"}

            # Обработка 401 (Unauthorized) - пробуем обновить токен один раз
            if response.status_code == 401 and not _is_retry:
                # Если это заведомо эндпоинт, к которому может не быть доступа (например, смены), логируем тише
                is_sensitive = any(k in endpoint for k in ["/cashshifts/", "/staff/", "/report/"])
                if is_sensitive:
                    logger.debug(f"iiko API 401 Unauthorized for {endpoint}. Retrying with fresh token...")
                else:
                    logger.warning(f"iiko API 401 Unauthorized for {endpoint}. Retrying with fresh token...")
                    
                async with self._get_token_lock():
                    # Очищаем кеш для этого логина, чтобы принудительно получить новый токен
                    if current_api_login in self._token_cache:
                        del self._token_cache[current_api_login]
                    
                    # КРИТИЧЕСКИ ВАЖНО: Очищаем токен в БД, чтобы _get_access_token не взял его оттуда снова
                    try:
                        def _clear_db_token():
                            from app.core.database import Session, engine
                            with Session(engine) as session:
                                s = session.exec(select(IikoSettings).where(IikoSettings.api_login == current_api_login)).first()
                                if s:
                                    s.access_token = None
                                    s.token_expires_at = None
                                    session.add(s)
                                    session.commit()
                        await asyncio.to_thread(_clear_db_token)
                        logger.info(f"Токен для {current_api_login[:4]}... сброшен в БД после 401")
                    except Exception as db_err:
                        logger.error(f"Не удалось сбросить токен в БД: {db_err}")
                    
                    if not api_login:
                        self.access_token = None
                        self.token_expires_at = None
                        
                return await self._request(
                    method, endpoint, json_data, timeout, 
                    current_api_login, organization_id, _is_retry=True,
                    _retry_count=_retry_count,
                    log_error=log_error
                )

            if response.status_code >= 400:
                # Читаем тело ошибки для диагностики
                try:
                    body = response.text
                except:
                    body = "Could not read response body"
                
                if log_error:
                    # Специальное уведомление для ошибок прав (Rights)
                    if "is not allowed for this ApiLogin" in body or response.status_code == 403:
                        error_msg = f"ОШИБКА ПРАВ IIKO (403/401): Для API Login не разрешен доступ к {endpoint}. Body: {body}"
                        logger.error(error_msg)
                        # Добавляем в кэш отказов на 1 час
                        self._denied_endpoints[endpoint] = datetime.now(timezone.utc) + timedelta(seconds=self._denied_duration)
                        return {"status": "error", "error": "IIKO_RIGHTS_ERROR", "message": error_msg}
                    else:
                        logger.error(f"iiko API Error: {response.status_code} | URL: {endpoint} | Body: {body}")
                
                # Для 401, который не прошел ретрай, тоже возвращаем ошибку вместо исключения
                if response.status_code == 401:
                    return {"status": "error", "error": "UNAUTHORIZED", "message": "iiko API: Ошибка авторизации (401)"}
                    
                response.raise_for_status()
                
            if response.encoding is None or response.encoding.lower() == 'iso-8859-1':
                response.encoding = 'utf-8'
                
            return response.json()
        except (httpx.RequestError, httpx.TimeoutException) as e:
            # Обработка сетевых ошибок и таймаутов
            if _retry_count < 3:
                wait_time = (2 ** _retry_count) * 3
                logger.warning(f"iiko API Network Error ({type(e).__name__}) for {endpoint}. Waiting {wait_time}s before retry {_retry_count + 1}/3...")
                await asyncio.sleep(wait_time)
                return await self._request(
                    method, endpoint, json_data, timeout, 
                    current_api_login, organization_id, _is_retry=_is_retry,
                    _retry_count=_retry_count + 1,
                    log_error=log_error
                )
            logger.error(f"iiko API failed after 3 retries due to network error: {e}")
            raise e
        except Exception as e:
            if not isinstance(e, httpx.HTTPStatusError):
                logger.error(f"iiko API unexpected error for {endpoint}: {e}")
            raise e

    # =========================================================================
    # Проверка подключения
    # =========================================================================

    async def test_connection(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Проверка подключения к iiko API
        """
        try:
            token = await self._get_access_token(api_login=api_login)
            orgs = await self._request(
                "POST", 
                "/api/1/organizations", 
                {"organizationIds": [], "returnAdditionalInfo": False},
                api_login=api_login,
                organization_id=organization_id
            )
            return {
                "success": True,
                "token_valid": bool(token),
                "organizations": orgs.get("organizations", [])
            }
        except Exception as e:
            logger.error(f"Ошибка при проверке соединения с iiko: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # =========================================================================
    # Организация и справочники
    # =========================================================================

    async def get_organizations(
        self,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получение списка всех организаций"""
        data = await self._request(
            "POST", "/api/1/organizations", 
            {"organizationIds": [], "returnAdditionalInfo": True},
            api_login=api_login
        )
        return data.get("organizations", [])

    async def get_organization_info(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение информации о текущей организации"""
        org_id = organization_id or self.organization_id
        data = await self._request(
            "POST", "/api/1/organizations", 
            {"organizationIds": [org_id], "returnAdditionalInfo": True},
            api_login=api_login,
            organization_id=org_id
        )
        return data["organizations"][0] if data.get("organizations") else {}

    async def get_terminal_groups(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получение списка терминальных групп"""
        org_id = organization_id or self.organization_id
        data = await self._request(
            "POST", "/api/1/terminal_groups", 
            {"organizationIds": [org_id]},
            api_login=api_login,
            organization_id=org_id
        )
        groups = data.get("terminalGroups", [])
        result = []
        for org_group in groups:
            for item in org_group.get("items", []):
                result.append(item)
        return result

    async def get_terminal_groups_is_alive(
        self,
        terminal_group_ids: List[str],
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Проверка статуса 'жив ли' для терминальных групп (is_alive)"""
        org_id = organization_id or self.organization_id
        return await self._request(
            "POST", "/api/1/terminal_groups/is_alive", 
            {
                "organizationIds": [org_id],
                "terminalGroupIds": terminal_group_ids
            },
            api_login=api_login,
            organization_id=org_id
        )

    async def get_payment_types(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получение типов оплаты"""
        org_id = organization_id or self.organization_id
        logger.info(f"Запрос типов оплаты для организации {org_id}")
        data = await self._request(
            "POST", "/api/1/payment_types", 
            {"organizationIds": [org_id]},
            api_login=api_login,
            organization_id=org_id
        )
        types = data.get("paymentTypes", [])
        logger.info(f"Получено {len(types)} групп типов оплаты из iiko Cloud")
        result = []
        for org_types in types:
            items = org_types.get("items", [])
            logger.debug(f"Орг {org_types.get('organizationId')}: {len(items)} типов")
            for item in items:
                result.append(item)
        logger.info(f"Итого: обработано {len(result)} типов оплаты")
        return result

    async def get_order_types(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получение типов заказа"""
        org_id = organization_id or self.organization_id
        data = await self._request(
            "POST", "/api/1/deliveries/order_types", 
            {"organizationIds": [org_id]},
            api_login=api_login,
            organization_id=org_id
        )
        types = data.get("orderTypes", [])
        result = []
        for org_types in types:
            for item in org_types.get("items", []):
                result.append(item)
        return result

    async def get_price_categories(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получение списка ценовых категорий из iiko Cloud"""
        org_id = organization_id or self.organization_id
        data = await self._request(
            "POST", "/api/2/menu", 
            {"organizationIds": [org_id]},
            api_login=api_login,
            organization_id=org_id
        )
        return data.get("priceCategories", [])

    async def get_discount_types(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получение доступных типов скидок"""
        org_id = organization_id or self.organization_id
        data = await self._request(
            "POST", "/api/1/discounts", 
            {"organizationIds": [org_id]},
            api_login=api_login,
            organization_id=org_id
        )
        discounts = data.get("discounts", [])
        result = []
        for org_disc in discounts:
            for item in org_disc.get("items", []):
                result.append(item)
        return result

    async def get_stop_lists(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение стоп-листов для организации"""
        org_id = organization_id or self.organization_id
        res = await self._request(
            "POST", "/api/1/stop_lists", 
            {"organizationIds": [org_id]},
            api_login=api_login,
            organization_id=org_id
        )
        
        # Если iiko вернула список (бывает при передаче нескольких org_id, 
        # или из-за особенностей прокси), берем первый элемент или оборачиваем.
        if isinstance(res, list):
            logger.warning(f"iiko API returned list for stop_lists instead of dict. Taking first element.")
            return res[0] if res else {"terminalGroupStopLists": []}
            
        return res if isinstance(res, dict) else {"terminalGroupStopLists": []}

    # =========================================================================
    # Меню и номенклатура
    # =========================================================================

    async def get_nomenclature(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Получение номенклатуры (меню) из iiko
        Возвращает категории (groups) и товары (products)
        """
        org_id = organization_id or self.organization_id
        return await self._request(
            "POST", "/api/1/nomenclature", 
            {"organizationId": org_id},
            api_login=api_login,
            organization_id=org_id
        )

    async def get_menu_v2(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Получение меню через API v2 (/api/2/menu/by_id)
        Возвращает данные о внешних меню.
        """
        org_id = organization_id or self.organization_id
        # Сначала получаем список внешних меню
        menus = await self.get_external_menus(api_login=api_login, organization_id=org_id)
        if not menus:
            logger.warning(f"No external menus found for org {org_id}")
            return {"groups": [], "products": []}
            
        # Берем первое доступное меню
        menu_id = menus[0].get("id")
        logger.info(f"Using external menu {menu_id} for org {org_id}")
        return await self.get_external_menu_by_id(
            external_menu_id=menu_id, 
            api_login=api_login, 
            organization_id=org_id
        )

    async def get_delivery_restrictions(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение ограничений доставки (зоны, условия)"""
        org_id = organization_id or self.organization_id
        return await self._request(
            "POST", "/api/1/delivery_restrictions", 
            {"organizationIds": [org_id]},
            api_login=api_login,
            organization_id=org_id
        )

    async def get_external_menus(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение списка внешних меню
        """
        org_id = organization_id or self.organization_id
        data = await self._request(
            "POST", "/api/2/menu", 
            {"organizationIds": [org_id]},
            api_login=api_login,
            organization_id=org_id
        )
        return data.get("externalMenus", [])

    async def get_external_menu_by_id(
        self, 
        external_menu_id: str, 
        price_category_id: Optional[str] = None,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Получение конкретного внешнего меню по ID через API v2.
        
        Использует прямой HTTP-запрос (минуя _request) во избежание
        автодобавления 'organizationId' (без s), что вызывает ошибку 400.
        
        Если iiko возвращает ошибку 'Price category id is not correct',
        автоматически пытается использовать базовую категорию или находит 
        первую доступную в списке меню и повторяет запрос.
        """
        org_id = organization_id or self.organization_id
        token = await self._get_access_token(api_login=api_login)
        
        async def _do_raw_request(pcid: Optional[str] = None) -> httpx.Response:
            payload: Dict[str, Any] = {
                "externalMenuId": external_menu_id,
                "organizationIds": [org_id]
            }
            if pcid:
                payload["priceCategoryId"] = pcid
            
            logger.info(f"Запрос iiko меню ID={external_menu_id} (org={org_id}, priceCategoryId={pcid})")
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{self.api_url}/api/2/menu/by_id",
                    headers={"Authorization": f"Bearer {token}"},
                    json=payload
                )
            return resp

        # 1. Пробуем основной запрос
        response = await _do_raw_request(price_category_id)
        
        if response.status_code == 401:
            self.access_token = None
            self.token_expires_at = None
            token = await self._get_access_token(api_login=api_login)
            response = await _do_raw_request(price_category_id)
            
        # 2. Если 400 и ошибка в ценовой категории — пробуем авто-исправление
        if response.status_code == 400:
            try:
                err_body = response.json()
            except:
                err_body = {}
            
            if "Price category" in err_body.get("errorDescription", "") or err_body.get("error") == "EXTERNAL_MENU_DATA_MISSED":
                logger.warning(f"iiko требует priceCategoryId для меню {external_menu_id} (переданный PCID: {price_category_id}). Ответ: {err_body}. Пробуем авто-подбор...")
                
                # Сначала пробуем "нулевую" (базовую) категорию
                base_pcid = "00000000-0000-0000-0000-000000000000"
                if price_category_id != base_pcid:
                    logger.info(f"Пробуем базовую ценовую категорию: {base_pcid}")
                    response = await _do_raw_request(base_pcid)
                
                # Если всё еще 400 — запрашиваем список всех доступных ценовых категорий для этого меню
                if response.status_code == 400:
                    try:
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            menu_list_resp = await client.post(
                                f"{self.api_url}/api/2/menu",
                                headers={"Authorization": f"Bearer {token}"},
                                json={"organizationIds": [org_id]}
                            )
                        if menu_list_resp.status_code == 200:
                            menus_data = menu_list_resp.json()
                            # Ищем наше меню в списке
                            found_pcid = None
                            for menu in menus_data.get("externalMenus", []):
                                if str(menu.get("id")) == str(external_menu_id):
                                    price_cats = menu.get("priceCategories", [])
                                    if price_cats:
                                        found_pcid = price_cats[0].get("id") or price_cats[0].get("priceCategoryId")
                                        break
                            
                            # Если не нашли в меню, попробуем первую из общего списка priceCategories (если есть)
                            if not found_pcid and menus_data.get("priceCategories"):
                                found_pcid = menus_data["priceCategories"][0].get("id")

                            if found_pcid:
                                logger.info(f"Найдена подходящая категория: {found_pcid}. Повторяем запрос.")
                                response = await _do_raw_request(found_pcid)
                    except Exception as e:
                        logger.error(f"Ошибка при попытке авто-подбора ценовой категории: {e}")

        if response.status_code >= 400:
            logger.error(f"iiko /api/2/menu/by_id критическая ошибка {response.status_code}: {response.text}")
            response.raise_for_status()
            
        return response.json()




    # =========================================================================
    # Заказы
    # =========================================================================

    async def create_delivery_order(
        self,
        customer_name: str,
        customer_phone: str,
        address: str,
        items: List[Dict[str, Any]],
        comment: Optional[str] = None,
        payment_type_id: Optional[str] = None,
        payment_sum: Optional[float] = None,
        discount_info: Optional[Dict] = None,
        terminal_group_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Создание заказа доставки в iiko с retry-логикой

        При неудаче — повтор через 15 секунд (до 3 раз).
        """
        order_data: Dict[str, Any] = {
            "organizationId": self.organization_id,
            "order": {
                "customer": {
                    "name": customer_name,
                    "phone": customer_phone
                },
                "deliveryPoint": {
                    "address": {
                        "street": {
                            "name": address
                        }
                    }
                },
                "items": [
                    {
                        "productId": item["product_id"],
                        "amount": item["quantity"],
                        "price": float(item["price"])
                    }
                    for item in items
                ],
                "comment": comment or ""
            }
        }

        if terminal_group_id:
            order_data["terminalGroupId"] = terminal_group_id

        # Добавляем оплату
        if payment_type_id and payment_sum:
            order_data["order"]["payments"] = [{
                "paymentTypeKind": "Cash",
                "paymentTypeId": payment_type_id,
                "sum": payment_sum,
                "isProcessedExternally": False
            }]

        # Добавляем скидку
        if discount_info:
            order_data["order"]["discountsInfo"] = discount_info

        # Retry логика: до 3 попыток с интервалом 15 секунд
        last_error = None
        for attempt in range(3):
            try:
                result = await self._request(
                    "POST",
                    "/api/1/deliveries/create",
                    order_data,
                    timeout=30.0
                )
                return result
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Попытка создания заказа {attempt + 1}/3 не удалась: {e}"
                )
                if attempt < 2:
                    await asyncio.sleep(15)

        raise last_error

    async def get_order_status(
        self, 
        order_id: str,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение статуса заказа из iiko"""
        org_id = organization_id or self.organization_id
        data = await self._request(
            "POST", "/api/1/deliveries/by_id", 
            {
                "organizationId": org_id,
                "orderIds": [order_id]
            },
            api_login=api_login,
            organization_id=org_id
        )
        orders = data.get("orders", [])
        return orders[0] if orders else {}

    async def cancel_order(
        self, 
        order_id: str,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> bool:
        """Отмена заказа в iiko"""
        org_id = organization_id or self.organization_id
        try:
            await self._request(
                "POST", "/api/1/deliveries/cancel", 
                {
                    "organizationId": org_id,
                    "orderId": order_id
                },
                api_login=api_login,
                organization_id=org_id
            )
            return True
        except Exception:
            return False

    async def get_customer_orders_history(
        self,
        phone: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение истории заказов гостя по номеру телефона.
        Обычно iiko хранит детали заказов за последние 90 дней, но через 
        этот метод можно получить список и за более долгий период.
        """
        org_id = organization_id or self.organization_id
        date_format = "%Y-%m-%d %H:%M:%S.000"
        
        payload = {
            "phone": phone,
            "organizationIds": [org_id],
            "rowsCount": 200 # Максимально допустимое значение
        }
        
        if date_from:
            payload["deliveryDateFrom"] = date_from.strftime(date_format)
        if date_to:
            payload["deliveryDateTo"] = date_to.strftime(date_format)
            
        logger.info(f"Запрос истории заказов iiko для телефона: {phone}")
        
        if phone and not phone.startswith('+'):
            phone = f"+{phone}"
        
        payload["phone"] = phone
            
        data = await self._request(
            "POST",
            "/api/1/deliveries/history/by_delivery_date_and_phone",
            payload,
            api_login=api_login,
            organization_id=org_id
        )
        
        orders = []
        organizations_data = data.get("ordersByOrganizations", [])
        if organizations_data:
            for org_data in organizations_data:
                batch = org_data.get("orders") or org_data.get("items") or []
                orders.extend(batch)
        
        if not orders:
            orders = data.get("orders") or data.get("items") or []
            
        logger.info(f"Получено {len(orders)} заказов из истории iiko для {phone}")
        return orders

    async def get_orders_by_date(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None,
        log_error: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Получение заказов за заданный период.
        Используется для ручной синхронизации.
        """
        org_id = organization_id or self.organization_id
        
        # Инструмент iiko требует дату в формате yyyy-MM-dd HH:mm:ss.fff
        date_format = "%Y-%m-%d %H:%M:%S.000"
        
        # Только валидные статусы из перечисления DeliveryStatus
        valid_statuses = [
            "Unconfirmed", "WaitCooking", "ReadyForCooking", "CookingStarted", 
            "CookingCompleted", "Waiting", "OnWay", "Delivered", "Closed", "Cancelled"
        ]
        
        # Используем переданный диапазон без принудительного расширения, 
        # чтобы не вызывать ошибку TOO_MANY_DATA_REQUESTED.
        query_from = date_from.strftime(date_format)
        query_to = date_to.strftime(date_format)
        
        logger.info(f"Запрос заказов iiko Cloud: {query_from} - {query_to} (Орг: {org_id})")
        
        data = await self._request(
            "POST", 
            "/api/1/deliveries/by_delivery_date_and_status", 
            {
                "organizationIds": [org_id],
                "deliveryDateFrom": query_from,
                "deliveryDateTo": query_to,
                "statuses": valid_statuses
            },
            api_login=api_login,
            organization_id=org_id
        )
        
        # В Iiko Cloud API v2 заказы сгруппированы по организациям
        orders = []
        organizations_data = data.get("ordersByOrganizations", [])
        
        logger.debug(f"Raw Iiko response keys: {list(data.keys())}")
        if organizations_data:
            logger.info(f"Найдено {len(organizations_data)} организаций в ответе Cloud")
            for org_data in organizations_data:
                # В разных версиях API заказы могут быть в поле 'orders' или 'items'
                batch = org_data.get("orders") or org_data.get("items") or []
                logger.info(f"Орг {org_data.get('organizationId')}: {len(batch)} заказов (поле: {'orders' if org_data.get('orders') else 'items' if org_data.get('items') else 'empty'})")
                orders.extend(batch)
        
        # Если в ordersByOrganizations пусто, пробуем поле 'orders' или 'items' на верхнем уровне
        if not orders:
            orders = data.get("orders") or data.get("items") or []
            
        if not orders and log_error:
            # Отсутствие заказов за 2-часовой период - это абсолютно штатная ситуация (например, ночью или когда нет доставок).
            # Мы логируем это только как INFO или DEBUG, чтобы не засорять таблицу системных логов (system_logs).
            logger.info(f"Заказы отсутствуют в периоде {query_from} - {query_to} (Нормальное поведение)")
            if data.get("ordersByOrganizations") == []:
                 logger.debug("Поле ordersByOrganizations присутствует, но пустое.")
            
        logger.info(f"Итого получено заказов из Cloud: {len(orders)}")
        return orders

    async def update_webhooks(
        self,
        webhook_url: str,
        auth_token: str,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Обновление настроек вебхуков в iiko Cloud.
        Регистрирует URL и подписывается на события.
        """
        org_id = organization_id or self.organization_id
        payload = {
            "organizationId": org_id,
            "webHooksUri": webhook_url,
            "authToken": auth_token,
            "filter": {
                "eventType": [
                    "DeliveryOrderCreate", 
                    "DeliveryOrderUpdate", 
                    "DeliveryOrderStatusChanged", 
                    "CourierAssigned",
                    "StopListUpdate", 
                    "PersonalShift"
                ]
            }
        }
        
        logger.info(f"Обновление вебхуков iiko: URL={webhook_url}, Орг={org_id}")
        try:
            result = await self._request(
                "POST", "/api/1/webhooks/update", 
                payload,
                api_login=api_login,
                organization_id=org_id
            )
            logger.info(f"Вебхуки iiko успешно обновлены: {result}")
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Ошибка при обновлении вебхуков iiko: {e}")
            return {"success": False, "error": str(e)}

    async def get_active_orders(
        self,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение всех текущих активных заказов из iiko.
        """
        org_id = organization_id or self.organization_id
        now = datetime.utcnow()
        # iiko API limits the time span, so we use the last 24 hours
        date_from = (now - timedelta(days=1)).strftime("%Y-%m-%d 00:00:00.000")
        date_to = (now + timedelta(days=1)).strftime("%Y-%m-%d 23:59:59.000")
        
        valid_statuses = [
            "Unconfirmed", "WaitCooking", "ReadyForCooking", 
            "CookingStarted", "CookingCompleted", "Waiting", "OnWay"
        ]
        
        data = await self._request(
            "POST", "/api/1/deliveries/by_delivery_date_and_status", 
            {
                "organizationIds": [org_id],
                "deliveryDateFrom": date_from,
                "deliveryDateTo": date_to,
                "statuses": valid_statuses
            },
            api_login=api_login,
            organization_id=org_id
        )
        
        # В Iiko Cloud API v2 заказы сгруппированы по организациям
        orders = []
        organizations_data = data.get("ordersByOrganizations", [])
        
        if organizations_data:
            for org_data in organizations_data:
                orders.extend(org_data.get("orders", []))
        else:
            orders = data.get("orders", [])
            
        logger.info(f"Активных заказов получено: {len(orders)}")
        return orders

    # =========================================================================
    # Сотрудники и смены
    # =========================================================================

    async def get_employees(
        self,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение списка сотрудников организации. 
        Сначала пробуем общий список, если нет прав - откатываемся на список курьеров.
        """
        org_id = organization_id or self.organization_id
        data = None
        used_fallback = False
        
        try:
            # 1. Пробуем получить полный список (требует прав на Staff Management)
            data = await self._request(
                "POST", "/api/1/employees", 
                {"organizationIds": [org_id]},
                api_login=api_login,
                organization_id=org_id,
                log_error=False
            )
        except httpx.HTTPStatusError as e:
            # Если 401 или 403 - значит нет прав на этот эндпоинт, пробуем курьеров
            if e.response.status_code in [401, 403]:
                logger.warning(f"Доступ к /api/1/employees ограничен (401/403). Переключение на /couriers.")
                used_fallback = True
                data = await self._request(
                    "POST", "/api/1/employees/couriers", 
                    {"organizationIds": [org_id]},
                    api_login=api_login,
                    organization_id=org_id
                )
            else:
                raise e
        
        employees_list = []
        # Ответ имеет структуру: {"employees": [{"organizationId": "...", "items": [{...}]}]}
        for org_data in data.get("employees", []):
            if org_data.get("organizationId") == org_id:
                for item in org_data.get("items", []):
                    # Универсальное получение имени (displayName или firstName + lastName)
                    name = item.get("displayName")
                    if not name or name == "": # Обработка битых символов если есть
                        fname = item.get("firstName") or ""
                        lname = item.get("lastName") or ""
                        name = f"{fname} {lname}".strip() or "Unnamed"
                    
                    # Извлекаем роли (в /couriers их нет)
                    role_id = "Courier" if used_fallback else None
                    roles = item.get("roles", [])
                    if roles:
                        role_id = roles[0].get("name") or roles[0].get("id")

                    employees_list.append({
                        "id": item.get("id"),
                        "name": name,
                        "phone": item.get("phone"), 
                        "roleId": role_id or "Employee",
                        "deleted": item.get("isDeleted", False)
                    })
        return employees_list

    async def get_courier_active_locations(
        self,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение активных локаций курьеров"""
        org_id = organization_id or self.organization_id
        return await self._request(
            "POST", "/api/1/couriers/active_locations", 
            {"organizationIds": [org_id]},
            api_login=api_login,
            organization_id=org_id
        )

    async def get_restaurant_sections(
        self,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение секций ресторана (залов)"""
        org_id = organization_id or self.organization_id
        return await self._request(
            "POST", "/api/1/reserve/available_restaurant_sections", 
            {"organizationIds": [org_id]},
            api_login=api_login,
            organization_id=org_id
        )

    async def get_max_revision(
        self, 
        organization_id: Optional[str] = None, 
        api_login: Optional[str] = None
    ) -> int:
        org_id = organization_id or self.organization_id
        now = datetime.now()
        # Запрашиваем за последние 2 часа, чтобы получить актуальный maxRevision
        date_from = now - timedelta(hours=2)
        date_to = now + timedelta(minutes=10)
        
        try:
            # Инструмент iiko требует дату в формате yyyy-MM-dd HH:mm:ss.fff
            date_format = "%Y-%m-%d %H:%M:%S.000"
            query_from = date_from.strftime(date_format)
            query_to = date_to.strftime(date_format)
            
            logger.info(f"Bootstrapping max revision for org {org_id} via time-based query ({query_from} - {query_to})...")
            
            # Мы вызываем by_delivery_date_and_status, потому что он возвращает maxRevision
            # и не требует startRevision (позволяет избежать 400 TOO_OLD_REVISION)
            data = await self._request(
                "POST", 
                "/api/1/deliveries/by_delivery_date_and_status", 
                {
                    "organizationIds": [org_id],
                    "deliveryDateFrom": query_from,
                    "deliveryDateTo": query_to
                },
                api_login=api_login,
                organization_id=org_id,
                log_error=True
            )
            
            max_rev = data.get("maxRevision", 0)
            if max_rev > 0:
                logger.info(f"Successfully bootstrapped max revision: {max_rev} for org {org_id}")
            else:
                logger.warning(f"Got max revision 0 for org {org_id}. This might be normal if there are no orders.")
                
            return max_rev
            
        except Exception as e:
            logger.error(f"Failed to bootstrap max revision for org {org_id}: {e}")
            return 0
    async def get_deliveries_by_revision(
        self,
        organization_id: Optional[str] = None,
        initial_revision: int = 0,
        api_login: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение доставок по ревизиям"""
        org_id = organization_id or self.organization_id
        data = await self._request(
            "POST", "/api/1/deliveries/by_revision", 
            {
                "organizationIds": [org_id],
                "startRevision": initial_revision
            },
            api_login=api_login,
            organization_id=org_id
        )
        
        # В новых версиях API заказы могут быть в ordersByOrganizations
        if data and "ordersByOrganizations" in data and not data.get("orders"):
            all_orders = []
            for org_item in data["ordersByOrganizations"]:
                all_orders.extend(org_item.get("orders", []))
            data["orders"] = all_orders
            
        return data

    async def get_shifts(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение списка смен за указанный период (iiko API)
        """
        org_id = organization_id or self.organization_id
        date_format = "%Y-%m-%d %H:%M:%S.000"
        
        try:
            data = await self._request(
                "POST", "/api/1/employees/shift", 
                {
                    "organizationIds": [org_id],
                    "dateFrom": date_from.strftime(date_format),
                    "dateTo": date_to.strftime(date_format)
                },
                api_login=api_login,
                organization_id=org_id
            )
            return data.get("shifts", [])
        except Exception as e:
            logger.error(f"Ошибка при получении смен: {e}")
            return []

    async def get_schedules(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение графика смен (запланированных) за указанный период (iiko API)
        """
        org_id = organization_id or self.organization_id
        date_format = "%Y-%m-%d %H:%M:%S.000"
        
        try:
            data = await self._request(
                "POST", "/api/1/employees/schedule", 
                {
                    "organizationIds": [org_id],
                    "from": date_from.strftime(date_format),
                    "to": date_to.strftime(date_format)
                },
                api_login=api_login,
                organization_id=org_id
            )
            # Ответ обычно содержит список расписаний для разных групп/организаций
            # Мы возвращаем плоский список всех записей графика
            schedules = []
            for org_schedule in data.get("schedules", []):
                schedules.extend(org_schedule.get("items", []))
            return schedules
        except Exception as e:
            logger.error(f"Ошибка при получении графиков: {e}")
            return []


    async def get_customer_balance(
        self,
        phone: str,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение баланса бонусов клиента"""
        customer = await self.get_customer_info(
            phone,
            api_login=api_login,
            organization_id=organization_id
        )
        if customer.get("found") is False:
            return {"balance": 0, "found": False}
        return {
            "balance": customer.get("walletBalances", [{}])[0].get("balance", 0)
                if customer.get("walletBalances") else 0,
            "found": True,
            "name": customer.get("name", "")
        }


    async def get_order_by_id(
        self,
        order_id: str,
        organization_id: str,
        api_login: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Получить детальную информацию о заказе по его ID"""
        org_id = organization_id or self.organization_id
        payload = {
            "organizationId": org_id,
            "orderIds": [order_id]
        }
        # В iiko Cloud API v1 эндпоинт для получения заказов по ID: /api/1/deliveries/by_id
        res = await self._request(
            "POST", "/api/1/deliveries/by_id",
            payload,
            api_login=api_login,
            organization_id=org_id
        )
        
        orders = []
        # Проверяем новую структуру v2
        if res and res.get("ordersByOrganizations"):
            for org_data in res["ordersByOrganizations"]:
                orders.extend(org_data.get("orders", []))
        
        # Если пусто, пробуем старую структуру v1
        if not orders and res:
            orders = res.get("orders", [])

        if orders:
            return orders[0]
        return None

    def get_public_url(self, request_url: Optional[str] = None) -> str:
        """
        Определяет текущий публичный URL сайта.
        Приоритет: 1. Явный URL из запроса 2. APP_PUBLIC_URL из конфига 3. Значение из БД
        """
        # 1. Сначала проверяем APP_PUBLIC_URL из .env
        env_url = settings.APP_PUBLIC_URL
        if env_url and ("your-public-url" in env_url or "ngrok" in env_url):
            env_url = None
            
        # 2. Если в .env пусто, пробуем URL из запроса
        req_url = request_url
        
        # Фильтрация: если URL содержит локальный IP, он нам не подходит для iiko
        def is_local(u):
            if not u: return True
            return "192.168." in u or "127.0.0.1" in u or "localhost" in u or "172." in u or "10." in u
            
        final_url = env_url
        source = "env"
        
        if not final_url or is_local(final_url):
            if req_url and not is_local(req_url):
                final_url = req_url
                source = "request"
        
        # 3. Если всё еще ничего нет, пробуем из БД
        if not final_url or is_local(final_url):
            from app.core.database import SessionLocal
            from app.models.iiko_settings import IikoSettings
            with SessionLocal() as db:
                db_settings = db.query(IikoSettings).first()
                if db_settings and db_settings.webhook_url and not is_local(db_settings.webhook_url):
                    from urllib.parse import urlparse
                    parsed = urlparse(db_settings.webhook_url)
                    final_url = f"{parsed.scheme}://{parsed.netloc}"
                    source = "db"
        
        # 4. Хардкод-фоллбэк для продакшена (vezuroll.ru)
        if not final_url or is_local(final_url):
            final_url = "https://vezuroll.ru"
            source = "hardcoded-fallback"
            
        logger.info(f"Determined public URL: {final_url} (source: {source}, env: {settings.APP_PUBLIC_URL}, req: {request_url})")
        return final_url


    # =========================================================================
    # Вебхуки
    # =========================================================================

    async def get_webhook_settings(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение текущих настроек вебхуков из iiko Cloud"""
        org_id = organization_id or self.organization_id
        try:
            return await self._request(
                "POST", "/api/1/webhooks/settings",
                {"organizationId": org_id},
                api_login=api_login,
                organization_id=org_id
            )
        except Exception as e:
            logger.error(f"Error getting iiko webhook settings: {e}")
            raise e

    async def update_webhook_settings(
        self,
        webhook_url: str,
        auth_token: Optional[str] = None,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Обновление настроек вебхуков. Применяет защиту от 429 (Too Many Requests),
        проверяя, нужно ли вообще обновить настройки перед отправкой.
        """
        org_id = organization_id or self.organization_id
        
        # Защита от 429: проверим, может быть настройки уже установлены те, что нужно?
        try:
            current = await self.get_webhook_settings(api_login=api_login, organization_id=org_id)
            if current:
                current_uri = current.get("webHooksUri")
                current_token = current.get("authToken")
                
                # Если URL и Токен уже совпадают - не мучаем iiko API (защита от 429)
                if current_uri == webhook_url and (not auth_token or current_token == auth_token):
                    logger.info(f"[iiko_service] Webhook settings (URI & Token) already match. Skipping update to avoid 429.")
                    # Возвращаем структуру, похожую на успешный ответ iiko, чтобы вызывающий код (register_webhook) мог продолжить
                    if "correlationId" not in current:
                        current["correlationId"] = "already-synced"
                    return current
        except Exception as e:
            logger.warning(f"[iiko_service] get_webhook_settings failed (possibly 429 too): {e}")

        payload = {
            "organizationId": str(org_id),
            "webHooksUri": webhook_url,
            "webHooksFilter": {
                "deliveryOrderFilter": {
                    "orderStatuses": [
                        "Unconfirmed", "WaitCooking", "ReadyForCooking", 
                        "CookingStarted", "CookingCompleted", "Waiting", 
                        "OnWay", "Delivered", "Closed", "Cancelled"
                    ],
                    "errors": True
                }
                # Убрали второстепенные фильтры для теста стабильности 400 ошибки
            }
        }
        if auth_token:
            payload["authToken"] = auth_token

        logger.info(f"[iiko_service] Registering webhook at {webhook_url} for org {org_id}")
        # Логируем payload как INFO для отладки
        logger.info(f"[iiko_service] Webhook payload: {json.dumps(payload, ensure_ascii=False)}")

        # Выполняем запрос через универсальный метод _request
        try:
            return await self._request(
                "POST", "/api/1/webhooks/update_settings", 
                payload,
                api_login=api_login,
                organization_id=org_id,
                log_error=True
            )
        except Exception as e:
            logger.error(f"[iiko_service] update_webhook_settings HTTP error: {e}")
            raise e

    async def auto_register_webhook(self,
        session: Optional[Session] = None,
        base_url: Optional[str] = None,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None,
        request_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Автоматическая регистрация вебхука:
        1. Генерация безопасного токена.
        2. Определение URL (используя get_public_url).
        3. Регистрация в iiko Cloud.
        4. Сохранение в БД.
        """
        try:
            # Определяем итоговый базовый URL через общую логику
            public_url = self.get_public_url(request_url or base_url)
            
            # Формируем полный путь к вебхуку
            webhook_path = "/api/v1/webhooks/iiko"
            url = f"{public_url.rstrip('/')}{webhook_path}"
            
            logger.info(f"[iiko_service] Starting auto-registration for: {url}")
            
            # Генерация токена
            auth_token = secrets.token_hex(16)
            
            # Регистрация в iiko
            result = await self.update_webhook_settings(
                webhook_url=url,
                auth_token=auth_token,
                api_login=api_login,
                organization_id=organization_id
            )
            
            # Проверяем успешность (iiko возвращает correlationId при успехе)
            is_success = bool(result.get("correlationId"))
            
            # Сохранение в БД
            if is_success:
                # Если сессия не передана, создаем свою временную
                if not session:
                    from app.core.database import SessionLocal
                    with SessionLocal() as db:
                        self._save_webhook_to_db(db, url, auth_token)
                else:
                    self._save_webhook_to_db(session, url, auth_token)
                
                return {
                    "success": True,
                    "webhook_url": url,
                    "auth_token": auth_token,
                    "iiko_response": result
                }
            else:
                error_data = result if isinstance(result, dict) else {}
                error_msg = error_data.get('message', 'iiko Cloud API не вернул ID подтверждения. Проверьте настройки авторизации.')
                
                # Специальная обработка для Cooling Period
                if error_data.get('error') == 'TOO_MANY_REQUESTS_COOLING':
                    error_msg = f"iiko API: Превышен лимит запросов. {error_msg}"
                
                logger.error(f"[iiko_service] Webhook registration failed: {json.dumps(result, ensure_ascii=False)}")
                return {
                    "success": False,
                    "error": error_msg,
                    "iiko_response": result
                }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[iiko_service] Critical error in auto_register_webhook: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "webhook_url": locals().get('url'),
                "auth_token": locals().get('auth_token')
            }

    def _save_webhook_to_db(self, db, url: str, token: str):
        """Вспомогательный метод для сохранения настроек вебхука в БД"""
        from app.models.iiko_settings import IikoSettings
        try:
            db_settings = db.query(IikoSettings).first()
            if db_settings:
                logger.info(f"Saving webhook settings to DB: {url}")
                db_settings.webhook_url = url
                db_settings.webhook_auth_token = token
                db.commit()
            else:
                logger.warning("No iiko settings found in DB to save webhook")
        except Exception as e:
            logger.error(f"Failed to save webhook settings to DB: {e}")
            db.rollback()

    # =========================================================================
    # iiko Card (Loyalty)
    # =========================================================================

    async def get_customer_info(
        self,
        phone: Optional[str] = None,
        customer_id: Optional[str] = None,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение информации о клиенте по номеру телефона или ID (iiko Card)"""
        org_id = organization_id or self.organization_id
        
        payload = {"organizationId": org_id}
        
        if customer_id:
            payload["type"] = "id"
            payload["id"] = customer_id
        elif phone:
            if not phone.startswith('+'):
                phone = f"+{phone}"
            payload["type"] = "phone"
            payload["phone"] = phone
        else:
            raise ValueError("Either phone or customer_id must be provided")
            
        try:
            return await self._request(
                "POST", "/api/1/loyalty/iiko/customer/info", 
                payload,
                api_login=api_login,
                organization_id=org_id,
                log_error=False  # Не логируем 400 ошибки как ERROR здесь
            )
        except httpx.HTTPStatusError as e:
            # Если клиент не найден - это штатная ситуация для новых гостей
            if e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    if error_data.get("code") in ["Transport_WrongCustomerNumber", "Validation_IncorrectPhone"]:
                        logger.info(f"Customer with phone {phone} not found in iiko Loyalty (Expected for new users)")
                        return {"found": False, "walletBalances": [], "id": None}
                except:
                    pass
            logger.error(f"Error getting customer info from iiko Card: {e.response.text}")
            return {"found": False, "walletBalances": [], "id": None}
        except Exception as e:
            logger.error(f"Unexpected error getting customer info from iiko Card: {e}")
            return {"found": False, "walletBalances": [], "id": None}

    async def get_customers(
        self,
        skip: int = 0,
        take: int = 50,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение списка клиентов (iiko Card)"""
        org_id = organization_id or self.organization_id
        return await self._request(
            "POST", "/api/1/loyalty/iiko/get_customers",
            {
                "organizationId": org_id,
                "skip": skip,
                "take": take
            },
            api_login=api_login,
            organization_id=org_id
        )


    async def add_customer_balance(
        self,
        customer_id: str,
        wallet_id: str,
        amount: float,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None,
        comment: str = "Начисление за активность"
    ) -> bool:
        """Начисление или списание баллов на кошелек клиента"""
        org_id = organization_id or self.organization_id
        
        # Определяем эндпоинт в зависимости от знака суммы
        endpoint = "/api/1/loyalty/iiko/customer/wallet/topup"
        if amount < 0:
            endpoint = "/api/1/loyalty/iiko/customer/wallet/chargeoff"
            amount = abs(amount) # Сумма в запросе должна быть положительной
            
        try:
            await self._request(
                "POST", endpoint, 
                {
                    "organizationId": org_id,
                    "customerId": customer_id,
                    "walletId": wallet_id,
                    "sum": amount,
                    "comment": comment
                },
                api_login=api_login,
                organization_id=org_id
            )
            return True
        except httpx.HTTPStatusError as e:
            # Пытаемся извлечь детальную ошибку из тела ответа iiko
            try:
                error_body = e.response.json()
                error_detail = error_body.get("errorDescription") or error_body.get("message") or e.response.text
            except Exception:
                error_detail = e.response.text or str(e)
            
            logger.error(f"iiko balance update failed ({endpoint}): {error_detail}")
            raise ValueError(f"iiko API error: {error_detail}")
        except Exception as e:
            logger.error(f"Error adjusting customer balance ({endpoint}): {e}")
            raise e
            
    async def create_or_update_customer(
        self,
        customer_data: Dict[str, Any],
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Создание или обновление клиента в iiko Cloud"""
        org_id = organization_id or self.organization_id
        
        # Очищаем данные клиента от None значений
        clean_customer_data = {k: v for k, v in customer_data.items() if v is not None}
        
        # iiko Cloud expects a FLAT structure for create_or_update_customer
        # organizationId should be at the top level alongside customer fields
        payload = {
            "organizationId": org_id,
            **clean_customer_data
        }
        
        try:
            return await self._request(
                "POST", "/api/1/loyalty/iiko/customer/create_or_update",
                payload,
                api_login=api_login,
                organization_id=org_id
            )
        except Exception as e:
            # При ошибке 400 логируем payload для отладки
            logger.error(f"iiko create_or_update failed. Payload: {payload}")
            raise e

    async def get_customer_categories(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение категорий гостей"""
        org_id = organization_id or self.organization_id
        return await self._request(
            "POST", "/api/1/loyalty/iiko/customer_category",
            {"organizationId": org_id},
            api_login=api_login,
            organization_id=org_id
        )

    async def add_customer_category(
        self,
        customer_id: str,
        category_id: str,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Добавление категории гостю"""
        org_id = organization_id or self.organization_id
        return await self._request(
            "POST", "/api/1/loyalty/iiko/customer_category/add",
            {
                "customerId": customer_id,
                "categoryId": category_id,
                "organizationId": org_id
            },
            organization_id=org_id
        )

    async def remove_customer_category(
        self,
        customer_id: str,
        category_id: str,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Удаление категории у гостя"""
        org_id = organization_id or self.organization_id
        return await self._request(
            "POST", "/api/1/loyalty/iiko/customer_category/remove",
            {
                "customerId": customer_id,
                "categoryId": category_id,
                "organizationId": org_id
            },
            organization_id=org_id
        )

    async def get_loyalty_programs(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение списка программ лояльности"""
        org_id = organization_id or self.organization_id
        return await self._request(
            "POST", "/api/1/loyalty/iiko/program",
            {"organizationId": org_id},
            api_login=api_login,
            organization_id=org_id
        )

    async def get_loyalty_coupons_series(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение списка серий купонов"""
        org_id = organization_id or self.organization_id
        return await self._request(
            "POST", "/api/1/loyalty/iiko/coupons/series",
            {"organizationId": org_id},
            api_login=api_login,
            organization_id=org_id
        )

    async def get_loyalty_manual_conditions(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение ручных условий лояльности"""
        org_id = organization_id or self.organization_id
        return await self._request(
            "POST", "/api/1/loyalty/iiko/manual_condition",
            {"organizationId": org_id},
            api_login=api_login,
            organization_id=org_id
        )

    async def get_customer_bonus_history(
        self,
        customer_id: str,
        date_from: str,
        date_to: Optional[str] = None,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение истории транзакций по бонусам гостя"""
        org_id = organization_id or self.organization_id
        # iiko API требует строгий формат ISO с миллисекундами: YYYY-MM-DD HH:mm:ss.SSS
        date_format = "%Y-%m-%d %H:%M:%S.000"
        
        # Обработка date_from (может прийти как ГГГГ-ММ-ДД или ГГГГ-ММ-ДД ЧЧ:ММ:СС)
        try:
            if isinstance(date_from, str):
                if len(date_from) == 10: # ГГГГ-ММ-ДД
                    dt_from = datetime.strptime(date_from, "%Y-%m-%d")
                else:
                    # Пытаемся распарсить как есть и переформатировать
                    dt_from = datetime.fromisoformat(date_from.replace(" ", "T"))
                date_from = dt_from.strftime(date_format)
            elif isinstance(date_from, datetime):
                date_from = date_from.strftime(date_format)
        except Exception as e:
            logger.warning(f"Failed to parse date_from '{date_from}': {e}. Using as is.")

        if not date_to:
            date_to = datetime.now().strftime(date_format)
        else:
            try:
                if isinstance(date_to, str):
                    dt_to = datetime.fromisoformat(date_to.replace(" ", "T"))
                    date_to = dt_to.strftime(date_format)
                elif isinstance(date_to, datetime):
                    date_to = date_to.strftime(date_format)
            except:
                pass
            
        payload = {
            "organizationId": org_id,
            "customerId": customer_id,
            "dateFrom": date_from,
            "dateTo": date_to,
            "pageNumber": 0,
            "pageSize": 100
        }
        
        try:
            return await self._request(
                "POST", "/api/1/loyalty/iiko/customer/transactions/by_date",
                payload,
                api_login=api_login,
                organization_id=org_id,
                log_error=False # Не спамим ERROR при неверных датах или клиентах
            )
        except httpx.HTTPStatusError as e:
            logger.warning(f"iiko API bonus history error: {e.response.status_code} | {e.response.text}")
            return {"transactions": []}
        except Exception as e:
            logger.error(f"Unexpected error fetching bonus history: {e}")
            return {"transactions": []}

    async def sync_full_customer_data(
        self,
        phone: str,
        session: Session,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Комплексная синхронизация всех данных гостя:
        1. Профиль и баланс (Cloud API)
        2. История бонусов (Cloud API)
        3. Аналитика (Server API OLAP)
        4. История заказов (Server API OLAP)
        """
        org_id = organization_id or self.organization_id
        
        # 1. Получаем базовую инфо (профиль, категории, баланс)
        info_task = self.get_customer_info(phone, organization_id=org_id)
        
        # 2. Аналитика OLAP (LTV, средний чек и т.д.)
        analytics_task = self.get_customer_analytics_olap(phone, session, organization_id=org_id)
        
        # 3. Список заказов из OLAP
        orders_task = self.get_customer_order_history_olap(phone, session, organization_id=org_id)
        
        # Выполняем параллельно основные запросы
        info, analytics, orders_olap = await asyncio.gather(
            info_task, analytics_task, orders_task, 
            return_exceptions=True
        )
        
        # Обработка ошибок в тасках
        if isinstance(info, Exception):
            logger.error(f"Full Sync: info_task failed: {info}")
            info = {"found": False}
        if isinstance(analytics, Exception):
            logger.warning(f"Full Sync: analytics_task failed: {analytics}")
            analytics = {"error": str(analytics)}
        if isinstance(orders_olap, Exception):
            logger.warning(f"Full Sync: orders_task failed: {orders_olap}")
            orders_olap = []

        # 4. Если гость найден, подтягиваем историю бонусов (требует customerId из info)
        bonus_history = {"transactions": []}
        customer_id = info.get("id")
        if customer_id:
            date_from = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S.000")
            try:
                bonus_history = await self.get_customer_bonus_history(
                    customer_id=customer_id,
                    date_from=date_from,
                    organization_id=org_id
                )
            except Exception as e:
                logger.error(f"Full Sync: bonus_history failed: {e}")

        return {
            "info": info,
            "analytics": analytics,
            "orders": orders_olap,
            "bonus_history": bonus_history.get("transactions", []),
            "sync_at": datetime.now().isoformat()
        }

    # =========================================================================
    # iiko Resto (Office API) - Расширенные данные
    # =========================================================================

    async def get_order_details_resto(
        self,
        order_id: str,
        resto_url: Optional[str] = None,
        resto_login: Optional[str] = None,
        resto_password: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение детальной информации о заказе из iiko Resto (Office)"""
        # Используем эндпоинт /deliveries/by_id или аналогичный в Office API
        # В Office API часто используется XML.
        try:
            data = await self._resto_request(
                "GET", f"/deliveries/by_id?id={order_id}", 
                resto_url=resto_url,
                resto_login=resto_login,
                resto_password=resto_password
            )
            # Если пришел XML, в _resto_request он превратится в строку.
            # Для простоты пока возвращаем как есть, парсинг будет в вызывающем коде или здесь.
            return data if isinstance(data, dict) else {"raw": data}
        except Exception as e:
            logger.error(f"Error getting order details from Resto: {e}")
            return {}

    # =========================================================================
    # OLAP Отчеты
    # =========================================================================

    async def get_organization_report(
        self,
        organization_id: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Формирует расширенный отчет по организации для дашборда (Dashboard).
        Объединяет данные о терминалах, заказах и OLAP-статистике.
        """
        from datetime import time
        import pytz
        import asyncio
        from app.core.database import get_session_sync
        from app.core.datetime_utils import get_tz_name
        
        # 0. Попытка получить из кеша (увеличиваем TTL до 10 минут)
        cache_key = f"org_report_{organization_id}_{date_from}_{date_to}"
        if settings.CACHE_ENABLED:
            try:
                cached_data = await redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as ce:
                logger.warning(f"Cache read error: {ce}")
        
        # 1. Парсинг дат и часовой пояс
        with get_session_sync() as db:
            tz_name = get_tz_name(db)
        
        tz = pytz.timezone(tz_name)
        if not date_from:
            dt_from = datetime.combine(datetime.now(tz).date(), time.min).replace(tzinfo=tz)
        else:
            try: dt_from = datetime.fromisoformat(date_from.replace(" ", "T"))
            except: dt_from = datetime.now(tz)
            
        if not date_to:
            dt_to = datetime.combine(datetime.now(tz).date(), time.max).replace(tzinfo=tz)
        else:
            try: dt_to = datetime.fromisoformat(date_to.replace(" ", "T"))
            except: dt_to = datetime.now(tz)

        # 2. Подготовка функций-оберток для сырых данных
        async def fetch_tg():
            try:
                raw = await self._request("POST", "/api/1/terminal_groups", {"organizationIds": [organization_id]}, organization_id=organization_id)
                return {"success": True, "data": raw, "cache": False, "cacheTime": False}
            except Exception as e:
                return {"success": False, "error": str(e)}

        async def fetch_ts(tg_ids):
            if not tg_ids: return {"success": True, "data": {"isAliveStatus": []}}
            try:
                raw = await self._request("POST", "/api/1/terminal_groups/is_alive", {"organizationIds": [organization_id], "terminalGroupIds": tg_ids}, organization_id=organization_id)
                return {"success": True, "data": raw, "cache": False, "cacheTime": False}
            except Exception as e:
                return {"success": False, "error": str(e)}

        async def fetch_orders_as_revision(dt_f, dt_t):
            try:
                # Получаем заказы за период (это надежнее чем by_revision с 0)
                orders = await self.get_orders_by_date(dt_f, dt_t, organization_id)
                # Формируем структуру как в by_revision
                return {
                    "success": True,
                    "data": {
                        "correlationId": "simulated",
                        "maxRevision": 0,
                        "ordersByOrganizations": [
                            {
                                "organizationId": organization_id,
                                "items": orders
                            }
                        ]
                    },
                    "cache": False,
                    "cacheTime": None
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

        async def fetch_employees():
            try:
                raw = await self._request("POST", "/api/1/employees", {"organizationIds": [organization_id]}, organization_id=organization_id)
                return {"success": True, "data": raw, "cache": False, "cacheTime": None}
            except Exception as e:
                # Если 401/403 (права) или любая другая ошибка, пробуем /couriers (Cloud) или Resto API
                logger.info(f"Cloud API employees failed ({e}), trying Resto API fallback...")
                try:
                    # Попытка через Resto API (Office)
                    resto_emps = await self.get_resto_employees(organization_id=organization_id)
                    if resto_emps:
                        # Приводим к формату Cloud API для совместимости с парсером ниже
                        return {"success": True, "data": {"employees": resto_emps}, "cache": False, "source": "resto"}
                except Exception as resto_e:
                    logger.warning(f"Resto API employees fallback also failed: {resto_e}")

                # Если Resto не помог, пробуем /couriers как последний шанс (иногда на них права есть)
                try:
                    raw = await self._request("POST", "/api/1/couriers", {"organizationIds": [organization_id]}, organization_id=organization_id)
                    return {"success": True, "data": raw, "cache": False, "cacheTime": None}
                except Exception as e2:
                    return {"success": False, "error": f"Employees: {e}, Couriers: {e2}"}

        async def fetch_courier_locations():
            try:
                raw = await self._request("POST", "/api/1/couriers/active_locations", {"organizationIds": [organization_id]}, organization_id=organization_id)
                return {"success": True, "data": raw, "cache": False, "cacheTime": None}
            except Exception as e:
                # Для локаций курьеров в Resto API нет прямого эквивалента в одном методе,
                # поэтому просто возвращаем пустой успех, чтобы не валить весь отчет
                logger.warning(f"Courier locations failed: {e}. Skipping locations data.")
                return {"success": True, "data": {"locations": []}, "error": str(e)}

        async def fetch_sections(tg_ids):
            try:
                raw = await self._request("POST", "/api/1/reserve/available_restaurant_sections", {"organizationIds": [organization_id], "terminalGroupIds": tg_ids}, organization_id=organization_id)
                return {"success": True, "data": raw, "cache": False, "cacheTime": False}
            except Exception as e:
                return {"success": False, "error": str(e)}

        # 3. Выполнение
        tg_res = await fetch_tg()
        tg_ids = []
        if tg_res.get("success") and "data" in tg_res:
            for org_tg in tg_res["data"].get("terminalGroups", []):
                for item in org_tg.get("items", []):
                    if item.get("id"): tg_ids.append(item["id"])

        results = await asyncio.gather(
            fetch_ts(tg_ids),
            fetch_orders_as_revision(dt_from, dt_to),
            fetch_employees(),
            fetch_courier_locations(),
            fetch_sections(tg_ids),
            # OLAP отчет может быть очень тяжелым, добавляем индивидуальный таймаут
            asyncio.wait_for(
                self.get_olap_report(date_from=dt_from, date_to=dt_to, organization_id=organization_id, raw_response=True),
                timeout=25.0
            ),
            return_exceptions=True
        )

        ts_res, orders_res, empl_res, loc_res, sect_res, olap_res = results

        # 4. KPI и Analytics
        orders_total = 0
        revenue_total = 0
        orders_by_status = {}
        top_items_by_qty = {}
        top_items_by_sum = {}
        short_orders = []

        if orders_res.get("success"):
            for org_orders in orders_res["data"].get("ordersByOrganizations", []):
                items = org_orders.get("items", [])
                orders_total += len(items)
                for o in items:
                    st = o.get("status") or "Unknown"
                    orders_by_status[st] = orders_by_status.get(st, 0) + 1
                    
                    # Сумма (для KPI если OLAP недоступен)
                    o_sum = o.get("sum", 0)
                    revenue_total += o_sum
                    
                    # Краткий список
                    short_orders.append({
                        "id": o.get("id"),
                        "number": o.get("number"),
                        "customer": (o.get("customer") or {}).get("name") or "Гость",
                        "status": st,
                        "sum": o_sum,
                        "whenCreated": o.get("whenCreated")
                    })
                    
                    # Топ товаров (из синхронизированных заказов)
                    for item in o.get("items", []):
                        name = item.get("name") or "Товар"
                        qty = item.get("amount", 0)
                        price = item.get("price", 0)
                        top_items_by_qty[name] = top_items_by_qty.get(name, 0) + qty
                        top_items_by_sum[name] = top_items_by_sum.get(name, 0) + (qty * price)
        
        # Если OLAP вернул данные, берем выручку оттуда (она точнее)
        olap_revenue = 0
        if isinstance(olap_res, list) and len(olap_res) > 0:
            for row in olap_res:
                if isinstance(row, dict):
                    olap_revenue += row.get("DishDiscountSumInt", row.get("revenue", row.get("OrderSum", 0)))
        
        if olap_revenue > 0:
            revenue_total = olap_revenue

        status_list = [{"status": k, "count": v} for k, v in orders_by_status.items()]
        
        # Сортировка топ-товаров
        top_qty_list = sorted([{"name": k, "value": v} for k, v in top_items_by_qty.items()], key=lambda x: x["value"], reverse=True)[:10]
        top_sum_list = sorted([{"name": k, "value": v} for k, v in top_items_by_sum.items()], key=lambda x: x["value"], reverse=True)[:10]

        couriers_total = 0
        if empl_res.get("success") and isinstance(empl_res.get("data"), dict):
            emps = empl_res["data"].get("employees") or empl_res["data"].get("couriers") or []
            for org_empl in emps:
                couriers_total += len(org_empl.get("items", []))
        
        couriers_active = 0
        if loc_res.get("success") and isinstance(loc_res.get("data"), dict):
            for org_loc in loc_res["data"].get("activeCourierLocations", []):
                couriers_active += len(org_loc.get("items", []))

        # Формирование плоского списка терминалов с доп. полями (как в RAW примере)
        flat_terminals = []
        if tg_res.get("success") and "data" in tg_res:
            alive_map = {}
            if ts_res.get("success") and "data" in ts_res:
                for s in ts_res["data"].get("isAliveStatus", []):
                    alive_map[s.get("terminalGroupId")] = s.get("isAlive", False)

            for org_tg in tg_res["data"].get("terminalGroups", []):
                for item in org_tg.get("items", []):
                    tid = item.get("id")
                    flat_terminals.append({
                        "id": tid,
                        "name": item.get("name"),
                        "address": item.get("address"),
                        "timeZone": item.get("timeZone"),
                        "isAlive": alive_map.get(tid, False),
                        "organizationId": item.get("organizationId")
                    })

        result = {
            "organizationId": organization_id,
            "dateFrom": dt_from.strftime("%Y-%m-%d %H:%M:%S.000"),
            "dateTo": dt_to.strftime("%Y-%m-%d %H:%M:%S.000"),
            "terminals": {
                "groups": tg_res,
                "status": ts_res,
                "flatList": flat_terminals
            },
            "orders": orders_res,
            "couriers": {
                "all": empl_res,
                "active": loc_res
            },
            "sections": {
                "list": sect_res,
                "bookings": None
            },
            "kpi": {
                "revenueTotal": round(revenue_total, 2),
                "ordersTotal": orders_total,
                "avgCheck": round(revenue_total / orders_total, 2) if orders_total > 0 else 0,
                "ordersByStatus": status_list,
                "kitchenAvgMin": 0, # Позже можно добавить из логов кухни
                "travelAvgMin": 0,
                "couriersTotal": couriers_total,
                "couriersActive": couriers_active
            },
            "analytics": {
                "topItems": {"byQty": top_qty_list, "bySum": top_sum_list},
                "payments": {"list": []},
                "ordersShort": short_orders[:20] # Последние 20 заказов
            },
            "olap": olap_res if isinstance(olap_res, dict) else {"error": str(olap_res)},
            "errors": []
        }
        
        # Сохранение в кеш на 5 минут
        if settings.CACHE_ENABLED:
            try:
                await redis_client.setex(cache_key, 300, json.dumps(result))
            except Exception as ce:
                logger.warning(f"Cache write error: {ce}")
                
        return result

    async def get_customer_order_history_olap(
        self,
        phone: str,
        session: Session,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение истории заказов гостя через OLAP (Server API).
        Возвращает список выполненных заказов с суммами и датами.
        """
        org_id = organization_id or self.organization_id
        
        # Кэширование истории заказов клиента на 1 час
        cache_key = f"customer_orders_olap_{phone}_{org_id}"
        if settings.CACHE_ENABLED:
            try:
                cached = await redis_client.get(cache_key)
                if cached: return json.loads(cached)
            except: pass
        
        # Очищаем телефон от лишних символов (нужны только цифры для iiko)
        clean_phone = "".join(filter(str.isdigit, phone))
        if clean_phone.startswith("8") and len(clean_phone) == 11:
            clean_phone = "7" + clean_phone[1:]
        elif len(clean_phone) == 10:
            clean_phone = "7" + clean_phone

        # Период: за все время (или за последние 5 лет)
        date_from = datetime.now() - timedelta(days=365*5)
        date_to = datetime.now()

        phone_variants = [clean_phone, f"+{clean_phone}", phone]
        possible_fields = ["Delivery.CustomerPhone", "Delivery.Phone", "OrderCustomer.Phone", "Customer.Phone", "Phone"]
        
        for field in possible_fields:
            filters = {
                field: {
                    "filterType": "IncludeValues",
                    "values": phone_variants
                },
                "OrderDeleted": {
                    "filterType": "IncludeValues",
                    "values": ["NOT_DELETED"]
                }
            }

            # Пробуем разные наборы полей, как в аналитике
            aggregate_variants = [
                ["DishDiscountSumInt", "fullSum", "UniqOrderId"],
                ["DishDiscountSum", "fullSum", "UniqOrderId"],
                ["fullSum", "UniqOrderId"]
            ]

            for agg_fields in aggregate_variants:
                try:
                    rows = await self.get_custom_olap_report(
                        report_type="SALES",
                        group_by_fields=["OpenDate.Typed"],
                        aggregate_fields=agg_fields,
                        date_from=date_from,
                        date_to=date_to,
                        organization_id=org_id,
                        filters=filters,
                        log_error=False # Не спамим в логи при переборе вариантов
                    )
                    if rows:
                        # Форматируем для фронтенда
                        processed = []
                        for r in rows:
                            # Сумма заказа (пробуем разные поля)
                            order_sum = 0
                            for sum_field in ["DishDiscountSumInt", "DishDiscountSum", "fullSum"]:
                                if sum_field in r and r[sum_field] is not None:
                                    order_sum = float(r[sum_field])
                                    break
                            
                            processed.append({
                                "date": r.get("OpenDate.Typed"),
                                "order_id": r.get("UniqOrderId"),
                                "sum": order_sum,
                                "status": "COMPLETED" # В этом отчете только выполненные (SALES)
                            })
                        
                        # Сортируем по дате
                        processed.sort(key=lambda x: str(x.get("date") or ""), reverse=True)
                        
                        if settings.CACHE_ENABLED:
                            try: await redis_client.setex(cache_key, 3600, json.dumps(processed))
                            except: pass
                            
                        return processed
                except Exception as e:
                    continue # Пробуем следующий набор полей или следующий фильтр по телефону
        
        return []

    async def get_customer_analytics_olap(
        self,
        phone: str,
        session: Session,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Получение расширенной аналитики гостя через OLAP (Server API).
        """
        org_id = organization_id or self.organization_id
        
        # Кэширование аналитики клиента на 1 час
        cache_key = f"customer_analytics_olap_{phone}_{org_id}"
        if settings.CACHE_ENABLED:
            try:
                cached = await redis_client.get(cache_key)
                if cached: return json.loads(cached)
            except: pass
        
        clean_phone = "".join(filter(str.isdigit, phone))
        if clean_phone.startswith("8") and len(clean_phone) == 11:
            clean_phone = "7" + clean_phone[1:]
        elif len(clean_phone) == 10:
            clean_phone = "7" + clean_phone
        
        # Период: 10 лет
        date_from = datetime.now() - timedelta(days=365*10)
        date_to = datetime.now()
        
        # Расширенный список полей для поиска телефона в разных версиях iiko
        # ПРИОРИТЕТ: Delivery.CustomerPhone (валидное поле для этой версии iiko)
        phone_variants = [clean_phone, f"+{clean_phone}", phone]
        possible_fields = ["Delivery.CustomerPhone", "Delivery.Phone", "OrderCustomer.Phone"]

        
        # Попробуем получить данные
        for field in possible_fields:
            filters = {
                field: {
                    "filterType": "IncludeValues",
                    "values": phone_variants
                },
                "OrderDeleted": {
                    "filterType": "IncludeValues",
                    "values": ["NOT_DELETED"]
                }
            }

            # Список полей агрегации для пробы (могут отличаться в разных версиях iiko)
            aggregate_variants = [
                ["DishDiscountSumInt", "fullSum", "DiscountSum", "UniqOrderId", "DishAmountInt"],
                ["fullSum", "DiscountSum", "UniqOrderId"] # Минимальный набор
            ]

            for agg_fields in aggregate_variants:
                try:
                    rows = await self.get_custom_olap_report(
                        report_type="SALES",
                        group_by_fields=["OpenDate.Typed"],
                        aggregate_fields=agg_fields,
                        date_from=date_from,
                        date_to=date_to,
                        organization_id=org_id,
                        filters=filters,
                        log_error=False
                    )
                    
                    if rows:
                        # Суммируем с учетом возможных имен полей
                        def get_val(r, names):
                            for n in names:
                                if n in r: return float(r[n] or 0)
                            return 0.0

                        total_sum = sum(get_val(r, ["DishDiscountSumInt", "fullSum"]) for r in rows)
                        total_count = sum(int(r.get("UniqOrderId", 1)) for r in rows)
                        total_discount = sum(get_val(r, ["DiscountSum"]) for r in rows)
                        total_items = sum(get_val(r, ["DishAmountInt"]) for r in rows)
                        
                        dates = []
                        for r in rows:
                            d = r.get("OpenDate.Typed")
                            if d:
                                try:
                                    dates.append(datetime.fromisoformat(str(d).replace(" ", "T")))
                                except:
                                    pass
                        
                        first_order = min(dates) if dates else None
                        last_order = max(dates) if dates else None
                        
                        result = {
                            "total_sum": round(total_sum, 2),
                            "total_revenue": round(total_sum, 2), # Для совместимости
                            "total_count": total_count,
                            "orders_count": total_count, # Для совместимости
                            "total_discount": round(total_discount, 2),
                            "total_items": total_items,
                            "average_check": round(total_sum / total_count, 2) if total_count > 0 else 0,
                            "first_order_date": first_order.isoformat() if first_order else None,
                            "last_order_date": last_order.isoformat() if last_order else None,
                            "days_since_last_order": (datetime.now() - last_order).days if last_order else None,
                            "frequency_days": round((last_order - first_order).days / total_count, 1) if (total_count > 1 and first_order and last_order) else 0
                        }
                        
                        if settings.CACHE_ENABLED:
                            try: await redis_client.setex(cache_key, 3600, json.dumps(result))
                            except: pass
                            
                        return result
                    else:
                        # Если отчет пустой, пробуем следующий вариант агрегации или выходим
                        break
                except Exception as e:
                    if "REST_API" in str(e):
                        raise e
                    logger.debug(f"OLAP analytics aggregate variant {agg_fields} failed with field {field}: {e}")
                    # Пробуем следующий вариант агрегации для этого же фильтра по телефону
                    continue
                
        return {
            "total_sum": 0,
            "total_count": 0,
            "total_discount": 0,
            "average_check": 0,
            "error": "Data not found or Resto API unavailable"
        }

    def _parse_olap_response(self, response: Any) -> List[Dict[str, Any]]:
        """Универсальный парсер для OLAP ответов iiko (v1/v2, Cloud/Server)"""
        if not response:
            return []
            
        data_rows = []
        if isinstance(response, dict):
            # Формат v2: {"data": [[...], [...]], "columnNames": [...]}
            if "data" in response and "columnNames" in response:
                cols = response["columnNames"]
                rows = response["data"]
                if rows and len(rows) > 0:
                    if isinstance(rows[0], dict):
                        data_rows = rows
                    else:
                        # Сопоставляем имена колонок со значениями строк
                        data_rows = [dict(zip(cols, r)) for r in rows if isinstance(r, list)]
            # Формат Cloud: {"data": [{"col1": val, ...}, ...]}
            elif "data" in response and isinstance(response["data"], list):
                data_rows = response["data"]
            # Прямой ответ как словарь
            elif any(k in response for k in ["DishDiscountSumInt", "fullSum", "OrderSum", "revenue", "Revenue"]):
                data_rows = [response]
        elif isinstance(response, list):
            data_rows = response
            
        return [r for r in data_rows if isinstance(r, dict)]

    async def get_olap_report(
        self,
        date_from: datetime,
        date_to: datetime,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None,
        include_deleted: bool = False,
        resto_url: Optional[str] = None,
        resto_login: Optional[str] = None,
        resto_password: Optional[str] = None,
        raw_response: bool = False
    ) -> Any:
        """
        Получение OLAP-отчета по выручке.
        Пробует iiko Resto (Office) API, так как Cloud API часто дает 401.
        """
        org_id = organization_id or self.organization_id
        logger.info(f"get_olap_report: resto_url={resto_url}, resto_login={resto_login}, org_id={org_id}")
        fmt_date = "%Y-%m-%d"
        
        # Сначала пробуем через Resto API (Office), используя рекомендуемую структуру v2 (POST)
        try:
            # iiko Office (RMS) v2 (POST) ожидает ISO формат с миллисекундами
            # Чтобы избежать ошибки 409 (пустой интервал) для одного дня, добавляем 1 день к 'to'
            v2_from = date_from.strftime("%Y-%m-%dT00:00:00.000")
            v2_to = (date_to + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000")
            
            # Старый формат для v1 (Fallback)
            v1_from = date_from.strftime("%d.%m.%Y")
            v1_to = date_to.strftime("%d.%m.%Y")
            
            payload = {
                "reportType": "SALES",
                "groupByRowFields": ["Department", "OpenDate.Typed"],
                "aggregateFields": [
                    "DishDiscountSumInt", 
                    "DiscountSum", 
                    "GuestNum", 
                    "DishAmountInt",
                    "UniqOrderId",
                    "ProductCostBase.ProductCost",
                    "ProductCostBase.MarkUp",
                    "ProductCostBase.Profit",
                    "ProductCostBase.Percent"
                ],
                "filters": {
                    "OpenDate.Typed": {
                        "filterType": "DateRange",
                        "periodType": "CUSTOM",
                        "from": v2_from,
                        "to": v2_to,
                        "includeLow": True,
                        "includeHigh": False
                    }
                }
            }
            
            if not include_deleted:
                payload["filters"]["OrderDeleted"] = {
                    "filterType": "IncludeValues",
                    "values": ["NOT_DELETED"]
                }

            # Пытаемся вызвать v2 эндпоинт. 
            try:
                try:
                    response = await self._resto_request(
                        "POST", "/v2/reports/olap",
                        json_data=payload,
                        resto_url=resto_url,
                        resto_login=resto_login,
                        resto_password=resto_password,
                        organization_id=org_id
                    )
                except httpx.HTTPStatusError as e:
                    # Если 400 (Bad Request), вероятно не поддерживаются поля себестоимости (Food Cost)
                    if e.response.status_code == 400:
                        logger.warning("Resto OLAP v2 failed (likely Food Cost fields). Retrying without ProductCostBase fields...")
                        payload["aggregateFields"] = [
                            "DishDiscountSumInt", 
                            "DiscountSum", 
                            "GuestNum", 
                            "DishAmountInt",
                            "UniqOrderId"
                        ]
                        response = await self._resto_request(
                            "POST", "/v2/reports/olap",
                            json_data=payload,
                            resto_url=resto_url,
                            resto_login=resto_login,
                            resto_password=resto_password,
                            organization_id=org_id
                        )
                    else:
                        raise e
            except httpx.HTTPStatusError as e:
                # Если 404, значит v2 не поддерживается, пробуем v1 (GET)
                if e.response.status_code == 404:
                    logger.info("Resto API v2 not found, falling back to v1 (GET)")
                    # В v1 (GET) агрегаты могут называться иначе, пробуем стандартные
                    params = [
                        ("key", "TOKEN"), # Заглушка, подставится в _resto_request
                        ("reportType", "Sales"),
                        ("from", v1_from),
                        ("to", v1_to),
                        ("groupRow", "OpenDate.Typed"),
                        ("groupRow", "Department"),
                        ("agg", "DishDiscountSumInt"),
                        ("agg", "DiscountSum"),
                        ("agg", "GuestNum"),
                    ]
                    if not include_deleted:
                        params.append(("filter", "OrderDeleted:is:NOT_DELETED"))
                        
                    response = await self._resto_request(
                        "GET", "/reports/olap",
                        params=params,
                        resto_url=resto_url,
                        resto_login=resto_login,
                        resto_password=resto_password,
                        organization_id=org_id
                    )
                else:
                    raise e
            
            # Парсинг ответа v2/v1
            data_rows = self._parse_olap_response(response)
            
            logger.info(f"Resto OLAP parsed rows count: {len(data_rows)}")
            
            if data_rows:
                result = []
                for row_dict in data_rows:
                    # Извлекаем данные, поддерживая оба формата ключей (v2 и v1)
                    rev = self._safe_float(row_dict.get("DishDiscountSumInt", row_dict.get("OrderSum", row_dict.get("fullSum", row_dict.get("OrderSumAfterDiscount", 0)))))
                    disc = self._safe_float(row_dict.get("DiscountSum", row_dict.get("discountSum", 0)))
                    guests = self._safe_int(row_dict.get("GuestNum", row_dict.get("guestNum", 0)))
                    amount = self._safe_float(row_dict.get("DishAmountInt", row_dict.get("dishAmountInt", 0)))
                    orders_count = self._safe_int(row_dict.get("UniqOrderId", row_dict.get("UniqOrderCount", guests)))
                    
                    if orders_count == 0:
                        orders_count = int(amount) if amount > 0 else 1

                    avg_check = rev / orders_count if orders_count > 0 else 0
                    
                    result.append({
                        "date": str(row_dict.get("OpenDate.Typed", row_dict.get("openDate.Typed", ""))).split("T")[0],
                        "department": row_dict.get("Department", row_dict.get("department", "")),
                        "revenue": rev,
                        "average_check": round(avg_check, 2),
                        "markup": self._safe_float(row_dict.get("ProductCostBase.Profit", row_dict.get("profitability", 0.0))),
                        "markup_percent": self._safe_float(row_dict.get("ProductCostBase.MarkUp", row_dict.get("profitabilityPercent", 0.0))),
                        "cost_price": self._safe_float(row_dict.get("ProductCostBase.ProductCost", row_dict.get("costPrice", 0.0))),
                        "cost_price_percent": self._safe_float(row_dict.get("ProductCostBase.Percent", row_dict.get("costPricePercent", 0.0))),
                        "discount_sum": disc,
                        "orders_count": orders_count,
                    })
                return result
            
            return []

        except Exception as resto_err:
            logger.error(f"Resto OLAP failed: {resto_err}. Cloud API fallback is disabled per user request.")
            return []

    async def get_daily_revenue_olap(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Получение ежедневной выручки и скидок через OLAP для расчета чистой прибыли.
        Использует DishDiscountSumInt как базу выручки.
        """
        try:
            # Используем универсальный метод для Server API (Resto)
            rows = await self.get_custom_olap_report(
                report_type="SALES",
                group_by_fields=["OpenDate.Typed"],
                aggregate_fields=["DishDiscountSumInt", "fullSum", "DiscountSum", "UniqOrderId"],
                date_from=date_from,
                date_to=date_to,
                organization_id=organization_id
            )
            
            result = {}
            for row in rows:
                raw_date = row.get("OpenDate.Typed", "")
                # Нормализация даты (2024-04-23T00:00:00 -> 2024-04-23)
                date_str = str(raw_date).split("T")[0].split(" ")[0] if raw_date else ""
                
                if date_str:
                    try:
                        # Используем DishDiscountSumInt для выручки (Net Revenue)
                        rev = float(row.get("DishDiscountSumInt", row.get("fullSum", 0)))
                        disc = float(row.get("DiscountSum", 0))
                        if date_str not in result:
                            result[date_str] = {"revenue": 0.0, "discounts": 0.0}
                        
                        result[date_str]["revenue"] += round(rev, 2)
                        result[date_str]["discounts"] += round(disc, 2)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Ошибка парсинга чисел в строке OLAP {date_str}: {e}")

            logger.info(f"Итоговый словарь выручки (Server API): {list(result.keys())}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при получении выручки из OLAP (Server API): {e}")
            return {}

    async def get_custom_olap_report(
        self,
        report_type: str,
        group_by_fields: List[str],
        aggregate_fields: List[str],
        date_from: datetime,
        date_to: datetime,
        organization_id: Optional[str] = None,
        filters: Optional[Dict] = None,
        log_error: bool = True
    ) -> List[Dict[str, Any]]:
        """Универсальный метод для получения любых OLAP-отчетов через Server API"""
        from datetime import timedelta
        org_id = organization_id or self.organization_id
        # [FIX] Для фильтра типа DATE в iiko v2 API нельзя передавать время
        v2_from = date_from.strftime("%Y-%m-%d")
        v2_to = (date_to + timedelta(days=1)).strftime("%Y-%m-%d")
        
        if "UniqOrderId" not in aggregate_fields:
            aggregate_fields.append("UniqOrderId")

        payload = {
            "reportType": report_type,
            "groupByRowFields": group_by_fields,
            "aggregateFields": aggregate_fields,
            "filters": {
                "OpenDate.Typed": {
                    "filterType": "DateRange",
                    "periodType": "CUSTOM",
                    "from": v2_from,
                    "to": v2_to,
                    "includeLow": True,
                    "includeHigh": False
                }
            }
        }
        
        if filters:
            payload["filters"].update(filters)
            
        try:
            response = await self._resto_request(
                "POST", "/v2/reports/olap",
                json_data=payload,
                organization_id=org_id,
                log_error=log_error
            )
            return self._parse_olap_response(response)
        except Exception as e:
            if log_error:
                logger.warning(f"Custom OLAP report ({report_type}) field/request failed: {e}")
            raise e

    async def get_payment_types_report(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Отчет по типам оплат через OLAP"""
        # Группируем по дате, отделу (терминалу) и типу оплаты
        return await self.get_custom_olap_report(
            report_type="SALES",
            group_by_fields=["OpenDate.Typed", "Department", "CashRegisterName", "PayTypes"],
            aggregate_fields=["fullSum", "UniqOrderId"],
            date_from=date_from,
            date_to=date_to,
            organization_id=organization_id
        )

    # =========================================================================
    # iiko Resto (Office API) - Прямое подключение
    # =========================================================================

    async def _resto_request(
        self,
        method: str,
        endpoint: str,
        resto_url: Optional[str] = None,
        resto_login: Optional[str] = None,
        resto_password: Optional[str] = None,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        timeout: float = 30.0,
        organization_id: Optional[str] = None,
        log_error: bool = True
    ) -> Any:
        """Метод для запросов к iiko Resto (Office) API с SHA-1 авторизацией"""
        # Пытаемся получить настройки из БД если передана организация
        db_settings = None
        if organization_id:
            db_settings = await self._get_settings_by_org_id(organization_id)
        
        url = resto_url or (db_settings.resto_url if db_settings else None) or settings.IIKO_RESTO_URL
        login = resto_login or (db_settings.resto_login if db_settings else None) or settings.IIKO_RESTO_LOGIN
        password = resto_password or (db_settings.resto_password if db_settings else None) or settings.IIKO_RESTO_PASSWORD

        if not url or not login:
            if log_error:
                logger.error(f"Resto API not configured for org {organization_id}. URL: {url}, Login: {login}")
            raise ValueError(f"Данные iiko Resto (URL/Login) не настроены для организации {organization_id}.")

        # Normalize URL
        base_url = url.rstrip('/')
        if not base_url.endswith('/api'):
            if base_url.endswith('/resto'):
                base_url = f"{base_url}/api"
            else:
                base_url = f"{base_url}/resto/api"
        
        # 1. Получаем токен из кэша или авторизуемся
        token = None
        cache_key = f"{login}_{base_url}"
        
        async with self._get_resto_token_lock():
            cached = self._resto_token_cache.get(cache_key)
            if cached:
                c_token, c_expiry = cached
                if datetime.now() < c_expiry:
                    token = c_token
            
            if not token:
                max_retries = 2
                client = self.insecure_client
                
                for attempt in range(max_retries):
                    # Добавляем небольшую задержку перед запросом
                    await asyncio.sleep(0.5)
                    auth_url = f"{base_url}/auth"
                    password_sha1 = hashlib.sha1(password.encode()).hexdigest()
                    auth_params = {"login": login, "pass": password_sha1}
                    
                    logger.info(f"Resto Auth attempt (SHA-1) {attempt+1}/{max_retries} for {login}")
                    try:
                        auth_response = await client.get(auth_url, params=auth_params)
                        
                        if auth_response.status_code == 403 and "no connections" in auth_response.text:
                            if attempt < max_retries - 1:
                                wait_time = (attempt + 1) * 3
                                logger.warning(f"Resto API limit reached (403). Retrying in {wait_time}s...")
                                await asyncio.sleep(wait_time)
                                continue
                        
                        if auth_response.status_code != 200:
                            # Fallback for older versions
                            auth_response = await client.get(auth_url, params={"login": login, "pass": password})
                        
                        if auth_response.status_code == 200:
                            token = auth_response.text.strip().replace('"', '')
                            # Кэшируем на 15 минут
                            self._resto_token_cache[cache_key] = (token, datetime.now() + timedelta(minutes=15))
                            logger.info(f"Resto Session {token[:8]}... created and cached for {login}")
                            break
                        elif attempt == max_retries - 1:
                            if log_error:
                                logger.error(f"Resto Auth failed: {auth_response.status_code} | {auth_response.text}")
                            raise HTTPException(status_code=401, detail=f"Ошибка авторизации Resto: {auth_response.text}")
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise
                        await asyncio.sleep(1)

        # 2. Выполняем основной запрос
        request_url = f"{base_url}{endpoint}"
        client = self.insecure_client
        
        # Подготовка параметров
        final_params = {}
        if isinstance(params, dict):
            final_params = params.copy()
        elif isinstance(params, list):
            final_params = params.copy()
        
        if isinstance(final_params, dict):
            final_params["key"] = token
        else:
            final_params.append(("key", token))
        
        logger.info(f"Resto Request: {method} {request_url}")
        try:
            response = await client.request(method, request_url, params=final_params, json=json_data)
            
            # Если токен протух (401), сбрасываем кэш
            if response.status_code == 401:
                logger.warning(f"Resto Token expired for {login}, clearing cache")
                if cache_key in self._resto_token_cache:
                    del self._resto_token_cache[cache_key]
        except Exception as e:
            logger.error(f"Resto Request failed: {e}")
            raise

        # 3. НЕ разлогиниваемся (переиспользуем сессию)

        if response.status_code >= 400:
            # Специальная обработка для ошибки лицензии iiko Resto
            if response.status_code == 403 and "module REST_API" in response.text:
                logger.error(f"ОШИБКА ЛИЦЕНЗИИ IIKO: Модуль REST API не активен на сервере iiko. Требуется активация лицензии. Ответ сервера: {response.text}")
                raise HTTPException(
                    status_code=403, 
                    detail="Ошибка iiko: Отсутствует лицензия на модуль 'iiko Server API' (REST_API). Пожалуйста, обратитесь в поддержку iiko для активации."
                )
            
            if log_error:
                # Логируем как ошибку только если это не подавленный запрос (например, не перебор вариантов)
                logger.error(f"iiko Resto error {response.status_code}: {response.text} | URL: {endpoint}")
            elif response.status_code != 400:
                # Для 400 при подавленном логе пишем только в debug, так как это штатный перебор полей
                logger.debug(f"iiko Resto suppressed 400 error: {response.text}")
            
            response.raise_for_status()

        if response.encoding is None or response.encoding.lower() == 'iso-8859-1':
            response.encoding = 'utf-8'

        try:
            return response.json()
        except Exception:
            return response.text

    async def get_resto_employees(
        self,
        resto_url: Optional[str] = None,
        resto_login: Optional[str] = None,
        resto_password: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получение детального списка сотрудников из iiko Resto"""
        # iiko Resto возвращает XML по умолчанию
        data = await self._resto_request(
            "GET", "/employees", 
            resto_url=resto_url or settings.IIKO_RESTO_URL,
            resto_login=resto_login or settings.IIKO_RESTO_LOGIN,
            resto_password=resto_password or settings.IIKO_RESTO_PASSWORD
        )
        
        # Если пришел XML (строка), нужно распарсить. 
        if isinstance(data, str):
            import xml.etree.ElementTree as ET
            root = ET.fromstring(data)
            
            employees = []
            for emp in root.findall('employee'):
                # Пользователь просил все данные о должностях и ролях
                # В iiko RESTO XML: mainRoleCode - основная роль, roleCodes - список кодов через запятую
                employees.append({
                    "id": emp.findtext('id'),
                    "name": emp.findtext('name'),
                    "firstName": emp.findtext('firstName'),
                    "lastName": emp.findtext('lastName'),
                    "code": emp.findtext('code'), # Внутренний код
                    "org_id": emp.findtext('preferredDepartmentCode') or (emp.find('mainRole').findtext('organizationId') if emp.find('mainRole') is not None else None),
                    "phone": emp.findtext('phone') or emp.findtext('cellPhone'),
                    "email": emp.findtext('email'),
                    "role": self._extract_role(emp),
                    "role_codes": emp.findtext('roleCodes'), # Все роли
                    "main_role_code": emp.findtext('mainRoleCode'), # Основная роль
                    "cardNumber": emp.findtext('cardNumber'),
                    "inn": emp.findtext('inn'),
                    "snils": emp.findtext('snils'),
                    "birthday": emp.findtext('birthday'),
                    "address": emp.findtext('address'),
                    "salary": self._safe_float(emp.findtext('salary')),
                    "deleted": emp.findtext('deleted') == 'true' or emp.findtext('fireDate') is not None
                })
            return employees
        return data if isinstance(data, list) else []

    async def get_resto_personal_sessions(
        self,
        date_from: datetime,
        date_to: datetime,
        resto_url: Optional[str] = None,
        resto_login: Optional[str] = None,
        resto_password: Optional[str] = None,
        log_error: bool = True
    ) -> List[Dict[str, Any]]:
        """Получение личных смен сотрудников из iiko Resto (Office) API"""
        try:
            # iiko Resto API v2: GET /resto/api/personalSessions?from=...&to=...
            params = {
                "from": date_from.strftime("%Y-%m-%d"),
                "to": date_to.strftime("%Y-%m-%d")
            }
            data = await self._resto_request(
                "GET", "/personalSessions",
                params=params,
                resto_url=resto_url,
                resto_login=resto_login,
                resto_password=resto_password,
                log_error=log_error
            )
            
            if isinstance(data, str):
                import xml.etree.ElementTree as ET
                root = ET.fromstring(data)
                sessions = []
                for att in root.findall('.//attendance'):
                    sessions.append({
                        "id": att.findtext('id'),
                        "employeeId": att.findtext('employeeId'),
                        "openTime": att.findtext('dateFrom'),
                        "closeTime": att.findtext('dateTo'),
                        "status": "CLOSED" if att.findtext('dateTo') else "OPEN"
                    })
                return sessions
            return []
        except Exception as e:
            logger.error(f"Error getting personal sessions from Resto: {e}")
            return []

    async def get_resto_schedules(
        self,
        date_from: datetime,
        date_to: datetime,
        resto_url: Optional[str] = None,
        resto_login: Optional[str] = None,
        resto_password: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получение графиков работы сотрудников из iiko Resto (Office) API"""
        try:
            params = {
                "from": date_from.strftime("%Y-%m-%d"),
                "to": date_to.strftime("%Y-%m-%d")
            }
            data = await self._resto_request(
                "GET", "/employees/schedule",
                params=params,
                resto_url=resto_url,
                resto_login=resto_login,
                resto_password=resto_password
            )
            
            if isinstance(data, str):
                import xml.etree.ElementTree as ET
                root = ET.fromstring(data)
                schedules = []
                for sch in root.findall('.//schedule'):
                    schedules.append({
                        "employeeId": sch.findtext('employeeId'),
                        "dateFrom": sch.findtext('dateFrom'),
                        "dateTo": sch.findtext('dateTo')
                    })
                return schedules
            return []
        except Exception as e:
            logger.error(f"Error getting schedules from Resto: {e}")
            return []

    async def get_resto_olap_columns(
        self,
        report_type: str = "DELIVERIES",
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получение списка доступных колонок для OLAP-отчета (диагностика)"""
        try:
            params = {"reportType": report_type}
            data = await self._resto_request(
                "GET", "/olaps/olapColumns",
                params=params,
                organization_id=organization_id
            )
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Error getting OLAP columns: {e}")
            return []

    async def get_resto_detailed_deliveries(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: str,
        resto_url: Optional[str] = None,
        resto_login: Optional[str] = None,
        resto_password: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получение детальной истории доставок из iiko Resto через OLAP"""
        try:
            from datetime import timedelta
            
            # Базовые поля группировки для DELIVERIES отчета
            base_fields = [
                "Delivery.Number", 
                "Delivery.Courier", 
                "Delivery.Courier.Id",
                "Delivery.Address",
                "Delivery.City",
                "Delivery.Street", 
                "Delivery.Region",
                "Delivery.Zone",
                "Delivery.Line1",
                "Delivery.SendTime",
                "Delivery.ActualTime",
                "Delivery.ExpectedTime",
                "Delivery.CookingFinishTime",
                "Delivery.CustomerName",
                "Delivery.Phone"
            ]
            
            # Расширенные поля адреса (могут не поддерживаться в OLAP на некоторых версиях iiko)
            extended_address_fields = [
                "Delivery.House",
                "Delivery.Flat",
                "Delivery.Entrance",
                "Delivery.Floor",
                "Delivery.Doorphone"
            ]

            v2_from = date_from.strftime("%Y-%m-%dT00:00:00.000")
            v2_to = (date_to + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000")
            
            response = None
            
            # 1. Пробуем v2 (POST) с расширенными полями
            try:
                payload = {
                    "reportType": "DELIVERIES",
                    "groupByRowFields": base_fields + extended_address_fields,
                    "aggregateFields": [
                        "fullSum",
                        "UniqOrderId"
                    ],
                    "filters": {
                        "OpenDate.Typed": {
                            "filterType": "DateRange",
                            "periodType": "CUSTOM",
                            "from": v2_from.split('T')[0],
                            "to": v2_to.split('T')[0],
                            "includeLow": True,
                            "includeHigh": True
                        }
                    }
                }
                
                response = await self._resto_request(
                    "POST", "/v2/reports/olap",
                    json_data=payload,
                    resto_url=resto_url,
                    resto_login=resto_login,
                    resto_password=resto_password,
                    organization_id=organization_id,
                    log_error=False # Подавляем ошибку, так как мы сделаем ретрий без расширенных полей
                )
            except Exception as e:
                # Если 400 (Bad Request), вероятно какое-то поле не поддерживается (например, Delivery.House)
                if "400" in str(e):
                    logger.info("Resto OLAP v2 extended address fields failed, retrying with base fields only")
                    payload["groupByRowFields"] = base_fields
                    try:
                        response = await self._resto_request(
                            "POST", "/v2/reports/olap",
                            json_data=payload,
                            resto_url=resto_url,
                            resto_login=resto_login,
                            resto_password=resto_password,
                            organization_id=organization_id
                        )
                    except Exception as e2:
                        if "400" in str(e2):
                            logger.warning("Resto OLAP v2 base fields failed, retrying with minimal fields only")
                            minimal_fields = [
                                "Delivery.Number", 
                                "Delivery.Courier", 
                                "Delivery.Courier.Id",
                                "Delivery.Address",
                                "Delivery.CustomerName",
                                "Delivery.Phone"
                            ]
                            payload["groupByRowFields"] = minimal_fields
                            response = await self._resto_request(
                                "POST", "/v2/reports/olap",
                                json_data=payload,
                                resto_url=resto_url,
                                resto_login=resto_login,
                                resto_password=resto_password,
                                organization_id=organization_id
                            )
                        else:
                            raise e2
                # Если 404, значит v2 API вообще не поддерживается сервером iiko, пробуем v1 (GET)
                elif "404" in str(e):
                    logger.info("Resto API v2 not found, falling back to v1 (GET)")
                    v1_from = date_from.strftime("%d.%m.%Y")
                    v1_to = date_to.strftime("%d.%m.%Y")
                    
                    params = [
                        ("reportType", "Deliveries"),
                        ("from", v1_from),
                        ("to", v1_to),
                        ("agg", "fullSum"),
                        ("agg", "UniqOrderId")
                    ]
                    # Добавляем все базовые поля как groupRow
                    for field in base_fields:
                        params.append(("groupRow", field))
                    
                    response = await self._resto_request(
                        "GET", "/reports/olap",
                        params=params,
                        resto_url=resto_url,
                        resto_login=resto_login,
                        resto_password=resto_password,
                        organization_id=organization_id
                    )
                else:
                    # Другие ошибки (например 401 или 403 Лицензия) пробрасываем выше
                    raise e
            
            if not response:
                return []
                
            data_rows = self._parse_olap_response(response)
            
            transformed = []
            for row in data_rows:
                # Пытаемся получить адрес из разных полей (зависит от версии API и настроек iiko)
                raw_address = row.get("Delivery.Address", row.get("delivery.address", ""))
                line1 = row.get("Delivery.Line1", row.get("delivery.line1", ""))
                
                # Собираем части для совместимости с format_address в iiko_sync_service
                # Поддерживаем разные варианты регистра ключей (v1 vs v2)
                addr_parts = {
                    "city": row.get("Delivery.City", row.get("delivery.city")),
                    "street": row.get("Delivery.Street", row.get("delivery.street")),
                    "house": row.get("Delivery.House", row.get("delivery.house")),
                    "flat": row.get("Delivery.Flat", row.get("delivery.flat")),
                    "entrance": row.get("Delivery.Entrance", row.get("delivery.entrance")),
                    "floor": row.get("Delivery.Floor", row.get("delivery.floor")),
                    "doorphone": row.get("Delivery.Doorphone", row.get("delivery.doorphone")),
                    "line1": line1 or raw_address,
                    "addressString": raw_address
                }
                
                # Формируем объект заказа для фронтенда и синхронизатора
                transformed.append({
                    "id": row.get("Delivery.Number", row.get("delivery.number")),
                    "iiko_order_id": row.get("UniqOrderId", row.get("uniqorderid")),
                    "address": addr_parts, 
                    "deliveryZone": row.get("Delivery.Zone", row.get("delivery.zone")) or row.get("Delivery.Region", row.get("delivery.region")),
                    "sum": self._safe_float(row.get("fullSum", row.get("fullsum", row.get("DishDiscountSumInt", 0)))),
                    "courierInfo": {
                        "courier": {
                            "name": row.get("Delivery.Courier", row.get("delivery.courier")),
                            "id": row.get("Delivery.Courier.Id", row.get("delivery.courier.id"))
                        }
                    },
                    "terminalName": None, 
                    "whenCookingCompleted": row.get("Delivery.CookingFinishTime", row.get("delivery.cookingfinishtime")),
                    "expectedDeliveryTime": row.get("Delivery.ExpectedTime", row.get("delivery.expectedtime")),
                    "whenDelivered": row.get("Delivery.ActualTime", row.get("delivery.actualtime")),
                    "whenConfirmationFinished": row.get("Delivery.SendTime", row.get("delivery.sendtime")),
                    "customer": {
                        "name": row.get("Delivery.CustomerName", row.get("delivery.customername")),
                        "phone": row.get("Delivery.CustomerPhone", row.get("delivery.customerphone"))
                    }
                })
            return transformed
        except Exception as e:
            logger.error(f"Error getting detailed deliveries from Resto: {e}")
            return []


    async def get_resto_roles(
        self,
        resto_url: Optional[str] = None,
        resto_login: Optional[str] = None,
        resto_password: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получение списка ролей (должностей) из iiko Resto"""
        try:
            data = await self._resto_request(
                "GET", "/employees/roles", 
                resto_url=resto_url,
                resto_login=resto_login,
                resto_password=resto_password
            )
            
            if isinstance(data, str):
                import xml.etree.ElementTree as ET
                root = ET.fromstring(data)
                roles = []
                for role in root.findall('role'):
                    roles.append({
                        "id": role.findtext('id'),
                        "code": role.findtext('code'),
                        "name": role.findtext('name')
                    })
                return roles
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Error fetching resto roles: {e}")
            return []

    async def get_resto_attendance(
        self,
        resto_url: str,
        resto_login: str,
        resto_password: str,
        date_from: datetime,
        date_to: datetime,
        log_error: bool = True
    ) -> List[Dict[str, Any]]:
        """Получение данных о явках (сменах) из iiko Resto"""
        params = {
            "from": date_from.strftime("%Y-%m-%d"),
            "to": date_to.strftime("%Y-%m-%d")
        }
        data = await self._resto_request(
            "GET", "/employees/attendance", 
            resto_url, resto_login, resto_password,
            params=params,
            log_error=log_error
        )
        # Аналогично парсим XML если нужно
        if isinstance(data, str):
            import xml.etree.ElementTree as ET
            root = ET.fromstring(data)
            
            records = []
            for rec in root.findall('attendance'):
                # Пробуем найти ID как в теге, так и в атрибуте
                rec_id = rec.findtext('id') or rec.get('id')
                if not rec_id: continue
                
                records.append({
                    "id": rec_id,
                    "employeeId": rec.find('employee').findtext('id') if rec.find('employee') is not None else rec.findtext('employeeId'),
                    "dateOpen": rec.findtext('dateFrom'),
                    "dateClose": rec.findtext('dateTo'),
                })
            return records
        return data if isinstance(data, list) else []

    async def get_resto_delivery_zones(
        self,
        resto_url: str,
        resto_login: str,
        resto_password: str
    ) -> List[Dict[str, Any]]:
        """Получение данных о зонах доставки из iiko Resto (Office)"""
        # Эндпоинт в Office API: /delivery/zones (версия 1) или /delivery/zones.json (если поддерживается)
        try:
            logger.info(f"Запрос зон доставки из iiko Resto: {resto_url}/resto/api/delivery/zones")
            data = await self._resto_request(
                "GET", "/delivery/zones", 
                resto_url, resto_login, resto_password
            )
            
            if isinstance(data, str):
                import xml.etree.ElementTree as ET
                root = ET.fromstring(data)
                
                zones = []
                for z in root.findall('deliveryZone'):
                    zone_id = z.findtext('id')
                    if not zone_id: continue
                    
                    zones.append({
                        "id": zone_id,
                        "name": z.findtext('name'),
                        "description": z.findtext('description'),
                        "active": z.findtext('active') == 'true',
                        "addresses": [a.text for a in z.findall('.//address')],
                        "raw_xml": ET.tostring(z, encoding='unicode')
                    })
                return zones
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Error fetching delivery zones from Resto: {e}")
            return []

    async def get_resto_delivery_history(
        self,
        date_from: datetime,
        date_to: datetime,
        resto_url: Optional[str] = None,
        resto_login: Optional[str] = None,
        resto_password: Optional[str] = None,
        log_error: bool = True
    ) -> List[str]:
        """
        Получение списка GUID заказов из iiko Resto.
        В RMS методе by_date параметры from и to в формате yyyy-MM-dd
        """
        try:
            params = {
                "from": date_from.strftime("%Y-%m-%d"),
                "to": date_to.strftime("%Y-%m-%d")
            }
            data = await self._resto_request(
                "GET", "/deliveries/by_date",
                params=params,
                resto_url=resto_url,
                resto_login=resto_login,
                resto_password=resto_password,
                log_error=log_error
            )
            
            if isinstance(data, str):
                import xml.etree.ElementTree as ET
                root = ET.fromstring(data)
                order_ids = []
                for delivery in root.findall('.//deliveryOrder'):
                    oid = delivery.findtext('id')
                    if oid:
                        order_ids.append(oid)
                return order_ids
            return []
        except Exception as e:
            if log_error:
                logger.error(f"Error getting delivery history from Resto: {e}")
            return []

    def _extract_role(self, emp) -> str:
        """Безопасное извлечение названия роли из разных структур XML iiko"""
        # 1. mainRoleCode (фактически найден в логах)
        role_code = emp.findtext('mainRoleCode')
        if role_code: return role_code

        # 2. roleCodes (список тегов)
        role_codes = emp.findall('roleCodes')
        if role_codes:
            for rc in role_codes:
                if rc.text and rc.text.lower() != 'apiuser':
                    return rc.text

        # 3. mainRole/name
        role_el = emp.find('mainRole')
        if role_el is not None:
            name = role_el.findtext('name')
            if name: return name
            
        # 4. role (прямой тег)
        role = emp.findtext('role')
        if role: return role
                
        return "Staff"

    @staticmethod
    def _safe_float(val: Any) -> float:
        """Безопасное преобразование значения к float"""
        try:
            return float(val) if val is not None else 0.0
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _safe_int(val: Any) -> int:
        """Безопасное преобразование значения к int"""
        try:
            return int(val) if val is not None else 0
        except (ValueError, TypeError):
            return 0

    # =========================================================================
    # iiko Transport (Cloud API) - Дополнительная статистика
    # =========================================================================

    async def get_courier_statistics(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: str,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получение статистики доставок по курьерам через Transport API"""
        # Используем эндпоинт истории доставок
        date_format = "%Y-%m-%d %H:%M:%S.000"
        payload = {
            "organizationIds": [organization_id],
            "deliveryDateFrom": date_from.strftime(date_format),
            "deliveryDateTo": date_to.strftime(date_format)
        }
        
        data = await self._request(
            "POST", "/api/1/deliveries/history", 
            payload,
            api_login=api_login,
            organization_id=organization_id
        )
        
        # Группируем по курьеру и ДАТЕ для точного маппинга в смены
        # stats[courier_id][date_str] = count
        stats = {}
        for order in data.get("orders", []):
            courier = order.get("courierInfo", {}).get("courier", {})
            courier_id = courier.get("id")
            if not courier_id: continue
            
            # Извлекаем дату (используем completeTime или creationTime)
            # Пример: "2024-03-27 15:30:00.000"
            dt_str = order.get("completeTime") or order.get("creationTime")
            if not dt_str: continue
            
            date_str = dt_str.split(" ")[0] # "2024-03-27"
            
            if courier_id not in stats:
                stats[courier_id] = {}
            
            stats[courier_id][date_str] = stats[courier_id].get(date_str, 0) + 1
                
        return stats

    async def get_courier_revenue_olap(
        self,
        date_from: datetime,
        date_to: datetime,
        resto_url: Optional[str] = None,
        resto_login: Optional[str] = None,
        resto_password: Optional[str] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Получение выручки по курьерам через OLAP-отчет iiko Resto (Office).
        Возвращает словарь {courier_id: {date_iso: revenue}}.
        """
        from datetime import timedelta
        try:
            # iiko Office (RMS) v2 (POST) ожидает ISO формат
            v2_from = date_from.strftime("%Y-%m-%dT00:00:00.000")
            v2_to = (date_to + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000")

            payload = {
                "reportType": "SALES",
                "groupByRowFields": ["Courier.Id", "OpenDate.Typed"],
                "aggregateFields": ["DishDiscountSum", "UniqOrderId"],
                "filters": {
                    "OpenDate.Typed": {
                        "filterType": "DateRange",
                        "periodType": "CUSTOM",
                        "from": v2_from,
                        "to": v2_to,
                        "includeLow": True,
                        "includeHigh": False
                    },
                    "OrderDeleted": {
                        "filterType": "IncludeValues",
                        "values": ["NOT_DELETED"]
                    }
                }
            }

            res = await self._resto_request(
                "POST", "/v2/reports/olap",
                json_data=payload,
                resto_url=resto_url,
                resto_login=resto_login,
                resto_password=resto_password
            )

            # revenues[courier_id][date_str] = revenue
            revenues = {}
            if isinstance(res, dict) and "data" in res:
                for row in res.get("data", []):
                    c_id = row.get("Courier.Id")
                    # OpenDate.Typed может приходить как "2024-03-27T00:00:00.000"
                    date_val = row.get("OpenDate.Typed")
                    if date_val and "T" in date_val:
                        date_str = date_val.split("T")[0]
                    else:
                        date_str = str(date_val)
                        
                    rev = self._safe_float(row.get("DishDiscountSum"))
                    
                    if c_id:
                        if c_id not in revenues:
                            revenues[c_id] = {}
                        revenues[c_id][date_str] = rev
            
            return revenues
        except Exception as e:
            logger.error(f"Error getting courier revenue OLAP: {e}")
            return {}

    async def get_detailed_deliveries_cloud(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: str,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получение детальной истории доставок из iiko Cloud API"""
        date_format = "%Y-%m-%d %H:%M:%S.000"
        payload = {
            "organizationIds": [organization_id],
            "deliveryDateFrom": date_from.strftime(date_format),
            "deliveryDateTo": date_to.strftime(date_format)
        }
        try:
            data = await self._request(
                "POST", "/api/1/deliveries/history", 
                payload,
                api_login=api_login,
                organization_id=organization_id
            )
            return data.get("orders", [])
        except Exception as e:
            logger.error(f"Error getting detailed deliveries: {e}")
            return []

    async def fetch_and_parse_kml(self, url: str) -> List[Dict[str, Any]]:
        """
        Загружает KML файл (например, из Google Maps или iiko Cloud) и возвращает полигоны.
        Формат координат: [[lat, lng], ...]
        """
        if not url:
            return []
            
        # Если ссылка на Google My Maps, пробуем получить прямую ссылку на KML
        if "google.com/maps/d/edit" in url or "google.com/maps/d/viewer" in url:
            if "mid=" in url:
                mid = url.split("mid=")[1].split("&")[0]
                url = f"https://www.google.com/maps/d/u/0/kml?mid={mid}&forcekml=1"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                content = response.text
                logger.info(f"KML загружен, размер: {len(content)} символов. Начинаем парсинг...")
                return self.parse_kml_content(content)
            except Exception as e:
                logger.error(f"Ошибка при загрузке KML по ссылке {url}: {e}")
                raise

    def parse_kml_content(self, kml_text: str) -> List[Dict[str, Any]]:
        """
        Парсит XML/KML содержимое в список полигонов.
        """
        from app.utils.geo_utils import parse_kml
        return parse_kml(kml_text)

    # =========================================================================
    # Delivery Management (iiko Cloud)
    # =========================================================================

    async def assign_delivery_courier(
        self,
        organization_id: str,
        order_id: str,
        courier_id: str,
        api_login: Optional[str] = None
    ) -> Dict[str, Any]:
        """Назначение курьера на заказ в iiko Cloud"""
        payload = {
            "organizationId": organization_id,
            "orderId": order_id,
            "courierId": courier_id
        }
        return await self._request(
            "POST", "/api/1/deliveries/assign_courier", 
            payload,
            api_login=api_login,
            organization_id=organization_id
        )

    async def change_delivery_status(
        self,
        organization_id: str,
        order_id: str,
        delivery_status: str,
        api_login: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Изменение статуса доставки в iiko Cloud.
        Возможные статусы: Waiting, OnWay, Delivered, Unconfirmed, Cancelled
        """
        payload = {
            "organizationId": organization_id,
            "orderId": order_id,
            "deliveryStatus": delivery_status
        }
        return await self._request(
            "POST", "/api/1/deliveries/update_order_delivery_status", 
            payload,
            api_login=api_login,
            organization_id=organization_id
        )

    async def change_order_payments(
        self,
        organization_id: str,
        order_id: str,
        payments: List[Dict[str, Any]],
        api_login: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Изменение списка оплат заказа.
        payments: список словарей с полями paymentTypeKind, sum, paymentTypeId
        """
        payload = {
            "organizationId": organization_id,
            "orderId": order_id,
            "payments": payments
        }
        return await self._request(
            "POST", "/api/1/deliveries/change_payments", 
            payload,
            api_login=api_login,
            organization_id=organization_id
        )

    async def close_delivery(
        self,
        organization_id: str,
        order_id: str,
        api_login: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Закрытие доставки в iiko Cloud. 
        Оплаты должны быть добавлены заранее через change_order_payments.
        """
        payload = {
            "organizationId": organization_id,
            "orderId": order_id
        }
        return await self._request(
            "POST", "/api/1/deliveries/close", 
            payload,
            api_login=api_login,
            organization_id=organization_id
        )

    # =========================================================================
    # Shifts and Couriers (iiko Cloud)
    # =========================================================================

    async def get_active_couriers(
        self,
        organization_id: str,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получение списка активных курьеров (с открытыми сменами) через эндпоинт локаций"""
        payload = {
            "organizationIds": [organization_id]
        }
        data = await self._request(
            "POST", "/api/1/employees/couriers/active_location", 
            payload,
            api_login=api_login,
            organization_id=organization_id
        )
        
        # Обработка ответа: маппинг из activeCourierLocations -> items
        couriers = []
        if isinstance(data, dict):
            locations = data.get("activeCourierLocations", [])
            for loc in locations:
                items = loc.get("items", [])
                for item in items:
                    couriers.append({
                        "id": item.get("courierId"),
                        "latitude": item.get("lastActiveLatitude"),
                        "longitude": item.get("lastActiveLongitude"),
                        "lastActiveClientDate": item.get("lastActiveClientDate")
                    })
        return couriers

    async def get_cash_shifts(
        self,
        organization_id: str,
        date_from: datetime,
        date_to: datetime,
        status: Optional[str] = "OPEN",
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получение списка кассовых смен"""
        payload = {
            "organizationIds": [organization_id],
            "openDateFrom": date_from.strftime("%Y-%m-%d %H:%M:%S.000"),
            "openDateTo": date_to.strftime("%Y-%m-%d %H:%M:%S.000")
        }
        if status:
            payload["status"] = status

        data = await self._request(
            "POST", "/api/1/cashshifts/list", 
            payload,
            api_login=api_login,
            organization_id=organization_id
        )
        return data.get("cashShifts", [])

# Глобальный экземпляр сервиса
iiko_service = IikoService()
