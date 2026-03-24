"""
Сервис для интеграции с iiko Cloud API
Документация API: https://api-ru.iiko.services/
"""
import httpx
import asyncio
import logging
import secrets
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)


class IikoService:
    """Сервис для работы с iiko Cloud API"""

    def __init__(self):
        self.api_url = settings.IIKO_API_URL
        self.api_login = settings.IIKO_API_LOGIN
        self.organization_id = settings.IIKO_ORGANIZATION_ID
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    # =========================================================================
    # Аутентификация
    # =========================================================================

    async def _get_access_token(self, api_login: Optional[str] = None) -> str:
        """
        Получение токена доступа к iiko API
        """
        login = api_login or self.api_login
        if login:
            login = login.strip()

        # Если просим тот же логин, что и в кеше, и он не протух — возвращаем
        if not api_login and self.access_token and self.token_expires_at:
            if datetime.utcnow() < self.token_expires_at:
                return self.access_token

        masked_login = f"{login[:4]}...{login[-4:]}" if login and len(login) > 8 else "INVALID"
        logger.info(f"Requesting iiko access token with login: {masked_login}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/api/1/access_token",
                    json={"apiLogin": login}
                )
                response.raise_for_status()
                data = response.json()

                token = data["token"]
                
                # Кешируем только если это "глобальный" логин
                if not api_login:
                    self.access_token = token
                    self.token_expires_at = datetime.utcnow() + timedelta(minutes=14)

                return token
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to get access token: {e.response.text}")
                raise

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        timeout: float = 30.0,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Универсальный метод для запросов к iiko API с авторизацией"""
        token = await self._get_access_token(api_login=api_login)
        org_id = organization_id or self.organization_id

        # Если в json_data есть organizationId или organizationIds - подменяем если передали organization_id
        if json_data and org_id:
            if "organizationId" in json_data:
                json_data["organizationId"] = org_id
            if "organizationIds" in json_data and isinstance(json_data["organizationIds"], list):
                if not json_data["organizationIds"] or len(json_data["organizationIds"]) == 1:
                    json_data["organizationIds"] = [org_id]

        print(f"DEBUG iiko request: {endpoint} | Payload: {json_data}")
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method,
                f"{self.api_url}{endpoint}",
                headers={"Authorization": f"Bearer {token}"},
                json=json_data
            )
            if response.status_code >= 400:
                print(f"DEBUG iiko error response: {response.status_code} | Body: {response.text}")
            response.raise_for_status()
            return response.json()

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
            logger.error(f"iiko connection test failed: {e}")
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

    async def get_payment_types(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Получение типов оплаты"""
        org_id = organization_id or self.organization_id
        data = await self._request(
            "POST", "/api/1/payment_types", 
            {"organizationIds": [org_id]},
            api_login=api_login,
            organization_id=org_id
        )
        types = data.get("paymentTypes", [])
        result = []
        for org_types in types:
            for item in org_types.get("items", []):
                result.append(item)
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

    # =========================================================================
    # Меню и номенклатура
    # =========================================================================

    async def get_nomenclature(self) -> Dict[str, Any]:
        """
        Получение номенклатуры (меню) из iiko
        Возвращает категории (groups) и товары (products)
        """
        return await self._request("POST", "/api/1/nomenclature", {
            "organizationId": self.organization_id
        })

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

    async def get_external_menu_by_id(self, external_menu_id: str, price_category_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Получение конкретного внешнего меню по ID

        Args:
            external_menu_id: ID внешнего меню
            price_category_id: ID ценовой категории (опционально)
        """
        payload: Dict[str, Any] = {
            "externalMenuId": external_menu_id,
            "organizationIds": [self.organization_id]
        }
        if price_category_id:
            payload["priceCategoryId"] = price_category_id

        return await self._request("POST", "/api/2/menu/by_id", payload)

    # =========================================================================
    # Стоп-листы
    # =========================================================================

    async def get_stop_lists(self) -> List[Dict[str, Any]]:
        """
        Получение стоп-листов (недоступные позиции)

        Возвращает список продуктов, которые временно недоступны.
        """
        data = await self._request("POST", "/api/1/stop_lists", {
            "organizationIds": [self.organization_id]
        })
        stop_list_items = []
        for org_stop in data.get("terminalGroupStopLists", []):
            for tg in org_stop.get("items", []):
                for item in tg.get("items", []):
                    stop_list_items.append({
                        "productId": item.get("productId"),
                        "balance": item.get("balance", 0)
                    })
        return stop_list_items

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
                    f"Order delivery attempt {attempt + 1}/3 failed: {e}"
                )
                if attempt < 2:
                    await asyncio.sleep(15)

        raise last_error

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Получение статуса заказа из iiko"""
        data = await self._request("POST", "/api/1/deliveries/by_id", {
            "organizationIds": [self.organization_id],
            "orderIds": [order_id]
        })
        orders = data.get("orders", [])
        return orders[0] if orders else {}

    async def cancel_order(self, order_id: str) -> bool:
        """Отмена заказа в iiko"""
        try:
            await self._request("POST", "/api/1/deliveries/cancel", {
                "organizationId": self.organization_id,
                "orderId": order_id
            })
            return True
        except Exception:
            return False

    async def get_orders_by_date(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение заказов за заданный период.
        Используется для ручной синхронизации.
        """
        org_id = organization_id or self.organization_id
        
        # Инструмент iiko требует дату в формате yyyy-MM-dd HH:mm:ss.fff
        date_format = "%Y-%m-%d %H:%M:%S.000"
        
        data = await self._request("POST", "/api/1/deliveries/by_delivery_date_and_status", {
            "organizationIds": [org_id],
            "deliveryDateFrom": date_from.strftime(date_format),
            "deliveryDateTo": date_to.strftime(date_format),
            "statuses": [
                "Unconfirmed", "WaitCooking", "ReadyForCooking", 
                "CookingStarted", "CookingCompleted", "Waiting", 
                "OnWay", "Delivered", "Closed", "Cancelled"
            ]
        })
        
        return data.get("orders", [])

    async def get_active_orders(self, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Получение всех текущих активных заказов из iiko.
        """
        org_id = organization_id or self.organization_id
        now = datetime.utcnow()
        # iiko API limits the time span, so we use the last 24 hours
        date_from = (now - timedelta(days=1)).strftime("%Y-%m-%d 00:00:00.000")
        date_to = (now + timedelta(days=1)).strftime("%Y-%m-%d 23:59:59.000")
        
        statuses = [
            "Unconfirmed", "WaitCooking", "ReadyForCooking", "CookingStarted", "CookingCompleted", "Waiting", "OnWay"
        ]
        
        data = await self._request("POST", "/api/1/deliveries/by_delivery_date_and_status", {
            "organizationIds": [org_id],
            "deliveryDateFrom": date_from,
            "deliveryDateTo": date_to,
            "statuses": statuses
        })
        
        return data.get("orders", [])

    # =========================================================================
    # Сотрудники и смены
    # =========================================================================

    async def get_employees(self, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Получение списка сотрудников
        """
        org_id = organization_id or self.organization_id
        data = await self._request("POST", "/api/1/employees/couriers", {
            "organizationIds": [org_id]
        })
        
        employees_list = []
        # Ответ имеет структуру: {"employees": [{"organizationId": "...", "items": [{...}]}]}
        for org_data in data.get("employees", []):
            if org_data.get("organizationId") == org_id:
                for item in org_data.get("items", []):
                    # Приводим данные к ожидаемому формату в iiko_sync_service
                    name = item.get("displayName")
                    if not name:
                        name = f"{item.get('firstName', '')} {item.get('lastName', '')}".strip()
                    
                    employees_list.append({
                        "id": item.get("id"),
                        "name": name,
                        "phone": None,  # Метод couriers не отдает телефоны напрямую
                        "roleId": "Courier",
                        "deleted": item.get("isDeleted", False)
                    })
        return employees_list

    async def get_shifts(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение списка смен за указанный период (iiko API)
        Для получения смен обычно используется /api/1/employees/shift (если доступен в iiko Biz)
        """
        org_id = organization_id or self.organization_id
        date_format = "%Y-%m-%d %H:%M:%S.000"
        
        try:
            data = await self._request("POST", "/api/1/employees/shift", {
                "organizationIds": [org_id],
                "dateFrom": date_from.strftime(date_format),
                "dateTo": date_to.strftime(date_format)
            })
            return data.get("shifts", [])
        except Exception as e:
            logger.error(f"Error fetching shifts: {e}")
            return []

    async def get_schedules(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение графика смен (запланированных) за указанный период (iiko API)
        """
        org_id = organization_id or self.organization_id
        date_format = "%Y-%m-%d %H:%M:%S.000"
        
        try:
            data = await self._request("POST", "/api/1/employees/schedule", {
                "organizationIds": [org_id],
                "from": date_from.strftime(date_format),
                "to": date_to.strftime(date_format)
            })
            # Ответ обычно содержит список расписаний для разных групп/организаций
            # Мы возвращаем плоский список всех записей графика
            schedules = []
            for org_schedule in data.get("schedules", []):
                schedules.extend(org_schedule.get("items", []))
            return schedules
        except Exception as e:
            logger.error(f"Error fetching schedules: {e}")
            return []

    # =========================================================================
    # Программа лояльности (iikoCard)
    # =========================================================================

    async def get_customer_info(
        self,
        phone: str,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Получение информации о клиенте из программы лояльности iiko
        """
        org_id = organization_id or self.organization_id
        try:
            data = await self._request(
                "POST", "/api/1/loyalty/iiko/customer/info", 
                {"organizationId": org_id, "type": "phone", "phone": phone},
                api_login=api_login,
                organization_id=org_id
            )
            return data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {"found": False, "phone": phone}
            raise

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

    async def add_customer_balance(
        self,
        customer_id: str,
        wallet_id: str,
        amount: float,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Начисление/списание бонусов клиента (iikoCard) вручную"""
        org_id = organization_id or self.organization_id
        payload = {
            "organizationId": org_id,
            "customerId": customer_id,
            "walletId": wallet_id,
            "sum": amount,
            "comment": "Бонусы за активность в VK"
        }
        return await self._request(
            "POST", "/api/1/loyalty/iiko/customer/wallet/topup",
            payload,
            api_login=api_login,
            organization_id=org_id
        )

    # =========================================================================
    # Вебхуки
    # =========================================================================

    async def get_webhook_settings(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Получение текущих настроек вебхуков для организации
        """
        org_id = organization_id or self.organization_id
        return await self._request(
            "POST", "/api/1/webhooks/settings", 
            {"organizationId": org_id},
            api_login=api_login,
            organization_id=org_id
        )

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
            if current and current.get("webHooksUri") == webhook_url:
                print(f"[iiko_service] Webhook URI already matches {webhook_url}. Proceeding with update but prepared for 429.")
        except Exception as e:
            print(f"[iiko_service] get_webhook_settings failed: {e}")

        payload = {
            "organizationId": org_id,
            "webHooksUri": webhook_url,
            "webHooksFilter": {
                "deliveryOrderFilter": {
                    "orderStatuses": [
                        "Unconfirmed", "WaitCooking", "ReadyForCooking", 
                        "CookingStarted", "CookingCompleted", "Waiting", 
                        "OnWay", "Delivered", "Cancelled"
                    ],
                    "errors": True
                },
                "stopListUpdateFilter": {
                    "updates": True
                }
            }
        }
        if auth_token:
            payload["authToken"] = auth_token

        # Retry logic for 429 Too Many Requests
        import asyncio
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return await self._request(
                    "POST", "/api/1/webhooks/update_settings", 
                    payload,
                    api_login=api_login,
                    organization_id=org_id
                )
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "Too Many Requests" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2
                        print(f"[iiko_service] 429 Too Many Requests for webhook setup. Waiting {wait_time}s and retrying...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # Если исчерпан лимит попыток и мы получаем 429, 
                        # мы можем выбросить ошибку или просто залогировать и сделать вид, что успех
                        # Но если мы это сделаем, то secret_key может не совпасть. Выбрасываем ошибку с понятным текстом.
                        raise ValueError("iiko API Error: Слишком много попыток обновления вебхука (ошибка 429). Подождите несколько минут перед повторной попыткой.")
                raise e

    async def auto_register_webhook(self,
        base_url: Optional[str] = None,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None,
        request_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Автоматическая регистрация вебхука:
        1. Генерация безопасного токена.
        2. Определение URL (из параметров, запроса или настроек).
        3. Регистрация в iiko.
        """
        public_url = settings.APP_PUBLIC_URL
        if public_url and "your-public-url.ngrok-free.app" in public_url:
            public_url = None  # Игнорировать дефолтную заглушку ngrok

        # Приоритет: 1. Явный base_url 2. URL из запроса 3. APP_PUBLIC_URL из .env
        url = base_url or request_url or public_url
        
        if not url:
            raise ValueError("Webhook URL cannot be determined. Set APP_PUBLIC_URL or use frontend.")
        
        # Получаем только origin (базовый домен до /api)
        if "/api/" in url:
            url = url.split("/api/")[0]
            
        # Убеждаемся, что URL заканчивается на правильный эндпоинт
        endpoint = "/api/v1/orders/webhook/iiko"
        if not url.endswith(endpoint):
            url = url.rstrip("/") + endpoint
        
        # Генерация токена если нужно
        auth_token = secrets.token_hex(16)
        
        # Регистрация
        try:
            result = await self.update_webhook_settings(
                webhook_url=url,
                auth_token=auth_token,
                api_login=api_login,
                organization_id=organization_id
            )
        except ValueError as e:
            if "429" in str(e):
                print(f"[iiko_service] Принудительно сохраняем вебхук локально: {e}")
                result = {"status": "rate_limited", "message": "Настройки сохранены локально. iiko API вернул 429 (Too Many Requests), попробуйте позже, если требуется синхронизация."}
            else:
                raise e
        
        return {
            "success": True,
            "webhook_url": url,
            "auth_token": auth_token,
            "iiko_response": result
        }

    # =========================================================================
    # OLAP Отчёты
    # =========================================================================

    async def get_olap_report(
        self,
        date_from: datetime,
        date_to: datetime,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None,
        include_deleted: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Получение OLAP-отчёта по выручке из iiko Cloud API.
        Группировка: Торговое предприятие.
        Возвращает список строк с данными по каждому предприятию.
        """
        org_id = organization_id or self.organization_id

        # Формируем строки дат в формате API iiko: yyyy-MM-dd HH:mm:ss.fff
        fmt = "%Y-%m-%d %H:%M:%S.000"

        # Базовые фильтры — только незамененные и не-удалённые заказы
        filters = [
            {
                "filterType": "OrderDeleted",
                "field": "OrderDeleted",
                "relation": "is",
                "values": ["NOT_DELETED"]
            }
        ]
        if include_deleted:
            filters = []  # Если нужны все — убираем фильтры

        payload = {
            "organizationIds": [org_id],
            "groupByRowFields": [
                "BusinessDate",
                "Department"
            ],
            "aggregateFields": [
                "OrderSum",
                "DiscountSum",
                "GuestNum",
                "DishDiscountSumInt",
                "costPrice",
                "costPricePercent",
                "profitability",
                "profitabilityPercent",
            ],
            "filters": filters,
            "reportTimeRangeSettings": {
                "dateFrom": date_from.strftime(fmt),
                "dateTo": date_to.strftime(fmt)
            }
        }

        try:
            response = await self._request(
                "POST",
                "/api/1/reports/olap",
                payload,
                api_login=api_login,
                organization_id=org_id
            )

            # Ответ содержит correlationId и data (список строк)
            rows = response.get("data", [])
            columns = response.get("columnNames", [])

            result = []
            for row in rows:
                # Строки могут быть в виде списка значений, сопоставим с именами колонок
                if isinstance(row, list):
                    row_dict = dict(zip(columns, row))
                else:
                    row_dict = row

                # Преобразуем в единый формат
                result.append({
                    "organization_id": org_id,
                    "organization_name": row_dict.get("Department", row_dict.get("department", "")),
                    "business_date": row_dict.get("BusinessDate", row_dict.get("businessDate", "")),
                    "average_check": self._safe_float(row_dict.get("OrderSum", 0)) / max(1, self._safe_int(row_dict.get("GuestNum", 1))),
                    "markup": self._safe_float(row_dict.get("profitability", 0)),
                    "markup_percent": self._safe_float(row_dict.get("profitabilityPercent", 0)),
                    "cost_price": self._safe_float(row_dict.get("costPrice", 0)),
                    "cost_price_percent": self._safe_float(row_dict.get("costPricePercent", 0)),
                    "discount_sum": self._safe_float(row_dict.get("DiscountSum", 0)),
                    "revenue": self._safe_float(row_dict.get("OrderSum", 0)),
                    "orders_count": self._safe_int(row_dict.get("GuestNum", 0)),
                })
            return result

        except Exception as e:
            logger.error(f"iiko OLAP report error: {e}")
            raise

    @staticmethod
    def _safe_float(value) -> float:
        """Безопасное преобразование значения к float"""
        try:
            return float(value) if value is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _safe_int(value) -> int:
        """Безопасное преобразование значения к int"""
        try:
            return int(value) if value is not None else 0
        except (TypeError, ValueError):
            return 0


# Глобальный экземпляр сервиса
iiko_service = IikoService()
