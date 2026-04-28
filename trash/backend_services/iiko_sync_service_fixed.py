"""
╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨┤╨░╨╜╨╜╤Л╤Е ╤Б iiko Cloud
"""
import logging
import asyncio
import json
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
import zoneinfo
from decimal import Decimal
from sqlmodel import Session, select
from sqlalchemy import func
from sqlalchemy.orm.attributes import flag_modified as sql_flag_modified

from app.models.category import Category
from app.models.product import Product, ProductSize, ProductModifierGroup, ProductModifier
from app.models.sync_log import SyncLog
# Order, OrderItem, OrderStatus ╨╕╨╝╨┐╨╛╤А╤В╨╕╤А╤Г╤О╤В╤Б╤П ╨╗╨╛╨║╨░╨╗╤М╨╜╨╛ ╨┤╨╗╤П ╨┐╤А╨╡╨┤╨╛╤В╨▓╤А╨░╤Й╨╡╨╜╨╕╤П ╤Ж╨╕╨║╨╗╨╕╤З╨╡╤Б╨║╨╕╤Е ╨╖╨░╨▓╨╕╤Б╨╕╨╝╨╛╤Б╤В╨╡╨╣
from app.models.employee import Employee, Shift, Schedule, CourierOrder
from app.models.company import Branch, Company, DeliveryZone, CustomPolygon
from app.models.customer import Customer
from app.models.iiko_settings import IikoSettings
from app.models.olap_revenue import OlapRevenueRecord
from app.core.config import settings
from app.services.iiko_service import iiko_service
from app.core.logging_utils import log_audit

logger = logging.getLogger(__name__)

