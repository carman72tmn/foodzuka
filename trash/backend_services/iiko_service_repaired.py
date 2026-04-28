"""
╨б╨╡╤А╨▓╨╕╤Б ╨┤╨╗╤П ╨╕╨╜╤В╨╡╨│╤А╨░╤Ж╨╕╨╕ ╤Б iiko Cloud API
╨Ф╨╛╨║╤Г╨╝╨╡╨╜╤В╨░╤Ж╨╕╤П API: https://api-ru.iiko.services/
"""
import httpx
import asyncio
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta, timezone
import secrets
import hashlib
from sqlmodel import Session, select
from fastapi import HTTPException
from app.core.config import settings
from app.core.database import engine
from app.models.iiko_settings import IikoSettings
from app.services.yandex_service import yandex_service
from app.utils.geo_utils import parse_kml

logger = logging.getLogger(__name__)


class IikoService:
    """╨б╨╡╤А╨▓╨╕╤Б ╨┤╨╗╤П ╤А╨░╨▒╨╛╤В╤Л ╤Б iiko Cloud API"""

    def __init__(self):
        self.api_url = settings.IIKO_API_URL
        self.api_login = settings.IIKO_API_LOGIN
        self.organization_id = settings.IIKO_ORGANIZATION_ID
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    # =========================================================================
    # ╨Э╨░╤Б╤В╤А╨╛╨╣╨║╨╕ ╨╕ ╨С╨Ф
    # =========================================================================

    def _get_settings_by_org_id(self, organization_id: str) -> Optional[IikoSettings]:
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨╜╨░╤Б╤В╤А╨╛╨╡╨║ API ╨╕╨╖ ╨С╨Ф ╨┐╨╛ organization_id"""
        if not organization_id:
            return None
        with Session(engine) as session:
            statement = select(IikoSettings).where(IikoSettings.organization_id == organization_id)
            return session.exec(statement).first()

    async def check_address_zone(
        self,
        organization_id: str,
        city: str,
        street: str,
        house: str,
        api_login: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ╨Р╨▓╤В╨╛╨╝╨░╤В╨╕╤З╨╡╤Б╨║╨╛╨╡ ╨╛╨┐╤А╨╡╨┤╨╡╨╗╨╡╨╜╨╕╨╡ ╨╖╨╛╨╜╤Л ╨┤╨╛╤Б╤В╨░╨▓╨║╨╕ ╨┐╨╛ ╨░╨┤╤А╨╡╤Б╤Г.
        1. ╨У╨╡╨╛╨║╨╛╨┤╨╕╤А╤Г╨╡╤В ╨░╨┤╤А╨╡╤Б ╤З╨╡╤А╨╡╨╖ ╨п╨╜╨┤╨╡╨║╤Б.
        2. ╨Ш╤Й╨╡╤В ╨▓╤Е╨╛╨╢╨┤╨╡╨╜╨╕╨╡ ╨║╨╛╨╛╤А╨┤╨╕╨╜╨░╤В ╨▓ ╨┐╨╛╨╗╨╕╨│╨╛╨╜╤Л ╨╖╨╛╨╜ ╨┤╨╛╤Б╤В╨░╨▓╨║╨╕.
        """
        full_address = f"{city}, {street}, {house}"
        logger.info(f"Checking delivery zone for address: {full_address}")

        try:
            with Session(engine) as session:
                # 1. ╨Я╨╛╨╗╤Г╤З╨░╨╡╨╝ ╨╜╨░╤Б╤В╤А╨╛╨╣╨║╨╕ ╨п╨╜╨┤╨╡╨║╤Б╨░
                yandex_settings = await yandex_service.get_settings(session)
                if not yandex_settings or not yandex_settings.api_key_js:
                    logger.warning("Yandex API key not configured for zone checking")
                    return {"zone": None, "error": "Yandex API key missing"}

                # 2. ╨У╨╡╨╛╨║╨╛╨┤╨╕╤А╤Г╨╡╨╝ ╨░╨┤╤А╨╡╤Б
                coords = await yandex_service.geocode_address(full_address, yandex_settings.api_key_js)
                if not coords:
                    logger.warning(f"Failed to geocode address: {full_address}")
                    return {"zone": None, "error": "Geocoding failed"}

                lat, lng = coords["lat"], coords["lng"]
                logger.debug(f"Coordinates for {full_address}: {lat}, {lng}")

                # 3. ╨Ю╨┐╤А╨╡╨┤╨╡╨╗╤П╨╡╨╝ ╨╖╨╛╨╜╤Г ╨┐╨╛ ╨║╨╛╨╛╤А╨┤╨╕╨╜╨░╤В╨░╨╝
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
    # ╨Р╤Г╤В╨╡╨╜╤В╨╕╤Д╨╕╨║╨░╤Ж╨╕╤П
    # =========================================================================

    async def _get_access_token(self, api_login: Optional[str] = None) -> str:
        """
        ╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤В╨╛╨║╨╡╨╜╨░ ╨┤╨╛╤Б╤В╤Г╨┐╨░ ╨║ iiko API
        """
        login = api_login or self.api_login
        
        # ╨Ч╨░╤Й╨╕╤В╨░ ╨╛╤В ╨┐╨╗╨╡╨╣╤Б╤Е╨╛╨╗╨┤╨╡╤А╨╛╨▓ ╨╕ ╨┐╤Г╤Б╤В╤Л╤Е ╨╖╨╜╨░╤З╨╡╨╜╨╕╨╣
        if not login or login.startswith("your_") or "placeholder" in login.lower() or "client error" in login.lower():
            logger.error(f"╨Э╨╡╨║╨╛╤А╤А╨╡╨║╤В╨╜╤Л╨╣ ╨╗╨╛╨│╨╕╨╜ iiko API: {login}")
            raise ValueError("╨Ы╨╛╨│╨╕╨╜ iiko API ╨╜╨╡ ╨╜╨░╤Б╤В╤А╨╛╨╡╨╜ ╨╕╨╗╨╕ ╤Б╨╛╨┤╨╡╤А╨╢╨╕╤В ╨╛╤И╨╕╨▒╨║╤Г. ╨Я╨╛╨╢╨░╨╗╤Г╨╣╤Б╤В╨░, ╨▓╨▓╨╡╨┤╨╕╤В╨╡ ╨║╨╗╤О╤З ╨╖╨░╨╜╨╛╨▓╨╛.")

        login = login.strip()

        # ╨Х╤Б╨╗╨╕ ╨┐╤А╨╛╤Б╨╕╨╝ ╤В╨╛╤В ╨╢╨╡ ╨╗╨╛╨│╨╕╨╜, ╤З╤В╨╛ ╨╕ ╨▓ ╨║╨╡╤И╨╡, ╨╕ ╨╛╨╜ ╨╜╨╡ ╨┐╤А╨╛╤В╤Г╤Е тАФ ╨▓╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╨╝
        if not api_login and self.access_token and self.token_expires_at:
            if datetime.utcnow() < self.token_expires_at:
                return self.access_token

        masked_login = f"{login[:4]}...{login[-4:]}" if login and len(login) > 8 else "╨Э╨Х╨Ъ╨Ю╨а╨а╨Х╨Ъ╨в╨Э╨Ю"
        logger.info(f"╨Ч╨░╨┐╤А╨╛╤Б ╤В╨╛╨║╨╡╨╜╨░ ╨┤╨╛╤Б╤В╤Г╨┐╨░ iiko ╨┤╨╗╤П ╨╗╨╛╨│╨╕╨╜╨░: {masked_login}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/api/1/access_token",
                    json={"apiLogin": login}
                )
                response.raise_for_status()
                data = response.json()

                token = data["token"]
                
                # ╨Ъ╨╡╤И╨╕╤А╤Г╨╡╨╝ ╤В╨╛╨╗╤М╨║╨╛ ╨╡╤Б╨╗╨╕ ╤Н╤В╨╛ "╨│╨╗╨╛╨▒╨░╨╗╤М╨╜╤Л╨╣" ╨╗╨╛╨│╨╕╨╜
                if not api_login:
                    self.access_token = token
                    self.token_expires_at = datetime.utcnow() + timedelta(minutes=14)

                return token
            except httpx.HTTPStatusError as e:
                logger.error(f"╨Э╨╡ ╤Г╨┤╨░╨╗╨╛╤Б╤М ╨┐╨╛╨╗╤Г╤З╨╕╤В╤М ╤В╨╛╨║╨╡╨╜ ╨┤╨╛╤Б╤В╤Г╨┐╨░: {e.response.text}")
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
        """╨г╨╜╨╕╨▓╨╡╤А╤Б╨░╨╗╤М╨╜╤Л╨╣ ╨╝╨╡╤В╨╛╨┤ ╨┤╨╗╤П ╨╖╨░╨┐╤А╨╛╤Б╨╛╨▓ ╨║ iiko API ╤Б ╨░╨▓╤В╨╛╤А╨╕╨╖╨░╤Ж╨╕╨╡╨╣"""
        # ╨Я╤Л╤В╨░╨╡╨╝╤Б╤П ╨┐╨╛╨╗╤Г╤З╨╕╤В╤М ╨░╨║╤В╤Г╨░╨╗╤М╨╜╤Л╨╣ api_login ╨╕╨╖ ╨С╨Ф ╨╡╤Б╨╗╨╕ ╨┐╨╡╤А╨╡╨┤╨░╨╜╨░ ╨╛╤А╨│╨░╨╜╨╕╨╖╨░╤Ж╨╕╤П
        current_api_login = api_login
        if organization_id and not current_api_login:
            db_settings = self._get_settings_by_org_id(organization_id)
            if db_settings and db_settings.api_login:
                current_api_login = db_settings.api_login
                
        token = await self._get_access_token(api_login=current_api_login)
        org_id = organization_id or self.organization_id
        
        # ╨Х╤Б╨╗╨╕ ╤Н╤В╨╛ ╨┐╨╗╨╡╨╣╤Б╤Е╨╛╨╗╨┤╨╡╤А - ╨╕╨│╨╜╨╛╤А╨╕╤А╤Г╨╡╨╝ ╨╡╨│╨╛
        if org_id and (org_id.startswith("your_") or "placeholder" in org_id.lower()):
            org_id = None

        # ╨Я╨╛╨┤╨│╨╛╤В╨╛╨▓╨║╨░ ╨┤╨░╨╜╨╜╤Л╤Е (╨║╨╛╨┐╨╕╤П ╤З╤В╨╛╨▒╤Л ╨╜╨╡ ╨╝╨╡╨╜╤П╤В╤М ╨╛╤А╨╕╨│╨╕╨╜╨░╨╗)
        payload = json_data.copy() if json_data else {}

        # ╨Х╤Б╨╗╨╕ ╨▓ payload ╨╡╤Б╤В╤М organizationId ╨╕╨╗╨╕ organizationIds - ╨┐╨╛╨┤╨╝╨╡╨╜╤П╨╡╨╝ ╨╡╤Б╨╗╨╕ ╨┐╨╡╤А╨╡╨┤╨░╨╗╨╕ organization_id
        if org_id:
            # ╨Т╤Б╨╡╨│╨┤╨░ ╤Б╤В╨░╤А╨░╨╡╨╝╤Б╤П ╨┤╨╛╨▒╨░╨▓╨╗╤П╤В╤М ╨╛╨▒╨░ ╨▓╨░╤А╨╕╨░╨╜╤В╨░ ╨┤╨╗╤П ╤Б╨╛╨▓╨╝╨╡╤Б╤В╨╕╨╝╨╛╤Б╤В╨╕ ╤Б ╤А╨░╨╖╨╜╤Л╨╝╨╕ ╨▓╨╡╤А╤Б╨╕╤П╨╝╨╕ iiko Cloud
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
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method,
                    f"{self.api_url}{endpoint}",
                    headers={"Authorization": f"Bearer {token}"},
                    json=payload
                )
                
                # ╨Ю╨▒╤А╨░╨▒╨╛╤В╨║╨░ 429 (Too Many Requests) - ╨н╨║╤Б╨┐╨╛╨╜╨╡╨╜╤Ж╨╕╨░╨╗╤М╨╜╤Л╨╣ ╨▒╤Н╨║╨╛╤Д╤Д
                if response.status_code == 429 and _retry_count < 3:
                    wait_time = (2 ** _retry_count) * 5 # 5, 10, 20 ╤Б╨╡╨║╤Г╨╜╨┤
                    logger.warning(f"iiko API 429 Too Many Requests for {endpoint}. Waiting {wait_time}s before retry {_retry_count + 1}/3...")
                    await asyncio.sleep(wait_time)
                    return await self._request(
                        method, endpoint, json_data, timeout, 
                        current_api_login, organization_id, _is_retry=_is_retry,
                        _retry_count=_retry_count + 1,
                        log_error=log_error
                    )

                # ╨Ю╨▒╤А╨░╨▒╨╛╤В╨║╨░ 401 (Unauthorized) - ╨┐╤А╨╛╨▒╤Г╨╡╨╝ ╨╛╨▒╨╜╨╛╨▓╨╕╤В╤М ╤В╨╛╨║╨╡╨╜ ╨╛╨┤╨╕╨╜ ╤А╨░╨╖
                if response.status_code == 401 and not _is_retry:
                    logger.warning(f"iiko API 401 Unauthorized for {endpoint}. Retrying with fresh token...")
                    self.access_token = None
                    self.token_expires_at = None
                    return await self._request(
                        method, endpoint, json_data, timeout, 
                        current_api_login, organization_id, _is_retry=True,
                        _retry_count=_retry_count,
                        log_error=log_error
                    )

                if response.status_code >= 400:
                    if log_error:
                        # ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ ╤В╨╡╨╗╨╛ ╨╛╤В╨▓╨╡╤В╨░ ╨┤╨╗╤П ╨╗╤Г╤З╤И╨╡╨╣ ╨┤╨╕╨░╨│╨╜╨╛╤Б╤В╨╕╨║╨╕ 400/422 ╨╛╤И╨╕╨▒╨╛╨║
                        logger.error(f"iiko API Error: {response.status_code} | URL: {endpoint} | Body: {response.text}")
                    response.raise_for_status()
                    
            if response.encoding is None or response.encoding.lower() == 'iso-8859-1':
                response.encoding = 'utf-8'
                
            return response.json()
        except Exception as e:
            if not isinstance(e, httpx.HTTPStatusError):
                logger.error(f"iiko API unexpected error for {endpoint}: {e}")
            raise e

    # =========================================================================
    # ╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╨┐╨╛╨┤╨║╨╗╤О╤З╨╡╨╜╨╕╤П
    # =========================================================================

    async def test_connection(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╨┐╨╛╨┤╨║╨╗╤О╤З╨╡╨╜╨╕╤П ╨║ iiko API
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
            logger.error(f"╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╨┐╤А╨╛╨▓╨╡╤А╨║╨╡ ╤Б╨╛╨╡╨┤╨╕╨╜╨╡╨╜╨╕╤П ╤Б iiko: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # =========================================================================
    # ╨Ю╤А╨│╨░╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨╕ ╤Б╨┐╤А╨░╨▓╨╛╤З╨╜╨╕╨║╨╕
    # =========================================================================

    async def get_organizations(
        self,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤Б╨┐╨╕╤Б╨║╨░ ╨▓╤Б╨╡╤Е ╨╛╤А╨│╨░╨╜╨╕╨╖╨░╤Ж╨╕╨╣"""
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨╕╨╜╤Д╨╛╤А╨╝╨░╤Ж╨╕╨╕ ╨╛ ╤В╨╡╨║╤Г╤Й╨╡╨╣ ╨╛╤А╨│╨░╨╜╨╕╨╖╨░╤Ж╨╕╨╕"""
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤Б╨┐╨╕╤Б╨║╨░ ╤В╨╡╤А╨╝╨╕╨╜╨░╨╗╤М╨╜╤Л╤Е ╨│╤А╤Г╨┐╨┐"""
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
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╤Б╤В╨░╤В╤Г╤Б╨░ '╨╢╨╕╨▓ ╨╗╨╕' ╨┤╨╗╤П ╤В╨╡╤А╨╝╨╕╨╜╨░╨╗╤М╨╜╤Л╤Е ╨│╤А╤Г╨┐╨┐ (is_alive)"""
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤В╨╕╨┐╨╛╨▓ ╨╛╨┐╨╗╨░╤В╤Л"""
        org_id = organization_id or self.organization_id
        logger.info(f"╨Ч╨░╨┐╤А╨╛╤Б ╤В╨╕╨┐╨╛╨▓ ╨╛╨┐╨╗╨░╤В╤Л ╨┤╨╗╤П ╨╛╤А╨│╨░╨╜╨╕╨╖╨░╤Ж╨╕╨╕ {org_id}")
        data = await self._request(
            "POST", "/api/1/payment_types", 
            {"organizationIds": [org_id]},
            api_login=api_login,
            organization_id=org_id
        )
        types = data.get("paymentTypes", [])
        logger.info(f"╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╛ {len(types)} ╨│╤А╤Г╨┐╨┐ ╤В╨╕╨┐╨╛╨▓ ╨╛╨┐╨╗╨░╤В╤Л ╨╕╨╖ iiko Cloud")
        result = []
        for org_types in types:
            items = org_types.get("items", [])
            logger.debug(f"╨Ю╤А╨│ {org_types.get('organizationId')}: {len(items)} ╤В╨╕╨┐╨╛╨▓")
            for item in items:
                result.append(item)
        logger.info(f"╨Ш╤В╨╛╨│╨╛: ╨╛╨▒╤А╨░╨▒╨╛╤В╨░╨╜╨╛ {len(result)} ╤В╨╕╨┐╨╛╨▓ ╨╛╨┐╨╗╨░╤В╤Л")
        return result

    async def get_order_types(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤В╨╕╨┐╨╛╨▓ ╨╖╨░╨║╨░╨╖╨░"""
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤Б╨┐╨╕╤Б╨║╨░ ╤Ж╨╡╨╜╨╛╨▓╤Л╤Е ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╣ ╨╕╨╖ iiko Cloud"""
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Л╤Е ╤В╨╕╨┐╨╛╨▓ ╤Б╨║╨╕╨┤╨╛╨║"""
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
    # ╨Ь╨╡╨╜╤О ╨╕ ╨╜╨╛╨╝╨╡╨╜╨║╨╗╨░╤В╤Г╤А╨░
    # =========================================================================

    async def get_nomenclature(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨╜╨╛╨╝╨╡╨╜╨║╨╗╨░╤В╤Г╤А╤Л (╨╝╨╡╨╜╤О) ╨╕╨╖ iiko
        ╨Т╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╤В ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╕ (groups) ╨╕ ╤В╨╛╨▓╨░╤А╤Л (products)
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨╛╨│╤А╨░╨╜╨╕╤З╨╡╨╜╨╕╨╣ ╨┤╨╛╤Б╤В╨░╨▓╨║╨╕ (╨╖╨╛╨╜╤Л, ╤Г╤Б╨╗╨╛╨▓╨╕╤П)"""
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
        ╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤Б╨┐╨╕╤Б╨║╨░ ╨▓╨╜╨╡╤И╨╜╨╕╤Е ╨╝╨╡╨╜╤О
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
        ╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨║╨╛╨╜╨║╤А╨╡╤В╨╜╨╛╨│╨╛ ╨▓╨╜╨╡╤И╨╜╨╡╨│╨╛ ╨╝╨╡╨╜╤О ╨┐╨╛ ID ╤З╨╡╤А╨╡╨╖ API v2.
        
        ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╤В ╨┐╤А╤П╨╝╨╛╨╣ HTTP-╨╖╨░╨┐╤А╨╛╤Б (╨╝╨╕╨╜╤Г╤П _request) ╨▓╨╛ ╨╕╨╖╨▒╨╡╨╢╨░╨╜╨╕╨╡
        ╨░╨▓╤В╨╛╨┤╨╛╨▒╨░╨▓╨╗╨╡╨╜╨╕╤П 'organizationId' (╨▒╨╡╨╖ s), ╤З╤В╨╛ ╨▓╤Л╨╖╤Л╨▓╨░╨╡╤В ╨╛╤И╨╕╨▒╨║╤Г 400.
        
        ╨Х╤Б╨╗╨╕ iiko ╨▓╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╤В ╨╛╤И╨╕╨▒╨║╤Г 'Price category id is not correct',
        ╨░╨▓╤В╨╛╨╝╨░╤В╨╕╤З╨╡╤Б╨║╨╕ ╨┐╤Л╤В╨░╨╡╤В╤Б╤П ╨╕╤Б╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╤М ╨▒╨░╨╖╨╛╨▓╤Г╤О ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤О ╨╕╨╗╨╕ ╨╜╨░╤Е╨╛╨┤╨╕╤В 
        ╨┐╨╡╤А╨▓╤Г╤О ╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Г╤О ╨▓ ╤Б╨┐╨╕╤Б╨║╨╡ ╨╝╨╡╨╜╤О ╨╕ ╨┐╨╛╨▓╤В╨╛╤А╤П╨╡╤В ╨╖╨░╨┐╤А╨╛╤Б.
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
            
            logger.info(f"╨Ч╨░╨┐╤А╨╛╤Б iiko ╨╝╨╡╨╜╤О ID={external_menu_id} (org={org_id}, priceCategoryId={pcid})")
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{self.api_url}/api/2/menu/by_id",
                    headers={"Authorization": f"Bearer {token}"},
                    json=payload
                )
            return resp

        # 1. ╨Я╤А╨╛╨▒╤Г╨╡╨╝ ╨╛╤Б╨╜╨╛╨▓╨╜╨╛╨╣ ╨╖╨░╨┐╤А╨╛╤Б
        response = await _do_raw_request(price_category_id)
        
        if response.status_code == 401:
            self.access_token = None
            self.token_expires_at = None
            token = await self._get_access_token(api_login=api_login)
            response = await _do_raw_request(price_category_id)
            
        # 2. ╨Х╤Б╨╗╨╕ 400 ╨╕ ╨╛╤И╨╕╨▒╨║╨░ ╨▓ ╤Ж╨╡╨╜╨╛╨▓╨╛╨╣ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╕ тАФ ╨┐╤А╨╛╨▒╤Г╨╡╨╝ ╨░╨▓╤В╨╛-╨╕╤Б╨┐╤А╨░╨▓╨╗╨╡╨╜╨╕╨╡
        if response.status_code == 400:
            try:
                err_body = response.json()
            except:
                err_body = {}
            
            if "Price category" in err_body.get("errorDescription", "") or err_body.get("error") == "EXTERNAL_MENU_DATA_MISSED":
                logger.warning(f"iiko ╤В╤А╨╡╨▒╤Г╨╡╤В priceCategoryId ╨┤╨╗╤П ╨╝╨╡╨╜╤О {external_menu_id} (╨┐╨╡╤А╨╡╨┤╨░╨╜╨╜╤Л╨╣ PCID: {price_category_id}). ╨Ю╤В╨▓╨╡╤В: {err_body}. ╨Я╤А╨╛╨▒╤Г╨╡╨╝ ╨░╨▓╤В╨╛-╨┐╨╛╨┤╨▒╨╛╤А...")
                
                # ╨б╨╜╨░╤З╨░╨╗╨░ ╨┐╤А╨╛╨▒╤Г╨╡╨╝ "╨╜╤Г╨╗╨╡╨▓╤Г╤О" (╨▒╨░╨╖╨╛╨▓╤Г╤О) ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤О
                base_pcid = "00000000-0000-0000-0000-000000000000"
                if price_category_id != base_pcid:
                    logger.info(f"╨Я╤А╨╛╨▒╤Г╨╡╨╝ ╨▒╨░╨╖╨╛╨▓╤Г╤О ╤Ж╨╡╨╜╨╛╨▓╤Г╤О ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤О: {base_pcid}")
                    response = await _do_raw_request(base_pcid)
                
                # ╨Х╤Б╨╗╨╕ ╨▓╤Б╤С ╨╡╤Й╨╡ 400 тАФ ╨╖╨░╨┐╤А╨░╤И╨╕╨▓╨░╨╡╨╝ ╤Б╨┐╨╕╤Б╨╛╨║ ╨▓╤Б╨╡╤Е ╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Л╤Е ╤Ж╨╡╨╜╨╛╨▓╤Л╤Е ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╣ ╨┤╨╗╤П ╤Н╤В╨╛╨│╨╛ ╨╝╨╡╨╜╤О
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
                            # ╨Ш╤Й╨╡╨╝ ╨╜╨░╤И╨╡ ╨╝╨╡╨╜╤О ╨▓ ╤Б╨┐╨╕╤Б╨║╨╡
                            found_pcid = None
                            for menu in menus_data.get("externalMenus", []):
                                if str(menu.get("id")) == str(external_menu_id):
                                    price_cats = menu.get("priceCategories", [])
                                    if price_cats:
                                        found_pcid = price_cats[0].get("id") or price_cats[0].get("priceCategoryId")
                                        break
                            
                            # ╨Х╤Б╨╗╨╕ ╨╜╨╡ ╨╜╨░╤И╨╗╨╕ ╨▓ ╨╝╨╡╨╜╤О, ╨┐╨╛╨┐╤А╨╛╨▒╤Г╨╡╨╝ ╨┐╨╡╤А╨▓╤Г╤О ╨╕╨╖ ╨╛╨▒╤Й╨╡╨│╨╛ ╤Б╨┐╨╕╤Б╨║╨░ priceCategories (╨╡╤Б╨╗╨╕ ╨╡╤Б╤В╤М)
                            if not found_pcid and menus_data.get("priceCategories"):
                                found_pcid = menus_data["priceCategories"][0].get("id")

                            if found_pcid:
                                logger.info(f"╨Э╨░╨╣╨┤╨╡╨╜╨░ ╨┐╨╛╨┤╤Е╨╛╨┤╤П╤Й╨░╤П ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П: {found_pcid}. ╨Я╨╛╨▓╤В╨╛╤А╤П╨╡╨╝ ╨╖╨░╨┐╤А╨╛╤Б.")
                                response = await _do_raw_request(found_pcid)
                    except Exception as e:
                        logger.error(f"╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╨┐╨╛╨┐╤Л╤В╨║╨╡ ╨░╨▓╤В╨╛-╨┐╨╛╨┤╨▒╨╛╤А╨░ ╤Ж╨╡╨╜╨╛╨▓╨╛╨╣ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╕: {e}")

        if response.status_code >= 400:
            logger.error(f"iiko /api/2/menu/by_id ╨║╤А╨╕╤В╨╕╤З╨╡╤Б╨║╨░╤П ╨╛╤И╨╕╨▒╨║╨░ {response.status_code}: {response.text}")
            response.raise_for_status()
            
        return response.json()



    # =========================================================================
    # ╨б╤В╨╛╨┐-╨╗╨╕╤Б╤В╤Л
    # =========================================================================

    async def get_stop_lists(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        ╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤Б╤В╨╛╨┐-╨╗╨╕╤Б╤В╨╛╨▓ (╨╜╨╡╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Л╨╡ ╨┐╨╛╨╖╨╕╤Ж╨╕╨╕)

        ╨Т╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╤В ╤Б╨┐╨╕╤Б╨╛╨║ ╨┐╤А╨╛╨┤╤Г╨║╤В╨╛╨▓, ╨║╨╛╤В╨╛╤А╤Л╨╡ ╨▓╤А╨╡╨╝╨╡╨╜╨╜╨╛ ╨╜╨╡╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Л.
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
    # ╨Ч╨░╨║╨░╨╖╤Л
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
        ╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡ ╨╖╨░╨║╨░╨╖╨░ ╨┤╨╛╤Б╤В╨░╨▓╨║╨╕ ╨▓ iiko ╤Б retry-╨╗╨╛╨│╨╕╨║╨╛╨╣

        ╨Я╤А╨╕ ╨╜╨╡╤Г╨┤╨░╤З╨╡ тАФ ╨┐╨╛╨▓╤В╨╛╤А ╤З╨╡╤А╨╡╨╖ 15 ╤Б╨╡╨║╤Г╨╜╨┤ (╨┤╨╛ 3 ╤А╨░╨╖).
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

        # ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ ╨╛╨┐╨╗╨░╤В╤Г
        if payment_type_id and payment_sum:
            order_data["order"]["payments"] = [{
                "paymentTypeKind": "Cash",
                "paymentTypeId": payment_type_id,
                "sum": payment_sum,
                "isProcessedExternally": False
            }]

        # ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ ╤Б╨║╨╕╨┤╨║╤Г
        if discount_info:
            order_data["order"]["discountsInfo"] = discount_info

        # Retry ╨╗╨╛╨│╨╕╨║╨░: ╨┤╨╛ 3 ╨┐╨╛╨┐╤Л╤В╨╛╨║ ╤Б ╨╕╨╜╤В╨╡╤А╨▓╨░╨╗╨╛╨╝ 15 ╤Б╨╡╨║╤Г╨╜╨┤
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
                    f"╨Я╨╛╨┐╤Л╤В╨║╨░ ╤Б╨╛╨╖╨┤╨░╨╜╨╕╤П ╨╖╨░╨║╨░╨╖╨░ {attempt + 1}/3 ╨╜╨╡ ╤Г╨┤╨░╨╗╨░╤Б╤М: {e}"
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤Б╤В╨░╤В╤Г╤Б╨░ ╨╖╨░╨║╨░╨╖╨░ ╨╕╨╖ iiko"""
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
        """╨Ю╤В╨╝╨╡╨╜╨░ ╨╖╨░╨║╨░╨╖╨░ ╨▓ iiko"""
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
        api_login: Optional[str] = None,
        log_error: bool = True
    ) -> List[Dict[str, Any]]:
        """
        ╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨╖╨░╨║╨░╨╖╨╛╨▓ ╨╖╨░ ╨╖╨░╨┤╨░╨╜╨╜╤Л╨╣ ╨┐╨╡╤А╨╕╨╛╨┤.
        ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╤В╤Б╤П ╨┤╨╗╤П ╤А╤Г╤З╨╜╨╛╨╣ ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╨╕.
        """
        org_id = organization_id or self.organization_id
        
        # ╨Ш╨╜╤Б╤В╤А╤Г╨╝╨╡╨╜╤В iiko ╤В╤А╨╡╨▒╤Г╨╡╤В ╨┤╨░╤В╤Г ╨▓ ╤Д╨╛╤А╨╝╨░╤В╨╡ yyyy-MM-dd HH:mm:ss.fff
        date_format = "%Y-%m-%d %H:%M:%S.000"
        
        # ╨в╨╛╨╗╤М╨║╨╛ ╨▓╨░╨╗╨╕╨┤╨╜╤Л╨╡ ╤Б╤В╨░╤В╤Г╤Б╤Л ╨╕╨╖ ╨┐╨╡╤А╨╡╤З╨╕╤Б╨╗╨╡╨╜╨╕╤П DeliveryStatus
        valid_statuses = [
            "Unconfirmed", "WaitCooking", "ReadyForCooking", "CookingStarted", 
            "CookingCompleted", "Waiting", "OnWay", "Delivered", "Closed", "Cancelled"
        ]
        
        # ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╨╝ ╨┐╨╡╤А╨╡╨┤╨░╨╜╨╜╤Л╨╣ ╨┤╨╕╨░╨┐╨░╨╖╨╛╨╜ ╨▒╨╡╨╖ ╨┐╤А╨╕╨╜╤Г╨┤╨╕╤В╨╡╨╗╤М╨╜╨╛╨│╨╛ ╤А╨░╤Б╤И╨╕╤А╨╡╨╜╨╕╤П, 
        # ╤З╤В╨╛╨▒╤Л ╨╜╨╡ ╨▓╤Л╨╖╤Л╨▓╨░╤В╤М ╨╛╤И╨╕╨▒╨║╤Г TOO_MANY_DATA_REQUESTED.
        query_from = date_from.strftime(date_format)
        query_to = date_to.strftime(date_format)
        
        logger.info(f"╨Ч╨░╨┐╤А╨╛╤Б ╨╖╨░╨║╨░╨╖╨╛╨▓ iiko Cloud: {query_from} - {query_to} (╨Ю╤А╨│: {org_id})")
        
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
        
        # ╨Т Iiko Cloud API v2 ╨╖╨░╨║╨░╨╖╤Л ╤Б╨│╤А╤Г╨┐╨┐╨╕╤А╨╛╨▓╨░╨╜╤Л ╨┐╨╛ ╨╛╤А╨│╨░╨╜╨╕╨╖╨░╤Ж╨╕╤П╨╝
        orders = []
        organizations_data = data.get("ordersByOrganizations", [])
        
        logger.debug(f"Raw Iiko response keys: {list(data.keys())}")
        if organizations_data:
            logger.info(f"╨Э╨░╨╣╨┤╨╡╨╜╨╛ {len(organizations_data)} ╨╛╤А╨│╨░╨╜╨╕╨╖╨░╤Ж╨╕╨╣ ╨▓ ╨╛╤В╨▓╨╡╤В╨╡ Cloud")
            for org_data in organizations_data:
                # ╨Т ╤А╨░╨╖╨╜╤Л╤Е ╨▓╨╡╤А╤Б╨╕╤П╤Е API ╨╖╨░╨║╨░╨╖╤Л ╨╝╨╛╨│╤Г╤В ╨▒╤Л╤В╤М ╨▓ ╨┐╨╛╨╗╨╡ 'orders' ╨╕╨╗╨╕ 'items'
                batch = org_data.get("orders") or org_data.get("items") or []
                logger.info(f"╨Ю╤А╨│ {org_data.get('organizationId')}: {len(batch)} ╨╖╨░╨║╨░╨╖╨╛╨▓ (╨┐╨╛╨╗╨╡: {'orders' if org_data.get('orders') else 'items' if org_data.get('items') else 'empty'})")
                orders.extend(batch)
        
        # ╨Х╤Б╨╗╨╕ ╨▓ ordersByOrganizations ╨┐╤Г╤Б╤В╨╛, ╨┐╤А╨╛╨▒╤Г╨╡╨╝ ╨┐╨╛╨╗╨╡ 'orders' ╨╕╨╗╨╕ 'items' ╨╜╨░ ╨▓╨╡╤А╤Е╨╜╨╡╨╝ ╤Г╤А╨╛╨▓╨╜╨╡
        if not orders:
            orders = data.get("orders") or data.get("items") or []
            
        if not orders and log_error:
            # ╨Ю╤В╤Б╤Г╤В╤Б╤В╨▓╨╕╨╡ ╨╖╨░╨║╨░╨╖╨╛╨▓ ╨╖╨░ 2-╤З╨░╤Б╨╛╨▓╨╛╨╣ ╨┐╨╡╤А╨╕╨╛╨┤ - ╤Н╤В╨╛ ╨░╨▒╤Б╨╛╨╗╤О╤В╨╜╨╛ ╤И╤В╨░╤В╨╜╨░╤П ╤Б╨╕╤В╤Г╨░╤Ж╨╕╤П (╨╜╨░╨┐╤А╨╕╨╝╨╡╤А, ╨╜╨╛╤З╤М╤О ╨╕╨╗╨╕ ╨║╨╛╨│╨┤╨░ ╨╜╨╡╤В ╨┤╨╛╤Б╤В╨░╨▓╨╛╨║).
            # ╨Ь╤Л ╨╗╨╛╨│╨╕╤А╤Г╨╡╨╝ ╤Н╤В╨╛ ╤В╨╛╨╗╤М╨║╨╛ ╨║╨░╨║ INFO ╨╕╨╗╨╕ DEBUG, ╤З╤В╨╛╨▒╤Л ╨╜╨╡ ╨╖╨░╤Б╨╛╤А╤П╤В╤М ╤В╨░╨▒╨╗╨╕╤Ж╤Г ╤Б╨╕╤Б╤В╨╡╨╝╨╜╤Л╤Е ╨╗╨╛╨│╨╛╨▓ (system_logs).
            logger.info(f"╨Ч╨░╨║╨░╨╖╤Л ╨╛╤В╤Б╤Г╤В╤Б╤В╨▓╤Г╤О╤В ╨▓ ╨┐╨╡╤А╨╕╨╛╨┤╨╡ {query_from} - {query_to} (╨Э╨╛╤А╨╝╨░╨╗╤М╨╜╨╛╨╡ ╨┐╨╛╨▓╨╡╨┤╨╡╨╜╨╕╨╡)")
            if data.get("ordersByOrganizations") == []:
                 logger.debug("╨Я╨╛╨╗╨╡ ordersByOrganizations ╨┐╤А╨╕╤Б╤Г╤В╤Б╤В╨▓╤Г╨╡╤В, ╨╜╨╛ ╨┐╤Г╤Б╤В╨╛╨╡.")
            
        logger.info(f"╨Ш╤В╨╛╨│╨╛ ╨┐╨╛╨╗╤Г╤З╨╡╨╜╨╛ ╨╖╨░╨║╨░╨╖╨╛╨▓ ╨╕╨╖ Cloud: {len(orders)}")
        return orders

    async def update_webhooks(
        self,
        webhook_url: str,
        auth_token: str,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ╨Ю╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╕╨╡ ╨╜╨░╤Б╤В╤А╨╛╨╡╨║ ╨▓╨╡╨▒╤Е╤Г╨║╨╛╨▓ ╨▓ iiko Cloud.
        ╨а╨╡╨│╨╕╤Б╤В╤А╨╕╤А╤Г╨╡╤В URL ╨╕ ╨┐╨╛╨┤╨┐╨╕╤Б╤Л╨▓╨░╨╡╤В╤Б╤П ╨╜╨░ ╤Б╨╛╨▒╤Л╤В╨╕╤П.
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
        
        logger.info(f"╨Ю╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╕╨╡ ╨▓╨╡╨▒╤Е╤Г╨║╨╛╨▓ iiko: URL={webhook_url}, ╨Ю╤А╨│={org_id}")
        try:
            result = await self._request(
                "POST", "/api/1/webhooks/update", 
                payload,
                api_login=api_login,
                organization_id=org_id
            )
            logger.info(f"╨Т╨╡╨▒╤Е╤Г╨║╨╕ iiko ╤Г╤Б╨┐╨╡╤И╨╜╨╛ ╨╛╨▒╨╜╨╛╨▓╨╗╨╡╨╜╤Л: {result}")
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╨╛╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╕╨╕ ╨▓╨╡╨▒╤Е╤Г╨║╨╛╨▓ iiko: {e}")
            return {"success": False, "error": str(e)}

    async def get_active_orders(
        self,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        ╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨▓╤Б╨╡╤Е ╤В╨╡╨║╤Г╤Й╨╕╤Е ╨░╨║╤В╨╕╨▓╨╜╤Л╤Е ╨╖╨░╨║╨░╨╖╨╛╨▓ ╨╕╨╖ iiko.
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
        
        # ╨Т Iiko Cloud API v2 ╨╖╨░╨║╨░╨╖╤Л ╤Б╨│╤А╤Г╨┐╨┐╨╕╤А╨╛╨▓╨░╨╜╤Л ╨┐╨╛ ╨╛╤А╨│╨░╨╜╨╕╨╖╨░╤Ж╨╕╤П╨╝
        orders = []
        organizations_data = data.get("ordersByOrganizations", [])
        
        if organizations_data:
            for org_data in organizations_data:
                orders.extend(org_data.get("orders", []))
        else:
            orders = data.get("orders", [])
            
        logger.info(f"╨Р╨║╤В╨╕╨▓╨╜╤Л╤Е ╨╖╨░╨║╨░╨╖╨╛╨▓ ╨┐╨╛╨╗╤Г╤З╨╡╨╜╨╛: {len(orders)}")
        return orders

    # =========================================================================
    # ╨б╨╛╤В╤А╤Г╨┤╨╜╨╕╨║╨╕ ╨╕ ╤Б╨╝╨╡╨╜╤Л
    # =========================================================================

    async def get_employees(
        self,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        ╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤Б╨┐╨╕╤Б╨║╨░ ╤Б╨╛╤В╤А╤Г╨┤╨╜╨╕╨║╨╛╨▓ ╨╛╤А╨│╨░╨╜╨╕╨╖╨░╤Ж╨╕╨╕. 
        ╨б╨╜╨░╤З╨░╨╗╨░ ╨┐╤А╨╛╨▒╤Г╨╡╨╝ ╨╛╨▒╤Й╨╕╨╣ ╤Б╨┐╨╕╤Б╨╛╨║, ╨╡╤Б╨╗╨╕ ╨╜╨╡╤В ╨┐╤А╨░╨▓ - ╨╛╤В╨║╨░╤В╤Л╨▓╨░╨╡╨╝╤Б╤П ╨╜╨░ ╤Б╨┐╨╕╤Б╨╛╨║ ╨║╤Г╤А╤М╨╡╤А╨╛╨▓.
        """
        org_id = organization_id or self.organization_id
        data = None
        used_fallback = False
        
        try:
            # 1. ╨Я╤А╨╛╨▒╤Г╨╡╨╝ ╨┐╨╛╨╗╤Г╤З╨╕╤В╤М ╨┐╨╛╨╗╨╜╤Л╨╣ ╤Б╨┐╨╕╤Б╨╛╨║ (╤В╤А╨╡╨▒╤Г╨╡╤В ╨┐╤А╨░╨▓ ╨╜╨░ Staff Management)
            data = await self._request(
                "POST", "/api/1/employees", 
                {"organizationIds": [org_id]},
                api_login=api_login,
                organization_id=org_id,
                log_error=False
            )
        except httpx.HTTPStatusError as e:
            # ╨Х╤Б╨╗╨╕ 401 ╨╕╨╗╨╕ 403 - ╨╖╨╜╨░╤З╨╕╤В ╨╜╨╡╤В ╨┐╤А╨░╨▓ ╨╜╨░ ╤Н╤В╨╛╤В ╤Н╨╜╨┤╨┐╨╛╨╕╨╜╤В, ╨┐╤А╨╛╨▒╤Г╨╡╨╝ ╨║╤Г╤А╤М╨╡╤А╨╛╨▓
            if e.response.status_code in [401, 403]:
                logger.warning(f"╨Ф╨╛╤Б╤В╤Г╨┐ ╨║ /api/1/employees ╨╛╨│╤А╨░╨╜╨╕╤З╨╡╨╜ (401/403). ╨Я╨╡╤А╨╡╨║╨╗╤О╤З╨╡╨╜╨╕╨╡ ╨╜╨░ /couriers.")
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
        # ╨Ю╤В╨▓╨╡╤В ╨╕╨╝╨╡╨╡╤В ╤Б╤В╤А╤Г╨║╤В╤Г╤А╤Г: {"employees": [{"organizationId": "...", "items": [{...}]}]}
        for org_data in data.get("employees", []):
            if org_data.get("organizationId") == org_id:
                for item in org_data.get("items", []):
                    # ╨г╨╜╨╕╨▓╨╡╤А╤Б╨░╨╗╤М╨╜╨╛╨╡ ╨┐╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨╕╨╝╨╡╨╜╨╕ (displayName ╨╕╨╗╨╕ firstName + lastName)
                    name = item.get("displayName")
                    if not name or name == "": # ╨Ю╨▒╤А╨░╨▒╨╛╤В╨║╨░ ╨▒╨╕╤В╤Л╤Е ╤Б╨╕╨╝╨▓╨╛╨╗╨╛╨▓ ╨╡╤Б╨╗╨╕ ╨╡╤Б╤В╤М
                        fname = item.get("firstName") or ""
                        lname = item.get("lastName") or ""
                        name = f"{fname} {lname}".strip() or "Unnamed"
                    
                    # ╨Ш╨╖╨▓╨╗╨╡╨║╨░╨╡╨╝ ╤А╨╛╨╗╨╕ (╨▓ /couriers ╨╕╤Е ╨╜╨╡╤В)
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨░╨║╤В╨╕╨▓╨╜╤Л╤Е ╨╗╨╛╨║╨░╤Ж╨╕╨╣ ╨║╤Г╤А╤М╨╡╤А╨╛╨▓"""
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤Б╨╡╨║╤Ж╨╕╨╣ ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨░ (╨╖╨░╨╗╨╛╨▓)"""
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
        # ╨Ч╨░╨┐╤А╨░╤И╨╕╨▓╨░╨╡╨╝ ╨╖╨░ ╨┐╨╛╤Б╨╗╨╡╨┤╨╜╨╕╨╡ 2 ╤З╨░╤Б╨░, ╤З╤В╨╛╨▒╤Л ╨┐╨╛╨╗╤Г╤З╨╕╤В╤М ╨░╨║╤В╤Г╨░╨╗╤М╨╜╤Л╨╣ maxRevision
        date_from = now - timedelta(hours=2)
        date_to = now + timedelta(minutes=10)
        
        try:
            # ╨Ш╨╜╤Б╤В╤А╤Г╨╝╨╡╨╜╤В iiko ╤В╤А╨╡╨▒╤Г╨╡╤В ╨┤╨░╤В╤Г ╨▓ ╤Д╨╛╤А╨╝╨░╤В╨╡ yyyy-MM-dd HH:mm:ss.fff
            date_format = "%Y-%m-%d %H:%M:%S.000"
            query_from = date_from.strftime(date_format)
            query_to = date_to.strftime(date_format)
            
            logger.info(f"Bootstrapping max revision for org {org_id} via time-based query ({query_from} - {query_to})...")
            
            # ╨Ь╤Л ╨▓╤Л╨╖╤Л╨▓╨░╨╡╨╝ by_delivery_date_and_status, ╨┐╨╛╤В╨╛╨╝╤Г ╤З╤В╨╛ ╨╛╨╜ ╨▓╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╤В maxRevision
            # ╨╕ ╨╜╨╡ ╤В╤А╨╡╨▒╤Г╨╡╤В startRevision (╨┐╨╛╨╖╨▓╨╛╨╗╤П╨╡╤В ╨╕╨╖╨▒╨╡╨╢╨░╤В╤М 400 TOO_OLD_REVISION)
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨┤╨╛╤Б╤В╨░╨▓╨╛╨║ ╨┐╨╛ ╤А╨╡╨▓╨╕╨╖╨╕╤П╨╝"""
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
        
        # ╨Т ╨╜╨╛╨▓╤Л╤Е ╨▓╨╡╤А╤Б╨╕╤П╤Е API ╨╖╨░╨║╨░╨╖╤Л ╨╝╨╛╨│╤Г╤В ╨▒╤Л╤В╤М ╨▓ ordersByOrganizations
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
        ╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤Б╨┐╨╕╤Б╨║╨░ ╤Б╨╝╨╡╨╜ ╨╖╨░ ╤Г╨║╨░╨╖╨░╨╜╨╜╤Л╨╣ ╨┐╨╡╤А╨╕╨╛╨┤ (iiko API)
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
            logger.error(f"╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╨┐╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╕ ╤Б╨╝╨╡╨╜: {e}")
            return []

    async def get_schedules(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: Optional[str] = None,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        ╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨│╤А╨░╤Д╨╕╨║╨░ ╤Б╨╝╨╡╨╜ (╨╖╨░╨┐╨╗╨░╨╜╨╕╤А╨╛╨▓╨░╨╜╨╜╤Л╤Е) ╨╖╨░ ╤Г╨║╨░╨╖╨░╨╜╨╜╤Л╨╣ ╨┐╨╡╤А╨╕╨╛╨┤ (iiko API)
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
            # ╨Ю╤В╨▓╨╡╤В ╨╛╨▒╤Л╤З╨╜╨╛ ╤Б╨╛╨┤╨╡╤А╨╢╨╕╤В ╤Б╨┐╨╕╤Б╨╛╨║ ╤А╨░╤Б╨┐╨╕╤Б╨░╨╜╨╕╨╣ ╨┤╨╗╤П ╤А╨░╨╖╨╜╤Л╤Е ╨│╤А╤Г╨┐╨┐/╨╛╤А╨│╨░╨╜╨╕╨╖╨░╤Ж╨╕╨╣
            # ╨Ь╤Л ╨▓╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╨╝ ╨┐╨╗╨╛╤Б╨║╨╕╨╣ ╤Б╨┐╨╕╤Б╨╛╨║ ╨▓╤Б╨╡╤Е ╨╖╨░╨┐╨╕╤Б╨╡╨╣ ╨│╤А╨░╤Д╨╕╨║╨░
            schedules = []
            for org_schedule in data.get("schedules", []):
                schedules.extend(org_schedule.get("items", []))
            return schedules
        except Exception as e:
            logger.error(f"╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╨┐╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╕ ╨│╤А╨░╤Д╨╕╨║╨╛╨▓: {e}")
            return []

    # =========================================================================
    # ╨Я╤А╨╛╨│╤А╨░╨╝╨╝╨░ ╨╗╨╛╤П╨╗╤М╨╜╨╛╤Б╤В╨╕ (iikoCard)
    # =========================================================================

    async def get_customer_info(
        self,
        phone: str,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨╕╨╜╤Д╨╛╤А╨╝╨░╤Ж╨╕╨╕ ╨╛ ╨║╨╗╨╕╨╡╨╜╤В╨╡ ╨╕╨╖ ╨┐╤А╨╛╨│╤А╨░╨╝╨╝╤Л ╨╗╨╛╤П╨╗╤М╨╜╨╛╤Б╤В╨╕ iiko
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨▒╨░╨╗╨░╨╜╤Б╨░ ╨▒╨╛╨╜╤Г╤Б╨╛╨▓ ╨║╨╗╨╕╨╡╨╜╤В╨░"""
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
        """╨Э╨░╤З╨╕╤Б╨╗╨╡╨╜╨╕╨╡/╤Б╨┐╨╕╤Б╨░╨╜╨╕╨╡ ╨▒╨╛╨╜╤Г╤Б╨╛╨▓ ╨║╨╗╨╕╨╡╨╜╤В╨░ (iikoCard) ╨▓╤А╤Г╤З╨╜╤Г╤О"""
        org_id = organization_id or self.organization_id
        payload = {
            "organizationId": org_id,
            "customerId": customer_id,
            "walletId": wallet_id,
            "sum": amount,
            "comment": "╨С╨╛╨╜╤Г╤Б╤Л ╨╖╨░ ╨░╨║╤В╨╕╨▓╨╜╨╛╤Б╤В╤М ╨▓ VK"
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
        """╨Я╨╛╨╗╤Г╤З╨╕╤В╤М ╨┤╨╡╤В╨░╨╗╤М╨╜╤Г╤О ╨╕╨╜╤Д╨╛╤А╨╝╨░╤Ж╨╕╤О ╨╛ ╨╖╨░╨║╨░╨╖╨╡ ╨┐╨╛ ╨╡╨│╨╛ ID"""
        org_id = organization_id or self.organization_id
        payload = {
            "organizationId": org_id,
            "orderIds": [order_id]
        }
        # ╨Т iiko Cloud API v1 ╤Н╨╜╨┤╨┐╨╛╨╕╨╜╤В ╨┤╨╗╤П ╨┐╨╛╨╗╤Г╤З╨╡╨╜╨╕╤П ╨╖╨░╨║╨░╨╖╨╛╨▓ ╨┐╨╛ ID: /api/1/deliveries/by_id
        res = await self._request(
            "POST", "/api/1/deliveries/by_id",
            payload,
            api_login=api_login,
            organization_id=org_id
        )
        
        orders = []
        # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝ ╨╜╨╛╨▓╤Г╤О ╤Б╤В╤А╤Г╨║╤В╤Г╤А╤Г v2
        if res and res.get("ordersByOrganizations"):
            for org_data in res["ordersByOrganizations"]:
                orders.extend(org_data.get("orders", []))
        
        # ╨Х╤Б╨╗╨╕ ╨┐╤Г╤Б╤В╨╛, ╨┐╤А╨╛╨▒╤Г╨╡╨╝ ╤Б╤В╨░╤А╤Г╤О ╤Б╤В╤А╤Г╨║╤В╤Г╤А╤Г v1
        if not orders and res:
            orders = res.get("orders", [])

        if orders:
            return orders[0]
        return None

    # =========================================================================
    # ╨Т╨╡╨▒╤Е╤Г╨║╨╕
    # =========================================================================

    async def get_webhook_settings(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤В╨╡╨║╤Г╤Й╨╕╤Е ╨╜╨░╤Б╤В╤А╨╛╨╡╨║ ╨▓╨╡╨▒╤Е╤Г╨║╨╛╨▓ ╨╕╨╖ iiko Cloud"""
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
        ╨Ю╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╕╨╡ ╨╜╨░╤Б╤В╤А╨╛╨╡╨║ ╨▓╨╡╨▒╤Е╤Г╨║╨╛╨▓. ╨Я╤А╨╕╨╝╨╡╨╜╤П╨╡╤В ╨╖╨░╤Й╨╕╤В╤Г ╨╛╤В 429 (Too Many Requests),
        ╨┐╤А╨╛╨▓╨╡╤А╤П╤П, ╨╜╤Г╨╢╨╜╨╛ ╨╗╨╕ ╨▓╨╛╨╛╨▒╤Й╨╡ ╨╛╨▒╨╜╨╛╨▓╨╕╤В╤М ╨╜╨░╤Б╤В╤А╨╛╨╣╨║╨╕ ╨┐╨╡╤А╨╡╨┤ ╨╛╤В╨┐╤А╨░╨▓╨║╨╛╨╣.
        """
        org_id = organization_id or self.organization_id
        
        # ╨Ч╨░╤Й╨╕╤В╨░ ╨╛╤В 429: ╨┐╤А╨╛╨▓╨╡╤А╨╕╨╝, ╨╝╨╛╨╢╨╡╤В ╨▒╤Л╤В╤М ╨╜╨░╤Б╤В╤А╨╛╨╣╨║╨╕ ╤Г╨╢╨╡ ╤Г╤Б╤В╨░╨╜╨╛╨▓╨╗╨╡╨╜╤Л ╤В╨╡, ╤З╤В╨╛ ╨╜╤Г╨╢╨╜╨╛?
        try:
            current = await self.get_webhook_settings(api_login=api_login, organization_id=org_id)
            if current:
                current_uri = current.get("webHooksUri")
                current_token = current.get("authToken")
                
                # ╨Х╤Б╨╗╨╕ URL ╨╕ ╨в╨╛╨║╨╡╨╜ ╤Г╨╢╨╡ ╤Б╨╛╨▓╨┐╨░╨┤╨░╤О╤В - ╨╜╨╡ ╨╝╤Г╤З╨░╨╡╨╝ iiko API (╨╖╨░╤Й╨╕╤В╨░ ╨╛╤В 429)
                if current_uri == webhook_url and (not auth_token or current_token == auth_token):
                    logger.info(f"[iiko_service] Webhook settings (URI & Token) already match. Skipping update to avoid 429.")
                    # ╨Т╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╨╝ ╤Б╤В╤А╤Г╨║╤В╤Г╤А╤Г, ╨┐╨╛╤Е╨╛╨╢╤Г╤О ╨╜╨░ ╤Г╤Б╨┐╨╡╤И╨╜╤Л╨╣ ╨╛╤В╨▓╨╡╤В iiko, ╤З╤В╨╛╨▒╤Л ╨▓╤Л╨╖╤Л╨▓╨░╤О╤Й╨╕╨╣ ╨║╨╛╨┤ (register_webhook) ╨╝╨╛╨│ ╨┐╤А╨╛╨┤╨╛╨╗╨╢╨╕╤В╤М
                    if "correlationId" not in current:
                        current["correlationId"] = "already-synced"
                    return current
        except Exception as e:
            logger.warning(f"[iiko_service] get_webhook_settings failed (possibly 429 too): {e}")

        payload = {
            "organizationId": org_id,
            "webHooksUri": webhook_url,
            "webHooksFilter": {
                "deliveryOrderFilter": {
                    "orderStatuses": [
                        "Unconfirmed", "WaitCooking", "ReadyForCooking", 
                        "CookingStarted", "CookingCompleted", "Waiting", 
                        "OnWay", "Delivered", "Closed", "Cancelled"
                    ],
                    "errors": True
                },
                "stopListUpdateFilter": {
                    "updates": True
                },
                "nomenclatureUpdateFilter": {
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
                        # ╨Х╤Б╨╗╨╕ ╨╕╤Б╤З╨╡╤А╨┐╨░╨╜ ╨╗╨╕╨╝╨╕╤В ╨┐╨╛╨┐╤Л╤В╨╛╨║ ╨╕ ╨╝╤Л ╨┐╨╛╨╗╤Г╤З╨░╨╡╨╝ 429, 
                        # ╨╝╤Л ╨╝╨╛╨╢╨╡╨╝ ╨▓╤Л╨▒╤А╨╛╤Б╨╕╤В╤М ╨╛╤И╨╕╨▒╨║╤Г ╨╕╨╗╨╕ ╨┐╤А╨╛╤Б╤В╨╛ ╨╖╨░╨╗╨╛╨│╨╕╤А╨╛╨▓╨░╤В╤М ╨╕ ╤Б╨┤╨╡╨╗╨░╤В╤М ╨▓╨╕╨┤, ╤З╤В╨╛ ╤Г╤Б╨┐╨╡╤Е
                        # ╨Э╨╛ ╨╡╤Б╨╗╨╕ ╨╝╤Л ╤Н╤В╨╛ ╤Б╨┤╨╡╨╗╨░╨╡╨╝, ╤В╨╛ secret_key ╨╝╨╛╨╢╨╡╤В ╨╜╨╡ ╤Б╨╛╨▓╨┐╨░╤Б╤В╤М. ╨Т╤Л╨▒╤А╨░╤Б╤Л╨▓╨░╨╡╨╝ ╨╛╤И╨╕╨▒╨║╤Г ╤Б ╨┐╨╛╨╜╤П╤В╨╜╤Л╨╝ ╤В╨╡╨║╤Б╤В╨╛╨╝.
                        raise ValueError("iiko API Error: ╨б╨╗╨╕╤И╨║╨╛╨╝ ╨╝╨╜╨╛╨│╨╛ ╨┐╨╛╨┐╤Л╤В╨╛╨║ ╨╛╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╕╤П ╨▓╨╡╨▒╤Е╤Г╨║╨░ (╨╛╤И╨╕╨▒╨║╨░ 429). ╨Я╨╛╨┤╨╛╨╢╨┤╨╕╤В╨╡ ╨╜╨╡╤Б╨║╨╛╨╗╤М╨║╨╛ ╨╝╨╕╨╜╤Г╤В ╨┐╨╡╤А╨╡╨┤ ╨┐╨╛╨▓╤В╨╛╤А╨╜╨╛╨╣ ╨┐╨╛╨┐╤Л╤В╨║╨╛╨╣.")
                raise e

    async def auto_register_webhook(self,
        session: Optional[Session] = None,
        base_url: Optional[str] = None,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None,
        request_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ╨Р╨▓╤В╨╛╨╝╨░╤В╨╕╤З╨╡╤Б╨║╨░╤П ╤А╨╡╨│╨╕╤Б╤В╤А╨░╤Ж╨╕╤П ╨▓╨╡╨▒╤Е╤Г╨║╨░:
        1. ╨У╨╡╨╜╨╡╤А╨░╤Ж╨╕╤П ╨▒╨╡╨╖╨╛╨┐╨░╤Б╨╜╨╛╨│╨╛ ╤В╨╛╨║╨╡╨╜╨░.
        2. ╨Ю╨┐╤А╨╡╨┤╨╡╨╗╨╡╨╜╨╕╨╡ URL (╨╕╨╖ ╨┐╨░╤А╨░╨╝╨╡╤В╤А╨╛╨▓, ╨╖╨░╨┐╤А╨╛╤Б╨░ ╨╕╨╗╨╕ ╨╜╨░╤Б╤В╤А╨╛╨╡╨║).
        3. ╨а╨╡╨│╨╕╤Б╤В╤А╨░╤Ж╨╕╤П ╨▓ iiko.
        4. ╨б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╨╡ ╨▓ ╨С╨Ф (╨╡╤Б╨╗╨╕ ╨┐╨╡╤А╨╡╨┤╨░╨╜ session).
        """
        public_url = settings.APP_PUBLIC_URL
        if public_url and "your-public-url.ngrok-free.app" in public_url:
            public_url = None  # ╨Ш╨│╨╜╨╛╤А╨╕╤А╨╛╨▓╨░╤В╤М ╨┤╨╡╤Д╨╛╨╗╤В╨╜╤Г╤О ╨╖╨░╨│╨╗╤Г╤И╨║╤Г ngrok

        # ╨Я╤А╨╕╨╛╤А╨╕╤В╨╡╤В: 1. ╨п╨▓╨╜╤Л╨╣ base_url 2. URL ╨╕╨╖ ╨╖╨░╨┐╤А╨╛╤Б╨░ 3. APP_PUBLIC_URL ╨╕╨╖ .env
        url = base_url or request_url or public_url
        
        if not url:
            raise ValueError("Webhook URL cannot be determined. Set APP_PUBLIC_URL or use frontend.")
        
        # ╨Я╨╛╨╗╤Г╤З╨░╨╡╨╝ ╤В╨╛╨╗╤М╨║╨╛ origin (╨▒╨░╨╖╨╛╨▓╤Л╨╣ ╨┤╨╛╨╝╨╡╨╜ ╨┤╨╛ /api)
        if "/api/" in url:
            url = url.split("/api/")[0]
            
        # ╨г╨▒╨╡╨╢╨┤╨░╨╡╨╝╤Б╤П, ╤З╤В╨╛ URL ╨╖╨░╨║╨░╨╜╤З╨╕╨▓╨░╨╡╤В╤Б╤П ╨╜╨░ ╨┐╤А╨░╨▓╨╕╨╗╤М╨╜╤Л╨╣ ╤Н╨╜╨┤╨┐╨╛╨╕╨╜╤В
        endpoint = "/api/v1/webhooks/iiko"
        if not url.endswith(endpoint):
            url = url.rstrip("/") + endpoint
        
        # ╨У╨╡╨╜╨╡╤А╨░╤Ж╨╕╤П ╤В╨╛╨║╨╡╨╜╨░ ╨╡╤Б╨╗╨╕ ╨╜╤Г╨╢╨╜╨╛
        auth_token = secrets.token_hex(16)
        
        # ╨а╨╡╨│╨╕╤Б╤В╤А╨░╤Ж╨╕╤П
        try:
            result = await self.update_webhook_settings(
                webhook_url=url,
                auth_token=auth_token,
                api_login=api_login,
                organization_id=organization_id
            )
        except ValueError as e:
            if "429" in str(e):
                print(f"[iiko_service] ╨Я╤А╨╕╨╜╤Г╨┤╨╕╤В╨╡╨╗╤М╨╜╨╛ ╤Б╨╛╤Е╤А╨░╨╜╤П╨╡╨╝ ╨▓╨╡╨▒╤Е╤Г╨║ ╨╗╨╛╨║╨░╨╗╤М╨╜╨╛: {e}")
                result = {"status": "rate_limited", "message": "╨Э╨░╤Б╤В╤А╨╛╨╣╨║╨╕ ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╤Л ╨╗╨╛╨║╨░╨╗╤М╨╜╨╛. iiko API ╨▓╨╡╤А╨╜╤Г╨╗ 429 (Too Many Requests), ╨┐╨╛╨┐╤А╨╛╨▒╤Г╨╣╤В╨╡ ╨┐╨╛╨╖╨╢╨╡, ╨╡╤Б╨╗╨╕ ╤В╤А╨╡╨▒╤Г╨╡╤В╤Б╤П ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П."}
            else:
                raise e
        
        # ╨б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╨╡ ╨▓ ╨С╨Ф (╤В╨╛╨╗╤М╨║╨╛ ╨╡╤Б╨╗╨╕ ╤А╨╡╨│╨╕╤Б╤В╤А╨░╤Ж╨╕╤П ╤Г╤Б╨┐╨╡╤И╨╜╨░)
        if session and result.get("correlationId"): # correlationId ╨╡╤Б╤В╤М ╤В╨╛╨╗╤М╨║╨╛ ╨▓ ╤Г╤Б╨┐╨╡╤И╨╜╨╛╨╝ ╨╛╤В╨▓╨╡╤В╨╡ iiko
            try:
                db_settings = session.exec(select(IikoSettings)).first()
                if db_settings:
                    db_settings.webhook_url = url
                    db_settings.webhook_auth_token = auth_token
                    session.add(db_settings)
                    session.commit()
                    logger.info(f"Webhook settings successfully registered and saved to DB: {url}")
            except Exception as e:
                logger.error(f"Failed to save webhook to DB: {e}")
        elif session:
            logger.warning(f"Webhook NOT saved to DB because registration failed or was rate limited: {result}")
        
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨╕╨╜╤Д╨╛╤А╨╝╨░╤Ж╨╕╨╕ ╨╛ ╨║╨╗╨╕╨╡╨╜╤В╨╡ ╨┐╨╛ ╨╜╨╛╨╝╨╡╤А╤Г ╤В╨╡╨╗╨╡╤Д╨╛╨╜╨░ (iiko Card)"""
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
                organization_id=org_id,
                log_error=False  # ╨Э╨╡ ╨╗╨╛╨│╨╕╤А╤Г╨╡╨╝ 400 ╨╛╤И╨╕╨▒╨║╨╕ ╨║╨░╨║ ERROR ╨╖╨┤╨╡╤Б╤М
            )
        except httpx.HTTPStatusError as e:
            # ╨Х╤Б╨╗╨╕ ╨║╨╗╨╕╨╡╨╜╤В ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜ - ╤Н╤В╨╛ ╤И╤В╨░╤В╨╜╨░╤П ╤Б╨╕╤В╤Г╨░╤Ж╨╕╤П ╨┤╨╗╤П ╨╜╨╛╨▓╤Л╤Е ╨│╨╛╤Б╤В╨╡╨╣
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

    async def get_customer_balance(
        self,
        customer_id: str,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> float:
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨▒╨░╨╗╨░╨╜╤Б╨░ ╨▒╨░╨╗╨╗╨╛╨▓ ╨║╨╗╨╕╨╡╨╜╤В╨░"""
        # ╨Т v1 ╨╕╨╜╤Д╨╛╤А╨╝╨░╤Ж╨╕╤П ╨╛ ╨▒╨░╨╗╨░╨╜╤Б╨╡ ╨╛╨▒╤Л╤З╨╜╨╛ ╨▓╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╤В╤Б╤П ╨▓ get_customer_info ╨▓ walletBalances
        # ╨Э╨╛ ╨╡╤Б╨╗╨╕ ╨╜╤Г╨╢╨╜╨╛ ╨╛╤В╨┤╨╡╨╗╤М╨╜╨╛╨╡ ╨┐╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡, iiko Card API ╨╕╨╝╨╡╨╡╤В ╤Б╨▓╨╛╨╕ ╨╛╤Б╨╛╨▒╨╡╨╜╨╜╨╛╤Б╤В╨╕
        info = await self.get_customer_info("", api_login=api_login, organization_id=organization_id)
        # ╨а╨╡╨░╨╗╨╕╨╖╨░╤Ж╨╕╤П ╨╖╨░╨▓╨╕╤Б╨╕╤В ╨╛╤В ╨║╨╛╨╜╨║╤А╨╡╤В╨╜╨╛╨╣ ╨▓╨╡╤А╤Б╨╕╨╕ iiko Card
        return 0.0

    async def add_customer_balance(
        self,
        customer_id: str,
        wallet_id: str,
        amount: float,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None,
        comment: str = "╨Э╨░╤З╨╕╤Б╨╗╨╡╨╜╨╕╨╡ ╨╖╨░ ╨░╨║╤В╨╕╨▓╨╜╨╛╤Б╤В╤М"
    ) -> bool:
        """╨Э╨░╤З╨╕╤Б╨╗╨╡╨╜╨╕╨╡ ╨▒╨░╨╗╨╗╨╛╨▓ ╨╜╨░ ╨║╨╛╤И╨╡╨╗╨╡╨║ ╨║╨╗╨╕╨╡╨╜╤В╨░"""
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
            
    async def create_or_update_customer(
        self,
        customer_data: Dict[str, Any],
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡ ╨╕╨╗╨╕ ╨╛╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╕╨╡ ╨║╨╗╨╕╨╡╨╜╤В╨░ ╨▓ iiko Cloud"""
        org_id = organization_id or self.organization_id
        payload = {
            "organizationId": org_id,
            "customer": customer_data
        }
        return await self._request(
            "POST", "/api/1/loyalty/iiko/customer/create_or_update",
            payload,
            api_login=api_login,
            organization_id=org_id
        )

    async def get_customer_categories(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╣ ╨│╨╛╤Б╤В╨╡╨╣"""
        org_id = organization_id or self.organization_id
        return await self._request(
            "POST", "/api/1/loyalty/iiko/customer_category",
            {"organizationId": org_id},
            api_login=api_login,
            organization_id=org_id
        )

    async def get_loyalty_programs(
        self,
        api_login: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤Б╨┐╨╕╤Б╨║╨░ ╨┐╤А╨╛╨│╤А╨░╨╝╨╝ ╨╗╨╛╤П╨╗╤М╨╜╨╛╤Б╤В╨╕"""
        org_id = organization_id or self.organization_id
        return await self._request(
            "POST", "/api/1/loyalty/iiko/program",
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨╕╤Б╤В╨╛╤А╨╕╨╕ ╤В╤А╨░╨╜╨╖╨░╨║╤Ж╨╕╨╣ ╨┐╨╛ ╨▒╨╛╨╜╤Г╤Б╨░╨╝ ╨│╨╛╤Б╤В╤П"""
        org_id = organization_id or self.organization_id
        from datetime import datetime
        
        # iiko API ╤В╤А╨╡╨▒╤Г╨╡╤В ╤Б╤В╤А╨╛╨│╨╕╨╣ ╤Д╨╛╤А╨╝╨░╤В ISO ╤Б ╨╝╨╕╨╗╨╗╨╕╤Б╨╡╨║╤Г╨╜╨┤╨░╨╝╨╕: YYYY-MM-DD HH:mm:ss.SSS
        date_format = "%Y-%m-%d %H:%M:%S.000"
        
        # ╨Ю╨▒╤А╨░╨▒╨╛╤В╨║╨░ date_from (╨╝╨╛╨╢╨╡╤В ╨┐╤А╨╕╨╣╤В╨╕ ╨║╨░╨║ ╨У╨У╨У╨У-╨Ь╨Ь-╨Ф╨Ф ╨╕╨╗╨╕ ╨У╨У╨У╨У-╨Ь╨Ь-╨Ф╨Ф ╨з╨з:╨Ь╨Ь:╨б╨б)
        try:
            if isinstance(date_from, str):
                if len(date_from) == 10: # ╨У╨У╨У╨У-╨Ь╨Ь-╨Ф╨Ф
                    dt_from = datetime.strptime(date_from, "%Y-%m-%d")
                else:
                    # ╨Я╤Л╤В╨░╨╡╨╝╤Б╤П ╤А╨░╤Б╨┐╨░╤А╤Б╨╕╤В╤М ╨║╨░╨║ ╨╡╤Б╤В╤М ╨╕ ╨┐╨╡╤А╨╡╤Д╨╛╤А╨╝╨░╤В╨╕╤А╨╛╨▓╨░╤В╤М
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
                log_error=False # ╨Э╨╡ ╤Б╨┐╨░╨╝╨╕╨╝ ERROR ╨┐╤А╨╕ ╨╜╨╡╨▓╨╡╤А╨╜╤Л╤Е ╨┤╨░╤В╨░╤Е ╨╕╨╗╨╕ ╨║╨╗╨╕╨╡╨╜╤В╨░╤Е
            )
        except httpx.HTTPStatusError as e:
            logger.warning(f"iiko API bonus history error: {e.response.status_code} | {e.response.text}")
            return {"transactions": []}
        except Exception as e:
            logger.error(f"Unexpected error fetching bonus history: {e}")
            return {"transactions": []}

    # =========================================================================
    # iiko Resto (Office API) - ╨а╨░╤Б╤И╨╕╤А╨╡╨╜╨╜╤Л╨╡ ╨┤╨░╨╜╨╜╤Л╨╡
    # =========================================================================

    async def get_order_details_resto(
        self,
        order_id: str,
        resto_url: Optional[str] = None,
        resto_login: Optional[str] = None,
        resto_password: Optional[str] = None
    ) -> Dict[str, Any]:
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨┤╨╡╤В╨░╨╗╤М╨╜╨╛╨╣ ╨╕╨╜╤Д╨╛╤А╨╝╨░╤Ж╨╕╨╕ ╨╛ ╨╖╨░╨║╨░╨╖╨╡ ╨╕╨╖ iiko Resto (Office)"""
        # ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╨╝ ╤Н╨╜╨┤╨┐╨╛╨╕╨╜╤В /deliveries/by_id ╨╕╨╗╨╕ ╨░╨╜╨░╨╗╨╛╨│╨╕╤З╨╜╤Л╨╣ ╨▓ Office API
        # ╨Т Office API ╤З╨░╤Б╤В╨╛ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╤В╤Б╤П XML.
        try:
            data = await self._resto_request(
                "GET", f"/deliveries/by_id?id={order_id}", 
                resto_url=resto_url,
                resto_login=resto_login,
                resto_password=resto_password
            )
            # ╨Х╤Б╨╗╨╕ ╨┐╤А╨╕╤И╨╡╨╗ XML, ╨▓ _resto_request ╨╛╨╜ ╨┐╤А╨╡╨▓╤А╨░╤В╨╕╤В╤Б╤П ╨▓ ╤Б╤В╤А╨╛╨║╤Г.
            # ╨Ф╨╗╤П ╨┐╤А╨╛╤Б╤В╨╛╤В╤Л ╨┐╨╛╨║╨░ ╨▓╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╨╝ ╨║╨░╨║ ╨╡╤Б╤В╤М, ╨┐╨░╤А╤Б╨╕╨╜╨│ ╨▒╤Г╨┤╨╡╤В ╨▓ ╨▓╤Л╨╖╤Л╨▓╨░╤О╤Й╨╡╨╝ ╨║╨╛╨┤╨╡ ╨╕╨╗╨╕ ╨╖╨┤╨╡╤Б╤М.
            return data if isinstance(data, dict) else {"raw": data}
        except Exception as e:
            logger.error(f"Error getting order details from Resto: {e}")
            return {}

    # =========================================================================
    # OLAP ╨Ю╤В╤З╨╡╤В╤Л
    # =========================================================================

    async def get_organization_report(
        self,
        organization_id: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ╨д╨╛╤А╨╝╨╕╤А╤Г╨╡╤В ╤А╨░╤Б╤И╨╕╤А╨╡╨╜╨╜╤Л╨╣ ╨╛╤В╤З╨╡╤В ╨┐╨╛ ╨╛╤А╨│╨░╨╜╨╕╨╖╨░╤Ж╨╕╨╕ ╨┤╨╗╤П ╨┤╨░╤И╨▒╨╛╤А╨┤╨░ (Dashboard).
        ╨Ю╨▒╤К╨╡╨┤╨╕╨╜╤П╨╡╤В ╨┤╨░╨╜╨╜╤Л╨╡ ╨╛ ╤В╨╡╤А╨╝╨╕╨╜╨░╨╗╨░╤Е, ╨╖╨░╨║╨░╨╖╨░╤Е ╨╕ OLAP-╤Б╤В╨░╤В╨╕╤Б╤В╨╕╨║╨╡.
        """
        from datetime import datetime, time
        import pytz
        import asyncio
        from app.core.database import get_session_sync
        from app.core.datetime_utils import get_tz_name
        
        # 1. ╨Я╨░╤А╤Б╨╕╨╜╨│ ╨┤╨░╤В ╨╕ ╤З╨░╤Б╨╛╨▓╨╛╨╣ ╨┐╨╛╤П╤Б
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

        # 2. ╨Я╨╛╨┤╨│╨╛╤В╨╛╨▓╨║╨░ ╤Д╤Г╨╜╨║╤Ж╨╕╨╣-╨╛╨▒╨╡╤А╤В╨╛╨║ ╨┤╨╗╤П ╤Б╤Л╤А╤Л╤Е ╨┤╨░╨╜╨╜╤Л╤Е
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
                # ╨Я╨╛╨╗╤Г╤З╨░╨╡╨╝ ╨╖╨░╨║╨░╨╖╤Л ╨╖╨░ ╨┐╨╡╤А╨╕╨╛╨┤ (╤Н╤В╨╛ ╨╜╨░╨┤╨╡╨╢╨╜╨╡╨╡ ╤З╨╡╨╝ by_revision ╤Б 0)
                orders = await self.get_orders_by_date(dt_f, dt_t, organization_id)
                # ╨д╨╛╤А╨╝╨╕╤А╤Г╨╡╨╝ ╤Б╤В╤А╤Г╨║╤В╤Г╤А╤Г ╨║╨░╨║ ╨▓ by_revision
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
                # ╨Х╤Б╨╗╨╕ 401/403, ╨┐╤А╨╛╨▒╤Г╨╡╨╝ /couriers
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
                return {"success": False, "error": str(e)}

        async def fetch_sections(tg_ids):
            try:
                raw = await self._request("POST", "/api/1/reserve/available_restaurant_sections", {"organizationIds": [organization_id], "terminalGroupIds": tg_ids}, organization_id=organization_id)
                return {"success": True, "data": raw, "cache": False, "cacheTime": False}
            except Exception as e:
                return {"success": False, "error": str(e)}

        # 3. ╨Т╤Л╨┐╨╛╨╗╨╜╨╡╨╜╨╕╨╡
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
            self.get_olap_report(date_from=dt_from, date_to=dt_to, organization_id=organization_id, raw_response=True),
            return_exceptions=True
        )

        ts_res, orders_res, empl_res, loc_res, sect_res, olap_res = results

        # 4. KPI ╨╕ Analytics
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
                    
                    # ╨б╤Г╨╝╨╝╨░ (╨┤╨╗╤П KPI ╨╡╤Б╨╗╨╕ OLAP ╨╜╨╡╨┤╨╛╤Б╤В╤Г╨┐╨╡╨╜)
                    o_sum = o.get("sum", 0)
                    revenue_total += o_sum
                    
                    # ╨Ъ╤А╨░╤В╨║╨╕╨╣ ╤Б╨┐╨╕╤Б╨╛╨║
                    short_orders.append({
                        "id": o.get("id"),
                        "number": o.get("number"),
                        "customer": (o.get("customer") or {}).get("name") or "╨У╨╛╤Б╤В╤М",
                        "status": st,
                        "sum": o_sum,
                        "whenCreated": o.get("whenCreated")
                    })
                    
                    # ╨в╨╛╨┐ ╤В╨╛╨▓╨░╤А╨╛╨▓ (╨╕╨╖ ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨╕╤А╨╛╨▓╨░╨╜╨╜╤Л╤Е ╨╖╨░╨║╨░╨╖╨╛╨▓)
                    for item in o.get("items", []):
                        name = item.get("name") or "╨в╨╛╨▓╨░╤А"
                        qty = item.get("amount", 0)
                        price = item.get("price", 0)
                        top_items_by_qty[name] = top_items_by_qty.get(name, 0) + qty
                        top_items_by_sum[name] = top_items_by_sum.get(name, 0) + (qty * price)
        
        # ╨Х╤Б╨╗╨╕ OLAP ╨▓╨╡╤А╨╜╤Г╨╗ ╨┤╨░╨╜╨╜╤Л╨╡, ╨▒╨╡╤А╨╡╨╝ ╨▓╤Л╤А╤Г╤З╨║╤Г ╨╛╤В╤В╤Г╨┤╨░ (╨╛╨╜╨░ ╤В╨╛╤З╨╜╨╡╨╡)
        olap_revenue = 0
        if isinstance(olap_res, list) and len(olap_res) > 0:
            for row in olap_res:
                if isinstance(row, dict):
                    olap_revenue += row.get("revenue", row.get("OrderSum", 0))
        
        if olap_revenue > 0:
            revenue_total = olap_revenue

        status_list = [{"status": k, "count": v} for k, v in orders_by_status.items()]
        
        # ╨б╨╛╤А╤В╨╕╤А╨╛╨▓╨║╨░ ╤В╨╛╨┐-╤В╨╛╨▓╨░╤А╨╛╨▓
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

        # ╨д╨╛╤А╨╝╨╕╤А╨╛╨▓╨░╨╜╨╕╨╡ ╨┐╨╗╨╛╤Б╨║╨╛╨│╨╛ ╤Б╨┐╨╕╤Б╨║╨░ ╤В╨╡╤А╨╝╨╕╨╜╨░╨╗╨╛╨▓ ╤Б ╨┤╨╛╨┐. ╨┐╨╛╨╗╤П╨╝╨╕ (╨║╨░╨║ ╨▓ RAW ╨┐╤А╨╕╨╝╨╡╤А╨╡)
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

        return {
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
                "kitchenAvgMin": 0, # ╨Я╨╛╨╖╨╢╨╡ ╨╝╨╛╨╢╨╜╨╛ ╨┤╨╛╨▒╨░╨▓╨╕╤В╤М ╨╕╨╖ ╨╗╨╛╨│╨╛╨▓ ╨║╤Г╤Е╨╜╨╕
                "travelAvgMin": 0,
                "couriersTotal": couriers_total,
                "couriersActive": couriers_active
            },
            "analytics": {
                "topItems": {"byQty": top_qty_list, "bySum": top_sum_list},
                "payments": {"list": []},
                "ordersShort": short_orders[:20] # ╨Я╨╛╤Б╨╗╨╡╨┤╨╜╨╕╨╡ 20 ╨╖╨░╨║╨░╨╖╨╛╨▓
            },
            "olap": olap_res if isinstance(olap_res, dict) else {"error": str(olap_res)},
            "errors": []
        }

    def _parse_olap_response(self, response: Any) -> List[Dict[str, Any]]:
        """╨г╨╜╨╕╨▓╨╡╤А╤Б╨░╨╗╤М╨╜╤Л╨╣ ╨┐╨░╤А╤Б╨╡╤А ╨┤╨╗╤П OLAP ╨╛╤В╨▓╨╡╤В╨╛╨▓ iiko (v1/v2, Cloud/Server)"""
        if not response:
            return []
            
        data_rows = []
        if isinstance(response, dict):
            # ╨д╨╛╤А╨╝╨░╤В: {"data": [[...], [...]], "columnNames": [...]}
            if "data" in response and "columnNames" in response:
                cols = response["columnNames"]
                rows = response["data"]
                if rows and len(rows) > 0:
                    if isinstance(rows[0], dict):
                        data_rows = rows
                    else:
                        data_rows = [dict(zip(cols, r)) for r in rows if isinstance(r, list)]
            # ╨д╨╛╤А╨╝╨░╤В: {"data": [{"col1": val, ...}, ...]}
            elif "data" in response and isinstance(response["data"], list):
                data_rows = response["data"]
            # ╨Я╤А╤П╨╝╨╛╨╣ ╨╛╤В╨▓╨╡╤В ╨║╨░╨║ ╤Б╨╗╨╛╨▓╨░╤А╤М
            elif any(k in response for k in ["fullSum", "OrderSum", "revenue", "Revenue"]):
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
        ╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ OLAP-╨╛╤В╤З╨╡╤В╨░ ╨┐╨╛ ╨▓╤Л╤А╤Г╤З╨║╨╡.
        ╨Я╤А╨╛╨▒╤Г╨╡╤В iiko Resto (Office) API, ╤В╨░╨║ ╨║╨░╨║ Cloud API ╤З╨░╤Б╤В╨╛ ╨┤╨░╨╡╤В 401.
        """
        org_id = organization_id or self.organization_id
        logger.info(f"get_olap_report: resto_url={resto_url}, resto_login={resto_login}, org_id={org_id}")
        fmt_date = "%Y-%m-%d"
        
        # ╨б╨╜╨░╤З╨░╨╗╨░ ╨┐╤А╨╛╨▒╤Г╨╡╨╝ ╤З╨╡╤А╨╡╨╖ Resto API (Office), ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╤П ╤А╨╡╨║╨╛╨╝╨╡╨╜╨┤╤Г╨╡╨╝╤Г╤О ╤Б╤В╤А╤Г╨║╤В╤Г╤А╤Г v2 (POST)
        try:
            # iiko Office (RMS) v2 (POST) ╨╛╨╢╨╕╨┤╨░╨╡╤В ISO ╤Д╨╛╤А╨╝╨░╤В ╤Б ╨╝╨╕╨╗╨╗╨╕╤Б╨╡╨║╤Г╨╜╨┤╨░╨╝╨╕
            # ╨з╤В╨╛╨▒╤Л ╨╕╨╖╨▒╨╡╨╢╨░╤В╤М ╨╛╤И╨╕╨▒╨║╨╕ 409 (╨┐╤Г╤Б╤В╨╛╨╣ ╨╕╨╜╤В╨╡╤А╨▓╨░╨╗) ╨┤╨╗╤П ╨╛╨┤╨╜╨╛╨│╨╛ ╨┤╨╜╤П, ╨┤╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ 1 ╨┤╨╡╨╜╤М ╨║ 'to'
            v2_from = date_from.strftime("%Y-%m-%dT00:00:00.000")
            v2_to = (date_to + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000")
            
            # ╨б╤В╨░╤А╤Л╨╣ ╤Д╨╛╤А╨╝╨░╤В ╨┤╨╗╤П v1 (Fallback)
            v1_from = date_from.strftime("%d.%m.%Y")
            v1_to = date_to.strftime("%d.%m.%Y")
            
            payload = {
                "reportType": "SALES",
                "groupByRowFields": ["Department", "OpenDate.Typed"],
                "aggregateFields": [
                    "OrderSum", 
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

            # ╨Я╤Л╤В╨░╨╡╨╝╤Б╤П ╨▓╤Л╨╖╨▓╨░╤В╤М v2 ╤Н╨╜╨┤╨┐╨╛╨╕╨╜╤В. 
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
                # ╨Х╤Б╨╗╨╕ 404, ╨╖╨╜╨░╤З╨╕╤В v2 ╨╜╨╡ ╨┐╨╛╨┤╨┤╨╡╤А╨╢╨╕╨▓╨░╨╡╤В╤Б╤П, ╨┐╤А╨╛╨▒╤Г╨╡╨╝ v1 (GET)
                if e.response.status_code == 404:
                    logger.info("Resto API v2 not found, falling back to v1 (GET)")
                    # ╨Т v1 (GET) ╨░╨│╤А╨╡╨│╨░╤В╤Л ╨╝╨╛╨│╤Г╤В ╨╜╨░╨╖╤Л╨▓╨░╤В╤М╤Б╤П ╨╕╨╜╨░╤З╨╡, ╨┐╤А╨╛╨▒╤Г╨╡╨╝ ╤Б╤В╨░╨╜╨┤╨░╤А╤В╨╜╤Л╨╡
                    params = [
                        ("key", "TOKEN"), # ╨Ч╨░╨│╨╗╤Г╤И╨║╨░, ╨┐╨╛╨┤╤Б╤В╨░╨▓╨╕╤В╤Б╤П ╨▓ _resto_request
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
                        resto_password=resto_password,
                        organization_id=org_id
                    )
                else:
                    raise e
            
            if raw_response:
                return response
                
            # ╨Я╨░╤А╤Б╨╕╨╜╨│ ╨╛╤В╨▓╨╡╤В╨░ v2/v1
            data_rows = self._parse_olap_response(response)
            
            logger.info(f"Resto OLAP parsed rows count: {len(data_rows)}")
            
            if raw_response:
                return data_rows
                
            if data_rows:
                result = []
                for row_dict in data_rows:
                    # ╨Ш╨╖╨▓╨╗╨╡╨║╨░╨╡╨╝ ╨┤╨░╨╜╨╜╤Л╨╡, ╨┐╨╛╨┤╨┤╨╡╤А╨╢╨╕╨▓╨░╤П ╨╛╨▒╨░ ╤Д╨╛╤А╨╝╨░╤В╨░ ╨║╨╗╤О╤З╨╡╨╣ (v2 ╨╕ v1)
                    rev = self._safe_float(row_dict.get("OrderSum", row_dict.get("fullSum", row_dict.get("OrderSumAfterDiscount", 0))))
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
        ╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨╡╨╢╨╡╨┤╨╜╨╡╨▓╨╜╨╛╨╣ ╨▓╤Л╤А╤Г╤З╨║╨╕ ╨╕ ╤Б╨║╨╕╨┤╨╛╨║ ╤З╨╡╤А╨╡╨╖ OLAP ╨┤╨╗╤П ╤А╨░╤Б╤З╨╡╤В╨░ ╤З╨╕╤Б╤В╨╛╨╣ ╨┐╤А╨╕╨▒╤Л╨╗╨╕.
        ╨Т╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╤В ╤Б╨╗╨╛╨▓╨░╤А╤М {╨┤╨░╤В╨░: {"revenue": float, "discounts": float}}
        """
        try:
            # ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╨╝ ╤Г╨╜╨╕╨▓╨╡╤А╤Б╨░╨╗╤М╨╜╤Л╨╣ ╨╝╨╡╤В╨╛╨┤ ╨┤╨╗╤П Server API (Resto)
            rows = await self.get_custom_olap_report(
                report_type="SALES",
                group_by_fields=["OpenDate.Typed"],
                aggregate_fields=["fullSum", "DiscountSum", "UniqOrderId"],
                date_from=date_from,
                date_to=date_to,
                organization_id=organization_id
            )
            
            result = {}
            for row in rows:
                raw_date = row.get("OpenDate.Typed", "")
                # ╨Э╨╛╤А╨╝╨░╨╗╨╕╨╖╨░╤Ж╨╕╤П ╨┤╨░╤В╤Л (2024-04-23T00:00:00 -> 2024-04-23)
                date_str = str(raw_date).split("T")[0].split(" ")[0] if raw_date else ""
                
                if date_str:
                    try:
                        rev = float(row.get("fullSum", 0))
                        disc = float(row.get("DiscountSum", 0))
                        
                        if date_str not in result:
                            result[date_str] = {"revenue": 0.0, "discounts": 0.0}
                        
                        result[date_str]["revenue"] += round(rev, 2)
                        result[date_str]["discounts"] += round(disc, 2)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"╨Ю╤И╨╕╨▒╨║╨░ ╨┐╨░╤А╤Б╨╕╨╜╨│╨░ ╤З╨╕╤Б╨╡╨╗ ╨▓ ╤Б╤В╤А╨╛╨║╨╡ OLAP {date_str}: {e}")

            logger.info(f"╨Ш╤В╨╛╨│╨╛╨▓╤Л╨╣ ╤Б╨╗╨╛╨▓╨░╤А╤М ╨▓╤Л╤А╤Г╤З╨║╨╕ (Server API): {list(result.keys())}")
            return result
            
        except Exception as e:
            logger.error(f"╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╨┐╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╕ ╨▓╤Л╤А╤Г╤З╨║╨╕ ╨╕╨╖ OLAP (Server API): {e}")
            return {}

    async def get_custom_olap_report(
        self,
        report_type: str,
        group_by_fields: List[str],
        aggregate_fields: List[str],
        date_from: datetime,
        date_to: datetime,
        organization_id: Optional[str] = None,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """╨г╨╜╨╕╨▓╨╡╤А╤Б╨░╨╗╤М╨╜╤Л╨╣ ╨╝╨╡╤В╨╛╨┤ ╨┤╨╗╤П ╨┐╨╛╨╗╤Г╤З╨╡╨╜╨╕╤П ╨╗╤О╨▒╤Л╤Е OLAP-╨╛╤В╤З╨╡╤В╨╛╨▓ ╤З╨╡╤А╨╡╨╖ Server API"""
        from datetime import timedelta
        org_id = organization_id or self.organization_id
        v2_from = date_from.strftime("%Y-%m-%dT00:00:00.000")
        v2_to = (date_to + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000")
        
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
                organization_id=org_id
            )
            return self._parse_olap_response(response)
        except Exception as e:
            logger.error(f"Custom OLAP report ({report_type}) failed: {e}")
            return []

    async def get_payment_types_report(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """╨Ю╤В╤З╨╡╤В ╨┐╨╛ ╤В╨╕╨┐╨░╨╝ ╨╛╨┐╨╗╨░╤В ╤З╨╡╤А╨╡╨╖ OLAP"""
        return await self.get_custom_olap_report(
            report_type="SALES",
            group_by_fields=["PayTypes", "OpenDate.Typed"],
            aggregate_fields=["fullSum", "UniqOrderId"],
            date_from=date_from,
            date_to=date_to,
            organization_id=organization_id
        )

    # =========================================================================
    # iiko Resto (Office API) - ╨Я╤А╤П╨╝╨╛╨╡ ╨┐╨╛╨┤╨║╨╗╤О╤З╨╡╨╜╨╕╨╡
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
        """╨Ь╨╡╤В╨╛╨┤ ╨┤╨╗╤П ╨╖╨░╨┐╤А╨╛╤Б╨╛╨▓ ╨║ iiko Resto (Office) API ╤Б SHA-1 ╨░╨▓╤В╨╛╤А╨╕╨╖╨░╤Ж╨╕╨╡╨╣"""
        # ╨Я╤Л╤В╨░╨╡╨╝╤Б╤П ╨┐╨╛╨╗╤Г╤З╨╕╤В╤М ╨╜╨░╤Б╤В╤А╨╛╨╣╨║╨╕ ╨╕╨╖ ╨С╨Ф ╨╡╤Б╨╗╨╕ ╨┐╨╡╤А╨╡╨┤╨░╨╜╨░ ╨╛╤А╨│╨░╨╜╨╕╨╖╨░╤Ж╨╕╤П
        db_settings = self._get_settings_by_org_id(organization_id) if organization_id else None
        
        url = resto_url or (db_settings.resto_url if db_settings else None) or settings.IIKO_RESTO_URL
        login = resto_login or (db_settings.resto_login if db_settings else None) or settings.IIKO_RESTO_LOGIN
        password = resto_password or (db_settings.resto_password if db_settings else None) or settings.IIKO_RESTO_PASSWORD

        if not url or not login:
            logger.error(f"Resto API not configured for org {organization_id}. URL: {url}, Login: {login}")
            raise ValueError("╨Ф╨░╨╜╨╜╤Л╨╡ iiko Resto (URL/Login) ╨╜╨╡ ╨╜╨░╤Б╤В╤А╨╛╨╡╨╜╤Л.")

        # Normalize URL
        base_url = url.rstrip('/')
        if not base_url.endswith('/api'):
            if base_url.endswith('/resto'):
                base_url = f"{base_url}/api"
            else:
                base_url = f"{base_url}/resto/api"
        
        # 1. ╨Я╨╛╨╗╤Г╤З╨░╨╡╨╝ ╤В╨╛╨║╨╡╨╜
        async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
            auth_url = f"{base_url}/auth"
            
            # ╨Я╤А╨╛╨▒╤Г╨╡╨╝ SHA-1 (╤Б╨╛╨▓╤А╨╡╨╝╨╡╨╜╨╜╤Л╨╣ iiko)
            password_sha1 = hashlib.sha1(password.encode()).hexdigest()
            auth_params = {"login": login, "pass": password_sha1}
            
            logger.info(f"Resto Auth attempt (SHA-1) for {login} at {auth_url}")
            auth_response = await client.get(auth_url, params=auth_params)
            
            if auth_response.status_code != 200:
                # ╨Я╤А╨╛╨▒╤Г╨╡╨╝ plain text (╤Б╤В╨░╤А╤Л╨╣ iiko)
                logger.info(f"Resto Auth SHA-1 failed ({auth_response.status_code}), trying plain text")
                auth_response = await client.get(auth_url, params={"login": login, "pass": password})
                
                if auth_response.status_code != 200:
                    if log_error:
                        logger.error(f"╨Ю╤И╨╕╨▒╨║╨░ ╨░╨▓╤В╨╛╤А╨╕╨╖╨░╤Ж╨╕╨╕ Resto: {auth_response.status_code} | {auth_response.text}")
                    raise HTTPException(status_code=401, detail=f"╨Ю╤И╨╕╨▒╨║╨░ ╨░╨▓╤В╨╛╤А╨╕╨╖╨░╤Ж╨╕╨╕ Resto: {auth_response.text}")
            
            token = auth_response.text.strip().replace('"', '')
            
            # 2. ╨Т╤Л╨┐╨╛╨╗╨╜╤П╨╡╨╝ ╨╛╤Б╨╜╨╛╨▓╨╜╨╛╨╣ ╨╖╨░╨┐╤А╨╛╤Б
            request_url = f"{base_url}{endpoint}"
            
            # ╨Я╨╛╨┤╨│╨╛╤В╨╛╨▓╨║╨░ ╨┐╨░╤А╨░╨╝╨╡╤В╤А╨╛╨▓
            final_params = {}
            if isinstance(params, dict):
                final_params = params.copy()
            elif isinstance(params, list):
                # ╨Х╤Б╨╗╨╕ ╨┐╨╡╤А╨╡╨┤╨░╨╜ ╤Б╨┐╨╕╤Б╨╛╨║ (╨╜╨░╨┐╤А╨╕╨╝╨╡╤А ╨┤╨╗╤П ╨┤╤Г╨▒╨╗╨╕╤А╤Г╤О╤Й╨╕╤Е╤Б╤П ╨║╨╗╤О╤З╨╡╨╣), ╨┐╤А╨╡╨▓╤А╨░╤Й╨░╨╡╨╝ ╨▓ dict ╨╡╤Б╨╗╨╕ ╨╝╨╛╨╢╨╜╨╛
                # ╨Э╨╛ iiko ╤З╨░╤Б╤В╨╛ ╤В╤А╨╡╨▒╤Г╨╡╤В ╨┤╤Г╨▒╨╗╨╕╤А╤Г╤О╤Й╨╕╨╡╤Б╤П ╨║╨╗╤О╤З╨╕ (groupRow), ╤В╨░╨║ ╤З╤В╨╛ ╨╗╤Г╤З╤И╨╡ ╨╛╤Б╤В╨░╨▓╨╕╤В╤М ╨║╨░╨║ ╨╡╤Б╤В╤М
                # httpx ╨┐╨╛╨┤╨┤╨╡╤А╨╢╨╕╨▓╨░╨╡╤В ╤Б╨┐╨╕╤Б╨╛╨║ ╨║╨╛╤А╤В╨╡╨╢╨╡╨╣
                final_params = params.copy()
            
            if isinstance(final_params, dict):
                final_params["key"] = token
            else:
                final_params.append(("key", token))
            
            logger.info(f"Resto Request: {method} {request_url}")
            response = await client.request(method, request_url, params=final_params, json=json_data)
            
            if response.status_code >= 400:
                if log_error:
                    logger.error(f"iiko Resto error {response.status_code}: {response.text} | URL: {endpoint}")
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
        resto_password: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨┤╨╡╤В╨░╨╗╤М╨╜╨╛╨│╨╛ ╤Б╨┐╨╕╤Б╨║╨░ ╤Б╨╛╤В╤А╤Г╨┤╨╜╨╕╨║╨╛╨▓ ╨╕╨╖ iiko Resto"""
        # iiko Resto ╨▓╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╤В XML ╨┐╨╛ ╤Г╨╝╨╛╨╗╤З╨░╨╜╨╕╤О
        data = await self._resto_request(
            "GET", "/employees", 
            resto_url=resto_url or settings.IIKO_RESTO_URL,
            resto_login=resto_login or settings.IIKO_RESTO_LOGIN,
            resto_password=resto_password or settings.IIKO_RESTO_PASSWORD
        )
        
        # ╨Х╤Б╨╗╨╕ ╨┐╤А╨╕╤И╨╡╨╗ XML (╤Б╤В╤А╨╛╨║╨░), ╨╜╤Г╨╢╨╜╨╛ ╤А╨░╤Б╨┐╨░╤А╤Б╨╕╤В╤М. 
        if isinstance(data, str):
            import xml.etree.ElementTree as ET
            root = ET.fromstring(data)
            
            employees = []
            for emp in root.findall('employee'):
                # ╨Я╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤М ╨┐╤А╨╛╤Б╨╕╨╗ ╨▓╤Б╨╡ ╨┤╨░╨╜╨╜╤Л╨╡ ╨╛ ╨┤╨╛╨╗╨╢╨╜╨╛╤Б╤В╤П╤Е ╨╕ ╤А╨╛╨╗╤П╤Е
                # ╨Т iiko RESTO XML: mainRoleCode - ╨╛╤Б╨╜╨╛╨▓╨╜╨░╤П ╤А╨╛╨╗╤М, roleCodes - ╤Б╨┐╨╕╤Б╨╛╨║ ╨║╨╛╨┤╨╛╨▓ ╤З╨╡╤А╨╡╨╖ ╨╖╨░╨┐╤П╤В╤Г╤О
                employees.append({
                    "id": emp.findtext('id'),
                    "name": emp.findtext('name'),
                    "firstName": emp.findtext('firstName'),
                    "lastName": emp.findtext('lastName'),
                    "code": emp.findtext('code'), # ╨Т╨╜╤Г╤В╤А╨╡╨╜╨╜╨╕╨╣ ╨║╨╛╨┤
                    "org_id": emp.findtext('preferredDepartmentCode') or (emp.find('mainRole').findtext('organizationId') if emp.find('mainRole') is not None else None),
                    "phone": emp.findtext('phone') or emp.findtext('cellPhone'),
                    "email": emp.findtext('email'),
                    "role": self._extract_role(emp),
                    "role_codes": emp.findtext('roleCodes'), # ╨Т╤Б╨╡ ╤А╨╛╨╗╨╕
                    "main_role_code": emp.findtext('mainRoleCode'), # ╨Ю╤Б╨╜╨╛╨▓╨╜╨░╤П ╤А╨╛╨╗╤М
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨╗╨╕╤З╨╜╤Л╤Е ╤Б╨╝╨╡╨╜ ╤Б╨╛╤В╤А╤Г╨┤╨╜╨╕╨║╨╛╨▓ ╨╕╨╖ iiko Resto (Office) API"""
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨│╤А╨░╤Д╨╕╨║╨╛╨▓ ╤А╨░╨▒╨╛╤В╤Л ╤Б╨╛╤В╤А╤Г╨┤╨╜╨╕╨║╨╛╨▓ ╨╕╨╖ iiko Resto (Office) API"""
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨┤╨╡╤В╨░╨╗╤М╨╜╨╛╨╣ ╨╕╤Б╤В╨╛╤А╨╕╨╕ ╨┤╨╛╤Б╤В╨░╨▓╨╛╨║ ╨╕╨╖ iiko Resto ╤З╨╡╤А╨╡╨╖ OLAP"""
        try:
            from datetime import timedelta
            v2_from = date_from.strftime("%Y-%m-%dT00:00:00.000")
            v2_to = (date_to + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000")
            
            # ╨Я╨╛╨╗╤П ╨│╤А╤Г╨┐╨┐╨╕╤А╨╛╨▓╨║╨╕ ╨┤╨╗╤П DELIVERIES ╨╛╤В╤З╨╡╤В╨░
            payload = {
                "reportType": "DELIVERIES",
                "groupByRowFields": [
                    "Delivery.Number", 
                    "Delivery.Courier", 
                    "Delivery.Courier.Id",
                    "Delivery.Address",
                    "Delivery.City",
                    "Delivery.Street", 
                    "Delivery.Address.House",
                    "Delivery.Address.Flat",
                    "Delivery.Address.Entrance",
                    "Delivery.Address.Floor",
                    "Delivery.Address.Doorphone",
                    "Delivery.Region",
                    "Delivery.SendTime",
                    "Delivery.ActualTime",
                    "Delivery.ExpectedTime",
                    "Delivery.CustomerName",
                    "Delivery.CustomerPhone"
                ],
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
                organization_id=organization_id
            )
            
            data_rows = self._parse_olap_response(response)
            
            transformed = []
            for row in data_rows:
                # ╨Т Resto OLAP ╤З╨░╤Б╤В╨╛ ╨╜╨╡╤В ╨╛╤В╨┤╨╡╨╗╤М╨╜╤Л╤Е ╨┐╨╛╨╗╨╡╨╣ House, Flat ╨╕ ╤В.╨┤.
                # ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╨╝ Delivery.Address ╨║╨░╨║ ╨╛╤Б╨╜╨╛╨▓╨╜╤Г╤О ╤Б╤В╤А╨╛╨║╤Г ╨░╨┤╤А╨╡╤Б╨░
                raw_address = row.get("Delivery.Address") or ""
                
                # ╨б╨╛╨▒╨╕╤А╨░╨╡╨╝ ╤З╨░╤Б╤В╨╕ ╨┤╨╗╤П ╤Б╨╛╨▓╨╝╨╡╤Б╤В╨╕╨╝╨╛╤Б╤В╨╕ ╤Б format_address
                addr_parts = {
                    "city": row.get("Delivery.City"),
                    "street": row.get("Delivery.Street"),
                    "house": row.get("Delivery.Address.House"),
                    "flat": row.get("Delivery.Address.Flat"),
                    "entrance": row.get("Delivery.Address.Entrance"),
                    "floor": row.get("Delivery.Address.Floor"),
                    "doorphone": row.get("Delivery.Address.Doorphone"),
                    "line1": raw_address,
                    "addressString": raw_address
                }
                
                transformed.append({
                    "id": row.get("Delivery.Number"),
                    "address": addr_parts, 
                    "courierInfo": {
                        "courier": {"name": row.get("Delivery.Courier")}
                    },
                    "deliveryZone": row.get("Delivery.Region"),
                    "terminalName": None, 
                    "sum": self._safe_float(row.get("fullSum")),
                    "whenCookingCompleted": row.get("Delivery.SendTime"),
                    "expectedDeliveryTime": row.get("Delivery.ExpectedTime"),
                    "whenDelivered": row.get("Delivery.ActualTime"),
                    "customer": {
                        "name": row.get("Delivery.CustomerName"),
                        "phone": row.get("Delivery.CustomerPhone")
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤Б╨┐╨╕╤Б╨║╨░ ╤А╨╛╨╗╨╡╨╣ (╨┤╨╛╨╗╨╢╨╜╨╛╤Б╤В╨╡╨╣) ╨╕╨╖ iiko Resto"""
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨┤╨░╨╜╨╜╤Л╤Е ╨╛ ╤П╨▓╨║╨░╤Е (╤Б╨╝╨╡╨╜╨░╤Е) ╨╕╨╖ iiko Resto"""
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
        # ╨Р╨╜╨░╨╗╨╛╨│╨╕╤З╨╜╨╛ ╨┐╨░╤А╤Б╨╕╨╝ XML ╨╡╤Б╨╗╨╕ ╨╜╤Г╨╢╨╜╨╛
        if isinstance(data, str):
            import xml.etree.ElementTree as ET
            root = ET.fromstring(data)
            
            records = []
            for rec in root.findall('attendance'):
                # ╨Я╤А╨╛╨▒╤Г╨╡╨╝ ╨╜╨░╨╣╤В╨╕ ID ╨║╨░╨║ ╨▓ ╤В╨╡╨│╨╡, ╤В╨░╨║ ╨╕ ╨▓ ╨░╤В╤А╨╕╨▒╤Г╤В╨╡
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
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨┤╨░╨╜╨╜╤Л╤Е ╨╛ ╨╖╨╛╨╜╨░╤Е ╨┤╨╛╤Б╤В╨░╨▓╨║╨╕ ╨╕╨╖ iiko Resto (Office)"""
        # ╨н╨╜╨┤╨┐╨╛╨╕╨╜╤В ╨▓ Office API: /delivery/zones (╨▓╨╡╤А╤Б╨╕╤П 1) ╨╕╨╗╨╕ /delivery/zones.json (╨╡╤Б╨╗╨╕ ╨┐╨╛╨┤╨┤╨╡╤А╨╢╨╕╨▓╨░╨╡╤В╤Б╤П)
        try:
            logger.info(f"╨Ч╨░╨┐╤А╨╛╤Б ╨╖╨╛╨╜ ╨┤╨╛╤Б╤В╨░╨▓╨║╨╕ ╨╕╨╖ iiko Resto: {resto_url}/resto/api/delivery/zones")
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
        ╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤Б╨┐╨╕╤Б╨║╨░ GUID ╨╖╨░╨║╨░╨╖╨╛╨▓ ╨╕╨╖ iiko Resto.
        ╨Т RMS ╨╝╨╡╤В╨╛╨┤╨╡ by_date ╨┐╨░╤А╨░╨╝╨╡╤В╤А╤Л from ╨╕ to ╨▓ ╤Д╨╛╤А╨╝╨░╤В╨╡ yyyy-MM-dd
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
        """╨С╨╡╨╖╨╛╨┐╨░╤Б╨╜╨╛╨╡ ╨╕╨╖╨▓╨╗╨╡╤З╨╡╨╜╨╕╨╡ ╨╜╨░╨╖╨▓╨░╨╜╨╕╤П ╤А╨╛╨╗╨╕ ╨╕╨╖ ╤А╨░╨╖╨╜╤Л╤Е ╤Б╤В╤А╤Г╨║╤В╤Г╤А XML iiko"""
        # 1. mainRoleCode (╤Д╨░╨║╤В╨╕╤З╨╡╤Б╨║╨╕ ╨╜╨░╨╣╨┤╨╡╨╜ ╨▓ ╨╗╨╛╨│╨░╤Е)
        role_code = emp.findtext('mainRoleCode')
        if role_code: return role_code

        # 2. roleCodes (╤Б╨┐╨╕╤Б╨╛╨║ ╤В╨╡╨│╨╛╨▓)
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
            
        # 4. role (╨┐╤А╤П╨╝╨╛╨╣ ╤В╨╡╨│)
        role = emp.findtext('role')
        if role: return role
                
        return "Staff"

    def _safe_float(self, val: Any) -> float:
        """╨С╨╡╨╖╨╛╨┐╨░╤Б╨╜╨╛╨╡ ╨┐╤А╨╡╨╛╨▒╤А╨░╨╖╨╛╨▓╨░╨╜╨╕╨╡ ╨╖╨╜╨░╤З╨╡╨╜╨╕╤П ╨║ float"""
        try:
            return float(val) if val is not None else 0.0
        except (ValueError, TypeError):
            return 0.0

    # =========================================================================
    # iiko Transport (Cloud API) - ╨Ф╨╛╨┐╨╛╨╗╨╜╨╕╤В╨╡╨╗╤М╨╜╨░╤П ╤Б╤В╨░╤В╨╕╤Б╤В╨╕╨║╨░
    # =========================================================================

    async def get_courier_statistics(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: str,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤Б╤В╨░╤В╨╕╤Б╤В╨╕╨║╨╕ ╨┤╨╛╤Б╤В╨░╨▓╨╛╨║ ╨┐╨╛ ╨║╤Г╤А╤М╨╡╤А╨░╨╝ ╤З╨╡╤А╨╡╨╖ Transport API"""
        # ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╨╝ ╤Н╨╜╨┤╨┐╨╛╨╕╨╜╤В ╨╕╤Б╤В╨╛╤А╨╕╨╕ ╨┤╨╛╤Б╤В╨░╨▓╨╛╨║
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
        
        # ╨У╤А╤Г╨┐╨┐╨╕╤А╤Г╨╡╨╝ ╨┐╨╛ ╨║╤Г╤А╤М╨╡╤А╤Г ╨╕ ╨Ф╨Р╨в╨Х ╨┤╨╗╤П ╤В╨╛╤З╨╜╨╛╨│╨╛ ╨╝╨░╨┐╨┐╨╕╨╜╨│╨░ ╨▓ ╤Б╨╝╨╡╨╜╤Л
        # stats[courier_id][date_str] = count
        stats = {}
        for order in data.get("orders", []):
            courier = order.get("courierInfo", {}).get("courier", {})
            courier_id = courier.get("id")
            if not courier_id: continue
            
            # ╨Ш╨╖╨▓╨╗╨╡╨║╨░╨╡╨╝ ╨┤╨░╤В╤Г (╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╨╝ completeTime ╨╕╨╗╨╕ creationTime)
            # ╨Я╤А╨╕╨╝╨╡╤А: "2024-03-27 15:30:00.000"
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
        ╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨▓╤Л╤А╤Г╤З╨║╨╕ ╨┐╨╛ ╨║╤Г╤А╤М╨╡╤А╨░╨╝ ╤З╨╡╤А╨╡╨╖ OLAP-╨╛╤В╤З╨╡╤В iiko Resto (Office).
        ╨Т╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╤В ╤Б╨╗╨╛╨▓╨░╤А╤М {courier_id: {date_iso: revenue}}.
        """
        from datetime import timedelta
        try:
            # iiko Office (RMS) v2 (POST) ╨╛╨╢╨╕╨┤╨░╨╡╤В ISO ╤Д╨╛╤А╨╝╨░╤В
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
                    # OpenDate.Typed ╨╝╨╛╨╢╨╡╤В ╨┐╤А╨╕╤Е╨╛╨┤╨╕╤В╤М ╨║╨░╨║ "2024-03-27T00:00:00.000"
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

    async def get_delivery_restrictions(
        self,
        organization_id: str,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨╛╨│╤А╨░╨╜╨╕╤З╨╡╨╜╨╕╨╣ ╨╕ ╨╖╨╛╨╜ ╨┤╨╛╤Б╤В╨░╨▓╨║╨╕ ╨╕╨╖ iiko Cloud"""
        payload = {"organizationIds": [organization_id]}
        try:
            res = await self._request(
                "POST", "/api/1/delivery_restrictions",
                payload,
                api_login=api_login,
                organization_id=organization_id
            )
            # ╨Т╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╤В ╤Б╨┐╨╕╤Б╨╛╨║ ╨╛╨│╤А╨░╨╜╨╕╤З╨╡╨╜╨╕╨╣, ╨▓ ╨║╨░╨╢╨┤╨╛╨╝ ╨╡╤Б╤В╤М deliveryZones
            return res.get("deliveryRestrictions", [])
        except Exception as e:
            logger.error(f"Error getting delivery restrictions: {e}")
            return []


    async def get_detailed_deliveries(
        self,
        date_from: datetime,
        date_to: datetime,
        organization_id: str,
        api_login: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╨┤╨╡╤В╨░╨╗╤М╨╜╨╛╨╣ ╨╕╤Б╤В╨╛╤А╨╕╨╕ ╨┤╨╛╤Б╤В╨░╨▓╨╛╨║ ╨╕╨╖ iiko Cloud API"""
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
        ╨Ч╨░╨│╤А╤Г╨╢╨░╨╡╤В KML ╤Д╨░╨╣╨╗ (╨╜╨░╨┐╤А╨╕╨╝╨╡╤А, ╨╕╨╖ Google Maps ╨╕╨╗╨╕ iiko Cloud) ╨╕ ╨▓╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╤В ╨┐╨╛╨╗╨╕╨│╨╛╨╜╤Л.
        ╨д╨╛╤А╨╝╨░╤В ╨║╨╛╨╛╤А╨┤╨╕╨╜╨░╤В: [[lat, lng], ...]
        """
        if not url:
            return []
            
        # ╨Х╤Б╨╗╨╕ ╤Б╤Б╤Л╨╗╨║╨░ ╨╜╨░ Google My Maps, ╨┐╤А╨╛╨▒╤Г╨╡╨╝ ╨┐╨╛╨╗╤Г╤З╨╕╤В╤М ╨┐╤А╤П╨╝╤Г╤О ╤Б╤Б╤Л╨╗╨║╤Г ╨╜╨░ KML
        if "google.com/maps/d/edit" in url or "google.com/maps/d/viewer" in url:
            if "mid=" in url:
                mid = url.split("mid=")[1].split("&")[0]
                url = f"https://www.google.com/maps/d/u/0/kml?mid={mid}&forcekml=1"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                # ╨Я╤Л╤В╨░╨╡╨╝╤Б╤П ╨┐╨╛╨╗╤Г╤З╨╕╤В╤М ╤В╨╡╨║╤Б╤В ╨▓ UTF-8
                content = response.text
                logger.info(f"KML ╨╖╨░╨│╤А╤Г╨╢╨╡╨╜, ╤А╨░╨╖╨╝╨╡╤А: {len(content)} ╤Б╨╕╨╝╨▓╨╛╨╗╨╛╨▓. ╨Э╨░╤З╨╕╨╜╨░╨╡╨╝ ╨┐╨░╤А╤Б╨╕╨╜╨│...")
                return self.parse_kml_content(content)
            except Exception as e:
                logger.error(f"╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╨╖╨░╨│╤А╤Г╨╖╨║╨╡ KML ╨┐╨╛ ╤Б╤Б╤Л╨╗╨║╨╡ {url}: {e}")
                raise

    def parse_kml_content(self, kml_text: str) -> List[Dict[str, Any]]:
        """
        ╨Я╨░╤А╤Б╨╕╤В XML/KML ╤Б╨╛╨┤╨╡╤А╨╢╨╕╨╝╨╛╨╡ ╨▓ ╤Б╨┐╨╕╤Б╨╛╨║ ╨┐╨╛╨╗╨╕╨│╨╛╨╜╨╛╨▓.
        ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╤В ╨▓╤Б╨┐╨╛╨╝╨╛╨│╨░╤В╨╡╨╗╤М╨╜╤Г╤О ╤Д╤Г╨╜╨║╤Ж╨╕╤О ╨╕╨╖ geo_utils.
        """
        from app.utils.geo_utils import parse_kml
        return parse_kml(kml_text)

    @staticmethod
    def _safe_float(value) -> float:
        """╨С╨╡╨╖╨╛╨┐╨░╤Б╨╜╨╛╨╡ ╨┐╤А╨╡╨╛╨▒╤А╨░╨╖╨╛╨▓╨░╨╜╨╕╨╡ ╨╖╨╜╨░╤З╨╡╨╜╨╕╤П ╨║ float"""
        try:
            return float(value) if value is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _safe_int(value) -> int:
        """╨С╨╡╨╖╨╛╨┐╨░╤Б╨╜╨╛╨╡ ╨┐╤А╨╡╨╛╨▒╤А╨░╨╖╨╛╨▓╨░╨╜╨╕╨╡ ╨╖╨╜╨░╤З╨╡╨╜╨╕╤П ╨║ int"""
        try:
            return int(value) if value is not None else 0
        except (TypeError, ValueError):
            return 0


# ╨У╨╗╨╛╨▒╨░╨╗╤М╨╜╤Л╨╣ ╤Н╨║╨╖╨╡╨╝╨┐╨╗╤П╤А ╤Б╨╡╤А╨▓╨╕╤Б╨░
iiko_service = IikoService()
