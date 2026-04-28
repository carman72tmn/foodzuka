"""
    iiko Cloud API
 API: https://api-ru.iiko.services/
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
    """    iiko Cloud API"""

    def __init__(self):
        self.api_url = settings.IIKO_API_URL
        self.api_login = settings.IIKO_API_LOGIN
        self.organization_id = settings.IIKO_ORGANIZATION_ID
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    # =========================================================================
    # 
    # =========================================================================

    async def _get_access_token(self, api_login: Optional[str] = None) -> str:
        """
            iiko API
        """
        login = api_login or self.api_login
        
        #      
        if not login or login.startswith("your_") or "placeholder" in login.lower() or "client error" in login.lower():
            logger.error(f"  iiko API: {login}")
            raise ValueError(" iiko API     . ,   .")

        login = login.strip()

        #     ,    ,      
        if not api_login and self.access_token and self.token_expires_at:
            if datetime.utcnow() < self.token_expires_at:
                return self.access_token

        masked_login = f"{login[:4]}...{login[-4:]}" if login and len(login) > 8 else ""
        logger.info(f"   iiko  : {masked_login}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/api/1/access_token",
                    json={"apiLogin": login}
                )
                response.raise_for_status()
                data = response.json()

                token = data["token"]
                
                #     "" 
                if not api_login:
                    self.access_token = token
                    self.token_expires_at = datetime.utcnow() + timedelta(minutes=14)

                return token
            except httpx.HTTPStatusError as e:
                logger.error(f"    : {e.response.text}")
                raise

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        timeout: float = 30.0,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None,
        _is_retry: bool = False
    ) -> Dict[str, Any]:
        """     iiko API  """
        token = await self._get_access_token(api_login=api_login)
        org_id = organization_id or self.organization_id
        
        #    -  
        if org_id and (org_id.startswith("your_") or "placeholder" in org_id.lower()):
            org_id = None

        #   (    )
        payload = json_data.copy() if json_data else {}

        #   payload  organizationId  organizationIds -    organization_id
        if org_id:
            #           iiko Cloud
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
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method,
                f"{self.api_url}{endpoint}",
                headers={"Authorization": f"Bearer {token}"},
                json=payload
            )
            
            #  401 (Unauthorized) -     
            if response.status_code == 401 and not _is_retry:
                logger.warning(f"iiko API 401 Unauthorized for {endpoint}. Retrying with fresh token...")
                self.access_token = None
                self.token_expires_at = None
                return await self._request(
                    method, endpoint, json_data, timeout, 
                    api_login, organization_id, _is_retry=True
                )

            if response.status_code >= 400:
                logger.error(f"iiko API Error: {response.status_code} | URL: {endpoint} | Body: {response.text}")
                response.raise_for_status()
                
            return response.json()

    # =========================================================================
    #  
    # =========================================================================

    async def test_connection(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
           iiko API
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
            logger.error(f"     iiko: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # =========================================================================
    #   
    # =========================================================================

    async def get_organizations(
        self,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """   """
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
        """    """
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
        """   """
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
        """  """
        org_id = organization_id or self.organization_id
        logger.info(f"     {org_id}")
        data = await self._request(
            "POST", "/api/1/payment_types", 
            {"organizationIds": [org_id]},
            api_login=api_login,
            organization_id=org_id
        )
        types = data.get("paymentTypes", [])
        logger.info(f" {len(types)}     iiko Cloud")
        result = []
        for org_types in types:
            items = org_types.get("items", [])
            logger.debug(f" {org_types.get('organizationId')}: {len(items)} ")
            for item in items:
                result.append(item)
        logger.info(f":  {len(result)}  ")
        return result

    async def get_order_types(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """  """
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
        """   """
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
    #   
    # =========================================================================

    async def get_nomenclature(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
          ()  iiko
          (groups)   (products)
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
        """   (, )"""
        org_id = organization_id or self.organization_id
        data = await self._request(
            "POST", "/api/1/delivery_restrictions", 
            {"organizationIds": [org_id]},
            api_login=api_login,
            organization_id=org_id
        )
        # ,      'deliveryRestrictions'
        # iiko    {"deliveryRestrictions": [...]},        API
        if isinstance(data, list):
            return {"deliveryRestrictions": data}
        if isinstance(data, dict) and "deliveryRestrictions" not in data:
            return {"deliveryRestrictions": [data]}
        return data

    async def get_external_menus(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
           
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
             ID  API v2.
        
          HTTP- ( _request)  
         'organizationId' ( s),    400.
        
         iiko   'Price category id is not correct',
               
               .
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
            
            logger.info(f" iiko  ID={external_menu_id} (org={org_id}, priceCategoryId={pcid})")
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{self.api_url}/api/2/menu/by_id",
                    headers={"Authorization": f"Bearer {token}"},
                    json=payload
                )
            return resp

        # 1.   
        response = await _do_raw_request(price_category_id)
        
        if response.status_code == 401:
            self.access_token = None
            self.token_expires_at = None
            token = await self._get_access_token(api_login=api_login)
            response = await _do_raw_request(price_category_id)
            
        # 2.  400        -
        if response.status_code == 400:
            try:
                err_body = response.json()
            except:
                err_body = {}
            
            if "Price category" in err_body.get("errorDescription", "") or err_body.get("error") == "EXTERNAL_MENU_DATA_MISSED":
                logger.warning(f"iiko  priceCategoryId   {external_menu_id}.  -...")
                
                #   "" () 
                base_pcid = "00000000-0000-0000-0000-000000000000"
                if price_category_id != base_pcid:
                    logger.info(f"   : {base_pcid}")
                    response = await _do_raw_request(base_pcid)
                
                #    400          
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
                            #     
                            found_pcid = None
                            for menu in menus_data.get("externalMenus", []):
                                if str(menu.get("id")) == str(external_menu_id):
                                    price_cats = menu.get("priceCategories", [])
                                    if price_cats:
                                        found_pcid = price_cats[0].get("id") or price_cats[0].get("priceCategoryId")
                                        break
                            
                            #     ,      priceCategories ( )
                            if not found_pcid and menus_data.get("priceCategories"):
                                found_pcid = menus_data["priceCategories"][0].get("id")

                            if found_pcid:
                                logger.info(f"  : {found_pcid}.  .")
                                response = await _do_raw_request(found_pcid)
                    except Exception as e:
                        logger.error(f"   -  : {e}")

        if response.status_code >= 400:
            logger.error(f"iiko /api/2/menu/by_id   {response.status_code}: {response.text}")
            response.raise_for_status()
            
        return response.json()



    # =========================================================================
    # -
    # =========================================================================

    async def get_stop_lists(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
         - ( )

          ,   .
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
    # 
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
            iiko  retry-

             15  ( 3 ).
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

        #  
        if payment_type_id and payment_sum:
            order_data["order"]["payments"] = [{
                "paymentTypeKind": "Cash",
                "paymentTypeId": payment_type_id,
                "sum": payment_sum,
                "isProcessedExternally": False
            }]

        #  
        if discount_info:
            order_data["order"]["discountsInfo"] = discount_info

        # Retry :  3    15 
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
                    f"   {attempt + 1}/3  : {e}"
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
        """    iiko"""
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
        """   iiko"""
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
            .
           .
        """
        org_id = organization_id or self.organization_id
        
        #  iiko     yyyy-MM-dd HH:mm:ss.fff
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
              iiko.
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
    #   
    # =========================================================================

    async def get_employees(
        self,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
           . 
           ,    -    .
        """
        org_id = organization_id or self.organization_id
        data = None
        used_fallback = False
        
        try:
            # 1.     (   Staff Management)
            data = await self._request(
                "POST", "/api/1/employees", 
                {"organizationIds": [org_id]},
                api_login=api_login,
                organization_id=org_id
            )
        except httpx.HTTPStatusError as e:
            #  401  403 -      ,  
            if e.response.status_code in [401, 403]:
                logger.warning(f"  /api/1/employees  (401/403).   /couriers.")
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
        #   : {"employees": [{"organizationId": "...", "items": [{...}]}]}
        for org_data in data.get("employees", []):
            if org_data.get("organizationId") == org_id:
                for item in org_data.get("items", []):
                    #    (displayName  firstName + lastName)
                    name = item.get("displayName")
                    if not name or name == "": #     
                        fname = item.get("firstName") or ""
                        lname = item.get("lastName") or ""
                        name = f"{fname} {lname}".strip() or "Unnamed"
                    
                    #   ( /couriers  )
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
              (iiko API)
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
            logger.error(f"   : {e}")
            return []

    async def get_schedules(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
           ()    (iiko API)
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
            #        /
            #       
            schedules = []
            for org_schedule in data.get("schedules", []):
                schedules.extend(org_schedule.get("items", []))
            return schedules
        except Exception as e:
            logger.error(f"   : {e}")
            return []

    # =========================================================================
    #   (iikoCard)
    # =========================================================================

    async def get_customer_info(
        self,
        phone: str,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
               iiko
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
        """   """
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
        """/   (iikoCard) """
        org_id = organization_id or self.organization_id
        payload = {
            "organizationId": org_id,
            "customerId": customer_id,
            "walletId": wallet_id,
            "sum": amount,
            "comment": "    VK"
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
        """       ID"""
        org_id = organization_id or self.organization_id
        payload = {
            "organizationIds": [org_id],
            "orderIds": [order_id]
        }
        #  iiko Cloud API v1      ID: /api/1/deliveries/by_id
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
    # 
    # =========================================================================

    async def get_webhook_settings(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
             
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
          .    429 (Too Many Requests),
        ,       .
        """
        org_id = organization_id or self.organization_id
        
        #   429: ,      ,  ?
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
                        #        429, 
                        #          ,  
                        #     ,  secret_key   .     .
                        raise ValueError("iiko API Error:      ( 429).      .")
                raise e

    async def auto_register_webhook(self,
        session: Optional[Session] = None,
        base_url: Optional[str] = None,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None,
        request_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
          :
        1.   .
        2.  URL ( ,   ).
        3.   iiko.
        4.    (  session).
        """
        public_url = settings.APP_PUBLIC_URL
        if public_url and "your-public-url.ngrok-free.app" in public_url:
            public_url = None  #    ngrok

        # : 1.  base_url 2. URL   3. APP_PUBLIC_URL  .env
        url = base_url or request_url or public_url
        
        if not url:
            raise ValueError("Webhook URL cannot be determined. Set APP_PUBLIC_URL or use frontend.")
        
        #   origin (   /api)
        if "/api/" in url:
            url = url.split("/api/")[0]
            
        # ,  URL    
        endpoint = "/api/v1/webhooks/iiko"
        if not url.endswith(endpoint):
            url = url.rstrip("/") + endpoint
        
        #    
        auth_token = secrets.token_hex(16)
        
        # 
        try:
            result = await self.update_webhook_settings(
                webhook_url=url,
                auth_token=auth_token,
                api_login=api_login,
                organization_id=organization_id
            )
        except ValueError as e:
            if "429" in str(e):
                print(f"[iiko_service]    : {e}")
                result = {"status": "rate_limited", "message": "  . iiko API  429 (Too Many Requests),  ,   ."}
            else:
                raise e
        
        #   
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
        """       (iiko Card)"""
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
        """   """
        #  v1       get_customer_info  walletBalances
        #     , iiko Card API   
        info = await self.get_customer_info("", api_login=api_login, organization_id=organization_id)
        #      iiko Card
        return 0.0

    async def add_customer_balance(
        self,
        customer_id: str,
        wallet_id: str,
        amount: float,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None,
        comment: str = "  "
    ) -> bool:
        """    """
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
    # iiko Resto (Office API) -  
    # =========================================================================

    async def get_order_details_resto(
        self,
        order_id: str,
        resto_url: Optional[str] = None,
        resto_login: Optional[str] = None,
        resto_password: Optional[str] = None
    ) -> Dict[str, Any]:
        """      iiko Resto (Office)"""
        #   /deliveries/by_id    Office API
        #  Office API   XML.
        try:
            data = await self._resto_request(
                "GET", f"/deliveries/by_id?id={order_id}", 
                resto_url=resto_url,
                resto_login=resto_login,
                resto_password=resto_password
            )
            #   XML,  _resto_request    .
            #      ,       .
            return data if isinstance(data, dict) else {"raw": data}
        except Exception as e:
            logger.error(f"Error getting order details from Resto: {e}")
            return {}

    # =========================================================================
    # OLAP 
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
         OLAP-  .
         iiko Resto (Office) API,   Cloud API   401.
        """
        org_id = organization_id or self.organization_id
        fmt_date = "%Y-%m-%d"
        
        #    Resto API (Office),    v2 (POST)
        try:
            # iiko Office (RMS) v2 (POST)  ISO   
            #    409 ( )   ,  1   'to'
            v2_from = date_from.strftime("%Y-%m-%dT00:00:00.000")
            v2_to = (date_to + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000")
            
            #    v1 (Fallback)
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

            #   v2 . 
            try:
                response = await self._resto_request(
                    "POST", "/v2/reports/olap",
                    json_data=payload,
                    resto_url=resto_url,
                    resto_login=resto_login,
                    resto_password=resto_password
                )
            except httpx.HTTPStatusError as e:
                #  404,  v2  ,  v1 (GET)
                if e.response.status_code == 404:
                    logger.info("Resto API v2 not found, falling back to v1 (GET)")
                    #  v1 (GET)    ,  
                    params = [
                        ("key", "TOKEN"), # ,   _resto_request
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
            
            #   v2/v1
            data_rows = []
            if isinstance(response, dict):
                if "data" in response:
                    rows = response.get("data", [])
                    #    (v2   dict, v1  list/array)
                    if rows and isinstance(rows[0], dict):
                        data_rows = rows
                    else:
                        cols = response.get("columnNames", [])
                        if cols and rows:
                            data_rows = [dict(zip(cols, r)) for r in rows]
                else:
                    #   RMS  JSON-   
                    data_rows = [response] if "revenue" in str(response).lower() else []
            elif isinstance(response, list):
                data_rows = response

            if data_rows:
                result = []
                for row_dict in data_rows:
                    if not isinstance(row_dict, dict): continue
                    
                    #      (v2 vs v1 vs aliases)
                    rev = self._safe_float(row_dict.get("DishDiscountSumInt", 
                                          row_dict.get("OrderSum", 
                                          row_dict.get("fullSum", 0))))
                    
                    disc = self._safe_float(row_dict.get("DiscountSum", 
                                           row_dict.get("DishDiscountSumInt", 0)))
                    
                    guests = self._safe_int(row_dict.get("GuestNum", 0))
                    amount = self._safe_float(row_dict.get("DishAmountInt", 0))
                    
                    # 
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
                        "orders_count": int(amount) if amount > 0 else guests, #     
                    })
                return result

            #   XML
            if isinstance(response, str) and "<" in response:
                logger.info(" XML  iiko Office.   ,   Cloud API.")
                raise ValueError("XML response from Resto not supported yet")

        except Exception as resto_err:
            logger.warning(f"Resto OLAP failed: {resto_err}. Response sample: {str(response)[:200] if 'response' in locals() else 'None'}. Trying Cloud API fallback.")

        # Fallback to Cloud API (  )
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
            logger.error(f" OLAP- iiko (Cloud): {e}")
            raise

    async def get_daily_revenue_olap(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None
    ) -> Dict[str, Dict[str, float]]:
        """
              OLAP    .
          {: {"revenue": float, "discounts": float}}
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
                    "values": ["Delivery"] #    ?    .
                }
            }
        }
        
        #   (  )
        if "OrderType" in payload["filters"]:
            del payload["filters"]["OrderType"]

        try:
            logger.info(f" OLAP-   {date_from.strftime(fmt)} - {date_to.strftime(fmt)}")
            response = await self._request(
                "POST", "/api/1/reports/olap",
                payload, api_login=api_login, organization_id=org_id
            )
            
            rows = response.get("data", [])
            columns = response.get("columnNames", [])
            logger.info(f"OLAP response: {len(rows)} , : {columns}")
            
            result = {}
            for row in rows:
                if isinstance(row, list):
                    rowData = dict(zip(columns, row))
                else:
                    rowData = row
                
                #   OLAP    "2024-04-01T00:00:00.000"   "2024-04-01"
                raw_date = rowData.get("OpenDate.Typed", "")
                date_str = str(raw_date).split("T")[0] if raw_date else ""
                
                if date_str:
                    # iiko       
                    try:
                        rev = float(rowData.get("OrderSum", 0))
                        disc = float(rowData.get("DiscountSum", 0))
                        
                        if date_str not in result:
                            result[date_str] = {"revenue": 0.0, "discounts": 0.0}
                        
                        result[date_str]["revenue"] += round(rev, 2)
                        result[date_str]["discounts"] += round(disc, 2)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"     OLAP {date_str}: {e}")

            logger.info(f"  : {list(result.keys())}")
            return result
        except Exception as e:
            logger.error(f"     OLAP: {e}")
            return {}

    # =========================================================================
    # iiko Resto (Office API) -  
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
        """    iiko Resto (Office) API  SHA-1 """
        import hashlib
        
        url = resto_url or settings.IIKO_RESTO_URL
        login = resto_login or settings.IIKO_RESTO_LOGIN
        password = resto_password or settings.IIKO_RESTO_PASSWORD

        if not url or not login:
            raise ValueError(" iiko Resto (URL/Login)  .")

        # Calculate SHA-1 hash of the password
        password_sha1 = hashlib.sha1(password.encode()).hexdigest()
        
        # Normalize URL
        base_url = url.rstrip('/')
        if not base_url.endswith('/api'):
            if base_url.endswith('/resto'):
                base_url = f"{base_url}/api"
            else:
                base_url = f"{base_url}/resto/api"
        
        # 1.  
        async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
            auth_url = f"{base_url}/auth"
            auth_params = {"login": login, "pass": password_sha1}
            
            auth_response = await client.get(auth_url, params=auth_params)
            if auth_response.status_code != 200:
                auth_response = await client.get(auth_url, params={"login": login, "pass": password})
                if auth_response.status_code != 200:
                    logger.error(f"  Resto: {auth_response.status_code} | {auth_response.text}")
                    raise HTTPException(status_code=401, detail=f"  Resto: {auth_response.text}")
            
            token = auth_response.text.strip().replace('"', '')
            
            # 2.   
            request_url = f"{base_url}{endpoint}"
            
            #   ,      
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
        """     iiko Resto"""
        # iiko Resto  XML  
        data = await self._resto_request(
            "GET", "/employees", 
            resto_url=resto_url or settings.IIKO_RESTO_URL,
            resto_login=resto_login or settings.IIKO_RESTO_LOGIN,
            resto_password=resto_password or settings.IIKO_RESTO_PASSWORD
        )
        
        #   XML (),  . 
        if isinstance(data, str):
            import xml.etree.ElementTree as ET
            root = ET.fromstring(data)
            
            employees = []
            for emp in root.findall('employee'):
                #        
                #  iiko RESTO XML: mainRoleCode -  , roleCodes -    
                employees.append({
                    "id": emp.findtext('id'),
                    "firstName": emp.findtext('firstName') or emp.findtext('name'),
                    "lastName": emp.findtext('lastName') or "",
                    "code": emp.findtext('code'), #  
                    "org_id": emp.findtext('preferredDepartmentCode') or (emp.find('mainRole').findtext('organizationId') if emp.find('mainRole') is not None else None),
                    "phone": emp.findtext('phone') or emp.findtext('cellPhone'),
                    "email": emp.findtext('email'),
                    "role": self._extract_role(emp),
                    "role_codes": emp.findtext('roleCodes'), #  
                    "main_role_code": emp.findtext('mainRoleCode'), #  
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
        resto_password: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """     iiko Resto (Office) API"""
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
                resto_password=resto_password
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
        """     iiko Resto (Office) API"""
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

    async def get_resto_detailed_deliveries(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: str,
        resto_url: Optional[str] = None,
        resto_login: Optional[str] = None,
        resto_password: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """     iiko Resto  OLAP"""
        try:
            from datetime import timedelta
            v2_from = date_from.strftime("%Y-%m-%dT00:00:00.000")
            v2_to = (date_to + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000")
            
            payload = {
                "reportType": "DELIVERIES",
                "groupByRowFields": [
                    "OrderNum", 
                    "Courier.Name", 
                    "Address.Street.Name", 
                    "Address.House", 
                    "Address.Flat",
                    "DeliveryZone",
                    "DeliveryTerminal.Name"
                ],
                "aggregateFields": [
                    "OrderSum", 
                    "CookingFinishTime", 
                    "ExpectedDeliveryTime", 
                    "ActualDeliveryTime"
                ],
                "filters": {
                    "ActualDeliveryTime": {
                        "filterType": "DateRange",
                        "periodType": "CUSTOM",
                        "from": v2_from,
                        "to": v2_to,
                        "includeLow": True,
                        "includeHigh": False
                    }
                }
            }
            
            response = await self._resto_request(
                "POST", "/v2/reports/olap",
                json_data=payload,
                resto_url=resto_url,
                resto_login=resto_login,
                resto_password=resto_password
            )
            
            data_rows = []
            if isinstance(response, dict):
                rows = response.get("data", [])
                cols = response.get("columnNames", [])
                if cols and rows:
                    data_rows = [dict(zip(cols, r)) for r in rows]
            
            transformed = []
            for row in data_rows:
                transformed.append({
                    "id": row.get("OrderNum"),
                    "address": {
                        "street": row.get("Address.Street.Name"),
                        "house": row.get("Address.House"),
                        "flat": row.get("Address.Flat")
                    },
                    "courierInfo": {
                        "courier": {"name": row.get("Courier.Name")}
                    },
                    "deliveryZone": row.get("DeliveryZone"),
                    "terminalName": row.get("DeliveryTerminal.Name"),
                    "sum": self._safe_float(row.get("OrderSum")),
                    "whenCookingCompleted": row.get("CookingFinishTime"),
                    "expectedDeliveryTime": row.get("ExpectedDeliveryTime"),
                    "whenDelivered": row.get("ActualDeliveryTime")
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
        """   ()  iiko Resto"""
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
        """    ()  iiko Resto"""
        params = {
            "from": date_from.strftime("%Y-%m-%d"),
            "to": date_to.strftime("%Y-%m-%d")
        }
        data = await self._resto_request(
            "GET", "/employees/attendance", 
            resto_url, resto_login, resto_password,
            params=params
        )
        #   XML  
        if isinstance(data, str):
            import xml.etree.ElementTree as ET
            root = ET.fromstring(data)
            
            records = []
            for rec in root.findall('attendance'):
                #   ID   ,    
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
        """      iiko Resto (Office)"""
        #   Office API: /delivery/zones ( 1)  /delivery/zones.json ( )
        try:
            logger.info(f"    iiko Resto: {resto_url}/resto/api/delivery/zones")
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
                    # OpenDate.Typed    "2024-03-27T00:00:00.000"
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

    async def get_detailed_deliveries(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: str,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """     iiko Cloud API"""
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

    async def get_resto_delivery_history(self, date_from: str, date_to: str, resto_url: str = None, key: str = None, **kwargs) -> List[str]:
        """
            iiko Office (Resto) API v2.
          ID  (GUID).
        """
        if not resto_url or not key:
            return []
            
        endpoint = f"{resto_url.rstrip('/')}/resto/api/deliveries/history"
        
        #  POST    v2
        payload = {
            "deliveryDateFrom": date_from,
            "deliveryDateTo": date_to
        }
        
        params = {"key": key}
        
        try:
            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                response = await client.post(endpoint, params=params, json=payload)
                
                if response.status_code != 200:
                    logger.error(f"iiko Resto error {response.status_code}: {response.text}")
                    return []
                
                #  
                import xml.etree.ElementTree as ET
                try:
                    root = ET.fromstring(response.content)
                    return [node.text for node in root.findall(".//id")]
                except:
                    #    JSON
                    try:
                        data = response.json()
                        return data if isinstance(data, list) else []
                    except:
                        return []
                    
        except Exception as e:
            logger.error(f"Error getting delivery history from Resto: {e}")
            return []

    @staticmethod
    def _safe_float(value) -> float:
        """    float"""
        try:
            return float(value) if value is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _safe_int(value) -> int:
        """    int"""
        try:
            return int(value) if value is not None else 0
        except (TypeError, ValueError):
            return 0


    # =========================================================================
    # KML  
    # =========================================================================

    async def fetch_and_parse_kml(self, url: str) -> List[Dict[str, Any]]:
        """
         KML    (, Google Maps)   .
            [[lat, lng], ...]
        """
        if not url:
            return []
            
        #    Google My Maps,   KML 
        if "google.com/maps/d/edit" in url or "google.com/maps/d/viewer" in url:
            if "mid=" in url:
                mid = url.split("mid=")[1].split("&")[0]
                url = f"https://www.google.com/maps/d/u/0/kml?mid={mid}&forcekml=1"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                #   UTF-8    
                content = response.text
                logger.info(f"KML , : {len(content)} .  ...")
                return self.parse_kml_content(content)
            except Exception as e:
                logger.error(f"  KML   {url}: {e}")
                raise

    def parse_kml_content(self, kml_text: str) -> List[Dict[str, Any]]:
        """
         XML/KML    .
         lxml  fallback   xml.etree.ElementTree.
        """
        import re
        import xml.etree.ElementTree as ET
        
        #    <?xml  <kml
        kml_text = re.sub(r'^[^<]+', '', kml_text.strip())
        
        #   lxml ( )
        try:
            from lxml import etree
            parser = etree.XMLParser(recover=True, remove_blank_text=True)
            root = etree.fromstring(kml_text.encode('utf-8'), parser=parser)
            #   namespace   XPath  
            for el in root.iter():
                if isinstance(el.tag, str) and '}' in el.tag:
                    el.tag = el.tag.split('}', 1)[1]
                #     namespace
                attribs = {k.split('}', 1)[-1]: v for k, v in el.attrib.items()}
                el.attrib.clear()
                el.attrib.update(attribs)
            placemarks = root.xpath('.//Placemark')
        except (ImportError, Exception) as e:
            logger.warning(f" lxml ({str(e)}),  fallback xml.etree.ElementTree")
            #  namespace  regex    ElementTree
            kml_clean = re.sub(r'\s+xmlns[^"]*"[^"]*"', '', kml_text)
            #    <prefix:tag> -> <tag>
            kml_clean = re.sub(r'<([^/!?])', lambda m: '<' + m.group(1).split(':')[-1] if ':' in m.group(1) else '<' + m.group(1), kml_clean)
            kml_clean = re.sub(r'</[^>]+:', '</', kml_clean)
            try:
                root = ET.fromstring(kml_clean)
                #  Placemark   
                placemarks = root.findall('.//Placemark') or root.findall('.//{*}Placemark')
            except Exception as e2:
                logger.error(f"Fallback parser also failed: {e2}")
                return []
        
        zones = []
        logger.info(f" Placemark : {len(placemarks)}")
        
        for pm in placemarks:
            #   
            name_el = pm.find('.//name')
            if name_el is None:
                name_el = pm.find('name')
            
            name = (name_el.text or '').strip() if name_el is not None else ' '
            
            #      
            coord_text = ''
            for coord_el in pm.iter():
                #  namespace    
                tag_name = coord_el.tag.split('}')[-1] if '}' in coord_el.tag else coord_el.tag
                if tag_name.lower() == 'coordinates':
                    coord_text = (coord_el.text or '').strip()
                    if coord_text:
                        break
            
            if not coord_text:
                logger.warning(f"Placemark '{name}'    ")
                continue
            
            points = []
            #   KML     
            #    : lng,lat,alt
            for entry in re.split(r'\s+', coord_text):
                if not entry.strip():
                    continue
                parts = entry.split(',')
                if len(parts) >= 2:
                    try:
                        lng = float(parts[0])
                        lat = float(parts[1])
                        #  Google Maps [lat, lng]
                        points.append([lat, lng])
                    except (ValueError, IndexError):
                        continue
            
            if len(points) >= 3:  #  3   
                zones.append({"name": name, "points": points})
                logger.info(f" '{name}': {len(points)} ")
            else:
                logger.warning(f" '{name}':    ({len(points)}), ")
        
        return zones


#   
iiko_service = IikoService()

                zones.append({"name": name, "points": points})
                logger.info(f" '{name}': {len(points)} ")
            else:
                logger.warning(f" '{name}':    ({len(points)}), ")
        
        return zones

            return []

    @staticmethod
    def _safe_float(value) -> float:
        """    float"""
        try:
            return float(value) if value is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _safe_int(value) -> int:
        """    int"""
        try:
            return int(value) if value is not None else 0
        except (TypeError, ValueError):
            return 0


    # =========================================================================
    # KML  
    # =========================================================================

    async def fetch_and_parse_kml(self, url: str) -> List[Dict[str, Any]]:
        """
         KML    (, Google Maps)   .
            [[lat, lng], ...]
        """
        if not url:
            return []
            
        #    Google My Maps,   KML 
        if "google.com/maps/d/edit" in url or "google.com/maps/d/viewer" in url:
            if "mid=" in url:
                mid = url.split("mid=")[1].split("&")[0]
                url = f"https://www.google.com/maps/d/u/0/kml?mid={mid}&forcekml=1"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                #   UTF-8    
                content = response.text
                logger.info(f"KML , : {len(content)} .  ...")
                return self.parse_kml_content(content)
            except Exception as e:
                logger.error(f"  KML   {url}: {e}")
                raise

    def parse_kml_content(self, kml_text: str) -> List[Dict[str, Any]]:
        """
         XML/KML    .
         lxml    .
        """
        from lxml import etree
        import re
        
        try:
            #   bytes  lxml   ,        
            if isinstance(kml_text, str):
                #       <?xml,  
                kml_text = re.sub(r'^[^<]+', '', kml_text)
                kml_bytes = kml_text.encode('utf-8')
            else:
                kml_bytes = kml_text

            #     (recover=True),     XML
            parser = etree.XMLParser(recover=True, remove_blank_text=True)
            root = etree.fromstring(kml_bytes, parser=parser)
            
            #     XPath
            for el in root.getiterator():
                if not (
                    isinstance(el.tag, str) and 
                    "}" in el.tag
                ):
                    continue
                el.tag = el.tag.split("}", 1)[1]
            
            zones = []
            #  Placemark   
            placemarks = root.xpath(".//Placemark")
            logger.info(f" Placemark : {len(placemarks)}")

            for placemark in placemarks:
                #  
                name_nodes = placemark.xpath("./name/text()")
                name = name_nodes[0].strip() if name_nodes else "Unnamed Zone"
                
                #        local-name() 
                #    (  KML)
                coord_nodes = placemark.xpath(".//*[local-name()='coordinates']/text()")
                
                if coord_nodes:
                    #          
                    #    (      )
                    coord_text = max(coord_nodes, key=len).strip()
                    points = []
                    
                    #    : lng,lat[,alt]
                    #   ,  
                    # : 37.123,55.123,0  37.123,55.123
                    entries = re.split(r'\s+', coord_text)
                    for entry in entries:
                        if not entry: continue
                        parts = entry.split(',')
                        if len(parts) >= 2:
                            try:
                                lng = float(parts[0])
                                lat = float(parts[1])
                                points.append([lat, lng])
                            except (ValueError, IndexError):
                                continue
                    
                    #    ,  XPath   (  )
                    if not points:
                        #   -   Placemark   
                        placemark_str = etree.tostring(placemark, encoding='unicode')
                        #    
                        coord_matches = re.findall(r'(-?\d+\.\d+,-?\d+\.\d+(?:,-?\d+\.\d+)?)', placemark_str)
                        if len(coord_matches) > 3: #  3   
                            for match in coord_matches:
                                try:
                                    parts = match.split(',')
                                    lng = float(parts[0])
                                    lat = float(parts[1])
                                    points.append([lat, lng])
                                except: continue

                    if points:
                        zones.append({
                            "name": name,
                            "points": points
                        })
                        logger.info(f" '{name}'  : {len(points)} ")
                    else:
                        #      Placemark  
                        logger.warning(f" Placemark '{name}'   . XML: {etree.tostring(placemark, encoding='unicode')[:200]}...")
            
            return zones
        except Exception as e:
            logger.error(f"   KML: {e}", exc_info=True)
            raise


#   
iiko_service = IikoService()

