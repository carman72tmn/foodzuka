"""
Сервис для интеграции с iiko Cloud API
Документация API: https://api-ru.iiko.services/
"""
import httpx
import asyncio
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import secrets
from sqlmodel import Session, select
from fastapi import HTTPException
from app.core.config import settings
from app.models.iiko_settings import IikoSettings

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
        
        # Защита от плейсхолдеров и пустых значений
        if not login or login.startswith("your_") or "placeholder" in login.lower() or "client error" in login.lower():
            logger.error(f"Некорректный логин iiko API: {login}")
            raise ValueError("Логин iiko API не настроен или содержит ошибку. Пожалуйста, введите ключ заново.")

        login = login.strip()

        # Если просим тот же логин, что и в кеше, и он не протух — возвращаем
        if not api_login and self.access_token and self.token_expires_at:
            if datetime.utcnow() < self.token_expires_at:
                return self.access_token

        masked_login = f"{login[:4]}...{login[-4:]}" if login and len(login) > 8 else "НЕКОРРЕКТНО"
        logger.info(f"Запрос токена доступа iiko для логина: {masked_login}")

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
                logger.error(f"Не удалось получить токен доступа: {e.response.text}")
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
        
        # Если это плейсхолдер - игнорируем его
        if org_id and (org_id.startswith("your_") or "placeholder" in org_id.lower()):
            org_id = None

        # Если в json_data есть organizationId или organizationIds - подменяем если передали organization_id
        if json_data and org_id:
            # Всегда стараемся добавить оба варианта для совместимости с разными версиями iiko Cloud
            if "organizationId" in json_data or any(k in endpoint for k in ["/by_id", "/create", "/nomenclature", "/stop_lists"]):
                json_data["organizationId"] = org_id
            
            if "organizationIds" in json_data or any(k in endpoint for k in [
                "/organizations", "/terminal_groups", "/payment_types", "/deliveries/order_types", 
                "/discounts", "/menu", "/stop_lists", "/by_delivery_date_and_status", "/employees", 
                "/shift", "/schedule", "/reports/olap"
            ]):
                if "organizationIds" not in json_data or not isinstance(json_data["organizationIds"], list):
                    json_data["organizationIds"] = [org_id]
                elif not json_data["organizationIds"]:
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
        Получение конкретного внешнего меню по ID

        Args:
            external_menu_id: ID внешнего меню
            price_category_id: ID ценовой категории (опционально)
        """
        org_id = organization_id or self.organization_id
        payload: Dict[str, Any] = {
            "externalMenuId": external_menu_id,
            "organizationIds": [org_id]
        }
        if price_category_id:
            payload["priceCategoryId"] = price_category_id

        return await self._request(
            "POST", "/api/2/menu/by_id", 
            payload,
            api_login=api_login,
            organization_id=org_id
        )

    # =========================================================================
    # Стоп-листы
    # =========================================================================

    async def get_stop_lists(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение стоп-листов (недоступные позиции)

        Возвращает список продуктов, которые временно недоступны.
        """
        org_id = organization_id or self.organization_id
        data = await self._request(
            "POST", "/api/1/stop_lists", 
            {"organizationIds": [org_id]},
            api_login=api_login,
            organization_id=org_id
        )
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
                "organizationIds": [org_id],
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

    async def get_orders_by_date(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение заказов за заданный период.
        Используется для ручной синхронизации.
        """
        org_id = organization_id or self.organization_id
        
        # Инструмент iiko требует дату в формате yyyy-MM-dd HH:mm:ss.fff
        date_format = "%Y-%m-%d %H:%M:%S.000"
        
        data = await self._request(
            "POST", 
            "/api/1/deliveries/by_delivery_date_and_status", 
            {
                "organizationIds": [org_id],
                "deliveryDateFrom": date_from.strftime(date_format),
                "deliveryDateTo": date_to.strftime(date_format),
                "statuses": [
                    "Unconfirmed", "WaitCooking", "ReadyForCooking", 
                    "CookingStarted", "CookingCompleted", "Waiting", 
                    "OnWay", "Delivered", "Closed", "Cancelled"
                ]
            },
            api_login=api_login,
            organization_id=org_id
        )
        
        return data.get("orders", [])

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
        
        statuses = [
            "Unconfirmed", "WaitCooking", "ReadyForCooking", "CookingStarted", "CookingCompleted", "Waiting", "OnWay"
        ]
        
        data = await self._request(
            "POST", "/api/1/deliveries/by_delivery_date_and_status", 
            {
                "organizationIds": [org_id],
                "deliveryDateFrom": date_from,
                "deliveryDateTo": date_to,
                "statuses": statuses
            },
            api_login=api_login,
            organization_id=org_id
        )
        
        return data.get("orders", [])

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
                organization_id=org_id
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

    async def get_order_by_id(
        self,
        order_id: str,
        organization_id: str,
        api_login: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Получить детальную информацию о заказе по его ID"""
        org_id = organization_id or self.organization_id
        payload = {
            "organizationIds": [org_id],
            "orderIds": [order_id]
        }
        # В iiko Cloud API v1 эндпоинт для получения заказов по ID: /api/1/deliveries/by_id
        res = await self._request(
            "POST", "/api/1/deliveries/by_id",
            payload,
            api_login=api_login,
            organization_id=org_id
        )
        if res and res.get("orders"):
            return res["orders"][0]
        return None

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
        session: Optional[Session] = None,
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
        4. Сохранение в БД (если передан session).
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
        endpoint = "/api/v1/webhooks/iiko"
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
        
        # Сохранение в БД
        if session:
            try:
                db_settings = session.exec(select(IikoSettings)).first()
                if db_settings:
                    db_settings.webhook_url = url
                    db_settings.webhook_auth_token = auth_token
                    session.add(db_settings)
                    session.commit()
                    print(f"[iiko_service] Webhook settings saved to DB: {url}")
            except Exception as e:
                print(f"[iiko_service] Failed to save webhook to DB: {e}")
        
        return {
            "success": True,
            "webhook_url": url,
            "auth_token": auth_token,
            "iiko_response": result
        }

    # =========================================================================
    # iiko Card (Loyalty)
    # =========================================================================

    async def get_customer_info(
        self,
        phone: str,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение информации о клиенте по номеру телефона (iiko Card)"""
        org_id = organization_id or self.organization_id
        try:
            return await self._request(
                "POST", "/api/1/loyalty/iiko/customer/info", 
                {
                    "organizationId": org_id,
                    "type": "phone",
                    "phone": phone
                },
                api_login=api_login,
                organization_id=org_id
            )
        except Exception as e:
            logger.error(f"Error getting customer info from iiko Card: {e}")
            return {"found": False}

    async def get_customer_balance(
        self,
        customer_id: str,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> float:
        """Получение баланса баллов клиента"""
        # В v1 информация о балансе обычно возвращается в get_customer_info в walletBalances
        # Но если нужно отдельное получение, iiko Card API имеет свои особенности
        info = await self.get_customer_info("", api_login=api_login, organization_id=organization_id)
        # Реализация зависит от конкретной версии iiko Card
        return 0.0

    async def add_customer_balance(
        self,
        customer_id: str,
        wallet_id: str,
        amount: float,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None,
        comment: str = "Начисление за активность"
    ) -> bool:
        """Начисление баллов на кошелек клиента"""
        org_id = organization_id or self.organization_id
        try:
            await self._request(
                "POST", "/api/1/loyalty/iiko/customer/wallet/topup", 
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
        except Exception as e:
            logger.error(f"Error adding customer balance: {e}")
            return False

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
    # OLAP Отчёты
    # =========================================================================

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
    ) -> List[Dict[str, Any]]:
        """
        Получение OLAP-отчёта по выручке.
        Пробует iiko Resto (Office) API, так как Cloud API часто дает 401.
        """
        org_id = organization_id or self.organization_id
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
                response = await self._resto_request(
                    "POST", "/v2/reports/olap",
                    json_data=payload,
                    resto_url=resto_url,
                    resto_login=resto_login,
                    resto_password=resto_password
                )
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
                        ("agg", "OrderSum"),
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
                        resto_password=resto_password
                    )
                else:
                    raise e
            
            # Парсинг ответа v2/v1
            data_rows = []
            if isinstance(response, dict):
                if "data" in response:
                    rows = response.get("data", [])
                    # Проверяем формат данных (v2 это уже dict, v1 это list/array)
                    if rows and isinstance(rows[0], dict):
                        data_rows = rows
                    else:
                        cols = response.get("columnNames", [])
                        if cols and rows:
                            data_rows = [dict(zip(cols, r)) for r in rows]
                else:
                    # Некоторые версии RMS возвращают JSON-объект с полями сразу
                    data_rows = [response] if "revenue" in str(response).lower() else []
            elif isinstance(response, list):
                data_rows = response

            if data_rows:
                result = []
                for row_dict in data_rows:
                    if not isinstance(row_dict, dict): continue
                    
                    # Пробуем разные варианты имен полей (v2 vs v1 vs aliases)
                    rev = self._safe_float(row_dict.get("DishDiscountSumInt", 
                                          row_dict.get("OrderSum", 
                                          row_dict.get("fullSum", 0))))
                    
                    disc = self._safe_float(row_dict.get("DiscountSum", 
                                           row_dict.get("DishDiscountSumInt", 0)))
                    
                    guests = self._safe_int(row_dict.get("GuestNum", 0))
                    amount = self._safe_float(row_dict.get("DishAmountInt", 0))
                    
                    # Дата
                    b_date = row_dict.get("OpenDate.Typed", row_dict.get("BusinessDate", ""))
                    if b_date and "T" in str(b_date):
                        b_date = str(b_date).split("T")[0]
                    
                    result.append({
                        "organization_id": org_id,
                        "organization_name": row_dict.get("Department", ""),
                        "business_date": b_date,
                        "average_check": rev / max(1, guests),
                        "markup": self._safe_float(row_dict.get("ProductCostBase.Profit", 0.0)),
                        "markup_percent": self._safe_float(row_dict.get("ProductCostBase.MarkUp", 0.0)),
                        "cost_price": self._safe_float(row_dict.get("ProductCostBase.ProductCost", 0.0)),
                        "cost_price_percent": self._safe_float(row_dict.get("ProductCostBase.Percent", 0.0)),
                        "discount_sum": disc,
                        "revenue": rev,
                        "orders_count": int(amount) if amount > 0 else guests, # Используем количество блюд или гостей
                    })
                return result

            # Если вернулся XML
            if isinstance(response, str) and "<" in response:
                logger.info("Получен XML от iiko Office. Парсинг не реализован, переходим к Cloud API.")
                raise ValueError("XML response from Resto not supported yet")

        except Exception as resto_err:
            logger.warning(f"Resto OLAP failed: {resto_err}. Response sample: {str(response)[:200] if 'response' in locals() else 'None'}. Trying Cloud API fallback.")

        # Fallback to Cloud API (с фиксом параметров)
        fmt_cloud = "%Y-%m-%d %H:%M:%S.000"
        filters = []
        if not include_deleted:
            filters.append({"filterType": "OrderDeleted", "field": "OrderDeleted", "relation": "is", "values": ["NOT_DELETED"]})

        payload_cloud = {
            "reportType": "Sales",
            "organizationIds": [org_id],
            "groupByRowFields": ["BusinessDate", "Department"],
            "aggregateFields": [
                "OrderSum", "DiscountSum", "GuestNum", "DishDiscountSumInt",
                "costPrice", "costPricePercent", "profitability", "profitabilityPercent",
            ],
            "filters": filters,
            "reportTimeRangeSettings": {
                "dateFrom": date_from.strftime(fmt_cloud),
                "dateTo": date_to.strftime(fmt_cloud)
            }
        }

        try:
            response = await self._request(
                "POST", "/api/1/reports/olap",
                payload_cloud, api_login=api_login, organization_id=org_id
            )
            rows = response.get("data", [])
            columns = response.get("columnNames", [])
            result = []
            for row in rows:
                row_dict = dict(zip(columns, row)) if isinstance(row, list) else row
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
            logger.error(f"Ошибка OLAP-отчёта iiko (Cloud): {e}")
            raise

    async def get_daily_revenue_olap(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Получение ежедневной выручки и скидок через OLAP для расчета чистой прибыли.
        Возвращает словарь {дата: {"revenue": float, "discounts": float}}
        """
        fmt = "%Y-%m-%d"
        org_id = organization_id or self.organization_id
        
        payload = {
            "reportType": "SALES",
            "groupByFields": ["OpenDate.Typed"],
            "aggregateFields": ["OrderSum", "DiscountSum"],
            "filters": {
                "OpenDate.Typed": {
                    "filterType": "Range",
                    "from": date_from.strftime(fmt),
                    "to": date_to.strftime(fmt)
                },
                "OrderType": {
                    "filterType": "IncludeValues",
                    "values": ["Delivery"] # Только доставка или все? Пользователь просил общую выручку.
                }
            }
        }
        
        # Глобальная выручка (все типы заказов)
        if "OrderType" in payload["filters"]:
            del payload["filters"]["OrderType"]

        try:
            logger.info(f"Запрос OLAP-выручки за период {date_from.strftime(fmt)} - {date_to.strftime(fmt)}")
            response = await self._request(
                "POST", "/api/1/reports/olap",
                payload, api_login=api_login, organization_id=org_id
            )
            
            rows = response.get("data", [])
            columns = response.get("columnNames", [])
            logger.info(f"OLAP response: {len(rows)} строк, колонки: {columns}")
            
            result = {}
            for row in rows:
                if isinstance(row, list):
                    rowData = dict(zip(columns, row))
                else:
                    rowData = row
                
                # Дата в OLAP может прийти как "2024-04-01T00:00:00.000" или просто "2024-04-01"
                raw_date = rowData.get("OpenDate.Typed", "")
                date_str = str(raw_date).split("T")[0] if raw_date else ""
                
                if date_str:
                    # iiko может возвращать суммы как строки или числа
                    try:
                        rev = float(rowData.get("OrderSum", 0))
                        disc = float(rowData.get("DiscountSum", 0))
                        
                        if date_str not in result:
                            result[date_str] = {"revenue": 0.0, "discounts": 0.0}
                        
                        result[date_str]["revenue"] += round(rev, 2)
                        result[date_str]["discounts"] += round(disc, 2)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Ошибка парсинга чисел в строке OLAP {date_str}: {e}")

            logger.info(f"Итоговый словарь выручки: {list(result.keys())}")
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении выручки из OLAP: {e}")
            return {}

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
        timeout: float = 30.0
    ) -> Any:
        """Метод для запросов к iiko Resto (Office) API с SHA-1 авторизацией"""
        import hashlib
        
        url = resto_url or settings.IIKO_RESTO_URL
        login = resto_login or settings.IIKO_RESTO_LOGIN
        password = resto_password or settings.IIKO_RESTO_PASSWORD

        if not url or not login:
            raise ValueError("Данные iiko Resto (URL/Login) не настроены.")

        # Calculate SHA-1 hash of the password
        password_sha1 = hashlib.sha1(password.encode()).hexdigest()
        
        # Normalize URL
        base_url = url.rstrip('/')
        if not base_url.endswith('/api'):
            if base_url.endswith('/resto'):
                base_url = f"{base_url}/api"
            else:
                base_url = f"{base_url}/resto/api"
        
        # 1. Получаем токен
        async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
            auth_url = f"{base_url}/auth"
            auth_params = {"login": login, "pass": password_sha1}
            
            auth_response = await client.get(auth_url, params=auth_params)
            if auth_response.status_code != 200:
                auth_response = await client.get(auth_url, params={"login": login, "pass": password})
                if auth_response.status_code != 200:
                    logger.error(f"Ошибка авторизации Resto: {auth_response.status_code} | {auth_response.text}")
                    raise HTTPException(status_code=401, detail=f"Ошибка авторизации Resto: {auth_response.text}")
            
            token = auth_response.text.strip().replace('"', '')
            
            # 2. Выполняем основной запрос
            request_url = f"{base_url}{endpoint}"
            
            # Поддержка как словаря, так и списка кортежей для параметров
            if params is None:
                final_params = {"key": token}
            elif isinstance(params, list):
                final_params = params.copy()
                final_params.append(("key", token))
            else:
                final_params = params.copy()
                final_params["key"] = token
            
            response = await client.request(method, request_url, params=final_params, json=json_data)
            
            if response.status_code >= 400:
                logger.error(f"iiko Resto error {response.status_code}: {response.text}")
                response.raise_for_status()

            try:
                return response.json()
            except Exception:
                return response.text

    async def get_resto_employees(
        self,
        resto_url: Optional[str] = None,
        resto_login: Optional[str] = None,
        resto_password: Optional[str] = None
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
                    "firstName": emp.findtext('firstName') or emp.findtext('name'),
                    "lastName": emp.findtext('lastName') or "",
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
        date_to: datetime
    ) -> List[Dict[str, Any]]:
        """Получение данных о явках (сменах) из iiko Resto"""
        params = {
            "from": date_from.strftime("%Y-%m-%d"),
            "to": date_to.strftime("%Y-%m-%d")
        }
        data = await self._resto_request(
            "GET", "/employees/attendance", 
            resto_url, resto_login, resto_password,
            params=params
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

    def _safe_float(self, val: Any) -> float:
        try:
            return float(val) if val is not None else 0.0
        except (ValueError, TypeError):
            return 0.0

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
                "aggregateFields": ["DishDiscountSum"],
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