class IikoSyncService:
    def __init__(self):
        self._terminal_groups_cache = {}
        self._last_rev_sync = {} # {org_id: last_time}

    @staticmethod
    def clean_str(val):
        if val is None:
            return ""
        
        # ╨Х╤Б╨╗╨╕ ╤Н╤В╨╛ ╨╜╨╡ ╤Б╤В╤А╨╛╨║╨░, ╨┐╤А╨╡╨╛╨▒╤А╨░╨╖╤Г╨╡╨╝ ╨▓ ╤Б╤В╤А╨╛╨║╤Г
        s = str(val).strip()
        
        # ╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╨╜╨░ ╤Б╨╗╤Г╨╢╨╡╨▒╨╜╤Л╨╡ ╨╖╨╜╨░╤З╨╡╨╜╨╕╤П, ╨║╨╛╤В╨╛╤А╤Л╨╡ iiko ╨╝╨╛╨╢╨╡╤В ╨┐╤А╨╕╤Б╤Л╨╗╨░╤В╤М ╨║╨░╨║ ╤Б╤В╤А╨╛╨║╨╕
        if s.lower() in ("none", "null", "", "-", "--", ".", "undefined", "nan"):
            return ""
            
        # ╨Ч╨░╤Й╨╕╤В╨░ ╨╛╤В mojibake: ╨╡╤Б╨╗╨╕ ╤Б╤В╤А╨╛╨║╨░ ╤Б╨╗╤Г╤З╨░╨╣╨╜╨╛ ╨┤╨╡╨║╨╛╨┤╨╕╤А╨╛╨▓╨░╨╜╨░ ╨║╨░╨║ ISO-8859-1 ╨▓╨╝╨╡╤Б╤В╨╛ UTF-8
        # (╨Ю╨▒╤Л╤З╨╜╨╛ ╤Н╤В╨╛ ╨▓╤Л╨│╨╗╤П╨┤╨╕╤В ╨║╨░╨║ ╨а╨Р╨а╨Р╨а╨Р...)
        try:
            # ╨Х╤Б╨╗╨╕ ╨▓ ╤Б╤В╤А╨╛╨║╨╡ ╨╝╨╜╨╛╨│╨╛ ╤Б╨╕╨╝╨▓╨╛╨╗╨╛╨▓ ╨╕╨╖ ╤А╨░╤Б╤И╨╕╤А╨╡╨╜╨╜╨╛╨╣ ╨╗╨░╤В╨╕╨╜╨╕╤Ж╤Л, ╨╜╨╛ ╨╜╨╡╤В ╨║╨╕╤А╨╕╨╗╨╗╨╕╤Ж╤Л
            # ╤Н╤В╨╛ ╨╝╨╛╨╢╨╡╤В ╨▒╤Л╤В╤М ╨╜╨╡╨▓╨╡╤А╨╜╨╛ ╨┤╨╡╨║╨╛╨┤╨╕╤А╨╛╨▓╨░╨╜╨╜╤Л╨╣ UTF-8
            if any(ord(c) > 127 and ord(c) < 255 for c in s) and not any(1040 <= ord(c) <= 1103 for c in s):
                test_s = s.encode('latin-1').decode('utf-8')
                if any(1040 <= ord(c) <= 1103 for c in test_s):
                    return test_s
        except Exception:
            pass
            
        return s

    def format_address(self, address_data: Any, city: Optional[str] = None, fmt: str = "components") -> str:
        """
        ╨д╨╛╤А╨╝╨░╤В╨╕╤А╤Г╨╡╤В ╨░╨┤╤А╨╡╤Б iiko. 
        ╨Я╤А╨╕╨╛╤А╨╕╤В╨╡╤В: line1 (╨╡╤Б╨╗╨╕ fmt='line1'), ╨╕╨╜╨░╤З╨╡ ╤Б╨▒╨╛╤А╨║╨░ ╨┐╨╛ ╨║╨╛╨╝╨┐╨╛╨╜╨╡╨╜╤В╨░╨╝.
        """
        if not address_data:
            return ""

        if not isinstance(address_data, dict):
            return str(address_data)

        # 1. ╨Ш╨╖╨▓╨╗╨╡╨║╨░╨╡╨╝ ╨║╨╛╨╝╨┐╨╛╨╜╨╡╨╜╤В╤Л ╤Б ╨╛╤З╨╕╤Б╤В╨║╨╛╨╣
        line1 = self.clean_str(address_data.get('line1'))
        city_val = self.clean_str(address_data.get('city') or city)
        street_val = address_data.get('street')
        street = street_val.get('name') if isinstance(street_val, dict) else self.clean_str(street_val)
        
        house = self.clean_str(address_data.get('house'))
        flat = self.clean_str(address_data.get('flat'))
        entrance = self.clean_str(address_data.get('entrance'))
        floor = self.clean_str(address_data.get('floor'))
        door_phone = self.clean_str(address_data.get('doorphone'))
        building = self.clean_str(address_data.get('building'))

        # 2. ╨Ы╨╛╨│╨╕╨║╨░ ╨┤╨╗╤П fmt="line1" (╨║╨░╨║ ╨▓ ╨╜╨░╤Б╤В╤А╨╛╨╣╨║╨░╤Е iiko)
        if fmt == "line1" and line1:
            addr = self.clean_str(line1)
            # ╨Ш╨╜╤В╨╡╨╗╨╗╨╡╨║╤В╤Г╨░╨╗╤М╨╜╨╛╨╡ ╨┤╨╛╨▒╨░╨▓╨╗╨╡╨╜╨╕╨╡ ╨╛╤В╤Б╤Г╤В╤Б╤В╨▓╤Г╤О╤Й╨╕╤Е ╤Н╨╗╨╡╨╝╨╡╨╜╤В╨╛╨▓
            extras = []
            if flat and str(flat) not in addr:
                extras.append(f"╨║╨▓. {flat}")
            if entrance and str(entrance) not in addr:
                extras.append(f"╨┐╨╛╨┤. {entrance}")
            if floor and str(floor) not in addr:
                extras.append(f"╤Н╤В. {floor}")
            if door_phone and str(door_phone) not in addr:
                extras.append(f"╨║╨╛╨┤ {door_phone}")
                
            if extras:
                addr = f"{addr}, {', '.join(extras)}"
            return addr

        # 3. ╨Ъ╨╗╨░╤Б╤Б╨╕╤З╨╡╤Б╨║╨░╤П ╤Б╨▒╨╛╤А╨║╨░ (╨│╨╛╤А╨╛╨┤, ╤Г╨╗╨╕╤Ж╨░, ╨┤╨╛╨╝, ╨║╨▓╨░╤А╤В╨╕╤А╨░...)
        if not street and not house and line1:
            return line1

        parts = []
        if city_val: parts.append(self.clean_str(city_val))
        if street:
            s = self.clean_str(street)
            if not any(p in s.lower() for p in ["╤Г╨╗╨╕╤Ж╨░", "╤Г╨╗.", "╨┐╤А.", "╨┐╨╡╤А.", "╨▒╤Г╨╗."]):
                s = f"╤Г╨╗. {s}"
            parts.append(s)
            
        if house: parts.append(f"╨┤. {house}")
        if building: parts.append(f"╨║╨╛╤А╨┐. {building}")
        if flat: parts.append(f"╨║╨▓. {flat}")
        if entrance: parts.append(f"╨┐╨╛╨┤. {entrance}")
        if floor: parts.append(f"╤Н╤В. {floor}")

        return ", ".join(parts) if parts else "╨Р╨┤╤А╨╡╤Б ╨╜╨╡ ╤Г╨║╨░╨╖╨░╨╜"

    def _get_tz(self, session: Session):
        """╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤З╨░╤Б╨╛╨▓╨╛╨│╨╛ ╨┐╨╛╤П╤Б╨░ ╨╕╨╖ ╨╜╨░╤Б╤В╤А╨╛╨╡╨║"""
        from app.core.datetime_utils import get_tz
        return get_tz(session)

    async def sync_menu(self, session: Session) -> Dict[str, Any]:
        """╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨║╨░╤В╨░╨╗╨╛╨│╨░ ╨╝╨╡╨╜╤О (╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╕ + ╤В╨╛╨▓╨░╤А╤Л)"""
        log = SyncLog(sync_type="menu", status="running")
        session.add(log)
        session.commit()
        
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login if settings_db else None
        org_id = settings_db.organization_id if settings_db else None
        ext_menu_id = settings_db.external_menu_id if settings_db else None
        
        try:
            price_cat_id = settings_db.price_category_id if settings_db else None
            if ext_menu_id:
                logger.info(f"Syncing from External Menu ID: {ext_menu_id} (Price Category: {price_cat_id})")
                menu_data = await iiko_service.get_external_menu_by_id(
                    ext_menu_id, 
                    price_category_id=price_cat_id,
                    api_login=api_login, 
                    organization_id=org_id
                )
                res = await self._sync_from_external_menu(session, menu_data, log)
            else:
                logger.info("Syncing from Nomenclature (Classic API)")
                nomenclature = await iiko_service.get_nomenclature(api_login=api_login, organization_id=org_id)
                res = await self._sync_from_nomenclature(session, nomenclature, log)
            
            # ╨У╨░╤А╨░╨╜╤В╨╕╤А╤Г╨╡╨╝ ╨╜╨░╨╗╨╕╤З╨╕╨╡ success ╨╕ ╨┐╨╛╨╗╨╡╨╣ ╨┤╨╗╤П ╤Б╤Е╨╡╨╝╤Л
            response = {
                "success": True,
                "categories_synced": res.get("categories", 0),
                "products_synced": res.get("products", 0),
                "message": f"╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨╖╨░╨▓╨╡╤А╤И╨╡╨╜╨░ ╤Г╤Б╨┐╨╡╤И╨╜╨╛: {res.get('categories', 0)} ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╣, {res.get('products', 0)} ╤В╨╛╨▓╨░╤А╨╛╨▓"
            }
            
            log.status = "success"
            log.details = response["message"]
            session.add(log)
            session.commit()
            
            # ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ ╨╖╨░╨┐╨╕╤Б╤М ╨▓ ╨░╤Г╨┤╨╕╤В
            log_audit(action="manual_sync", resource_type="menu", message=response["message"])
            
            return response
        except Exception as e:
            logger.error(f"Menu sync failed: {e}", exc_info=True)
            log.status = "error"
            log.details = str(e)
            session.add(log)
            session.commit()
            
            # ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ ╨╖╨░╨┐╨╕╤Б╤М ╨▓ ╨░╤Г╨┤╨╕╤В ╨╛╨▒ ╨╛╤И╨╕╨▒╨║╨╡
            log_audit(action="manual_sync_failed", resource_type="menu", message=str(e))
            
            return {
                "success": False,
                "error": str(e),
                "message": f"╨Ю╤И╨╕╨▒╨║╨░ ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╨╕: {str(e)}"
            }

    async def sync_categories_only(self, session: Session) -> Dict[str, Any]:
        """╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╤В╨╛╨╗╤М╨║╨╛ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╣ ╨╕╨╖ iiko (╨▓╤Л╨╖╤Л╨▓╨░╨╡╤В ╨┐╨╛╨╗╨╜╤Г╤О ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤О ╨╝╨╡╨╜╤О)"""
        res = await self.sync_menu(session)
        return {
            "success": res.get("success", False),
            "categories_synced": res.get("categories_synced", 0),
            "message": f"╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨╕╤А╨╛╨▓╨░╨╜╨╛ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╣: {res.get('categories_synced', 0)}"
        }

    async def _sync_from_external_menu(self, session: Session, menu_data: Dict[str, Any], log: SyncLog) -> Dict[str, Any]:
        """╨Ы╨╛╨│╨╕╨║╨░ ╨╛╨▒╤А╨░╨▒╨╛╤В╨║╨╕ ╨▓╨╜╨╡╤И╨╜╨╡╨│╨╛ ╨╝╨╡╨╜╤О iiko (API v2 /menu/by_id)"""
        if not menu_data:
            return {"categories": 0, "products": 0}
        
        categories_synced = 0
        products_synced = 0

        # 1. ╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╣
        cats_list = menu_data.get("itemCategories") or menu_data.get("groups") or []
        for cat_data in cats_list:
            cat_id = cat_data.get("id")
            if not cat_id: continue
            
            cat = session.exec(select(Category).where(Category.iiko_id == cat_id)).first()
            if cat:
                cat.name = cat_data["name"]
                cat.updated_at = datetime.now(timezone.utc)
            else:
                cat = Category(
                    iiko_id=cat_id,
                    name=cat_data["name"],
                    is_active=True
                )
                session.add(cat)
            categories_synced += 1
        session.commit()

        # 2. ╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╤В╨╛╨▓╨░╤А╨╛╨▓
        # ╨Т v2 ╤В╨╛╨▓╨░╤А╤Л ╤Б╨│╤А╤Г╨┐╨┐╨╕╤А╨╛╨▓╨░╨╜╤Л ╨┐╨╛ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╤П╨╝ ╨▓ itemCategories
        for cat_data in cats_list:
            iiko_cat_id = cat_data.get("id")
            local_cat = session.exec(select(Category).where(Category.iiko_id == iiko_cat_id)).first()
            category_id = local_cat.id if local_cat else None
            
            items_list = cat_data.get("items") or cat_data.get("products") or []
            for item_data in items_list:
                item_id = item_data.get("itemId") or item_data.get("id")
                if not item_id: continue
                
                prod = session.exec(select(Product).where(Product.iiko_id == item_id)).first()
                
                # ╨Ш╨╖╨▓╨╗╨╡╨║╨░╨╡╨╝ ╨┤╨░╨╜╨╜╤Л╨╡ ╨╕╨╖ ╨┐╨╡╤А╨▓╨╛╨│╨╛ ╤А╨░╨╖╨╝╨╡╤А╨░ ╨┤╨╗╤П ╨▒╨░╨╖╨╛╨▓╤Л╤Е ╨┐╨╛╨╗╨╡╨╣ ╤В╨╛╨▓╨░╤А╨░
                sizes = item_data.get("itemSizes", [])
                price = 0
                nutritions = {}
                weight = None
                
                if sizes:
                    s0 = sizes[0]
                    prices = s0.get("prices", [])
                    if prices: price = prices[0].get("price", 0)
                    nutritions = s0.get("nutritionPerHundredGrams") or s0.get("nutritions") or {}
                    weight = s0.get("portionWeightGrams")
                elif "price" in item_data: 
                    price = item_data["price"]

                updated_data = {
                    "name": item_data["name"],
                    "description": item_data.get("description") or "",
                    "price": float(price or 0),
                    "article": item_data.get("sku") or "", 
                    "category_id": category_id,
                    "is_available": not item_data.get("isHidden", False),
                    "weight_grams": int(weight) if weight else None,
                    "calories": int(nutritions.get("energy") or 0) or None,
                    "proteins": float(nutritions.get("proteins") or 0) or None,
                    "fats": float(nutritions.get("fats") or 0) or None,
                    "carbohydrates": float(nutritions.get("carbs") or 0) or None,
                    "updated_at": datetime.now(timezone.utc)
                }

                if prod:
                    for key, val in updated_data.items(): setattr(prod, key, val)
                else:
                    prod = Product(iiko_id=item_id, **updated_data)
                    session.add(prod)
                
                session.flush() # ╨Я╨╛╨╗╤Г╤З╨░╨╡╨╝ ID

                # --- ╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╤А╨░╨╖╨╝╨╡╤А╨╛╨▓ ---
                for existing_size in session.exec(select(ProductSize).where(ProductSize.product_id == prod.id)).all():
                    session.delete(existing_size)
                
                if sizes:
                    for s_data in sizes:
                        s_price = 0
                        if s_data.get("prices"): s_price = s_data["prices"][0].get("price", 0)
                        
                        session.add(ProductSize(
                            product_id=prod.id,
                            iiko_id=s_data.get("sizeId") or item_id,
                            name=s_data.get("sizeName") or "╨б╤В╨░╨╜╨┤╨░╤А╤В",
                            price=float(s_price or 0),
                            is_default=s_data.get("isDefault", False)
                        ))
                else:
                    session.add(ProductSize(
                        product_id=prod.id,
                        iiko_id=item_id,
                        name="╨б╤В╨░╨╜╨┤╨░╤А╤В",
                        price=float(price or 0),
                        is_default=True
                    ))

                # --- ╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨╝╨╛╨┤╨╕╤Д╨╕╨║╨░╤В╨╛╤А╨╛╨▓ ---
                # ╨С╨╡╤А╨╡╨╝ ╨╝╨╛╨┤╨╕╤Д╨╕╨║╨░╤В╨╛╤А╤Л ╨╕╨╖ ╨┤╨╡╤Д╨╛╨╗╤В╨╜╨╛╨│╨╛ ╤А╨░╨╖╨╝╨╡╤А╨░ (╨╕╨╗╨╕ ╨┐╨╡╤А╨▓╨╛╨│╨╛ ╨┤╨╛╤Б╤В╤Г╨┐╨╜╨╛╨│╨╛)
                target_size = next((s for s in sizes if s.get("isDefault")), sizes[0] if sizes else None)
                if target_size:
                    # ╨Ю╤З╨╕╤Й╨░╨╡╨╝ ╤Б╤В╨░╤А╤Л╨╡ ╨│╤А╤Г╨┐╨┐╤Л ╨╝╨╛╨┤╨╕╤Д╨╕╨║╨░╤В╨╛╤А╨╛╨▓
                    for existing_group in session.exec(select(ProductModifierGroup).where(ProductModifierGroup.product_id == prod.id)).all():
                        session.delete(existing_group)
                    
                    mod_groups = target_size.get("itemModifierGroups", [])
                    for mg_data in mod_groups:
                        mg_id = mg_data.get("itemGroupId") or mg_data.get("modifierGroupId") or f"mg_{mg_data['name']}"
                        
                        new_group = ProductModifierGroup(
                            product_id=prod.id,
                            iiko_id=mg_id,
                            name=mg_data["name"],
                            min_amount=mg_data.get("minAmount", 0),
                            max_amount=mg_data.get("maxAmount", 1),
                            is_required=mg_data.get("minAmount", 0) > 0
                        )
                        session.add(new_group)
                        session.flush()
                        
                        for m_item in mg_data.get("items", []):
                            m_price = 0
                            if m_item.get("prices"): m_price = m_item["prices"][0].get("price", 0)
                            
                            session.add(ProductModifier(
                                group_id=new_group.id,
                                iiko_id=m_item["itemId"],
                                name=m_item["name"],
                                price=float(m_price),
                                min_amount=m_item.get("minAmount", 0),
                                max_amount=m_item.get("maxAmount", 1),
                                default_amount=m_item.get("defaultAmount", 0)
                            ))

                products_synced += 1
        
        session.commit()
        return {"categories": categories_synced, "products": products_synced}

    async def _sync_from_nomenclature(self, session: Session, nomenclature: Dict[str, Any], log: SyncLog) -> Dict[str, Any]:
        """╨Ю╨▒╤А╨░╨▒╨╛╤В╨║╨░ ╨║╨╗╨░╤Б╤Б╨╕╤З╨╡╤Б╨║╨╛╨╣ ╨╜╨╛╨╝╨╡╨╜╨║╨╗╨░╤В╤Г╤А╤Л iiko (groups + products + sizes)"""
        if not nomenclature:
            return {"categories": 0, "products": 0}

        categories_synced = 0
        products_synced = 0

        # 1. ╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╣ (groups)
        if "groups" in nomenclature:
            for g in nomenclature["groups"]:
                if g.get("isDeleted"): continue
                
                cat = session.exec(select(Category).where(Category.iiko_id == g["id"])).first()
                if cat:
                    cat.name = g["name"]
                    cat.updated_at = datetime.now(timezone.utc)
                else:
                    cat = Category(
                        iiko_id=g["id"],
                        name=g["name"],
                        is_active=True
                    )
                    session.add(cat)
                categories_synced += 1
            session.commit()

        # 2. ╨Ь╨░╨┐╨┐╨╕╨╜╨│ ╤А╨░╨╖╨╝╨╡╤А╨╛╨▓ ╨┤╨╗╤П ╤В╨╛╨▓╨░╤А╨╛╨▓
        size_map = {s["id"]: s["name"] for s in nomenclature.get("sizes", [])}

        # 3. ╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╤В╨╛╨▓╨░╤А╨╛╨▓ (products)
        if "products" in nomenclature:
            for p in nomenclature["products"]:
                if p.get("type") == "Service": continue # ╨Я╤А╨╛╨┐╤Г╤Б╨║╨░╨╡╨╝ ╤Г╤Б╨╗╤Г╨│╨╕
                
                prod = session.exec(select(Product).where(Product.iiko_id == p["id"])).first()
                
                # ╨Я╨╛╨╕╤Б╨║ ╨╗╨╛╨║╨░╨╗╤М╨╜╨╛╨╣ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╕
                category_id = None
                if p.get("parentGroup"):
                    local_cat = session.exec(select(Category).where(Category.iiko_id == p["parentGroup"])).first()
                    if local_cat: category_id = local_cat.id
                
                # ╨Ю╨┐╤А╨╡╨┤╨╡╨╗╨╡╨╜╨╕╨╡ ╨▒╨░╨╖╨╛╨▓╨╛╨╣ ╤Ж╨╡╨╜╤Л (╨┐╨╡╤А╨▓╤Л╨╣ ╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Л╨╣ ╤А╨░╨╖╨╝╨╡╤А)
                price = 0
                if p.get("sizePrices"):
                    price = p["sizePrices"][0].get("price", {}).get("currentPrice", 0)

                updated_data = {
                    "name": p["name"],
                    "description": p.get("description") or "",
                    "price": float(price),
                    "article": p.get("code") or "",
                    "category_id": category_id,
                    "is_available": not p.get("isDeleted", False),
                    "updated_at": datetime.now(timezone.utc)
                }

                if prod:
                    for key, val in updated_data.items(): setattr(prod, key, val)
                else:
                    prod = Product(iiko_id=p["id"], **updated_data)
                    session.add(prod)
                
                session.flush() # ╨Я╨╛╨╗╤Г╤З╨░╨╡╨╝ ID ╤В╨╛╨▓╨░╤А╨░
                
                # --- ╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╤А╨░╨╖╨╝╨╡╤А╨╛╨▓ ---
                for existing_size in session.exec(select(ProductSize).where(ProductSize.product_id == prod.id)).all():
                    session.delete(existing_size)
                
                if p.get("sizePrices"):
                    for sp in p["sizePrices"]:
                        s_id = sp.get("sizeId")
                        s_name = size_map.get(s_id, "╨б╤В╨░╨╜╨┤╨░╤А╤В")
                        session.add(ProductSize(
                            product_id=prod.id,
                            iiko_id=s_id or "default",
                            name=s_name,
                            price=float(sp.get("price", {}).get("currentPrice", 0)),
                            is_default=(len(p["sizePrices"]) == 1 or sp.get("isDefault", False))
                        ))

                products_synced += 1
            
            session.commit()

        return {"categories": categories_synced, "products": products_synced}

    async def process_iiko_order(self, session: Session, iiko_order_data: Dict[str, Any], organization_id: str, iiko_card_data: Optional[Dict[str, Any]] = None):
        from app.models.order import Order, OrderStatus # ╨Ы╨╛╨║╨░╨╗╤М╨╜╤Л╨╣ ╨╕╨╝╨┐╨╛╤А╤В ╨┤╨╗╤П ╨┐╤А╨╡╨┤╨╛╤В╨▓╤А╨░╤Й╨╡╨╜╨╕╤П UnboundLocalError ╨╕ ╤Ж╨╕╨║╨╗╨╕╤З╨╡╤Б╨║╨╕╤Е ╨╖╨░╨▓╨╕╤Б╨╕╨╝╨╛╤Б╤В╨╡╨╣
        """╨Ш╨╜╤В╨╡╨│╤А╨╕╤А╨╛╨▓╨░╨╜╨╜╤Л╨╣ ╨╝╨╡╤В╨╛╨┤ ╨╛╨▒╤А╨░╨▒╨╛╤В╨║╨╕ ╨╖╨░╨║╨░╨╖╨░: ╨║╨╛╨╜╤Б╨╛╨╗╨╕╨┤╨╕╤А╨╛╨▓╨░╨╜╨╜╨░╤П ╨╕ ╨╛╤З╨╕╤Й╨╡╨╜╨╜╨░╤П ╨▓╨╡╤А╤Б╨╕╤П"""
        if not iiko_order_data:
            logger.warning("Received empty order data from iiko")
            return
            
        try:
            # 1. ╨С╨░╨╖╨╛╨▓╤Л╨╡ ╨┤╨░╨╜╨╜╤Л╨╡ ╨╖╨░╨║╨░╨╖╨░
            order_id_iiko = iiko_order_data.get("id")
            o_data = iiko_order_data.get("order")
            if not o_data:
                o_data = iiko_order_data
            
            if not order_id_iiko:
                order_id_iiko = o_data.get("id")

            if not order_id_iiko:
                logger.warning(f"Order data missing ID. Keys available: {list(o_data.keys())}. Full data sample: {str(o_data)[:500]}")
                return
            
            # ╨Ы╨╛╨│╨╕╤А╤Г╨╡╨╝ ╨╜╨░╤З╨░╨╗╨╛ ╨╛╨▒╤А╨░╨▒╨╛╤В╨║╨╕ ╨┤╨╗╤П ╨┤╨╕╨░╨│╨╜╨╛╤Б╤В╨╕╨║╨╕
            ext_num = o_data.get("number") or o_data.get("externalNumber")
            logger.info(f"==> Processing Iiko Order: ID={order_id_iiko}, Num={ext_num}, Status={o_data.get('status')}")
            
            settings_db = session.exec(select(IikoSettings)).first()
            city_from_settings = settings_db.city_name if settings_db else "╨в╤О╨╝╨╡╨╜╤М"

            # ╨Ю╤З╨╕╤Б╤В╨║╨░ ╤Б╤В╤А╨╛╨║ ╨╛╤В ╨┐╨╗╨╡╨╣╤Б╤Е╨╛╨╗╨┤╨╡╤А╨╛╨▓
            def clean(v):
                if v is None: return None
                s = str(v).strip()
                # ╨г╨┤╨░╨╗╤П╨╡╨╝ ╨░╤А╤В╨╡╤Д╨░╨║╤В╤Л "None", "null" ╨╕ ╨┐╤А╨╛╤З╨╕╨╡ ╨┐╨╗╨╡╨╣╤Б╤Е╨╛╨╗╨┤╨╡╤А╤Л
                if s.lower() in ["none", "null", "", "-", "--", "---", "----", "----------", ".", "undefined"]: 
                    return None
                return s

            # 2. ╨б╤В╨░╤В╤Г╤Б ╨╕ ╨▓╨╜╨╡╤И╨╜╨╕╨╡ ╨╜╨╛╨╝╨╡╤А╨░
            raw_status = clean(o_data.get("status") or iiko_order_data.get("creationStatus"))
            raw_status_lower = raw_status.lower() if raw_status else ""
            external_number = clean(o_data.get("number") or o_data.get("externalNumber")) or None

            # 3. ╨в╨░╨╣╨╝╨╖╨╛╨╜╨░ ╨╕ ╨▓╤А╨╡╨╝╤П
            from app.core.datetime_utils import get_tz_name
            tz_name = get_tz_name(session)
            try:
                import zoneinfo
                tz = zoneinfo.ZoneInfo(tz_name)
            except Exception:
                import zoneinfo
                tz = zoneinfo.ZoneInfo("Asia/Yekaterinburg")
            
            current_time_tz = datetime.now(tz)
            
            # ╨Я╨╛╨╕╤Б╨║ ╨┤╨░╤В╤Л ╤Б╨╛╨╖╨┤╨░╨╜╨╕╤П ╨▓ ╤А╨░╨╖╨╜╤Л╤Е ╨╝╨╡╤Б╤В╨░╤Е (iiko API ╨╝╨╛╨╢╨╡╤В ╨╝╨╡╨╜╤П╤В╤М ╤Б╤В╤А╤Г╨║╤В╤Г╤А╤Г)
            iiko_creation_time_raw = (
                (o_data.get("creationInfo") or {}).get("creationDate") or 
                o_data.get("creationDate") or
                o_data.get("whenCreated")
            )
            iiko_creation_time = None
            if iiko_creation_time_raw:
                try:
                    # ╨Я╤А╨╕╨╜╨╕╨╝╨░╨╡╨╝ ╨▓╤А╨╡╨╝╤П ╨║╨░╨║ UTC 0, ╨╡╤Б╨╗╨╕ ╨╡╤Б╤В╤М ╨┐╨╛╨╝╨╡╤В╨║╨░ Z ╨╕╨╗╨╕ ╤Б╨╝╨╡╤Й╨╡╨╜╨╕╨╡.
                    # ╨н╤В╨╛ ╨╕╤Б╨┐╤А╨░╨▓╨╕╤В ╨┐╤А╨╛╨▒╨╗╨╡╨╝╤Г 5-╤З╨░╤Б╨╛╨▓╨╛╨│╨╛ ╤Б╨╝╨╡╤Й╨╡╨╜╨╕╤П ╨▓ ╨░╨┤╨╝╨╕╨╜╨║╨╡.
                    if 'Z' in iiko_creation_time_raw or '+' in iiko_creation_time_raw or '-' in iiko_creation_time_raw[10:]:
                        # ISO ╤Д╨╛╤А╨╝╨░╤В ╤Б Z ╨╕╨╗╨╕ ╤Б╨╝╨╡╤Й╨╡╨╜╨╕╨╡╨╝ ╨┐╨░╤А╤Б╨╕╤В╤Б╤П ╨║╨░╨║ aware datetime
                        dt = datetime.fromisoformat(iiko_creation_time_raw.replace('Z', '+00:00'))
                        iiko_creation_time = dt.astimezone(timezone.utc).replace(tzinfo=None)
                    else:
                        # ╨Х╤Б╨╗╨╕ ╨▓╤А╨╡╨╝╤П ╨▒╨╡╨╖ ╨┐╨╛╤П╤Б╨░ (naive), ╤Б╤З╨╕╤В╨░╨╡╨╝ ╨╡╨│╨╛ ╨╗╨╛╨║╨░╨╗╤М╨╜╤Л╨╝ ╨┤╨╗╤П ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П
                        dt = datetime.fromisoformat(iiko_creation_time_raw)
                        iiko_creation_time = dt.replace(tzinfo=tz).astimezone(timezone.utc).replace(tzinfo=None)
                    
                    logger.info(f"Parsed iiko time (naive UTC): raw={iiko_creation_time_raw}, result={iiko_creation_time}")
                except Exception as e:
                    logger.error(f"Error parsing iiko creation time {iiko_creation_time_raw}: {e}")

            # 4. ╨Ъ╨╗╨╕╨╡╨╜╤В
            c_data = o_data.get("customer") or {}
            c_first = clean(c_data.get("name"))
            c_last = clean(c_data.get("surname"))
            full_customer_name = f"{c_first or ''} {c_last or ''}".strip() or "╨У╨╛╤Б╤В╤М"
            phone = clean(o_data.get("phone") or c_data.get("phone"))

            # 5. ╨Р╨┤╤А╨╡╤Б
            has_new_address = False
            raw_addr = o_data.get("address") or {}
            dp = o_data.get("deliveryPoint") or {}
            raw_addr_dp = dp.get("address") or {}

            city = clean(raw_addr.get("city"))
            if not city and isinstance(raw_addr.get("city"), dict):
                city = clean(raw_addr.get("city").get("name"))
            if not city:
                city = clean(raw_addr_dp.get("city"))
                if not city and isinstance(raw_addr_dp.get("city"), dict):
                    city = clean(raw_addr_dp.get("city").get("name"))
            
            city = city or city_from_settings or "╨в╤О╨╝╨╡╨╜╤М"

            # ╨н╨║╤Б╤В╤А╨░╨║╤Ж╨╕╤П ╨║╨╛╨╝╨┐╨╛╨╜╨╡╨╜╤В╨╛╨▓ ╨┤╨╗╤П ╨С╨Ф (╤Б╨╗╨╕╨▓╨░╨╡╨╝ ╨┤╨░╨╜╨╜╤Л╨╡ ╨╕╨╖ address ╨╕ deliveryPoint)
            house = clean(raw_addr.get("house")) or clean(raw_addr_dp.get("house"))
            if house and all(char in "-. " for char in house): house = None
            
            flat = clean(raw_addr.get("flat")) or clean(raw_addr_dp.get("flat"))
            if flat and all(char in "-. " for char in flat): flat = None
            
            entrance = clean(raw_addr.get("entrance")) or clean(raw_addr_dp.get("entrance"))
            floor = clean(raw_addr.get("floor")) or clean(raw_addr_dp.get("floor"))
            doorphone = clean(raw_addr.get("doorphone")) or clean(raw_addr_dp.get("doorphone"))
            
            s_obj = raw_addr.get("street")
            street_name = s_obj.get("name") if isinstance(s_obj, dict) else (clean(s_obj) or None)
            if not street_name:
                s_obj_dp = raw_addr_dp.get("street")
                street_name = s_obj_dp.get("name") if isinstance(s_obj_dp, dict) else (clean(s_obj_dp) or None)
            
            if street_name and all(char in "-. " for char in street_name): street_name = None

            addr_fmt = (settings_db.address_format or "components") if settings_db else "components"
            
            # ╨б╨╜╨░╤З╨░╨╗╨░ ╨┐╤А╨╛╨▒╤Г╨╡╨╝ ╤Б╨╛╨▒╤А╨░╤В╤М ╨░╨┤╤А╨╡╤Б ╨╕╨╖ ╨╜╨░╨╕╨▒╨╛╨╗╨╡╨╡ ╨┐╨╛╨╗╨╜╨╛╨│╨╛ ╨╛╨▒╤К╨╡╨║╤В╨░ (╨╛╨▒╤Л╤З╨╜╨╛ ╤Н╤В╨╛ raw_addr, ╨╜╨╛ ╨╡╤Б╨╗╨╕ ╤В╨░╨╝ ╨┐╤Г╤Б╤В╨╛ - raw_addr_dp)
            # ╨Ф╨╗╤П ╤Н╤В╨╛╨│╨╛ ╤Б╨╛╨╖╨┤╨░╨╡╨╝ ╨▓╤А╨╡╨╝╨╡╨╜╨╜╤Л╨╣ ╨╛╨▒╤К╨╡╨║╤В ╤Б╨╛ ╨▓╤Б╨╡╨╝╨╕ ╨┐╨╛╨╗╤П╨╝╨╕
            merged_addr_obj = {
                "city": city,
                "street": {"name": street_name} if street_name else None,
                "house": house,
                "flat": flat,
                "entrance": entrance,
                "floor": floor,
                "doorphone": doorphone,
                "line1": clean(raw_addr.get("line1")) or clean(raw_addr_dp.get("line1"))
            }
            
            try:
                delivery_address = self.format_address(merged_addr_obj, city=city, fmt=addr_fmt)
            except TypeError as e:
                logger.error(f"Address formatting failed: {e}. Falling back to default.")
                delivery_address = self.format_address(merged_addr_obj, fmt=addr_fmt)
            
            # ╨Х╤Б╨╗╨╕ ╨▓ ╨╕╤В╨╛╨│╨╡ ╨░╨┤╤А╨╡╤Б ╨┐╤Г╤Б╤В╨╛╨╣ ╨╕╨╗╨╕ "╨б╨░╨╝╨╛╨▓╤Л╨▓╨╛╨╖", ╨┐╤А╨╛╨▓╨╡╤А╤П╨╡╨╝ ╨┤╤А╤Г╨│╨╕╨╡ ╨┐╨╛╨╗╤П
            is_only_city = not delivery_address or delivery_address.strip() in [city, f"╨│. {city}", "╨│.╨в╤О╨╝╨╡╨╜╤М", "╨в╤О╨╝╨╡╨╜╤М"]
            
            if is_only_city:
                # ╨Х╤Б╨╗╨╕ ╨▓╤Б╤П ╨╡╤Й╨╡ ╨┐╤Г╤Б╤В╨╛, ╨┐╤А╨╛╨▒╤Г╨╡╨╝ deliveryAddress ╨╜╨░ ╨▓╨╜╨╡╤И╨╜╨╡╨╝ ╤Г╤А╨╛╨▓╨╜╨╡
                addr_str = self.clean_str(o_data.get("deliveryAddress"))
                if addr_str and len(addr_str) > len(city or "") + 2:
                    delivery_address = addr_str
                    has_new_address = True
                else:
                    delivery_address = "╨б╨░╨╝╨╛╨▓╤Л╨▓╨╛╨╖"
            else:
                has_new_address = True
            
            # ╨Х╤Б╨╗╨╕ ╨▓ ╨╕╤В╨╛╨│╨╡ ╨▓╤Б╨╡ ╤А╨░╨▓╨╜╨╛ ╤В╨╛╨╗╤М╨║╨╛ ╨│╨╛╤А╨╛╨┤, ╨╜╨╛ ╨╡╤Б╤В╤М addressString ╨╜╨░ ╨▓╨╜╨╡╤И╨╜╨╡╨╝ ╤Г╤А╨╛╨▓╨╜╨╡ - ╨┐╤А╨╛╨▒╤Г╨╡╨╝ ╨╡╨│╨╛
            if not has_new_address:
                addr_str = self.clean_str(o_data.get("deliveryAddress"))
                if addr_str and len(addr_str) > len(city or "") + 2:
                    delivery_address = addr_str
                    has_new_address = True

            # --- ╨Э╨Ю╨Т╨Р╨п ╨Ы╨Ю╨У╨Ш╨Ъ╨Р ╨Ю╨Я╨Ы╨Р╨в╨л ---
            sum_total = Decimal(str(o_data.get("sum") or 0)) # ╨С╨░╨╖╨╛╨▓╨░╤П ╤Б╤Г╨╝╨╝╨░ (╨┤╨╛ ╤Б╨║╨╕╨┤╨╛╨║)
            # ╨б╤Г╨╝╨╝╨░ ╨║ ╨╛╨┐╨╗╨░╤В╨╡ ╨┐╨╛╤Б╨╗╨╡ ╨┐╤А╨╕╨╝╨╡╨╜╨╡╨╜╨╕╤П ╤Б╨║╨╕╨┤╨╛╨║
            total_with_discount = Decimal(str(o_data.get("totalSum") or o_data.get("total") or sum_total))
            
            # ╨б╨║╨╕╨┤╨║╨╕
            disc_list = o_data.get("discounts") or o_data.get("concessions") or []
            total_discount = sum([Decimal(str((d or {}).get("sum") or 0)) for d in disc_list if isinstance(d, dict)])

            payments = o_data.get("payments") or []
            total_paid = 0
            pm_list_detailed = []
            pm_list = []
            
            for p in payments:
                if not isinstance(p, dict): continue
                pt = p.get("paymentType") or {}
                pn = pt.get("name") if isinstance(pt, dict) else clean(pt)
                pk = (clean(p.get("paymentTypeKind") or p.get("kind") or "") or "").lower()
                if not pn: pn = pk or "╨в╨╕╨┐ ╨╛╨┐╨╗╨░╤В╤Л"
                
                psum = float(p.get("sum") or 0)
                
                is_processed_externally = p.get("isProcessedExternally", False) or p.get("processedExternally", False)
                is_prepay = p.get("isPrepay", False) or p.get("prepay", False)
                status_payment = p.get("status", "").lower()
                
                # ╨б╤З╨╕╤В╨░╨╡╨╝ ╨┐╨╗╨░╤В╨╡╨╢ ╨┐╤А╨╛╨▓╨╡╨┤╨╡╨╜╨╜╤Л╨╝
                is_processed = bool(is_processed_externally or is_prepay or status_payment in ["processed", "closed", "success"] or pk in ["card", "online", "external"])
                
                if is_processed:
                    total_paid += psum
                
                pm_list_detailed.append({
                    "name": pn,
                    "kind": pk,
                    "sum": psum,
                    "is_processed": is_processed
                })
                if pn: pm_list.append(pn)
            
            # ╨г╤З╨╕╤В╤Л╨▓╨░╨╡╨╝ iiko Cloud processedPaymentsSum (╨╡╤Б╨╗╨╕ ╨╛╨╜ ╨▒╨╛╨╗╤М╤И╨╡ ╤В╨╛╨│╨╛ ╤З╤В╨╛ ╨╝╤Л ╤Б╨┐╨░╤А╤Б╨╕╨╗╨╕)
            processed_params = float(o_data.get("processedPaymentsSum") or 0)
            if processed_params > total_paid:
                total_paid = processed_params

            # ╨б╤З╨╕╤В╨░╨╡╨╝ ╨╛╤Б╤В╨░╤В╨╛╨║
            left_to_pay = max(Decimal('0.00'), total_with_discount - Decimal(str(total_paid)))
            is_paid = (left_to_pay <= 0)
            
            payment_method = ", ".join(list(set(pm_list))) or "╨Э╨╡ ╤Г╨║╨░╨╖╨░╨╜"
            
            # ╨д╨╛╨╗╨▒╤Н╨║ ╤Б╤В╨░╤В╤Г╤Б╨░ ╨╖╨░╨║╤А╤Л╤В╨╛╨│╨╛ ╨╖╨░╨║╨░╨╖╨░
            if not is_paid and raw_status_lower in ("closed", "delivered"):
                is_paid = True
                left_to_pay = Decimal('0.00')

            status_map = {
                "unconfirmed": OrderStatus.unconfirmed, 
                "waitapproval": OrderStatus.unconfirmed, 
                "waitingforselection": OrderStatus.unconfirmed,
                "awaitingconfirmation": OrderStatus.unconfirmed,
                "accepted": OrderStatus.confirmed,
                "waitcooking": OrderStatus.confirmed,
                "readyforcooking": OrderStatus.confirmed,
                "cooking": OrderStatus.cooking, 
                "cookingstarted": OrderStatus.cooking,
                "cookingfinished": OrderStatus.ready, 
                "cookingcompleted": OrderStatus.ready,
                "waiting": OrderStatus.ready, 
                "ready": OrderStatus.ready,
                "readyforpickup": OrderStatus.ready_for_pickup,
                "onway": OrderStatus.delivering, 
                "delivered": OrderStatus.delivered, 
                "closed": OrderStatus.closed,
                "cancelled": OrderStatus.cancelled
            }
            mapped_status = status_map.get(raw_status_lower, OrderStatus.new)

            # ╨Х╤Б╨╗╨╕ ╨╖╨░╨║╨░╨╖ ╨╖╨░╨║╤А╤Л╤В ╨▓ iiko - ╨╛╨╜ ╤В╨╛╤З╨╜╨╛ ╨╛╨┐╨╗╨░╤З╨╡╨╜ (╨┤╨╗╤П ╨╜╨░╤И╨╡╨╣ CRM)
            if not is_paid and mapped_status in (OrderStatus.closed, OrderStatus.delivered):
                is_paid = True
                left_to_pay = Decimal('0.00')
                logger.info(f"Order {order_id_iiko}: Paid via status enforcement ('{mapped_status}')")

            # 7. ╨Ъ╤Г╤А╤М╨╡╤А, ╤В╨╕╨┐ ╨╕ ╨┤╨╛╨┐╨╛╨╗╨╜╨╕╤В╨╡╨╗╤М╨╜╤Л╨╡ ╨┤╨░╨╜╨╜╤Л╨╡
            courier_name = "╨Э╨╡ ╨╜╨░╨╖╨╜╨░╤З╨╡╨╜"
            ci = o_data.get("courierInfo") or {}
            if isinstance(ci, dict):
                c_obj = ci.get("courier") or {}
                if isinstance(c_obj, dict):
                    fn = clean(c_obj.get("firstName") or c_obj.get("name")) or ""
                    ln = clean(c_obj.get("lastName")) or ""
                    courier_name = " ".join(filter(None, [fn, ln])).strip() or clean(ci.get("courierName")) or "╨Э╨╡ ╨╜╨░╨╖╨╜╨░╤З╨╡╨╜"
                    # ╨Ф╨╛╨┐╨╛╨╗╨╜╨╕╤В╨╡╨╗╤М╨╜╨░╤П ╨╖╨░╤Й╨╕╤В╨░ ╨╛╤В "None" ╨▓ ╨║╨╛╨╜╤Ж╨╡ ╨╕╨╝╨╡╨╜╨╕
                    if " None" in courier_name:
                        courier_name = courier_name.replace(" None", "").strip()

            stype = (clean(o_data.get("orderServiceType")) or "").lower()
            if not stype and isinstance(o_data.get("orderType"), dict):
                stype = (clean((o_data.get("orderType") or {}).get("orderServiceType")) or "").lower()
            
            order_type = "╨Ф╨╛╤Б╤В╨░╨▓╨║╨░"
            if any(x in stype for x in ["pickup", "client", "╤Б╨░╨╝╨╛╨▓╤Л╨▓╨╛╨╖"]): 
                order_type = "╨б╨░╨╝╨╛╨▓╤Л╨▓╨╛╨╖"
            elif any(x in stype for x in ["common", "table", "╨╖╨░╨╗╨╡", "╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨╡"]): 
                order_type = "╨Т ╤А╨╡╤Б╤В╨╛╤А╨░╨╜╨╡"

            # ╨Э╨╛╨▓╤Л╨╡ ╨┐╨╛╨╗╤П ╨┤╨╗╤П ╨┐╨╛╨╗╨╜╨╛╨╣ ╨╕╨╜╤Д╨╛╤А╨╝╨░╤В╨╕╨▓╨╜╨╛╤Б╤В╨╕
            source = clean(o_data.get("source")) or "iiko"
            def parse_dt(dt_str):
                if not dt_str:
                    return None
                try:
                    # ISO 8601 ╤Б Z ╨╕╨╗╨╕ ╤Б╨╝╨╡╤Й╨╡╨╜╨╕╨╡╨╝
                    if 'Z' in dt_str or '+' in dt_str or '-' in dt_str[10:]:
                        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                        return dt.astimezone(timezone.utc).replace(tzinfo=None)
                    # ╨Э╨░╨╕╨▓╨╜╨╛╨╡ ╨▓╤А╨╡╨╝╤П - ╤Б╤З╨╕╤В╨░╨╡╨╝ ╨╗╨╛╨║╨░╨╗╤М╨╜╤Л╨╝ ╨┤╨╗╤П ╨╖╨░╨▓╨╡╨┤╨╡╨╜╨╕╤П
                    dt = datetime.fromisoformat(dt_str)
                    return dt.replace(tzinfo=tz).astimezone(timezone.utc).replace(tzinfo=None)
                except Exception as e:
                    logger.error(f"Error parsing date {dt_str}: {e}")
                    return None

            di = o_data.get("deliveryInfo") or {}
            expected_time = None
            actual_time = None
            if di:
                expected_time = parse_dt(di.get("expectedDate") or di.get("completeBefore"))
                actual_time = parse_dt(di.get("actualDate") or di.get("actualTime"))
            
            # ╨д╨╛╨╗╨▒╤Н╨║ ╨╜╨░ ╨▓╨╡╤А╤Е╨╜╨╕╨╣ ╤Г╤А╨╛╨▓╨╡╨╜╤М ╨╛╨▒╤К╨╡╨║╤В╨░ ╨╖╨░╨║╨░╨╖╨░ (iiko Cloud API v2)
            if not expected_time:
                expected_time = parse_dt(o_data.get("completeBefore"))
            if not actual_time:
                actual_time = parse_dt(o_data.get("actualDate"))
            
            # 8. ╨д╨╕╨╜╨░╨╗╤М╨╜╤Л╨╡ ╤Д╨╗╨░╨│╨╕ ╨╕ ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╨╡
            delay = di.get("delayMinutes")
            admin_name = self.clean_str((o_data.get("conformationInfo") or {}).get("confirmedBy"))
            if not admin_name:
                admin_name = self.clean_str((o_data.get("confirmationInfo") or {}).get("confirmedBy"))

            # 8. ╨б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╨╡
            order = session.exec(select(Order).where(Order.iiko_order_id == order_id_iiko)).first()
            
            # ╨Ю╨┐╤А╨╡╨┤╨╡╨╗╤П╨╡╨╝ ╤Д╨╕╨╗╨╕╨░╨╗ (branch) ╨┐╨╛ terminalGroupId
            terminal_group_id = o_data.get("terminalGroupId")
            branch_id = 1 # Fallback
            terminal_group_name = None
            
            if terminal_group_id:
                branch = session.exec(select(Branch).where(Branch.iiko_terminal_id == terminal_group_id)).first()
                if branch:
                    branch_id = branch.id
                    terminal_group_name = branch.name
            
            if not order:
                order = Order(iiko_order_id=order_id_iiko, branch_id=branch_id)
                order.iiko_creation_time = iiko_creation_time
                order.status_history = [{"status": mapped_status, "time": current_time_tz.isoformat(), "comment": "╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨╕╤А╨╛╨▓╨░╨╜"}]
            else:
                # ╨Х╤Б╨╗╨╕ ╨╖╨░╨║╨░╨╖ ╤Г╨╢╨╡ ╨╡╤Б╤В╤М, ╨╛╨▒╨╜╨╛╨▓╨╗╤П╨╡╨╝ branch_id ╨╡╤Б╨╗╨╕ ╨╛╨╜ ╨╕╨╖╨╝╨╡╨╜╨╕╨╗╤Б╤П
                order.branch_id = branch_id
            
            # --- ╨Ы╨Ю╨У╨Ш╨Ъ╨Р ╨Ю╨Я╨а╨Х╨Ф╨Х╨Ы╨Х╨Э╨Ш╨п ASAP / ╨Я╨а╨Х╨Ф╨Ч╨Р╨Ъ╨Р╨Ч ---
            raw_comment = self.clean_str(o_data.get("comment"))
            comment_lower = (raw_comment or "").lower()
            
            # ╨С╨░╨╖╨╛╨▓╤Л╨╡ ╨╖╨╜╨░╤З╨╡╨╜╨╕╤П ╨╕╨╖ iiko (╨┐╤А╨╕╨╛╤А╨╕╤В╨╡╤В - ╤Д╨╗╨░╨│╤Г isAsap)
            final_is_asap = bool(o_data.get("isAsap", True))
            
            # 1. ╨Х╤Б╨╗╨╕ ╤Д╨╗╨░╨│ isAsap ╤П╨▓╨╜╨╛ False - ╤Н╤В╨╛ ╨┐╤А╨╡╨┤╨╖╨░╨║╨░╨╖
            if o_data.get("isAsap") is False:
                final_is_asap = False
            
            # 2. ╨Х╤Б╨╗╨╕ ╨╡╤Б╤В╤М ╨▓╤А╨╡╨╝╤П ╨│╨╛╤В╨╛╨▓╨╜╨╛╤Б╤В╨╕ ╨╕ ╨╛╨╜╨╛ ╨╖╨╜╨░╤З╨╕╤В╨╡╨╗╤М╨╜╨╛ ╨╛╤В╨╗╨╕╤З╨░╨╡╤В╤Б╤П ╨╛╤В ╨▓╤А╨╡╨╝╨╡╨╜╨╕ ╤Б╨╛╨╖╨┤╨░╨╜╨╕╤П
            if expected_time and iiko_creation_time:
                diff_mins = (expected_time - iiko_creation_time).total_seconds() / 60
                # ╨Х╤Б╨╗╨╕ ╤А╨░╨╖╨╜╨╕╤Ж╨░ ╨▒╨╛╨╗╨╡╨╡ 90 ╨╝╨╕╨╜╤Г╤В - ╤Б╨║╨╛╤А╨╡╨╡ ╨▓╤Б╨╡╨│╨╛ ╤Н╤В╨╛ ╨┐╤А╨╡╨┤╨╖╨░╨║╨░╨╖ (╨╜╨░ ╨▓╤А╨╡╨╝╤П)
                if diff_mins > 90:
                    final_is_asap = False
            
            # 3. ╨Ф╨╛╨┐╨╛╨╗╨╜╨╕╤В╨╡╨╗╤М╨╜╤Л╨╡ ╨┐╤А╨╛╨▓╨╡╤А╨║╨╕ ╨┐╨╛ ╨║╨╛╨╝╨╝╨╡╨╜╤В╨░╤А╨╕╤О (╨╡╤Б╨╗╨╕ ╤Д╨╗╨░╨│ ╨▓╤Б╨╡ ╨╡╤Й╨╡ True)
            if final_is_asap:
                if "╨╜╨░ ╨▓╤А╨╡╨╝╤П" in comment_lower or "╨┐╤А╨╡╨┤╨╖╨░╨║╨░╨╖" in comment_lower:
                    final_is_asap = False
            
            # 4. ╨Х╤Б╨╗╨╕ ╨▓ ╨║╨╛╨╝╨╝╨╡╨╜╤В╨░╤А╨╕╨╕ ╨Э╨Х╨в ╨║╨╗╤О╤З╨╡╨▓╤Л╤Е ╤Б╨╗╨╛╨▓ ╨┐╤А╨╡╨┤╨╖╨░╨║╨░╨╖╨░, ╨╜╨╛ ╨╡╤Б╤В╤М ╨┤╤А╤Г╨│╨╛╨╣ ╤В╨╡╨║╤Б╤В, 
            # ╨╕ ╨┐╤А╨╕ ╤Н╤В╨╛╨╝ ╨▓╤А╨╡╨╝╤П ╨┤╨╛╤Б╤В╨░╨▓╨║╨╕ ╨▒╨╗╨╕╨╖╨║╨╛ ╨║ ╨▓╤А╨╡╨╝╨╡╨╜╨╕ ╤Б╨╛╨╖╨┤╨░╨╜╨╕╤П - ╨╛╤Б╤В╨░╨▓╨╗╤П╨╡╨╝ ASAP
            elif raw_comment and "╨╜╨░ ╨▓╤А╨╡╨╝╤П" not in comment_lower and "╨┐╤А╨╡╨┤╨╖╨░╨║╨░╨╖" not in comment_lower:
                if expected_time and iiko_creation_time:
                    diff_mins = (expected_time - iiko_creation_time).total_seconds() / 60
                    if diff_mins < 90:
                        final_is_asap = True

            # 3. ╨Х╤Б╨╗╨╕ ╨▓╤А╨╡╨╝╤П ╨│╨╛╤В╨╛╨▓╨╜╨╛╤Б╤В╨╕ ╨╕╨╖╨╝╨╡╨╜╨╕╨╗╨╛╤Б╤М ╨▓ ╨┐╤А╨╛╤Ж╨╡╤Б╤Б╨╡ (╤Б╤А╨░╨▓╨╜╨╕╨▓╨░╨╡╨╝ ╤Б ╤Г╨╢╨╡ ╤Б╤Г╤Й╨╡╤Б╤В╨▓╤Г╤О╤Й╨╕╨╝ ╨╖╨░╨║╨░╨╖╨╛╨╝ ╨▓ ╨С╨Ф)
            if order and order.expected_time and expected_time:
                # ╨С╨╡╨╖╨╛╨┐╨░╤Б╨╜╨╛╨╡ ╨▓╤Л╤З╨╕╤В╨░╨╜╨╕╨╡ naive/aware
                oe = order.expected_time.replace(tzinfo=None) if order.expected_time.tzinfo else order.expected_time
                ne = expected_time.replace(tzinfo=None) if expected_time.tzinfo else expected_time
                if abs((oe - ne).total_seconds()) > 60:
                    final_is_asap = False

            # ╨д╨╕╨╜╨░╨╗╤М╨╜╤Л╨╡ ╤Д╨╗╨░╨│╨╕
            is_asap = final_is_asap
            is_on_time = not final_is_asap

            # ╨Т╨╛╤Б╤Б╤В╨░╨╜╨░╨▓╨╗╨╕╨▓╨░╨╡╨╝ ╨╗╨╛╨│╨╕╨║╤Г ╨╕╤Б╤В╨╛╤А╨╕╨╕ ╤Б╤В╨░╤В╤Г╤Б╨╛╨▓
            if order.id and order.status != mapped_status:
                h = list(order.status_history or [])
                h.append({"status": mapped_status, "time": current_time_tz.isoformat(), "comment": f"iiko: {raw_status}"})
                order.status_history = h
                sql_flag_modified(order, "status_history")

            # ╨Ь╨░╨┐╨┐╨╕╨╜╨│ ╨▓╤Б╨╡╤Е ╨┐╨╛╨╗╨╡╨╣
            order.status = mapped_status
            order.external_number = external_number or order.external_number
            order.customer_name = full_customer_name
            order.customer_phone = phone
            order.courier_name = courier_name
            
            # ╨Ю╨▒╨╜╨╛╨▓╨╗╤П╨╡╨╝ ╨░╨┤╤А╨╡╤Б╨╜╤Л╨╡ ╨┐╨╛╨╗╤П ╤В╨╛╨╗╤М╨║╨╛ ╨╡╤Б╨╗╨╕ ╨▓ ╨╜╨╛╨▓╨╛╨╝ ╨┐╨░╨║╨╡╤В╨╡ ╨╡╤Б╤В╤М ╤А╨╡╨░╨╗╤М╨╜╤Л╨╣ ╨░╨┤╤А╨╡╤Б
            # ╨Ш╨Ы╨Ш ╨╡╤Б╨╗╨╕ ╨▓ ╨С╨Ф ╨░╨┤╤А╨╡╤Б ╨╡╤Й╨╡ ╨╜╨╡ ╨╖╨░╨┐╨╛╨╗╨╜╨╡╨╜ (╨│╨╛╤А╨╛╨┤ ╨╜╨╡ ╤Б╤З╨╕╤В╨░╨╡╤В╤Б╤П ╨╖╨░╨┐╨╛╨╗╨╜╨╡╨╜╨╜╤Л╨╝ ╨░╨┤╤А╨╡╤Б╨╛╨╝)
            db_addr_empty = not order.delivery_address or order.delivery_address == city
            if has_new_address or db_addr_empty:
                order.delivery_address = delivery_address or order.delivery_address or city
                order.city = city or order.city
                order.street = street_name or order.street
                order.house = house or order.house
                order.flat = flat or order.flat
                order.entrance = entrance or order.entrance
                order.floor = floor or order.floor
                order.doorphone = doorphone or order.doorphone
            
            order.comment = clean(o_data.get("comment")) or None
            order.total_amount, order.total_with_discount, order.total_discount = sum_total, total_with_discount, total_discount
            order.is_paid, order.payment_method, order.order_type = is_paid, payment_method, order_type
            
            # ╨в╨╡╤А╨╝╨╕╨╜╨░╨╗╤М╨╜╨░╤П ╨│╤А╤Г╨┐╨┐╨░
            order.terminal_group_id = terminal_group_id or order.terminal_group_id
            order.terminal_group_name = terminal_group_name or order.terminal_group_name
            
            # ╨Ф╨╛╨┐. ╨┐╨╛╨╗╤П
            order.source = source
            order.iiko_creation_time = iiko_creation_time or order.iiko_creation_time
            order.expected_time = expected_time or order.expected_time
            order.actual_time = actual_time or order.actual_time
            order.is_on_time = is_on_time
            order.is_asap = is_asap
            order.delay_minutes = delay
            order.admin_name = admin_name or order.admin_name

            # --- ╨Ю╨┐╤А╨╡╨┤╨╡╨╗╨╡╨╜╨╕╨╡ ╨╖╨╛╨╜╤Л ╨┤╨╛╤Б╤В╨░╨▓╨║╨╕ ╨┐╨╛ ╨░╨┤╤А╨╡╤Б╤Г ---
            # 1. ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝ ╨║╨╛╨╛╤А╨┤╨╕╨╜╨░╤В╤Л ╨╜╨░╨┐╤А╤П╨╝╤Г╤О ╨╕╨╖ iiko (deliveryPoint)
            coords_iiko = dp.get("coordinates", {})
            lat_iiko = coords_iiko.get("latitude")
            lng_iiko = coords_iiko.get("longitude")
            
            # ╨Х╤Б╨╗╨╕ ╤Н╤В╨╛ ╨┤╨╛╤Б╤В╨░╨▓╨║╨░, ╨┐╤Л╤В╨░╨╡╨╝╤Б╤П ╨╛╨┐╤А╨╡╨┤╨╡╨╗╨╕╤В╤М ╨╖╨╛╨╜╤Г
            if order_type == "╨Ф╨╛╤Б╤В╨░╨▓╨║╨░":
                logger.info(f"Auto-detecting zone for order {order_id_iiko}")
                
                # ╨Я╤А╨╕╨╛╤А╨╕╤В╨╡╤В 1: ╨Ъ╨╛╨╛╤А╨┤╨╕╨╜╨░╤В╤Л ╨╕╨╖ iiko
                if lat_iiko and lng_iiko and abs(float(lat_iiko)) > 1.0:
                    try:
                        from app.services.yandex_service import yandex_service
                        order.latitude = float(lat_iiko)
                        order.longitude = float(lng_iiko)
                        zone = await yandex_service.resolve_zone_for_point(order.latitude, order.longitude, session)
                        if zone:
                            order.resolved_delivery_zone_id = zone.id
                            order.delivery_zone = zone.name
                            logger.info(f"Order {order_id_iiko}: Resolved zone {zone.name} via iiko coordinates")
                    except Exception as ze:
                        logger.error(f"Error resolving zone from iiko coordinates: {ze}")

                # ╨Я╤А╨╕╨╛╤А╨╕╤В╨╡╤В 2: ╨У╨╡╨╛╨║╨╛╨┤╨╡╤А (╨╡╤Б╨╗╨╕ ╨╖╨╛╨╜╨░ ╨╡╤Й╨╡ ╨╜╨╡ ╨╛╨┐╤А╨╡╨┤╨╡╨╗╨╡╨╜╨░)
                if not order.resolved_delivery_zone_id:
                    # ╨Я╤Л╤В╨░╨╡╨╝╤Б╤П ╨╛╨┐╤А╨╡╨┤╨╡╨╗╨╕╤В╤М ╨╖╨╛╨╜╤Г ╤В╨╛╨╗╤М╨║╨╛ ╨╡╤Б╨╗╨╕ ╨╡╤Б╤В╤М ╨░╨┤╤А╨╡╤Б╨╜╤Л╨╡ ╨┤╨░╨╜╨╜╤Л╨╡
                    # ╨в╨╡╨┐╨╡╤А╤М ╨╝╤Л ╨▒╨╛╨╗╨╡╨╡ ╨╗╨╛╤П╨╗╤М╨╜╤Л ╨║ ╨║╨╛╨╝╨┐╨╛╨╜╨╡╨╜╤В╨░╨╝: ╨╡╤Б╨╗╨╕ ╨╡╤Б╤В╤М ╤Е╨╛╤В╤П ╨▒╤Л ╤Б╤В╤А╨╛╨║╨░ ╨░╨┤╤А╨╡╤Б╨░
                    full_addr_str = delivery_address if (delivery_address and delivery_address != "╨б╨░╨╝╨╛╨▓╤Л╨▓╨╛╨╖") else None
                    
                    if full_addr_str or (city and street_name):
                        try:
                            # ╨Х╤Б╨╗╨╕ ╨║╨╛╨╝╨┐╨╛╨╜╨╡╨╜╤В╨╛╨▓ ╨╜╨╡╤В, ╨╜╨╛ ╨╡╤Б╤В╤М ╤Б╤В╤А╨╛╨║╨░ - iiko_service.check_address_zone 
                            # ╨▓╤Б╨╡ ╤А╨░╨▓╨╜╨╛ ╨┐╨╛╨┐╤А╨╛╨▒╤Г╨╡╤В ╨│╨╡╨╛╨║╨╛╨┤╨╕╤А╨╛╨▓╨░╤В╤М (╨╝╤Л ╨┐╨╡╤А╨╡╨┤╨░╨┤╨╕╨╝ ╨╡╨╣ ╨║╨╛╨╝╨┐╨╛╨╜╨╡╨╜╤В╤Л, ╨┤╨░╨╢╨╡ ╨╡╤Б╨╗╨╕ ╨╛╨╜╨╕ ╨┐╤Г╤Б╤В╤Л╨╡)
                            zone_data = await iiko_service.check_address_zone(
                                city=city or city_from_settings or "╨в╤О╨╝╨╡╨╜╤М",
                                street=street_name or "",
                                house=house or "",
                                api_login=settings_db.api_login if settings_db else None
                            )
                            
                            if zone_data:
                                if zone_data.get("zone"):
                                    order.delivery_zone = zone_data.get("zone")
                                if zone_data.get("zone_id"):
                                    order.resolved_delivery_zone_id = zone_data.get("zone_id")
                                if zone_data.get("coordinates"):
                                    order.latitude = zone_data["coordinates"].get("lat")
                                    order.longitude = zone_data["coordinates"].get("lng")
                                
                                if zone_data.get("zone"):
                                    logger.info(f"Order {order_id_iiko}: Resolved zone {order.delivery_zone} via geocoder")
                        except Exception as e:
                            logger.warning(f"Could not auto-detect zone via geocoder: {e}")
            
            elif order_type == "╨б╨░╨╝╨╛╨▓╤Л╨▓╨╛╨╖":
                order.delivery_zone = "╤Б╨░╨╝╨╛╨▓╤Л╨▓╨╛╨╖"
                order.resolved_delivery_zone_id = None
                logger.info(f"Order {order_id_iiko}: Type is Pickup, skipping zone detection")
            # ---------------------------------------------

            # --- ╨Э╨Ю╨Т╨Р╨п ╨Ы╨Ю╨У╨Ш╨Ъ╨Р ╨б╨Ю╨б╨в╨Р╨Т╨Р ╨Ч╨Р╨Ъ╨Р╨Ч╨Р (╤Б ╨╕╨╝╨╡╨╜╨░╨╝╨╕ ╨╕ ╨╖╨░╤Й╨╕╤В╨╛╨╣ ╨╛╤В ╨╖╨░╤В╨╕╤А╨░╨╜╨╕╤П) ---
            
            if "items" in o_data and isinstance(o_data["items"], list) and len(o_data["items"]) > 0:
                raw_items = o_data.get("items", [])
                enriched_items = []
                
                product_ids = []
                for item in raw_items:
                    if not item: continue
                    pid = (
                        item.get("productId") or 
                        item.get("product", {}).get("id") or 
                        item.get("primaryComponent", {}).get("product", {}).get("id")
                    )
                    if pid: 
                        product_ids.append(pid)
                        if not item.get("productId"): item["productId"] = pid
                        
                    for mod in (item.get("modifiers") or []):
                        if not mod: continue
                        mpid = (
                            mod.get("productId") or 
                            mod.get("product", {}).get("id") or 
                            mod.get("primaryComponent", {}).get("product", {}).get("id")
                        )
                        if mpid: 
                            product_ids.append(mpid)
                            if not mod.get("productId"): mod["productId"] = mpid
                        
                # ╨Ф╨╛╤Б╤В╨░╨╡╨╝ ╨╜╨░╨╖╨▓╨░╨╜╨╕╤П ╨╕╨╖ ╨╗╨╛╨║╨░╨╗╤М╨╜╨╛╨╣ ╨▒╨░╨╖╤Л
                db_products = session.exec(select(Product).where(Product.iiko_id.in_(product_ids))).all()
                prod_map = {p.iiko_id: p.name for p in db_products}

                # ╨Ф╨╛╤Б╤В╨░╨╡╨╝ ╤Б╤В╨░╤А╤Л╨╡ ╨╜╨░╨╖╨▓╨░╨╜╨╕╤П ╨╕╨╖ ╤В╨╡╨║╤Г╤Й╨╡╨│╨╛ ╤Б╨╛╤Б╤В╨╛╤П╨╜╨╕╤П ╨╖╨░╨║╨░╨╖╨░
                old_names_map = {}
                if order.order_items_details:
                    for old_item in order.order_items_details:
                        old_pid = (
                            old_item.get("productId") or 
                            old_item.get("id") or 
                            old_item.get("product", {}).get("id") or 
                            old_item.get("primaryComponent", {}).get("product", {}).get("id")
                        )
                        old_name = old_item.get("name")
                        if old_pid and old_name and old_name != "╨Э╨╡╨╕╨╖╨▓╨╡╤Б╤В╨╜╤Л╨╣ ╤В╨╛╨▓╨░╤А":
                            old_names_map[old_pid] = old_name
                        
                        modifiers_list = old_item.get("modifiers") or []
                        for old_mod in modifiers_list:
                            old_mpid = (
                                old_mod.get("productId") or 
                                old_mod.get("id") or 
                                old_mod.get("product", {}).get("id") or 
                                old_mod.get("primaryComponent", {}).get("product", {}).get("id")
                            )
                            old_mname = old_mod.get("name")
                            if old_mpid and old_mname and old_mname != "╨Ь╨╛╨┤╨╕╤Д╨╕╨║╨░╤В╨╛╤А":
                                old_names_map[old_mpid] = old_mname
                
                for item in raw_items:
                    enriched_item = item.copy()
                    pid = item.get("productId")
                    
                    # ╨Я╤А╨╕╨╛╤А╨╕╤В╨╡╤В ╨╕╨╝╨╡╨╜╨╕: product.name -> primaryComponent.product.name -> productName -> ╨С╨Ф -> ╨Ш╤Б╤В╨╛╤А╨╕╤П -> Fallback
                    if not enriched_item.get("name") or enriched_item.get("name") == "╨Э╨╡╨╕╨╖╨▓╨╡╤Б╤В╨╜╤Л╨╣ ╤В╨╛╨▓╨░╤А":
                        enriched_item["name"] = (
                            enriched_item.get("product", {}).get("name") or 
                            enriched_item.get("primaryComponent", {}).get("product", {}).get("name") or 
                            enriched_item.get("productName") or 
                            prod_map.get(pid) or 
                            old_names_map.get(pid) or 
                            "╨Э╨╡╨╕╨╖╨▓╨╡╤Б╤В╨╜╤Л╨╣ ╤В╨╛╨▓╨░╤А"
                        )
                    if not enriched_item.get("sum"):
                        enriched_item["sum"] = float(enriched_item.get("amount", 0)) * float(enriched_item.get("price", 0))
                        
                    enriched_mods = []
                    for mod in (item.get("modifiers") or []):
                        if not mod: continue
                        emod = mod.copy()
                        mpid = mod.get("productId")
                        
                        if not emod.get("name") or emod.get("name") == "╨Э╨╡╨╕╨╖╨▓╨╡╤Б╤В╨╜╤Л╨╣ ╤В╨╛╨▓╨░╤А":
                            emod["name"] = (
                                emod.get("product", {}).get("name") or 
                                emod.get("primaryComponent", {}).get("product", {}).get("name") or 
                                prod_map.get(mpid) or 
                                old_names_map.get(mpid) or 
                                "╨Э╨╡╨╕╨╖╨▓╨╡╤Б╤В╨╜╤Л╨╣ ╤В╨╛╨▓╨░╤А"
                            )
                        
                        if not emod.get("sum"):
                            emod["sum"] = float(emod.get("amount", 0)) * float(emod.get("price", 0))
                            
                        enriched_mods.append(emod)
                    
                    enriched_item["modifiers"] = enriched_mods
                    enriched_items.append(enriched_item)

                order.order_items_details = enriched_items
                sql_flag_modified(order, "order_items_details")
            else:
                logger.info(f"Order {order_id_iiko}: No valid items in webhook payload, skipping items update to prevent data loss")

            order.base_amount = sum_total
            order.left_to_pay = left_to_pay
            order.payments_details = {"items": pm_list_detailed, "total_paid": total_paid}
            order.discounts_details = {"items": disc_list}
            order.updated_at = datetime.now(timezone.utc)
            
            sql_flag_modified(order, "order_items_details")
            sql_flag_modified(order, "discounts_details")
            sql_flag_modified(order, "payments_details")
            session.add(order)
            session.commit()
            logger.info(f"Order {order_id_iiko} ({external_number}) synced. Status={mapped_status}, Paid={is_paid}")
            
        except Exception as e:
            import traceback
            logger.error(f"CRITICAL Error processing order {iiko_order_data.get('id', 'unknown')}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # ╨Ь╤Л ╨╜╨╡ ╨┤╨╡╨╗╨░╨╡╨╝ rollback ╨┐╨╛╨╗╨╜╨╛╤Б╤В╤М╤О, ╤З╤В╨╛╨▒╤Л ╨╛╨┤╨╕╨╜ ╨║╤А╨╕╨▓╨╛╨╣ ╨╖╨░╨║╨░╨╖ ╨╜╨╡ ╨╛╤Б╤В╨░╨╜╨░╨▓╨╗╨╕╨▓╨░╨╗ ╨▓╨╡╤Б╤М ╤Ж╨╕╨║╨╗, 
            # ╨╜╨╛ ╨╕ ╨╜╨╡ ╨║╨╛╨╝╨╝╨╕╤В╨╕╨╝ ╤З╨░╤Б╤В╨╕╤З╨╜╨╛ ╤Б╨╗╨╛╨╝╨░╨╜╨╜╤Л╨╡ ╨┤╨░╨╜╨╜╤Л╨╡.
            try:
                session.rollback()
            except:
                pass

    async def sync_orders(self, session: Session, hours: int = 24):
        from app.models.order import Order, OrderStatus
        """
        ╨Ь╨░╤Б╤Б╨╛╨▓╨░╤П ╨╖╨░╨│╤А╤Г╨╖╨║╨░ ╨╕ ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨╖╨░╨║╨░╨╖╨╛╨▓.
        ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╤В╤Б╤П ╨┤╨╗╤П ╨┐╨╡╤А╨▓╨╛╨╜╨░╤З╨░╨╗╤М╨╜╨╛╨╣ ╨╖╨░╨│╤А╤Г╨╖╨║╨╕ (╨╜╨░ ╤Б╨╗╤Г╤З╨░╨╣ ╨┐╤А╨╛╨┐╤Г╤Б╨║╨░ ╨▓╨╡╨▒╤Е╤Г╨║╨╛╨▓).
        """
        log = SyncLog(sync_type="orders", status="running")
        session.add(log)
        session.commit()
        
        try:
            settings_db = session.exec(select(IikoSettings)).first()
            if not settings_db or not settings_db.organization_id:
                logger.warning("Iiko settings not found, sync aborted")
                log.status = "error"
                log.details = "╨Э╨░╤Б╤В╤А╨╛╨╣╨║╨╕ Iiko ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜╤Л"
                session.add(log)
                session.commit()
                return
                
            org_id = settings_db.organization_id
        
            # ╨Ю╨┐╤А╨╡╨┤╨╡╨╗╤П╨╡╨╝ ╨╕╨╜╤В╨╡╤А╨▓╨░╨╗ ╨╜╨░ ╨╛╤Б╨╜╨╛╨▓╨╡ ╤З╨░╤Б╨╛╨▓╨╛╨│╨╛ ╨┐╨╛╤П╤Б╨░ ╨╕╨╖ ╨╜╨░╤Б╤В╤А╨╛╨╡╨║
            from app.core.datetime_utils import get_tz_name, get_local_now
            tz_name = get_tz_name(session)
            now = get_local_now(tz_name)
            
            # ╨Ю╤Е╨▓╨░╤В╤Л╨▓╨░╨╡╨╝ ╨┤╨╕╨░╨┐╨░╨╖╨╛╨╜: 24 ╤З╨░╤Б╨░ ╨╜╨░╨╖╨░╨┤ ╨╕ 24 ╤З╨░╤Б╨░ ╨▓╨┐╨╡╤А╨╡╨┤ (╨╕╤В╨╛╨│╨╛ 48 ╤З╨░╤Б╨╛╨▓ ╨▓╨╛╨╖╨╝╨╛╨╢╨╜╨╛╨│╨╛ ╤А╨░╨╖╨▒╤А╨╛╤Б╨░)
            date_from = now - timedelta(hours=24)
            date_to = now + timedelta(hours=24)
            
            logger.info(f"Mass sync starting: orders from {date_from} to {date_to} for org {org_id}")
            
            all_ids = set()

            # 0. ╨Ш╨╜╨║╤А╨╡╨╝╨╡╨╜╤В╨░╨╗╤М╨╜╨░╤П ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨┐╨╛ ╤А╨╡╨▓╨╕╨╖╨╕╤П╨╝ (╨▒╤Л╤Б╤В╤А╤Л╨╣ catch-up ╨┐╤А╨╛╨┐╤Г╤Й╨╡╨╜╨╜╤Л╤Е ╨▓╨╡╨▒╤Е╤Г╨║╨╛╨▓)
            # ╨Ь╤Л ╨▓╤Л╨╖╤Л╨▓╨░╨╡╨╝ ╨╡╨╡, ╤В╨░╨║ ╨║╨░╨║ ╨╛╨╜╨░ ╨╜╨░╨╕╨▒╨╛╨╗╨╡╨╡ ╨╜╨░╨┤╨╡╨╢╨╜╨░ ╨┤╨╗╤П ╨┐╨╛╨╗╤Г╤З╨╡╨╜╨╕╤П ╨╕╨╖╨╝╨╡╨╜╨╡╨╜╨╕╨╣ ╨▒╨╡╨╖ ╨┐╨╡╤А╨╡╨▒╨╛╤А╨░ ╨▓╤Б╨╡╤Е ╨┤╨░╤В.
            try:
                await self.sync_orders_by_revision(session, org_id)
            except Exception as rev_err:
                logger.error(f"Revision sync failed, falling back to date polling: {rev_err}")

            # 1. ╨Ш╨╖ iiko Cloud (╨┐╨╛ ╨┤╨░╤В╨░╨╝ ╨┤╨╛╤Б╤В╨░╨▓╨║╨╕) - ╨║╨░╨║ ╨╖╨░╨┐╨░╤Б╨╜╨╛╨╣ ╨╝╨╡╤Е╨░╨╜╨╕╨╖╨╝
            # ╨Ь╤Л ╤А╨░╨╖╨▒╨╕╨▓╨░╨╡╨╝ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╨╜╨╕╨╡ ╨╕╨╜╤В╨╡╤А╨▓╨░╨╗╨╛╨▓ ╨╜╨░ ╤З╨░╨╜╨║╨╕, ╤В╨░╨║ ╨║╨░╨║ ╤Н╤В╨╛ ╤Б╨╜╨╕╨╢╨░╨╡╤В ╨▓╨╡╤А╨╛╤П╤В╨╜╨╛╤Б╤В╤М ╨╛╤И╨╕╨▒╨║╨╕ TOO_MANY_DATA_REQUESTED
            logger.info(f"Starting robust polling in 2-hour chunks for period {date_from} - {date_to}")
            
            cloud_orders = []
            chunk_start = date_from
            while chunk_start < date_to:
                chunk_end = chunk_start + timedelta(hours=2)
                if chunk_end > date_to:
                    chunk_end = date_to
                    
                try:
                    logger.debug(f"Polling chunk: {chunk_start} - {chunk_end}")
                    batch = await iiko_service.get_orders_by_date(
                        date_from=chunk_start,
                        date_to=chunk_end,
                        organization_id=org_id,
                        api_login=settings_db.api_login,
                        log_error=True # ╨Т╨║╨╗╤О╤З╨░╨╡╨╝ ╨╗╨╛╨│╨╕╤А╨╛╨▓╨░╨╜╨╕╨╡, ╤З╤В╨╛╨▒╤Л ╨▓╨╕╨┤╨╡╤В╤М ╨┐╨╛╨┤╤А╨╛╨▒╨╜╨╛╤Б╤В╨╕ ╨╛╤И╨╕╨▒╨╛╨║
                    )
                    if batch:
                        logger.info(f"Fetched {len(batch)} orders for period {chunk_start} - {chunk_end}")
                        cloud_orders.extend(batch)
                    
                    # ╨Э╨╡╨▒╨╛╨╗╤М╤И╨░╤П ╨┐╨░╤Г╨╖╨░ ╨╝╨╡╨╢╨┤╤Г ╤З╨░╨╜╨║╨░╨╝╨╕ ╨┤╨╗╤П ╨▒╨╡╨╖╨╛╨┐╨░╤Б╨╜╨╛╤Б╤В╨╕
                    await asyncio.sleep(0.5)
                except Exception as chunk_err:
                    logger.error(f"Failed to fetch orders chunk ({chunk_start} - {chunk_end}): {chunk_err}")
                    if "429" in str(chunk_err):
                        await asyncio.sleep(5.0)
                
                chunk_start = chunk_end

            for o in cloud_orders:
                if o.get("id"): all_ids.add(o["id"])
            logger.info(f"Found {len(cloud_orders)} orders in Cloud (via date polling)")
                
            # 2. ╨Ш╨╖ iiko Resto (╨╡╤Б╨╗╨╕ ╨╜╨░╤Б╤В╤А╨╛╨╡╨╜)
            if settings_db.resto_url and settings_db.resto_login:
                try:
                    resto_ids = await iiko_service.get_resto_delivery_history(
                        date_from=date_from,
                        date_to=date_to,
                        resto_url=settings_db.resto_url,
                        resto_login=settings_db.resto_login,
                        resto_password=settings_db.resto_password,
                        log_error=False
                    )
                    for rid in resto_ids: all_ids.add(rid)
                    logger.info(f"Found {len(resto_ids)} orders in Resto")
                except Exception as e:
                    logger.error(f"Failed to fetch Resto orders: {e}")
                    
            # 3. ╨Ф╨╛╨┐╨╛╨╗╨╜╨╕╤В╨╡╨╗╤М╨╜╨╛: ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝ ╨▓╤Б╨╡ ╨░╨║╤В╨╕╨▓╨╜╤Л╨╡ ╨╖╨░╨║╨░╨╖╤Л ╨╕╨╖ ╨╜╨░╤И╨╡╨╣ ╨С╨Ф
            # ╨н╤В╨╛ ╨║╤А╨░╨╣╨╜╨╡ ╨▓╨░╨╢╨╜╨╛, ╨╡╤Б╨╗╨╕ iiko Cloud API ╨┐╨╛ ╨┤╨░╤В╨░╨╝ ╨▓╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╤В ╨╜╨╡╨║╨╛╤А╤А╨╡╨║╤В╨╜╤Л╨╡ ╨┤╨░╨╜╨╜╤Л╨╡ ╨╕╨╗╨╕ ╨▓╨╡╨▒╤Е╤Г╨║╨╕ ╨┐╤А╨╛╨┐╤Г╤Й╨╡╨╜╤Л
            try:
                # ╨Т╨║╨╗╤О╤З╨░╨╡╨╝ ╨▓╤Б╨╡ ╤Б╤В╨░╤В╤Г╤Б╤Л, ╨║╨╛╤В╨╛╤А╤Л╨╡ ╨╜╨╡ ╤П╨▓╨╗╤П╤О╤В╤Б╤П ╤Д╨╕╨╜╨░╨╗╤М╨╜╤Л╨╝╨╕ (╨╖╨░╨║╤А╤Л╤В/╨╛╤В╨╝╨╡╨╜╨╡╨╜)
                active_statuses = [
                    OrderStatus.new, 
                    OrderStatus.unconfirmed, 
                    OrderStatus.confirmed, 
                    OrderStatus.preparing, 
                    OrderStatus.cooking, 
                    OrderStatus.ready, 
                    OrderStatus.ready_for_pickup, 
                    OrderStatus.delivering, 
                    OrderStatus.delivered
                ]
                
                # ╨Т╤Б╨╡ ╤Б╤В╨░╤В╤Г╤Б╤Л ╨┐╨╡╤А╨╡╨▓╨╛╨┤╨╕╨╝ ╨▓ ╨▓╨╡╤А╤Е╨╜╨╕╨╣ ╤А╨╡╨│╨╕╤Б╤В╤А ╨╜╨░ ╨▓╤Б╤П╨║╨╕╨╣ ╤Б╨╗╤Г╤З╨░╨╣, ╨╡╤Б╨╗╨╕ ╨▓ ╨С╨Ф ╨╖╨░╨┐╨╕╤Б╨░╨╜╤Л ╨╖╨╜╨░╤З╨╡╨╜╨╕╤П
                active_strings = [s.value for s in active_statuses] + [s.value.upper() for s in active_statuses]
                
                query = select(Order).where(Order.status.in_(active_strings))
                db_active_orders = session.exec(query).all()
                
                if db_active_orders:
                    logger.info(f"Checking {len(db_active_orders)} active orders from local database: {[o.id for o in db_active_orders]}")
                    for db_order in db_active_orders:
                        if db_order.iiko_order_id:
                            all_ids.add(str(db_order.iiko_order_id))
                else:
                    logger.info("No active orders found in local database for extra sync check.")
                
            except Exception as e:
                logger.error(f"Failed to fetch active orders from DB for sync: {e}")
                import traceback
                logger.error(traceback.format_exc())

            logger.info(f"Syncing {len(all_ids)} unique orders...")
            
            success_count = 0
            for order_id in all_ids:
                try:
                    # ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ ╨╜╨╡╨▒╨╛╨╗╤М╤И╤Г╤О ╨╖╨░╨┤╨╡╤А╨╢╨║╤Г, ╤З╤В╨╛╨▒╤Л ╨╜╨╡ ╨┐╤А╨╡╨▓╤Л╤И╨░╤В╤М ╨╗╨╕╨╝╨╕╤В╤Л API (429) 
                    if success_count > 0 and success_count % 15 == 0:
                        await asyncio.sleep(0.5)

                    # ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╨╝ sync_order_by_id ╨┤╨╗╤П ╨║╨░╨╢╨┤╨╛╨│╨╛ ╨╖╨░╨║╨░╨╖╨░
                    # ╨Ь╤Л ╨╜╨╡ ╤Е╨╛╤В╨╕╨╝, ╤З╤В╨╛╨▒╤Л ╨╛╤И╨╕╨▒╨║╨░ ╨▓ ╨╛╨┤╨╜╨╛╨╝ ╨╖╨░╨║╨░╨╖╨╡ ╨┐╤А╨╡╤А╨▓╨░╨╗╨░ ╨▓╨╡╤Б╤М ╤Ж╨╕╨║╨╗
                    res = await self.sync_order_by_id(session, order_id, org_id)
                    if res: success_count += 1
                except Exception as e:
                    logger.error(f"Failed to sync order {order_id}: {e}")
                    
            logger.info(f"Mass sync finished. Total: {len(all_ids)}, Success: {success_count}")
            log.status = "success"
            log.processed_count = success_count
            log.details = f"╨г╤Б╨┐╨╡╤И╨╜╨╛ ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨╕╤А╨╛╨▓╨░╨╜╨╛ {success_count} ╨╖╨░╨║╨░╨╖╨╛╨▓ ╨╕╨╖ {len(all_ids)}"
            session.add(log)
            session.commit()
        
        except Exception as e:
            logger.error(f"Error in mass order sync: {e}", exc_info=True)
            log.status = "error"
            log.details = str(e)
            session.add(log)
            session.commit()

    async def sync_orders_by_revision(self, session: Session, organization_id: str):
        """
        ╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨╖╨░╨║╨░╨╖╨╛╨▓ ╨┐╨╛ ╤А╨╡╨▓╨╕╨╖╨╕╤П╨╝ (catch-up).
        ╨Я╨╛╨╖╨▓╨╛╨╗╤П╨╡╤В ╨┐╨╛╨╗╤Г╤З╨╕╤В╤М ╨▓╤Б╨╡ ╨╕╨╖╨╝╨╡╨╜╨╡╨╜╨╜╤Л╨╡ ╨╖╨░╨║╨░╨╖╤Л, ╨║╨╛╤В╨╛╤А╤Л╨╡ ╨▒╤Л╨╗╨╕ ╨┐╤А╨╛╨┐╤Г╤Й╨╡╨╜╤Л ╨▓╨╡╨▒╤Е╤Г╨║╨░╨╝╨╕, ╨╜╨╡╨╖╨░╨▓╨╕╤Б╨╕╨╝╨╛ ╨╛╤В ╨┤╨░╤В╤Л.
        """
        # 0. ╨Ч╨░╤Й╨╕╤В╨░ ╨╛╤В ╤Б╨╗╨╕╤И╨║╨╛╨╝ ╤З╨░╤Б╤В╤Л╤Е ╨▓╤Л╨╖╨╛╨▓╨╛╨▓ (╨╜╨╡ ╤З╨░╤Й╨╡ ╤З╨╡╨╝ ╤А╨░╨╖ ╨▓ 20 ╤Б╨╡╨║╤Г╨╜╨┤)
        now = datetime.now()
        last_sync = self._last_rev_sync.get(organization_id)
        if last_sync and (now - last_sync).total_seconds() < 20:
            logger.debug(f"Revision sync for {organization_id} skipped (too soon)")
            return
        self._last_rev_sync[organization_id] = now

        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db: return
        
        current_revision = settings_db.last_order_revision or 0
        logger.info(f"Starting revision sync from revision {current_revision} for org {organization_id}")
        
        try:
            # 1. ╨Х╤Б╨╗╨╕ ╤А╨╡╨▓╨╕╨╖╨╕╤П 0 ╨╕╨╗╨╕ ╨┐╤Г╤Б╤В╨░╤П - ╨╖╨░╨┐╤Г╤Б╨║╨░╨╡╨╝ 'Cold Start' ╨▓╨╛╤Б╤Б╤В╨░╨╜╨╛╨▓╨╗╨╡╨╜╨╕╨╡
            if current_revision == 0:
                logger.warning(f"Revision 0 detected. Starting 'Cold Start' recovery for org {organization_id}...")
                
                # ╨░) ╨Я╤А╨╕╨╜╤Г╨┤╨╕╤В╨╡╨╗╤М╨╜╨░╤П ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨╖╨░ ╨┐╨╛╤Б╨╗╨╡╨┤╨╜╨╕╨╡ 48 ╤З╨░╤Б╨╛╨▓, ╤З╤В╨╛╨▒╤Л ╨╜╨╡ ╨┐╨╛╤В╨╡╤А╤П╤В╤М ╨┤╨░╨╜╨╜╤Л╨╡
                await self.sync_orders(session, hours=48)
                
                # ╨▒) ╨Я╨╛╨╗╤Г╤З╨░╨╡╨╝ ╨░╨║╤В╤Г╨░╨╗╤М╨╜╤Г╤О ╤А╨╡╨▓╨╕╨╖╨╕╤О ╨╕╨╖ Iiko ╨┤╨╗╤П ╨┤╨░╨╗╤М╨╜╨╡╨╣╤И╨╕╤Е ╨╕╨╜╨║╤А╨╡╨╝╨╡╨╜╤В╨░╨╗╤М╨╜╤Л╤Е ╨╛╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╕╨╣
                new_max = await iiko_service.get_max_revision(
                    organization_id=organization_id,
                    api_login=settings_db.api_login
                )
                if new_max:
                    settings_db.last_order_revision = new_max
                    session.add(settings_db)
                    session.commit()
                    logger.info(f"Cold Start successful. New baseline revision: {new_max}")
                return

            # 2. ╨Ч╨░╨┐╤А╨░╤И╨╕╨▓╨░╨╡╨╝ ╨╕╨╖╨╝╨╡╨╜╨╡╨╜╨╕╤П ╤Б ╨┐╨╛╤Б╨╗╨╡╨┤╨╜╨╡╨╣ ╤А╨╡╨▓╨╕╨╖╨╕╨╕
            data = await iiko_service.get_deliveries_by_revision(
                organization_id=organization_id,
                initial_revision=current_revision,
                api_login=settings_db.api_login
            )
            
            # iiko_service.get_deliveries_by_revision ╨▓╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╤В ╤Г╨╢╨╡ ╤А╨░╤Б╨┐╨░╨║╨╛╨▓╨░╨╜╨╜╤Л╨╣ ordersByOrganizations
            orders = data.get("orders", [])
            max_revision = data.get("maxRevision")
            
            if not orders:
                logger.info("No new orders found by revision sync")
                if max_revision and max_revision > current_revision:
                    settings_db.last_order_revision = max_revision
                    session.add(settings_db)
                    session.commit()
                    logger.info(f"Revision updated to {max_revision} even with no orders")
                return

            logger.info(f"Found {len(orders)} orders via revision sync. Processing...")
            
            count = 0
            for order_data in orders:
                try:
                    # ╨Ю╨▒╤А╨░╨▒╨░╤В╤Л╨▓╨░╨╡╨╝ ╨║╨░╨╢╨┤╤Л╨╣ ╨╖╨░╨║╨░╨╖
                    await self.process_iiko_order(session, order_data, organization_id)
                    count += 1
                except Exception as e:
                    logger.error(f"Error processing order from revision: {e}")
            
            # ╨Ю╨▒╨╜╨╛╨▓╨╗╤П╨╡╨╝ ╤А╨╡╨▓╨╕╨╖╨╕╤О ╨▓ ╨╜╨░╤Б╤В╤А╨╛╨╣╨║╨░╤Е
            if max_revision:
                settings_db.last_order_revision = max_revision
                session.add(settings_db)
                session.commit()
                logger.info(f"Revision sync finished. New revision: {max_revision}, Processed: {count}")
                
        except httpx.HTTPStatusError as e:
            # 3. ╨Ю╨▒╤А╨░╨▒╨░╤В╤Л╨▓╨░╨╡╨╝ ╨╛╤И╨╕╨▒╨║╤Г "TOO_OLD_REVISION" (╨Ъ╨╛╨┤ 400)
            if e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    if error_data.get("error") == "TOO_OLD_REVISION":
                        logger.warning(f"Revision {current_revision} is too old. Starting 'Cold Start' recovery...")
                        
                        # ╨б╨▒╤А╨░╤Б╤Л╨▓╨░╨╡╨╝ ╤А╨╡╨▓╨╕╨╖╨╕╤О, ╤З╤В╨╛╨▒╤Л ╨┐╤А╨╕ ╤Б╨╗╨╡╨┤╤Г╤О╤Й╨╡╨╝ ╨▓╤Л╨╖╨╛╨▓╨╡ (╨╕╨╗╨╕ ╤А╨╡╨║╤Г╤А╤Б╨╕╨▓╨╜╨╛╨╝) ╤Б╤А╨░╨▒╨╛╤В╨░╨╗ Cold Start
                        settings_db.last_order_revision = 0
                        session.add(settings_db)
                        session.commit()
                        
                        # ╨Ч╨░╨┐╤Г╤Б╨║╨░╨╡╨╝ Cold Start ╨╜╨╡╨╝╨╡╨┤╨╗╨╡╨╜╨╜╨╛
                        await self.sync_orders_by_revision(session, organization_id)
                        return 
                except Exception as parse_err:
                    logger.error(f"Failed to handle 400 error: {parse_err}")
            
            logger.error(f"Iiko API error during revision sync: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in sync_orders_by_revision: {e}")

    async def sync_order_by_id(self, session: Session, order_id: str, organization_id: str) -> bool:
        """╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨║╨╛╨╜╨║╤А╨╡╤В╨╜╨╛╨│╨╛ ╨╖╨░╨║╨░╨╖╨░ ╨┐╨╛ ID (╨▓╤Л╨╖╤Л╨▓╨░╨╡╤В╤Б╤П ╨▓╨╡╨▒╤Е╤Г╨║╨░╨╝╨╕)"""
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login if settings_db else None
        try:
            order_data = await iiko_service.get_order_by_id(order_id, organization_id, api_login=api_login)
            if order_data:
                await self.process_iiko_order(session, order_data, organization_id)
                return True
        except Exception as e:
            logger.error(f"Failed to sync order {order_id}: {e}")
        return False

    async def sync_delivery_restrictions(self, session: Session) -> Dict[str, Any]:
        """╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨╖╨╛╨╜ ╨╕ ╤Г╤Б╨╗╨╛╨▓╨╕╨╣ ╨┤╨╛╤Б╤В╨░╨▓╨║╨╕ ╨╕╨╖ iiko Cloud"""
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db or not settings_db.organization_id:
            return {"error": "Iiko not configured"}
            
        try:
            data = await iiko_service.get_delivery_restrictions(
                api_login=settings_db.api_login,
                organization_id=settings_db.organization_id
            )
            
            # ╨Ю╨▒╤А╨░╨▒╨╛╤В╨║╨░ ╨╛╤В╨▓╨╡╤В╨░ iiko ╨╝╨╛╨╢╨╡╤В ╨▒╤Л╤В╤М {"deliveryRestrictions": [...]} ╨╕╨╗╨╕ ╨┐╤А╨╛╤Б╤В╨╛ ╤Б╨┐╨╕╤Б╨║╨╛╨╝
            restrictions_data = []
            if isinstance(data, dict):
                restrictions_data = data.get("deliveryRestrictions", [])
            elif isinstance(data, list):
                restrictions_data = data
                
            if not restrictions_data:
                logger.warning("╨Э╨╡╤В ╨┤╨░╨╜╨╜╤Л╤Е ╨╛╨▒ ╨╛╨│╤А╨░╨╜╨╕╤З╨╡╨╜╨╕╤П╤Е ╨┤╨╛╤Б╤В╨░╨▓╨║╨╕ ╨╛╤В iiko")
                return {"success": True, "synced": 0, "message": "No restrictions data"}

            synced_count = 0
            
            for restriction_item in restrictions_data:
                if not isinstance(restriction_item, dict):
                    continue
                    
                # 1. ╨Э╨░╤Е╨╛╨┤╨╕╨╝ ╤Д╨╕╨╗╨╕╨░╨╗ (╤В╨╡╤А╨╝╨╕╨╜╨░╨╗╤М╨╜╤Г╤О ╨│╤А╤Г╨┐╨┐╤Г)
                tg_id = restriction_item.get("terminalGroupId")
                if not tg_id:
                    # ╨Х╤Б╨╗╨╕ terminalGroupId ╨╜╨╡╤В, ╨▓╨╛╨╖╨╝╨╛╨╢╨╜╨╛ ╤Н╤В╨╛ ╨╛╨▒╤Й╨╕╨╡ ╨╛╨│╤А╨░╨╜╨╕╤З╨╡╨╜╨╕╤П ╨┤╨╗╤П ╨▓╤Б╨╡╤Е ╤Д╨╕╨╗╨╕╨░╨╗╨╛╨▓ ╨╛╤А╨│╨░╨╜╨╕╨╖╨░╤Ж╨╕╨╕?
                    # ╨Э╨╛ ╨╛╨▒╤Л╤З╨╜╨╛ ╨▓ iiko ╨╛╨╜╨╕ ╨┐╤А╨╕╨▓╤П╨╖╤Л╨▓╨░╤О╤В╤Б╤П ╨║ TG. 
                    # ╨Я╤А╨╛╨▒╤Г╨╡╨╝ ╨╜╨░╨╣╤В╨╕ ╨┐╨╡╤А╨▓╤Л╨╣ ╤Д╨╕╨╗╨╕╨░╨╗ ╨║╨░╨║ fallback, ╨╡╤Б╨╗╨╕ ╨╛╨╜ ╨╛╨┤╨╕╨╜.
                    branch = session.exec(select(Branch)).first()
                    logger.warning("restriction_item missing terminalGroupId, using first branch as fallback")
                else:
                    branch = session.exec(select(Branch).where(Branch.iiko_terminal_id == tg_id)).first()
                
                if not branch:
                    logger.warning(f"╨д╨╕╨╗╨╕╨░╨╗ ╤Б iiko_terminal_id {tg_id} ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜ ╨▓ ╨С╨Ф, ╨┐╤А╨╛╨┐╤Г╤Б╨║╨░╨╡╨╝ ╨╛╨│╤А╨░╨╜╨╕╤З╨╡╨╜╨╕╤П")
                    continue

                # 2. ╨б╨╛╨▒╨╕╤А╨░╨╡╨╝ ╨┐╨╛╨╗╨╕╨│╨╛╨╜╤Л ╨╕╨╖ KML ╨┤╨╗╤П ╤Н╤В╨╛╨│╨╛ ╤Д╨╕╨╗╨╕╨░╨╗╨░/╨╛╨│╤А╨░╨╜╨╕╤З╨╡╨╜╨╕╤П
                branch_polygons = {}
                map_url = restriction_item.get("deliveryRegionsMapUrl")
                if map_url:
                    logger.info(f"╨Э╨░╨╣╨┤╨╡╨╜╨░ ╤Б╤Б╤Л╨╗╨║╨░ ╨╜╨░ ╨║╨░╤А╤В╤Г ╨┤╨╗╤П ╤Д╨╕╨╗╨╕╨░╨╗╨░ {branch.name}: {map_url}. ╨Ч╨░╨│╤А╤Г╨╢╨░╨╡╨╝ ╨┐╨╛╨╗╨╕╨│╨╛╨╜╤Л...")
                    try:
                        kml_zones = await iiko_service.fetch_and_parse_kml(map_url)
                        for kz in kml_zones:
                            # ╨б╨╛╤Е╤А╨░╨╜╤П╨╡╨╝ ╨┐╨╛╨╗╨╕╨│╨╛╨╜ ╨┐╨╛ ╨╕╨╝╨╡╨╜╨╕ ╨╖╨╛╨╜╤Л (╨▓ ╨╜╨╕╨╢╨╜╨╡╨╝ ╤А╨╡╨│╨╕╤Б╤В╤А╨╡ ╨┤╨╗╤П ╤Б╨╛╨┐╨╛╤Б╤В╨░╨▓╨╗╨╡╨╜╨╕╤П)
                            name_key = kz["name"].lower().strip()
                            branch_polygons[name_key] = kz["coordinates"]
                            logger.info(f"╨Ч╨░╨│╤А╤Г╨╢╨╡╨╜╨░ ╨│╨╡╨╛╨╝╨╡╤В╤А╨╕╤П ╨┤╨╗╤П ╨╖╨╛╨╜╤Л '{kz['name']}' ╨╕╨╖ iiko-╨║╨░╤А╤В╤Л")
                    except Exception as e:
                        logger.error(f"╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╨╖╨░╨│╤А╤Г╨╖╨║╨╡ ╨┐╨╛╨╗╨╕╨│╨╛╨╜╨╛╨▓ ╨┤╨╗╤П ╤Д╨╕╨╗╨╕╨░╨╗╨░ {branch.name}: {e}")

                # 3. ╨Ю╨▒╤А╨░╨▒╨░╤В╤Л╨▓╨░╨╡╨╝ ╨╖╨╛╨╜╤Л ╨▓╨╜╤Г╤В╤А╨╕ ╨╛╨│╤А╨░╨╜╨╕╤З╨╡╨╜╨╕╨╣
                for res in restriction_item.get("restrictions", []):
                    zone_name = res.get("zone")
                    if not zone_name:
                        continue
                        
                    min_sum = float(res.get("minSum") or 0)
                    delivery_cost = float(res.get("deliveryPrice") or 0)
                    
                    # ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╨╝ zoneId ╨╕╨╖ iiko ╨╡╤Б╨╗╨╕ ╨╡╤Б╤В╤М, ╨╕╨╜╨░╤З╨╡ ╨╕╨╝╤П
                    iiko_zone_id = res.get("zoneId") or zone_name
                    
                    # ╨Ш╤Й╨╡╨╝ ╨╖╨╛╨╜╤Г ╨┤╨╗╤П ╨║╨╛╨╜╨║╤А╨╡╤В╨╜╨╛╨│╨╛ ╤Д╨╕╨╗╨╕╨░╨╗╨░
                    zone = session.exec(select(DeliveryZone).where(
                        (DeliveryZone.branch_id == branch.id) & 
                        ((DeliveryZone.iiko_id == iiko_zone_id) | (DeliveryZone.name == zone_name))
                    )).first()
                    
                    if not zone:
                        logger.info(f"╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡ ╨╜╨╛╨▓╨╛╨╣ ╨╖╨╛╨╜╤Л ╨┤╨╛╤Б╤В╨░╨▓╨║╨╕ '{zone_name}' ╨┤╨╗╤П ╤Д╨╕╨╗╨╕╨░╨╗╨░ {branch.name}")
                        zone = DeliveryZone(
                            name=zone_name, 
                            branch_id=branch.id, 
                            iiko_id=iiko_zone_id
                        )
                        session.add(zone)
                        session.flush() # ╨Я╨╛╨╗╤Г╤З╨░╨╡╨╝ ID
                    
                    # ╨Ю╨▒╨╜╨╛╨▓╨╗╤П╨╡╨╝ ╨┐╨░╤А╨░╨╝╨╡╤В╤А╤Л ╨╖╨╛╨╜╤Л
                    zone.iiko_id = iiko_zone_id
                    zone.min_order_amount = min_sum
                    zone.delivery_cost = delivery_cost
                    zone.min_delivery_time = res.get("minDeliveryTime")
                    zone.max_delivery_time = res.get("maxDeliveryTime")
                    zone.free_delivery_sum = float(res.get("freeDeliverySum") or 0) if res.get("freeDeliverySum") is not None else None
                    zone.priority = int(res.get("priority") or 0)
                    zone.is_default = bool(res.get("isDefault"))
                    zone.updated_at = datetime.now(timezone.utc)
                    zone.is_active = True
                    
                    # 4. ╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨╕╤А╤Г╨╡╨╝ ╨│╨╡╨╛╨╝╨╡╤В╤А╨╕╤О ╨▓ CustomPolygon
                    zone_key = zone_name.lower().strip()
                    if zone_key in branch_polygons:
                        coords = branch_polygons[zone_key]
                        # ╨Ш╤Й╨╡╨╝ ╤Б╤Г╤Й╨╡╤Б╤В╨▓╤Г╤О╤Й╨╕╨╣ ╨┐╨╛╨╗╨╕╨│╨╛╨╜ ╨┤╨╗╤П ╤Н╤В╨╛╨╣ ╨╖╨╛╨╜╤Л
                        poly = session.exec(select(CustomPolygon).where(
                            CustomPolygon.delivery_zone_id == zone.id
                        )).first()
                        
                        if not poly:
                            poly = CustomPolygon(
                                name=zone.name,
                                delivery_zone_id=zone.id,
                                branch_id=branch.id,
                                coordinates=coords,
                                fill_color="#4caf50",
                                priority=zone.priority,
                                min_order_amount=zone.min_order_amount,
                                delivery_cost=zone.delivery_cost,
                                is_active=True
                            )
                            session.add(poly)
                            logger.info(f"╨б╨╛╨╖╨┤╨░╨╜ ╨╜╨╛╨▓╤Л╨╣ ╨┐╨╛╨╗╨╕╨│╨╛╨╜ ╨┤╨╗╤П ╨╖╨╛╨╜╤Л '{zone.name}'")
                        else:
                            # ╨Ю╨▒╨╜╨╛╨▓╨╗╤П╨╡╨╝ ╨║╨╛╨╛╤А╨┤╨╕╨╜╨░╤В╤Л ╨╕ ╨┐╨░╤А╨░╨╝╨╡╤В╤А╤Л
                            poly.coordinates = coords
                            poly.priority = zone.priority
                            poly.min_order_amount = zone.min_order_amount
                            poly.delivery_cost = zone.delivery_cost
                            poly.is_active = True
                            session.add(poly)
                            logger.info(f"╨Ю╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨░ ╨│╨╡╨╛╨╝╨╡╤В╤А╨╕╤П ╨╕ ╨┐╨░╤А╨░╨╝╨╡╤В╤А╤Л ╨┐╨╛╨╗╨╕╨│╨╛╨╜╨░ ╨┤╨╗╤П ╨╖╨╛╨╜╤Л '{zone.name}'")
                        
                        # ╨б╨╛╤Е╤А╨░╨╜╤П╨╡╨╝ ╨╕ ╨▓ ╤В╨╡╨║╤Б╤В╨╛╨▓╨╛╨╡ ╨┐╨╛╨╗╨╡ ╨╖╨╛╨╜╤Л (╨┤╨╗╤П ╤Б╨╛╨▓╨╝╨╡╤Б╤В╨╕╨╝╨╛╤Б╤В╨╕)
                        zone.polygon_coordinates = json.dumps(coords)
                    
                    zone.additional_info = res
                    session.add(zone)
                    synced_count += 1
                
            session.commit()
            logger.info(f"╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨╛╨│╤А╨░╨╜╨╕╤З╨╡╨╜╨╕╨╣ ╨┤╨╛╤Б╤В╨░╨▓╨║╨╕ ╨╖╨░╨▓╨╡╤А╤И╨╡╨╜╨░: {synced_count} ╨╖╨╛╨╜")
            return {"success": True, "synced": synced_count, "message": f"Successfully synced {synced_count} zones"}
            
        except Exception as e:
            session.rollback()
            logger.error(f"╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╨╕ ╨╛╨│╤А╨░╨╜╨╕╤З╨╡╨╜╨╕╨╣ ╨┤╨╛╤Б╤В╨░╨▓╨║╨╕ iiko: {e}", exc_info=True)
            return {"error": str(e)}

    async def get_available_iiko_zones(self, session: Session) -> List[Dict[str, Any]]:
        """╨Я╨╛╨╗╤Г╤З╨░╨╡╤В ╤Б╨┐╨╕╤Б╨╛╨║ ╨▓╤Б╨╡╤Е ╨┤╨╛╤Б╤В╤Г╨┐╨╜╤Л╤Е ╨╖╨╛╨╜ ╨╕╨╖ iiko Cloud (╨▒╨╡╨╖ ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╤П)"""
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db or not settings_db.organization_id:
            return []
            
        try:
            data = await iiko_service.get_delivery_restrictions(
                api_login=settings_db.api_login,
                organization_id=settings_db.organization_id
            )
            
            unique_zones = {}
            for org_data in data:
                for res in org_data.get("restrictions", []):
                    z_name = res.get("zone")
                    z_id = res.get("zoneId") or z_name
                    if z_name and z_id not in unique_zones:
                        unique_zones[z_id] = {
                            "iiko_id": z_id,
                            "name": z_name
                        }
            
            return list(unique_zones.values())
        except Exception as e:
            logger.error(f"Failed to fetch iiko zones list: {e}")
            return []

    async def sync_payment_types(self, session: Session) -> Dict[str, Any]:
        """╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╤В╨╕╨┐╨╛╨▓ ╨╛╨┐╨╗╨░╤В╤Л ╨╕╨╖ iiko Cloud"""
        from app.models.payment_type import PaymentType
        
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db or not settings_db.organization_id:
            return {"error": "Iiko not configured"}
            
        try:
            print(f"DEBUG: Calling iiko_service.get_payment_types with login: {settings_db.api_login}", flush=True)
            payment_types = await iiko_service.get_payment_types(
                api_login=settings_db.api_login,
                organization_id=settings_db.organization_id
            )
            
            synced_count = 0
            logger.info(f"╨Э╨░╤З╨╕╨╜╨░╤О ╨╛╨▒╤А╨░╨▒╨╛╤В╨║╤Г {len(payment_types)} ╤В╨╕╨┐╨╛╨▓ ╨╛╨┐╨╗╨░╤В╤Л ╨╕╨╖ iiko")
            for pt in payment_types:
                pt_id = pt.get("id")
                if not pt_id: continue
                
                existing = session.exec(select(PaymentType).where(PaymentType.iiko_id == pt_id)).first()
                if existing:
                    existing.name = pt.get("name") or existing.name
                    existing.kind = pt.get("paymentTypeKind") or existing.kind
                    existing.updated_at = datetime.now(timezone.utc)
                    session.add(existing)
                else:
                    new_pt = PaymentType(
                        iiko_id=pt_id,
                        name=pt.get("name"),
                        kind=pt.get("paymentTypeKind"),
                        is_active=True # ╨Т╨Р╨Ц╨Э╨Ю! ╨Ш╨╜╨░╤З╨╡ ╨╛╨╜╨╕ ╨┐╤А╨╛╨┐╨░╨┤╤Г╤В ╨┐╤А╨╕ F5
                    )
                    session.add(new_pt)
                synced_count += 1
            
            logger.info(f"╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨╖╨░╨▓╨╡╤А╤И╨╡╨╜╨░. ╨Т╤Б╨╡╨│╨╛: {synced_count}")
            session.commit()
            return {"status": "success", "synced_count": synced_count}
        except Exception as e:
            logger.error(f"Payment types sync failed: {e}")
            session.rollback()
            return {"error": str(e)}


    async def sync_stop_lists(self, session: Session = None):
        """╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╤Б╤В╨╛╨┐-╨╗╨╕╤Б╤В╨╛╨▓"""
        # ╨Ы╨╛╨│╨╕╨║╨░ ╤Б╤В╨╛╨┐-╨╗╨╕╤Б╤В╨╛╨▓
        pass

    async def sync_employees_full(self, session: Session, days: int = 7) -> None:
        """
        ╨Я╨╛╨╗╨╜╨░╤П ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╤Б╨╛╤В╤А╤Г╨┤╨╜╨╕╨║╨╛╨▓ ╨╕ ╨╕╤Е ╤Б╨╝╨╡╨╜ ╤З╨╡╤А╨╡╨╖ iiko RESTO (Office) API.
        """
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db or not settings_db.resto_url:
            logger.error("╨Э╨░╤Б╤В╤А╨╛╨╣╨║╨╕ iiko Resto (Office) ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜╤Л. ╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨╛╤В╨╝╨╡╨╜╨╡╨╜╨░.")
            return

        tz = self._get_tz(session)
        now_local = datetime.now(tz)
        date_from = now_local - timedelta(days=days)

        # --- ╨и╨░╨│ 1: ╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨┐╤А╨╛╤Д╨╕╨╗╨╡╨╣ ╤Б╨╛╤В╤А╤Г╨┤╨╜╨╕╨║╨╛╨▓ ---
        # ╨Я╨░╤А╨░╨╝╨╡╤В╤А╤Л ╨┐╨╛╨┤╨║╨╗╤О╤З╨╡╨╜╨╕╤П ╨▒╨╡╤А╨╡╨╝ ╨╕╨╖ ╨С╨Ф, ╨░ ╨╜╨╡ ╨╕╨╖ ENV
        r_url = settings_db.resto_url
        r_login = settings_db.resto_login
        r_password = settings_db.resto_password
        try:
            logger.info("╨Ч╨░╨┐╤А╨╛╤Б ╤Б╨┐╨╕╤Б╨║╨░ ╤Б╨╛╤В╤А╤Г╨┤╨╜╨╕╨║╨╛╨▓ ╨╕╨╖ iiko Resto...")
            iiko_employees = await iiko_service.get_resto_employees(
                resto_url=r_url, resto_login=r_login, resto_password=r_password
            )
            
            for emp in iiko_employees:
                emp_iiko_id = emp.get("id")
                if not emp_iiko_id: continue
                
                name = emp.get("name") or f"{emp.get('firstName', '')} {emp.get('lastName', '')}".strip()
                role = emp.get("role")
                rate = emp.get("salary")
                
                # ╨Ф╨╛╨║╤Г╨╝╨╡╨╜╤В╤Л ╨╕ ╨┤╨╛╨┐. ╨╕╨╜╤Д╨╛
                doc_info = {
                    "inn": emp.get("inn"),
                    "snils": emp.get("snils"),
                    "code": emp.get("code"),
                    "cardNumber": emp.get("cardNumber"),
                    "birthday": emp.get("birthday")
                }
                
                existing = session.exec(
                    select(Employee).where(Employee.iiko_id == emp_iiko_id)
                ).first()
                
                def _flag_courier(r, n=""):
                    r_l = (r or "").lower()
                    n_l = (n or "").lower()
                    return ("╨║╤Г╤А╤М╨╡╤А" in r_l or "courier" in r_l or r_l in ["cur", "cour"]
                            or "╨║╤Г╤А╤М╨╡╤А" in n_l or "courier" in n_l)
                def _flag_admin(r, n=""):
                    r_l = (r or "").lower()
                    return any(k in r_l for k in ["╨░╨┤╨╝╨╕╨╜╨╕╤Б╤В╤А╨░╤В╨╛╤А", "╨╛╨┐╨╡╤А╨░╤В╨╛╤А", "manager", "╤Б╤В╨░╤А╤И╨╕╨╣", "adm", "admin"])

                if existing:
                    existing.name = name
                    existing.role = role or existing.role
                    existing.phone = emp.get("phone") or existing.phone
                    existing.email = emp.get("email") or existing.email
                    existing.address = emp.get("address") or existing.address
                    existing.rate = rate if rate is not None else existing.rate
                    existing.document_info = doc_info
                    existing.name = name  # ╨Ю╨▒╨╜╨╛╨▓╨╗╤П╨╡╨╝ ╨╕╨╝╤П, ╨╡╤Б╨╗╨╕ ╨╛╨╜╨╛ ╨╕╨╖╨╝╨╡╨╜╨╕╨╗╨╛╤Б╤М ╨▓ iiko
                    existing.status = "Deleted" if emp.get("deleted") else "Active"
                    existing.is_courier = _flag_courier(existing.role, name)
                    existing.is_admin = _flag_admin(existing.role)
                    existing.updated_at = datetime.now(timezone.utc)
                    session.add(existing)
                else:
                    new_emp = Employee(
                        iiko_id=emp_iiko_id,
                        name=name,
                        role=role,
                        phone=emp.get("phone"),
                        email=emp.get("email"),
                        address=emp.get("address"),
                        rate=rate or 0.0,
                        document_info=doc_info,
                        status="Deleted" if emp.get("deleted") else "Active",
                        is_courier=_flag_courier(role, name),
                        is_admin=_flag_admin(role),
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    session.add(new_emp)
            
            session.commit()
            logger.info(f"╨г╤Б╨┐╨╡╤И╨╜╨╛ ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨╕╤А╨╛╨▓╨░╨╜╨╛ {len(iiko_employees)} ╨┐╤А╨╛╤Д╨╕╨╗╨╡╨╣ ╤Б╨╛╤В╤А╤Г╨┤╨╜╨╕╨║╨╛╨▓ ╨╕╨╖ iiko Resto")
        except Exception as e:
            logger.error(f"╨Ю╤И╨╕╨▒╨║╨░ ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╨╕ ╨┐╤А╨╛╤Д╨╕╨╗╨╡╨╣: {e}")
            session.rollback()

        # --- ╨и╨░╨│ 1.5: ╨Ф╨╛╨┐╨╛╨╗╨╜╨╡╨╜╨╕╨╡ ╨┤╨░╨╜╨╜╤Л╨╝╨╕ ╨╕╨╖ iiko Cloud (╨Ю╨в╨Ъ╨Ы╨о╨з╨Х╨Э╨Ю ╨┐╨╛ ╤В╤А╨╡╨▒╨╛╨▓╨░╨╜╨╕╤О ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П - ╤Б╤В╨░╤А╨╛╨│╨╛ Server API) ---
        # try:
        #     logger.info("╨Ч╨░╨┐╤А╨╛╤Б ╨┤╨╛╨┐╨╛╨╗╨╜╨╕╤В╨╡╨╗╤М╨╜╤Л╤Е ╨┤╨░╨╜╨╜╤Л╤Е ╨╕╨╖ iiko Cloud...")
        #     cloud_employees = await iiko_service.get_employees(api_login=settings_db.api_login, organization_id=settings_db.organization_id)
        #     updated_cloud_c = 0
        #     for c_emp in cloud_employees:
        #         emp_iiko_id = c_emp.get("id")
        #         if not emp_iiko_id: continue
        #         
        #         existing = session.exec(select(Employee).where(Employee.iiko_id == emp_iiko_id)).first()
        #         # ╨Х╤Б╨╗╨╕ ╤Б╨╛╤В╤А╤Г╨┤╨╜╨╕╨║╨░ ╨╜╨╡╤В ╨╕╨╖ Resto, ╨╜╨╛ ╨╛╨╜ ╨╡╤Б╤В╤М ╨▓ Cloud (╨╜╨░╨┐╤А╨╕╨╝╨╡╤А, ╨▓╨╜╨╡╤И╨╜╨╕╨╣ ╨║╤Г╤А╤М╨╡╤А)
        #         if not existing:
        #             role = ""
        #             if c_emp.get("isCourier"): role = "╨Ъ╤Г╤А╤М╨╡╤А (Cloud)"
        #             
        #             new_emp = Employee(
        #                 iiko_id=emp_iiko_id,
        #                 name=c_emp.get("name", "Unknown"),
        #                 role=role,
        #                 phone=c_emp.get("phone"),
        #                 status="Active",
        #                 is_courier=c_emp.get("isCourier", False),
        #                 created_at=datetime.now(timezone.utc),
        #                 updated_at=datetime.now(timezone.utc)
        #             )
        #             session.add(new_emp)
        #             updated_cloud_c += 1
        #         else:
        #             # ╨Ф╨╛╨┐╨╛╨╗╨╜╤П╨╡╨╝ ╨┤╨░╨╜╨╜╤Л╨╡, ╨╡╤Б╨╗╨╕ ╨╕╤Е ╨╜╨╡╤В
        #             if c_emp.get("isCourier") and not existing.is_courier:
        #                 existing.is_courier = True
        #                 session.add(existing)
        #                 updated_cloud_c += 1
        #     session.commit()
        #     logger.info(f"╨г╤Б╨┐╨╡╤И╨╜╨╛ ╨┤╨╛╨┐╨╛╨╗╨╜╨╡╨╜╨╛ {updated_cloud_c} ╨┐╤А╨╛╤Д╨╕╨╗╨╡╨╣ ╨╕╨╖ iiko Cloud")
        # except Exception as e:
        #     logger.error(f"╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╨╕ ╨┐╤А╨╛╤Д╨╕╨╗╨╡╨╣ ╨╕╨╖ Cloud: {e}")
        #     session.rollback()

        # --- ╨и╨░╨│ 2: ╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨╕╤Б╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╨╜╨╕╤П ╤Б╨╝╨╡╨╜ ╤З╨╡╤А╨╡╨╖ Attendance API ---
        try:
            logger.info(f"╨Ч╨░╨┐╤А╨╛╤Б ╤П╨▓╨╛╨║ (╤Б╨╝╨╡╨╜) ╤З╨╡╤А╨╡╨╖ Attendance API ({date_from.date()} - {now_local.date()})...")
            attendance_records = await iiko_service.get_resto_attendance(
                resto_url=r_url, resto_login=r_login, resto_password=r_password,
                date_from=date_from, date_to=now_local,
                log_error=False
            )

            def _parse_to_utc(s):
                if not s: return None
                try:
                    # ╨д╨╛╤А╨╝╨░╤В ISO 8601 ╤Б ╤В╨░╨╣╨╝╨╖╨╛╨╜╨╛╨╣ (╨╜╨░╨┐╤А╨╕╨╝╨╡╤А 2026-04-11T10:17:00+05:00)
                    return datetime.fromisoformat(str(s)).astimezone(timezone.utc)
                except Exception:
                    return None

            created_c, updated_c = 0, 0
            for row in attendance_records:
                emp_iiko_id = row.get("employeeId")
                if not emp_iiko_id:
                    continue

                employee = session.exec(select(Employee).where(Employee.iiko_id == emp_iiko_id)).first()
                if not employee:
                    # logger.debug(f"Attendance: ╨б╨╛╤В╤А╤Г╨┤╨╜╨╕╨║ ╤Б ID '{emp_iiko_id}' ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜ ╨▓ ╨С╨Ф")
                    continue

                date_open = _parse_to_utc(row.get("dateOpen"))
                date_close = _parse_to_utc(row.get("dateClose"))
                if not date_open:
                    continue

                if not date_close:
                    now_utc = datetime.now(timezone.utc)
                    work_hours = (now_utc - date_open).total_seconds() / 3600.0
                else:
                    work_hours = (date_close - date_open).total_seconds() / 3600.0

                # ╨Ю╨│╤А╨░╨╜╨╕╤З╨╕╨▓╨░╨╡╨╝ ╨╝╨░╨║╤Б╨╕╨╝╨░╨╗╤М╨╜╤Г╤О ╨┤╨╗╨╕╤В╨╡╨╗╤М╨╜╨╛╤Б╤В╤М ╤Б╨╝╨╡╨╜╤Л (╨╝╨░╨║╤Б 24 ╤З╨░╤Б╨░)
                work_hours = min(work_hours, 24.0)

                # ╨г╨╜╨╕╨║╨░╨╗╤М╨╜╤Л╨╣ ╨║╨╗╤О╤З
                shift_iiko_id = row.get("id")
                if not shift_iiko_id:
                     shift_iiko_id = f"att_{employee.id}_{date_open.strftime('%Y%m%d%H%M')}"

                # ╨Я╨╛╨╕╤Б╨║ ╨▓╤Л╤А╤Г╤З╨║╨╕ ╨┐╤А╨╕ ╨╖╨░╨║╤А╤Л╤В╨╕╨╕ (╨╕╨╖ ╨╖╨░╨│╤А╤Г╨╢╨╡╨╜╨╜╤Л╤Е ╨╛╤В╤З╨╡╤В╨╛╨▓ OLAP)
                revenue_at_close = 0.0
                if date_close:
                    biz_date_str = date_open.astimezone(tz).strftime("%Y-%m-%d")
                    # ╨С╨╡╤А╨╡╨╝ ╨▓╤Л╤А╤Г╤З╨║╤Г ╨╖╨░ ╨▒╨╕╨╖╨╜╨╡╤Б-╨┤╨╡╨╜╤М ╨╛╤В╨║╤А╤Л╤В╨╕╤П ╤Б╨╝╨╡╨╜╤Л
                    rev_record = session.exec(
                        select(OlapRevenueRecord)
                        .where(OlapRevenueRecord.business_date == biz_date_str)
                        .order_by(OlapRevenueRecord.updated_at.desc())
                    ).first()
                    if rev_record:
                        revenue_at_close = rev_record.revenue

                existing_shift = session.exec(
                    select(Shift).where(Shift.iiko_id == shift_iiko_id)
                ).first()

                if existing_shift:
                    existing_shift.date_close = date_close
                    existing_shift.status = "CLOSED" if date_close else "OPEN"
                    existing_shift.work_hours = round(work_hours, 2)
                    # ╨Ю╨▒╨╜╨╛╨▓╨╗╤П╨╡╨╝ ╨▓╤Л╤А╤Г╤З╨║╤Г ╤В╨╛╨╗╤М╨║╨╛ ╨╡╤Б╨╗╨╕ ╨╛╨╜╨░ ╨╡╤Й╨╡ ╨╜╨╡ ╨▒╤Л╨╗╨░ ╤Г╤Б╤В╨░╨╜╨╛╨▓╨╗╨╡╨╜╨░
                    if date_close and (not existing_shift.revenue_at_close or existing_shift.revenue_at_close == 0):
                        existing_shift.revenue_at_close = revenue_at_close
                    existing_shift.updated_at = datetime.now(timezone.utc)
                    session.add(existing_shift)
                    updated_c += 1
                else:
                    new_shift = Shift(
                        iiko_id=shift_iiko_id,
                        employee_id=employee.id,
                        date_open=date_open,
                        date_close=date_close,
                        status="CLOSED" if date_close else "OPEN",
                        work_hours=round(work_hours, 2),
                        cancelled_orders_count=0,
                        revenue_at_close=revenue_at_close,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    session.add(new_shift)
                    created_c += 1

            session.commit()
            logger.info(f"╨г╤Б╨┐╨╡╤И╨╜╨╛: Attendance ╤Б╨╝╨╡╨╜╤Л: ╤Б╨╛╨╖╨┤╨░╨╜╨╛ {created_c}, ╨╛╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╛ {updated_c} ╨╕╨╖ {len(attendance_records)} ╨╖╨░╨┐╨╕╤Б╨╡╨╣")
        except Exception as e:
            logger.error(f"╨Ю╤И╨╕╨▒╨║╨░ ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╨╕ Attendance ╤Б╨╝╨╡╨╜: {e}", exc_info=True)
            session.rollback()

        # --- ╨и╨░╨│ 3 (╨г╨┤╨░╨╗╨╡╨╜): ╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╤З╨╡╤А╨╡╨╖ personalSessions ╨▓╨╖╨░╨╝╨╡╨╜ Attendance ---
        # ╨Ы╨╕╤З╨╜╤Л╨╡ ╤Б╨╝╨╡╨╜╤Л ╨╛╨▒╤А╨░╨▒╨░╤В╤Л╨▓╨░╤О╤В╤Б╤П ╨▓ ╨и╨░╨│╨╡ 2 ╤З╨╡╤А╨╡╨╖ Attendance API,
        # ╨┐╨╛╤Н╤В╨╛╨╝╤Г ╨▓╤Л╨╖╨╛╨▓ personalSessions ╨╖╨┤╨╡╤Б╤М ╨╜╨╡ ╨╜╤Г╨╢╨╡╨╜ (╨╛╨╜ ╨┤╤Г╨▒╨╗╨╕╤А╤Г╨╡╤В ╨╕ ╨▓╤Л╨┤╨░╨╡╤В 404).
        pass

    async def get_employee_stats(self, session: Session, employee_id: int, mode: str = "calendar") -> Dict[str, Any]:
        """
        ╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤Б╤В╨░╤В╨╕╤Б╤В╨╕╨║╨╕ ╤Б╨╛╤В╤А╤Г╨┤╨╜╨╕╨║╨░ ╨╖╨░ ╨┐╨╡╤А╨╕╨╛╨┤.
        mode: 'calendar' (╤В╨╡╨║╤Г╤Й╨░╤П ╨╜╨╡╨┤╨╡╨╗╤П) ╨╕╨╗╨╕ 'sliding' (╨┐╨╛╤Б╨╗╨╡╨┤╨╜╨╕╨╡ 7 ╨┤╨╜╨╡╨╣)
        """
        tz = self._get_tz(session)
        now_local = datetime.now(tz)
        
        if mode == "calendar":
            # ╨б ╨┐╨╛╨╜╨╡╨┤╨╡╨╗╤М╨╜╨╕╨║╨░ ╤В╨╡╨║╤Г╤Й╨╡╨╣ ╨╜╨╡╨┤╨╡╨╗╨╕
            start_date = (now_local - timedelta(days=now_local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now_local
        else:
            # ╨Я╨╛╤Б╨╗╨╡╨┤╨╜╨╕╨╡ 7 ╨┤╨╜╨╡╨╣
            start_date = (now_local - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now_local
            
        # ╨Ч╨░╨│╤А╤Г╨╢╨░╨╡╨╝ ╤Б╨╝╨╡╨╜╤Л ╨╕╨╖ ╨С╨Ф
        shifts = session.exec(
            select(Shift)
            .where(Shift.employee_id == employee_id)
            .where(Shift.date_open >= start_date.astimezone(timezone.utc))
            .order_by(Shift.date_open.desc())
        ).all()
        
        total_hours = sum(s.work_hours for s in shifts if s.work_hours)
        total_revenue = sum(float(s.revenue_at_close or 0) for s in shifts)
        
        # ╨У╤А╤Г╨┐╨┐╨╕╤А╨╛╨▓╨║╨░ ╨┐╨╛ ╨┤╨╜╤П╨╝
        daily_stats = {}
        for s in shifts:
            # ╨Я╨╡╤А╨╡╨▓╨╛╨┤╨╕╨╝ ╨▓╤А╨╡╨╝╤П ╨╛╤В╨║╤А╤Л╤В╨╕╤П ╨▓ ╨╗╨╛╨║╨░╨╗╤М╨╜╨╛╨╡ ╨┤╨╗╤П ╨│╤А╤Г╨┐╨┐╨╕╤А╨╛╨▓╨║╨╕ ╨┐╨╛ ╨┤╨░╤В╨░╨╝
            s_open_local = s.date_open.astimezone(tz)
            day_key = s_open_local.date().isoformat()
            
            if day_key not in daily_stats:
                daily_stats[day_key] = {
                    "date": day_key,
                    "total_hours": 0.0,
                    "shifts_count": 0,
                    "revenue": 0.0,
                    "shifts": []
                }
            daily_stats[day_key]["total_hours"] += float(s.work_hours or 0)
            daily_stats[day_key]["shifts_count"] += 1
            daily_stats[day_key]["revenue"] += float(s.revenue_at_close or 0)
            
            # ╨д╨╛╤А╨╝╨╕╤А╤Г╨╡╨╝ ╨╛╨▒╤К╨╡╨║╤В ╤Б╨╝╨╡╨╜╤Л ╨┤╨╗╤П ╤Д╤А╨╛╨╜╤В╨╡╨╜╨┤╨░
            shift_info = {
                "id": s.id,
                "open": s_open_local.isoformat(),
                "close": s.date_close.astimezone(tz).isoformat() if s.date_close else None,
                "status": s.status,
                "hours": round(s.work_hours, 2) if s.work_hours else 0,
                "revenue": float(s.revenue_at_close or 0)
            }
            daily_stats[day_key]["shifts"].append(shift_info)
            
        return {
            "total_hours_period": round(total_hours, 2),
            "total_shifts": len(shifts),
            "total_revenue": round(total_revenue, 2),
            "daily_stats": sorted(daily_stats.values(), key=lambda x: x["date"], reverse=True)
        }

    async def sync_courier_deliveries(self, session: Session, days: int = 14, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> None:
        from app.models.order import Order
        """
        ╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨┤╨╡╤В╨░╨╗╤М╨╜╤Л╤Е ╨┤╨╛╤Б╤В╨░╨▓╨╛╨║ ╨║╤Г╤А╤М╨╡╤А╨╛╨▓ ╨╕╨╖ iiko Resto OLAP.
        ╨Ч╨░╨┐╨╛╨╗╨╜╤П╨╡╤В ╤В╨░╨▒╨╗╨╕╤Ж╤Г courier_orders: ╨╖╨╛╨╜╤Л, ╤Б╤Г╨╝╨╝╤Л, ╨▓╤А╨╡╨╝╨╡╨╜╨╜╤Л╨╡ ╨╝╨╡╤В╨║╨╕, ╨╖╨░╨┤╨╡╤А╨╢╨║╨╕.
        """
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db or not settings_db.resto_url:
            logger.warning("Resto ╨╜╨╡ ╨╜╨░╤Б╤В╤А╨╛╨╡╨╜, ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨┤╨╛╤Б╤В╨░╨▓╨╛╨║ ╨┐╤А╨╛╨┐╤Г╤Й╨╡╨╜╨░")
            return

        tz = self._get_tz(session)
        now_local = datetime.now(tz)
        
        if not date_from:
            date_from = now_local - timedelta(days=days)
        if not date_to:
            date_to = now_local

        logger.info(f"╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨┤╨╛╤Б╤В╨░╨▓╨╛╨║ ╨║╤Г╤А╤М╨╡╤А╨╛╨▓ ╨╕╨╖ Resto OLAP ({date_from} ╨┤╨╛ {date_to})...")

        try:
            deliveries = await iiko_service.get_resto_detailed_deliveries(
                date_from=date_from,
                date_to=date_to,
                organization_id=settings_db.organization_id or "",
                resto_url=settings_db.resto_url,
                resto_login=settings_db.resto_login,
                resto_password=settings_db.resto_password
            )
            logger.info(f"Fetched {len(deliveries)} deliveries from OLAP")
        except Exception as e:
            logger.error(f"╨Ю╤И╨╕╨▒╨║╨░ ╨┐╨╛╨╗╤Г╤З╨╡╨╜╨╕╤П ╨┤╨╛╤Б╤В╨░╨▓╨╛╨║ ╨╕╨╖ Resto OLAP: {e}")
            return

        # ╨Ъ╤Н╤И ╨║╤Г╤А╤М╨╡╤А╨╛╨▓ ╨┐╨╛ ╨╕╨╝╨╡╨╜╨╕ ╨╕ ╨┐╨╛ ID
        all_employees = session.exec(select(Employee)).all()
        courier_by_name: Dict[str, Employee] = {}
        courier_by_id: Dict[str, Employee] = {}
        for emp in all_employees:
            # ╨г╤З╨╕╤В╤Л╨▓╨░╨╡╨╝ ╤Д╨╗╨░╨│ is_courier ╨╕ ╤А╨░╨╖╨╗╨╕╤З╨╜╤Л╨╡ ╨╜╨░╨┐╨╕╤Б╨░╨╜╨╕╤П ╤А╨╛╨╗╨╡╨╣
            is_c = emp.is_courier or any(k in (emp.role or "").lower() for k in ["╨║╤Г╤А╤М╨╡╤А", "courier", "cur"])
            if is_c:
                courier_by_name[(emp.name or "").lower().strip()] = emp
                if emp.iiko_id:
                    courier_by_id[emp.iiko_id] = emp

        def _parse_dt(s):
            if not s: return None
            try:
                s_str = str(s)
                if 'T' in s_str:
                    s_c = s_str.replace("T", " ").split(".")[0]
                else:
                    s_c = s_str.split(".")[0]
                dt = datetime.fromisoformat(s_c)
                return dt.replace(tzinfo=tz).astimezone(timezone.utc).replace(tzinfo=None)
            except Exception:
                return None

        created_count, updated_count = 0, 0
        for d in deliveries:
            order_num = str(d.get("id") or "").strip()
            if not order_num:
                continue

            # ╨Ш╤Й╨╡╨╝ ╨║╤Г╤А╤М╨╡╤А╨░ ╨┐╨╛ ID ╨╕╨╗╨╕ ╨┐╨╛ ╨╕╨╝╨╡╨╜╨╕
            courier_emp = None
            courier_iiko_id = d.get("Delivery.Courier.Id")
            if courier_iiko_id:
                courier_emp = courier_by_id.get(courier_iiko_id)
            
            if not courier_emp:
                courier_name_raw = (d.get("Delivery.Courier") or "")
                courier_name_key = (courier_name_raw or "").lower().strip()
                courier_emp = courier_by_name.get(courier_name_key)
                
                if not courier_emp:
                    def _get_meaningful_words(name):
                        words = (name or "").lower().split()
                        return {w for w in words if len(w) > 2 and w not in ["╨║╤Г╤А╤М╨╡╤А", "courier", "cur"]}
                    
                    target_words = _get_meaningful_words(courier_name_raw)
                    for key, emp in courier_by_name.items():
                        emp_words = _get_meaningful_words(emp.name)
                        if target_words and emp_words and (target_words & emp_words):
                            courier_emp = emp
                            break

            if not courier_emp:
                db_order = session.exec(
                    select(Order).where(Order.external_number == order_num)
                ).first()
                if db_order and db_order.courier_name and db_order.courier_name != "╨Э╨╡ ╨╜╨░╨╖╨╜╨░╤З╨╡╨╜":
                    c_name_raw = db_order.courier_name
                    c_name_key = (c_name_raw or "").lower().strip()
                    courier_emp = courier_by_name.get(c_name_key)
                    if not courier_emp:
                        target_words = _get_meaningful_words(c_name_raw)
                        for key, emp in courier_by_name.items():
                            emp_words = _get_meaningful_words(emp.name)
                            if target_words and emp_words and (target_words & emp_words):
                                courier_emp = emp
                                break

            if not courier_emp:
                continue

            order_num = str(d.get("id") or "")
            if not order_num:
                continue

            cooking_done = _parse_dt(d.get("whenCookingCompleted"))
            expected_dt = _parse_dt(d.get("expectedDeliveryTime"))
            actual_dt = _parse_dt(d.get("whenDelivered"))

            delay_min = None
            is_late = False
            if expected_dt and actual_dt:
                diff = (actual_dt - expected_dt).total_seconds() / 60
                delay_min = int(diff)
                is_late = diff > 0

            # ╨Х╤Б╨╗╨╕ ╨▓ ╨┤╨╡╤В╨░╨╗╤П╤Е Resto ╨╜╨╡╤В ╨░╨┤╤А╨╡╤Б╨░, ╨┐╤А╨╛╨▒╤Г╨╡╨╝ ╨▓╨╖╤П╤В╤М ╨╡╨│╨╛ ╨╕╨╖ ╨╖╨░╨║╨░╨╖╨░ ╨▓ ╨С╨Ф
            # (Resto OLAP ╨▓╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╤В ╨░╨┤╤А╨╡╤Б ╨╛╨┤╨╜╨╛╨╣ ╤Б╤В╤А╨╛╨║╨╛╨╣)
            addr_parts = d.get("address") or {}
            db_order = session.exec(select(Order).where(Order.external_number == order_num)).first()
            if db_order and db_order.address_parts:
                # ╨Ю╨▒╤К╨╡╨┤╨╕╨╜╤П╨╡╨╝: ╨┤╨░╨╜╨╜╤Л╨╡ ╨╕╨╖ OLAP (╨╡╤Б╨╗╨╕ ╨╡╤Б╤В╤М) ╨┐╤А╨╕╨╛╤А╨╕╤В╨╡╤В╨╜╨╡╨╡, ╨╜╨╛ ╨╡╤Б╨╗╨╕ ╨▓ OLAP ╤З╨╡╨│╨╛-╤В╨╛ ╨╜╨╡╤В, ╨▒╨╡╤А╨╡╨╝ ╨╕╨╖ ╨С╨Ф
                for key, val in db_order.address_parts.items():
                    if not addr_parts.get(key) and val:
                        addr_parts[key] = val
            
            city_name = settings_db.city_name if settings_db else "╨в╤О╨╝╨╡╨╜╤М"
            addr_fmt = (settings_db.address_format or "components") if settings_db else "components"
            address_str = self.format_address(addr_parts, city=city_name, fmt=addr_fmt)
            
            # ╨Ы╨╛╨│╨╕╤А╤Г╨╡╨╝ ╨┤╨╗╤П ╨╛╤В╨╗╨░╨┤╨║╨╕ ╨╡╤Б╨╗╨╕ ╨╜╤Г╨╢╨╜╨╛
            if order_num == "debug_order":
                logger.info(f"DEBUG Address: parts={addr_parts}, fmt={addr_fmt}, result={address_str}")

            ref_date = actual_dt or cooking_done or datetime.now(timezone.utc)
            iiko_uid = f"olap_{order_num}_{ref_date.strftime('%Y%m%d')}"

            existing = session.exec(
                select(CourierOrder).where(CourierOrder.iiko_id == iiko_uid)
            ).first()

            if existing:
                existing.delivery_zone = d.get("deliveryZone") or existing.delivery_zone
                existing.amount = float(d.get("sum") or 0) or existing.amount
                existing.cooking_completed_at = cooking_done or existing.cooking_completed_at
                existing.expected_delivery_time = expected_dt or existing.expected_delivery_time
                existing.actual_delivery_time = actual_dt or existing.actual_delivery_time
                existing.delay_minutes = delay_min
                existing.is_late = is_late
                existing.address = address_str or existing.address
                existing.address_parts = addr_parts
                existing.customer_name = (d.get("customer") or {}).get("name") or existing.customer_name
                existing.customer_phone = (d.get("customer") or {}).get("phone") or existing.customer_phone
                existing.close_time = actual_dt
                existing.updated_at = datetime.now(timezone.utc)
                session.add(existing)
                updated_count += 1
            else:
                new_order = CourierOrder(
                    iiko_id=iiko_uid,
                    order_num=order_num,
                    employee_id=courier_emp.id,
                    address=address_str,
                    address_parts=addr_parts,
                    delivery_zone=d.get("deliveryZone"),
                    amount=float(d.get("sum") or 0),
                    created_at_iiko=cooking_done,
                    cooking_completed_at=cooking_done,
                    expected_delivery_time=expected_dt,
                    actual_delivery_time=actual_dt,
                    close_time=actual_dt,
                    delay_minutes=delay_min,
                    is_late=is_late,
                    customer_name=(d.get("customer") or {}).get("name"),
                    customer_phone=(d.get("customer") or {}).get("phone"),
                    updated_at=datetime.now(timezone.utc)
                )
                session.add(new_order)
                created_count += 1
        
        try:
            session.commit()
            logger.info(f"╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨┤╨╛╤Б╤В╨░╨▓╨╛╨║ ╨║╤Г╤А╤М╨╡╤А╨╛╨▓ ╨╖╨░╨▓╨╡╤А╤И╨╡╨╜╨░: {created_count} ╤Б╨╛╨╖╨┤╨░╨╜╨╛, {updated_count} ╨╛╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╛")
        except Exception as e:
            session.rollback()
            logger.error(f"╨Ю╤И╨╕╨▒╨║╨░ ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╤П ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╨╕ ╨┤╨╛╤Б╤В╨░╨▓╨╛╨║: {e}")

    async def sync_courier_deliveries_bg(self, date_from: datetime, date_to: datetime):
        """╨Т╤Б╨┐╨╛╨╝╨╛╨│╨░╤В╨╡╨╗╤М╨╜╤Л╨╣ ╨╝╨╡╤В╨╛╨┤ ╨┤╨╗╤П ╨╖╨░╨┐╤Г╤Б╨║╨░ ╤Б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╨╕ ╨▓ ╨▒╤Н╨║╨│╤А╨░╤Г╨╜╨┤╨╡ (╤З╨╡╤А╨╡╨╖ ╨┐╨╛╤В╨╛╨║╨╕)"""
        from app.core.database import SessionLocal
        with SessionLocal() as session:
            try:
                await self.sync_courier_deliveries(session, date_from=date_from, date_to=date_to)
            except Exception as e:
                logger.error(f"Error in courier deliveries background sync: {e}")
                session.rollback()


    async def sync_zones_from_external_map(self, session: Session, url: Optional[str] = None) -> Dict[str, Any]:
        """
        ╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨▓╨╜╨╡╤И╨╜╨╕╤Е ╨┐╨╛╨╗╨╕╨│╨╛╨╜╨╛╨▓ ╨╖╨╛╨╜ ╨╕╨╖ ╨╛╨▒╨╗╨░╤З╨╜╨╛╨│╨╛ ╤Е╤А╨░╨╜╨╕╨╗╨╕╤Й╨░ (Google Maps KML)
        """
        settings = session.exec(select(IikoSettings)).first()
        
        # ╨Х╤Б╨╗╨╕ URL ╨┐╨╡╤А╨╡╨┤╨░╨╜ ╤П╨▓╨╜╨╛, ╤Б╨╛╤Е╤А╨░╨╜╤П╨╡╨╝ ╨╡╨│╨╛ ╨▓ ╨╜╨░╤Б╤В╤А╨╛╨╣╨║╨╕
        if url:
            if settings:
                settings.delivery_zones_map_url = url
                session.add(settings)
                session.commit()
            map_url = url
        else:
            map_url = settings.delivery_zones_map_url if settings else None

        if not map_url:
            return {"success": False, "error": "╨б╤Б╤Л╨╗╨║╨░ ╨╜╨░ ╨║╨░╤А╤В╤Г ╨╜╨╡ ╨╖╨░╨┤╨░╨╜╨░ ╨▓ ╨╜╨░╤Б╤В╤А╨╛╨╣╨║╨░╤Е"}
        
        logger.info(f"╨Э╨░╤З╨░╨╗╨╛ ╨╕╨╝╨┐╨╛╤А╤В╨░ ╨│╨╡╨╛╨╝╨╡╤В╤А╨╕╨╕ ╨╖╨╛╨╜ ╨╕╨╖: {map_url}")
        
        # 1. ╨Ч╨░╨│╤А╤Г╨╢╨░╨╡╨╝ ╨╕ ╨┐╨░╤А╤Б╨╕╨╝ KML
        try:
            from .iiko_service import iiko_service
            kml_zones = await iiko_service.fetch_and_parse_kml(settings.delivery_zones_map_url)
            if not kml_zones:
                return {"success": False, "error": "╨Э╨╡ ╤Г╨┤╨░╨╗╨╛╤Б╤М ╨┐╨╛╨╗╤Г╤З╨╕╤В╤М ╨╖╨╛╨╜╤Л ╨╕╨╖ ╤Г╨║╨░╨╖╨░╨╜╨╜╨╛╨╣ ╤Б╤Б╤Л╨╗╨║╨╕. ╨Я╤А╨╛╨▓╨╡╤А╤М╤В╨╡ ╨┤╨╛╤Б╤В╤Г╨┐ ╨║ ╨║╨░╤А╤В╨╡."}
        except Exception as e:
            return {"success": False, "error": f"╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╨╖╨░╨│╤А╤Г╨╖╨║╨╡ ╨║╨░╤А╤В╤Л: {str(e)}"}
            
        # 2. ╨б╨╛╨┐╨╛╤Б╤В╨░╨▓╨╗╤П╨╡╨╝ ╨╕ ╨╛╨▒╨╜╨╛╨▓╨╗╤П╨╡╨╝
        updated_count = 0
        import json
        from app.models.company import DeliveryZone
        
        all_zones = session.exec(select(DeliveryZone)).all()
        
        for kz in kml_zones:
            name = kz["name"].strip()
            points = kz["points"]
            
            # ╨Ш╤Й╨╡╨╝ ╨╖╨╛╨╜╤Г ╨▓ ╨С╨Ф ╨┐╨╛ ╨╕╨╝╨╡╨╜╨╕ (╤А╨╡╨│╨╕╤Б╤В╤А╨╛╨╜╨╡╨╖╨░╨▓╨╕╤Б╨╕╨╝╨╛)
            matched_zone = next((z for z in all_zones if (z.name or "").lower() == (name or "").lower()), None)
            
            if matched_zone:
                # ╨б╨╛╤Е╤А╨░╨╜╤П╨╡╨╝ ╨║╨░╨║ JSON ╤Б╤В╤А╨╛╨║╤Г (╤Б╨╛╨│╨╗╨░╤Б╨╜╨╛ ╨╝╨╛╨┤╨╡╨╗╨╕)
                matched_zone.polygon_coordinates = json.dumps(points)
                matched_zone.updated_at = datetime.now(timezone.utc)
                session.add(matched_zone)
                updated_count += 1
                logger.info(f"╨Ю╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨░ ╨│╨╡╨╛╨╝╨╡╤В╤А╨╕╤П ╨┤╨╗╤П ╨╖╨╛╨╜╤Л: {name}")
            else:
                logger.warning(f"╨Ч╨╛╨╜╨░ ╨╕╨╖ KML '{name}' ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜╨░ ╨▓ ╨▒╨░╨╖╨╡ ╨┤╨░╨╜╨╜╤Л╤Е iiko")
                
        try:
            session.commit()
            # ╨Ю╤З╨╕╤Й╨░╨╡╨╝ ╨║╤Н╤И ╨┐╨╛╤Б╨╗╨╡ ╨╛╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╕╤П ╨╖╨╛╨╜ (╨╡╤Б╨╗╨╕ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╤В╤Б╤П Redis ╨╕╨╗╨╕ ╨╗╨╛╨║╨░╨╗╤М╨╜╤Л╨╣ ╨║╤Н╤И)
            try:
                from app.core.redis import redis_client
                await redis_client.delete("delivery_zones_all")
                logger.info("╨Ъ╤Н╤И ╨╖╨╛╨╜ ╨┤╨╛╤Б╤В╨░╨▓╨║╨╕ ╨╛╤З╨╕╤Й╨╡╨╜")
            except Exception:
                pass

            return {
                "success": True, 
                "updated_count": updated_count, 
                "total_from_map": len(kml_zones),
                "message": f"╨Ю╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╛ ╨╖╨╛╨╜: {updated_count} ╨╕╨╖ {len(kml_zones)}"
            }
        except Exception as e:
            session.rollback()
            logger.error(f"╨Ю╤И╨╕╨▒╨║╨░ ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╤П ╨│╨╡╨╛╨╝╨╡╤В╤А╨╕╨╕ ╨╖╨╛╨╜: {e}")
            return {"success": False, "error": f"╨Ю╤И╨╕╨▒╨║╨░ ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╤П ╨▓ ╨С╨Ф: {str(e)}"}


    async def sync_zones_from_kml_file(self, session: Session, kml_content: str) -> Dict[str, Any]:
        """
        ╨б╨╕╨╜╤Е╤А╨╛╨╜╨╕╨╖╨░╤Ж╨╕╤П ╨│╨╡╨╛╨╝╨╡╤В╤А╨╕╨╕ ╨╖╨╛╨╜ ╨┤╨╛╤Б╤В╨░╨▓╨║╨╕ ╨╕╨╖ ╨╖╨░╨│╤А╤Г╨╢╨╡╨╜╨╜╨╛╨│╨╛ KML ╤Д╨░╨╣╨╗╨░
        """
        logger.info("╨Э╨░╤З╨░╨╗╨╛ ╨╕╨╝╨┐╨╛╤А╤В╨░ ╨│╨╡╨╛╨╝╨╡╤В╤А╨╕╨╕ ╨╖╨╛╨╜ ╨╕╨╖ ╨╖╨░╨│╤А╤Г╨╢╨╡╨╜╨╜╨╛╨│╨╛ ╤Д╨░╨╣╨╗╨░")
        
        # 1. ╨Я╨░╤А╤Б╨╕╨╝ KML
        try:
            from .iiko_service import iiko_service
            kml_zones = iiko_service.parse_kml_content(kml_content)
            if not kml_zones:
                return {"success": False, "error": "╨Т ╤Д╨░╨╣╨╗╨╡ ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜╨╛ ╨┐╨╛╨╗╨╕╨│╨╛╨╜╨╛╨▓ ╨╖╨╛╨╜ ╨┤╨╛╤Б╤В╨░╨▓╨║╨╕."}
        except Exception as e:
            return {"success": False, "error": f"╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╨┐╨░╤А╤Б╨╕╨╜╨│╨╡ ╤Д╨░╨╣╨╗╨░: {str(e)}"}
            
        # 2. ╨б╨╛╨┐╨╛╤Б╤В╨░╨▓╨╗╤П╨╡╨╝ ╨╕ ╨╛╨▒╨╜╨╛╨▓╨╗╤П╨╡╨╝
        updated_count = 0
        import json
        from app.models.company import DeliveryZone
        
        all_zones = session.exec(select(DeliveryZone)).all()
        
        for kz in kml_zones:
            name = kz["name"].strip()
            points = kz["points"]
            description = kz.get("description", "")
            extended_data = kz.get("extended_data", {})
            
            # ╨Ш╤Й╨╡╨╝ ╨╖╨╛╨╜╤Г ╨▓ ╨С╨Ф ╨┐╨╛ ╨╕╨╝╨╡╨╜╨╕ (╤А╨╡╨│╨╕╤Б╤В╤А╨╛╨╜╨╡╨╖╨░╨▓╨╕╤Б╨╕╨╝╨╛)
            matched_zone = session.exec(select(DeliveryZone).where(func.lower(DeliveryZone.name) == (name or "").lower())).first()
            
            if matched_zone:
                matched_zone.polygon_coordinates = json.dumps(points)
                matched_zone.description = description
                matched_zone.additional_info = extended_data
                matched_zone.is_manual_override = True  # ╨Я╤А╨╕╨╛╤А╨╕╤В╨╡╤В ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П
                matched_zone.updated_at = datetime.now(timezone.utc)
                session.add(matched_zone)
                updated_count += 1
                logger.info(f"╨Ю╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨░ ╨│╨╡╨╛╨╝╨╡╤В╤А╨╕╤П ╨╕ ╨╝╨╡╤В╨░╨┤╨░╨╜╨╜╤Л╨╡ ╨┤╨╗╤П ╨╖╨╛╨╜╤Л (╨╕╨╖ KML): {name}")
            else:
                # ╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡ ╨╜╨╛╨▓╨╛╨╣ ╨┐╤А╨╕╨╛╤А╨╕╤В╨╡╤В╨╜╨╛╨╣ ╨╖╨╛╨╜╤Л ╨╕╨╖ KML ╤Д╨░╨╣╨╗╨░
                logger.info(f"╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡ ╨╜╨╛╨▓╨╛╨╣ ╨┐╤А╨╕╨╛╤А╨╕╤В╨╡╤В╨╜╨╛╨╣ ╨╖╨╛╨╜╤Л ╨╕╨╖ KML ╤Д╨░╨╣╨╗╨░: {name}")
                from app.models.company import Branch
                branch = session.exec(select(Branch)).first()
                if branch:
                    new_zone = DeliveryZone(
                        name=name,
                        branch_id=branch.id,
                        polygon_coordinates=json.dumps(points),
                        description=description,
                        additional_info=extended_data,
                        is_manual_override=True,  # ╨Я╤А╨╕╨╛╤А╨╕╤В╨╡╤В ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П
                        is_active=True
                    )
                    session.add(new_zone)
                    updated_count += 1
                else:
                    logger.warning(f"╨Э╨╡ ╤Г╨┤╨░╨╗╨╛╤Б╤М ╤Б╨╛╨╖╨┤╨░╤В╤М ╨╖╨╛╨╜╤Г {name}: ╤Д╨╕╨╗╨╕╨░╨╗ ╨╜╨╡ ╨╜╨░╨╣╨┤╨╡╨╜")
                
        try:
            session.commit()
            # ╨Ю╤З╨╕╤Й╨░╨╡╨╝ ╨║╤Н╤И
            try:
                from app.core.redis import redis_client
                await redis_client.delete("delivery_zones_all")
            except Exception:
                pass

            return {
                "success": True, 
                "updated_count": updated_count, 
                "total_from_file": len(kml_zones),
                "message": f"╨Ю╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╛ ╨╖╨╛╨╜ ╨╕╨╖ ╤Д╨░╨╣╨╗╨░: {updated_count} ╨╕╨╖ {len(kml_zones)}"
            }
        except Exception as e:
            session.rollback()
            logger.error(f"╨Ю╤И╨╕╨▒╨║╨░ ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╤П ╨│╨╡╨╛╨╝╨╡╤В╤А╨╕╨╕ ╨╖╨╛╨╜ ╨╕╨╖ ╤Д╨░╨╣╨╗╨░: {e}")
            return {"success": False, "error": f"╨Ю╤И╨╕╨▒╨║╨░ ╤Б╨╛╤Е╤А╨░╨╜╨╡╨╜╨╕╤П ╨▓ ╨С╨Ф: {str(e)}"}


iiko_sync_service = IikoSyncService()
