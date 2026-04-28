"""
тХи╨▒тХитХбтХд╨РтХитЦУтХитХХтХд╨С-тХитХЫтХд╨РтХитХСтХитХбтХд╨СтХд╨ТтХд╨РтХитЦСтХд╨ТтХитХЫтХд╨Р тХитФдтХитХЧтХд╨Я тХд╨СтХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХитХХ тХитФдтХитЦСтХитХЬтХитХЬтХд╨ЫтХд╨Х тХд╨С iiko Cloud
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
from app.models.order import Order, OrderItem, OrderStatus
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
        s = str(val).strip()
        if s.lower() in ("none", "null", "", "-", "--", ".", "undefined"):
            return ""
        return s

    def format_address(self, address_data: Any, city: Optional[str] = None, fmt: str = "components") -> str:
        """тХи╨ктХд╨РтХитЦСтХд╨СтХитХХтХитЦУтХитХЫ тХд╨ФтХитХЫтХд╨РтХитХЭтХитЦСтХд╨ТтХитХХтХд╨РтХд╨УтХитХбтХд╨Т тХитЦСтХитФдтХд╨РтХитХбтХд╨С тХитФдтХитХЧтХд╨Я тХитХЫтХд╨ТтХитХЫтХитЦТтХд╨РтХитЦСтХитХвтХитХбтХитХЬтХитХХтХд╨Я тХитЦУ тХитЦСтХитФдтХитХЭтХитХХтХитХЬтХитХСтХитХб."""
        if not address_data:
            return ""
            
        # logger.debug(f"Formatting address: data={address_data}, city={city}, fmt={fmt}")
            
        # тХи╨етХд╨СтХитХЧтХитХХ тХитФРтХд╨РтХитХХтХд╨ШтХитХбтХитХЧ тХд╨УтХитХвтХитХб тХитФВтХитХЫтХд╨ТтХитХЫтХитЦУтХд╨ЫтХитХг тХд╨СтХитХЧтХитХЫтХитЦУтХитЦСтХд╨РтХд╨Ь (тХитХХтХитХЦ тХитЦТтХитЦСтХитХЦтХд╨Ы тХитХХтХитХЧтХитХХ тХитХЬтХитЦСтХитФРтХд╨РтХд╨ЯтХитХЭтХд╨УтХд╨Ю)
        if isinstance(address_data, dict):
            # тХи╨итХитХЦтХитЦУтХитХЧтХитХбтХитХСтХитЦСтХитХбтХитХЭ тХитЦУтХд╨СтХитХб тХитЦУтХитХЫтХитХЦтХитХЭтХитХЫтХитХвтХитХЬтХд╨ЫтХитХб тХитФРтХитХЫтХитХЧтХд╨Я
            city_val = address_data.get('city') or city or ''
            street_val = address_data.get('street')
            # street тХитХЭтХитХЫтХитХвтХитХбтХд╨Т тХитЦТтХд╨ЫтХд╨ТтХд╨Ь тХитХЫтХитЦТтХд╨ЪтХитХбтХитХСтХд╨ТтХитХЫтХитХЭ {"name": "..."}
            street = street_val.get('name') if isinstance(street_val, dict) else street_val
            
            house = address_data.get('house', '')
            flat = address_data.get('flat', '')
            entrance = address_data.get('entrance', '')
            floor = address_data.get('floor', '')
            doorphone = address_data.get('doorphone', '')
            line1 = address_data.get('line1', '')
            
            # тХи╨етХд╨СтХитХЧтХитХХ тХд╨ФтХитХЫтХд╨РтХитХЭтХитЦСтХд╨Т "line1" тХитХХ тХитХЫтХитХЬтХитЦС тХитХбтХд╨СтХд╨ТтХд╨Ь, тХитХХтХд╨СтХитФРтХитХЫтХитХЧтХд╨ЬтХитХЦтХд╨УтХитХбтХитХЭ тХитХбтХд╨б тХитХСтХитЦСтХитХС тХитЦТтХитЦСтХитХЦтХд╨У
            if fmt == "line1" and line1:
                addr = line1
                # тХи╨дтХитХЫтХитЦТтХитЦСтХитЦУтХитХЧтХд╨ЯтХитХбтХитХЭ тХитХСтХитЦУтХитЦСтХд╨РтХд╨ТтХитХХтХд╨РтХд╨У/тХитФРтХитХЫтХитФдтХд╨ЪтХитХбтХитХЦтХитФд, тХитХбтХд╨СтХитХЧтХитХХ тХитХХтХд╨Х тХитХЬтХитХбтХд╨Т тХитЦУ line1
                parts = []
                if flat and str(flat) not in addr:
                    parts.append(f"тХитХСтХитЦУ. {flat}")
                if entrance and str(entrance) not in addr:
                    parts.append(f"тХитФРтХитХЫтХитФд. {entrance}")
                if floor and str(floor) not in addr:
                    parts.append(f"тХд╨ЭтХд╨Т. {floor}")
                
                if parts:
                    addr += ", " + ", ".join(parts)
                return addr

            # тХи╨итХитХЬтХитЦСтХд╨ЧтХитХб тХд╨СтХитХЫтХитЦТтХитХХтХд╨РтХитЦСтХитХбтХитХЭ тХитЦУтХд╨РтХд╨УтХд╨ЧтХитХЬтХд╨УтХд╨Ю тХитФРтХитХЫ тХитХСтХитХЫтХитХЭтХитФРтХитХЫтХитХЬтХитХбтХитХЬтХд╨ТтХитЦСтХитХЭ
            parts = []
            if city_val: parts.append(str(city_val))
            if street: 
                s = str(street)
                parts.append(f"тХд╨УтХитХЧтХитХХтХд╨ЦтХитЦС {s}" if "тХд╨УтХитХЧтХитХХтХд╨ЦтХитЦС" not in s.lower() and "тХд╨УтХитХЧ." not in s.lower() else s)
            if house: parts.append(f"тХитФд. {house}")
            if flat: parts.append(f"тХитХСтХитЦУ. {flat}")
            if entrance: parts.append(f"тХитФРтХитХЫтХитФд. {entrance}")
            if floor: parts.append(f"тХд╨ЭтХд╨Т. {floor}")
            if doorphone: parts.append(f"тХитФдтХитХЫтХитХЭ. {doorphone}")
            
            return ", ".join(filter(None, parts))
            
        return str(address_data)

    def _get_tz(self, session: Session):
        """тХи╨птХитХЫтХитХЧтХд╨УтХд╨ЧтХитХбтХитХЬтХитХХтХитХб тХд╨ЧтХитЦСтХд╨СтХитХЫтХитЦУтХитХЫтХитФВтХитХЫ тХитФРтХитХЫтХд╨ЯтХд╨СтХитЦС тХитХХтХитХЦ тХитХЬтХитЦСтХд╨СтХд╨ТтХд╨РтХитХЫтХитХбтХитХС"""
        from app.core.datetime_utils import get_tz
        return get_tz(session)

    async def sync_menu(self, session: Session) -> Dict[str, Any]:
        """тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитХСтХитЦСтХд╨ТтХитЦСтХитХЧтХитХЫтХитФВтХитЦС тХитХЭтХитХбтХитХЬтХд╨Ю (тХитХСтХитЦСтХд╨ТтХитХбтХитФВтХитХЫтХд╨РтХитХХтХитХХ + тХд╨ТтХитХЫтХитЦУтХитЦСтХд╨РтХд╨Ы)"""
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
            
            # тХи╨гтХитЦСтХд╨РтХитЦСтХитХЬтХд╨ТтХитХХтХд╨РтХд╨УтХитХбтХитХЭ тХитХЬтХитЦСтХитХЧтХитХХтХд╨ЧтХитХХтХитХб success тХитХХ тХитФРтХитХЫтХитХЧтХитХбтХитХг тХитФдтХитХЧтХд╨Я тХд╨СтХд╨ХтХитХбтХитХЭтХд╨Ы
            response = {
                "success": True,
                "categories_synced": res.get("categories", 0),
                "products_synced": res.get("products", 0),
                "message": f"тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитХЦтХитЦСтХитЦУтХитХбтХд╨РтХд╨ШтХитХбтХитХЬтХитЦС тХд╨УтХд╨СтХитФРтХитХбтХд╨ШтХитХЬтХитХЫ: {res.get('categories', 0)} тХитХСтХитЦСтХд╨ТтХитХбтХитФВтХитХЫтХд╨РтХитХХтХитХг, {res.get('products', 0)} тХд╨ТтХитХЫтХитЦУтХитЦСтХд╨РтХитХЫтХитЦУ"
            }
            
            log.status = "success"
            log.details = response["message"]
            session.add(log)
            session.commit()
            
            # тХи╨дтХитХЫтХитЦТтХитЦСтХитЦУтХитХЧтХд╨ЯтХитХбтХитХЭ тХитХЦтХитЦСтХитФРтХитХХтХд╨СтХд╨Ь тХитЦУ тХитЦСтХд╨УтХитФдтХитХХтХд╨Т
            log_audit(action="manual_sync", resource_type="menu", message=response["message"])
            
            return response
        except Exception as e:
            logger.error(f"Menu sync failed: {e}", exc_info=True)
            log.status = "error"
            log.details = str(e)
            session.add(log)
            session.commit()
            
            # тХи╨дтХитХЫтХитЦТтХитЦСтХитЦУтХитХЧтХд╨ЯтХитХбтХитХЭ тХитХЦтХитЦСтХитФРтХитХХтХд╨СтХд╨Ь тХитЦУ тХитЦСтХд╨УтХитФдтХитХХтХд╨Т тХитХЫтХитЦТ тХитХЫтХд╨ШтХитХХтХитЦТтХитХСтХитХб
            log_audit(action="manual_sync_failed", resource_type="menu", message=str(e))
            
            return {
                "success": False,
                "error": str(e),
                "message": f"тХи╨отХд╨ШтХитХХтХитЦТтХитХСтХитЦС тХд╨СтХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХитХХ: {str(e)}"
            }

    async def sync_categories_only(self, session: Session) -> Dict[str, Any]:
        """тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХд╨ТтХитХЫтХитХЧтХд╨ЬтХитХСтХитХЫ тХитХСтХитЦСтХд╨ТтХитХбтХитФВтХитХЫтХд╨РтХитХХтХитХг тХитХХтХитХЦ iiko (тХитЦУтХд╨ЫтХитХЦтХд╨ЫтХитЦУтХитЦСтХитХбтХд╨Т тХитФРтХитХЫтХитХЧтХитХЬтХд╨УтХд╨Ю тХд╨СтХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Ю тХитХЭтХитХбтХитХЬтХд╨Ю)"""
        res = await self.sync_menu(session)
        return {
            "success": res.get("success", False),
            "categories_synced": res.get("categories_synced", 0),
            "message": f"тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитХХтХд╨РтХитХЫтХитЦУтХитЦСтХитХЬтХитХЫ тХитХСтХитЦСтХд╨ТтХитХбтХитФВтХитХЫтХд╨РтХитХХтХитХг: {res.get('categories_synced', 0)}"
        }

    async def _sync_from_external_menu(self, session: Session, menu_data: Dict[str, Any], log: SyncLog) -> Dict[str, Any]:
        """тХи╨лтХитХЫтХитФВтХитХХтХитХСтХитЦС тХитХЫтХитЦТтХд╨РтХитЦСтХитЦТтХитХЫтХд╨ТтХитХСтХитХХ тХитЦУтХитХЬтХитХбтХд╨ШтХитХЬтХитХбтХитФВтХитХЫ тХитХЭтХитХбтХитХЬтХд╨Ю iiko (API v2 /menu/by_id)"""
        if not menu_data:
            return {"categories": 0, "products": 0}
        
        categories_synced = 0
        products_synced = 0

        # 1. тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитХСтХитЦСтХд╨ТтХитХбтХитФВтХитХЫтХд╨РтХитХХтХитХг
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

        # 2. тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХд╨ТтХитХЫтХитЦУтХитЦСтХд╨РтХитХЫтХитЦУ
        # тХи╨в v2 тХд╨ТтХитХЫтХитЦУтХитЦСтХд╨РтХд╨Ы тХд╨СтХитФВтХд╨РтХд╨УтХитФРтХитФРтХитХХтХд╨РтХитХЫтХитЦУтХитЦСтХитХЬтХд╨Ы тХитФРтХитХЫ тХитХСтХитЦСтХд╨ТтХитХбтХитФВтХитХЫтХд╨РтХитХХтХд╨ЯтХитХЭ тХитЦУ itemCategories
        for cat_data in cats_list:
            iiko_cat_id = cat_data.get("id")
            local_cat = session.exec(select(Category).where(Category.iiko_id == iiko_cat_id)).first()
            category_id = local_cat.id if local_cat else None
            
            items_list = cat_data.get("items") or cat_data.get("products") or []
            for item_data in items_list:
                item_id = item_data.get("itemId") or item_data.get("id")
                if not item_id: continue
                
                prod = session.exec(select(Product).where(Product.iiko_id == item_id)).first()
                
                # тХи╨итХитХЦтХитЦУтХитХЧтХитХбтХитХСтХитЦСтХитХбтХитХЭ тХитФдтХитЦСтХитХЬтХитХЬтХд╨ЫтХитХб тХитХХтХитХЦ тХитФРтХитХбтХд╨РтХитЦУтХитХЫтХитФВтХитХЫ тХд╨РтХитЦСтХитХЦтХитХЭтХитХбтХд╨РтХитЦС тХитФдтХитХЧтХд╨Я тХитЦТтХитЦСтХитХЦтХитХЫтХитЦУтХд╨ЫтХд╨Х тХитФРтХитХЫтХитХЧтХитХбтХитХг тХд╨ТтХитХЫтХитЦУтХитЦСтХд╨РтХитЦС
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
                
                session.flush() # тХи╨птХитХЫтХитХЧтХд╨УтХд╨ЧтХитЦСтХитХбтХитХЭ ID

                # --- тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХд╨РтХитЦСтХитХЦтХитХЭтХитХбтХд╨РтХитХЫтХитЦУ ---
                for existing_size in session.exec(select(ProductSize).where(ProductSize.product_id == prod.id)).all():
                    session.delete(existing_size)
                
                if sizes:
                    for s_data in sizes:
                        s_price = 0
                        if s_data.get("prices"): s_price = s_data["prices"][0].get("price", 0)
                        
                        session.add(ProductSize(
                            product_id=prod.id,
                            iiko_id=s_data.get("sizeId") or item_id,
                            name=s_data.get("sizeName") or "тХи╨▒тХд╨ТтХитЦСтХитХЬтХитФдтХитЦСтХд╨РтХд╨Т",
                            price=float(s_price or 0),
                            is_default=s_data.get("isDefault", False)
                        ))
                else:
                    session.add(ProductSize(
                        product_id=prod.id,
                        iiko_id=item_id,
                        name="тХи╨▒тХд╨ТтХитЦСтХитХЬтХитФдтХитЦСтХд╨РтХд╨Т",
                        price=float(price or 0),
                        is_default=True
                    ))

                # --- тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитХЭтХитХЫтХитФдтХитХХтХд╨ФтХитХХтХитХСтХитЦСтХд╨ТтХитХЫтХд╨РтХитХЫтХитЦУ ---
                # тХи╨бтХитХбтХд╨РтХитХбтХитХЭ тХитХЭтХитХЫтХитФдтХитХХтХд╨ФтХитХХтХитХСтХитЦСтХд╨ТтХитХЫтХд╨РтХд╨Ы тХитХХтХитХЦ тХитФдтХитХбтХд╨ФтХитХЫтХитХЧтХд╨ТтХитХЬтХитХЫтХитФВтХитХЫ тХд╨РтХитЦСтХитХЦтХитХЭтХитХбтХд╨РтХитЦС (тХитХХтХитХЧтХитХХ тХитФРтХитХбтХд╨РтХитЦУтХитХЫтХитФВтХитХЫ тХитФдтХитХЫтХд╨СтХд╨ТтХд╨УтХитФРтХитХЬтХитХЫтХитФВтХитХЫ)
                target_size = next((s for s in sizes if s.get("isDefault")), sizes[0] if sizes else None)
                if target_size:
                    # тХи╨отХд╨ЧтХитХХтХд╨ЩтХитЦСтХитХбтХитХЭ тХд╨СтХд╨ТтХитЦСтХд╨РтХд╨ЫтХитХб тХитФВтХд╨РтХд╨УтХитФРтХитФРтХд╨Ы тХитХЭтХитХЫтХитФдтХитХХтХд╨ФтХитХХтХитХСтХитЦСтХд╨ТтХитХЫтХд╨РтХитХЫтХитЦУ
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
        """тХи╨отХитЦТтХд╨РтХитЦСтХитЦТтХитХЫтХд╨ТтХитХСтХитЦС тХитХСтХитХЧтХитЦСтХд╨СтХд╨СтХитХХтХд╨ЧтХитХбтХд╨СтХитХСтХитХЫтХитХг тХитХЬтХитХЫтХитХЭтХитХбтХитХЬтХитХСтХитХЧтХитЦСтХд╨ТтХд╨УтХд╨РтХд╨Ы iiko (groups + products + sizes)"""
        if not nomenclature:
            return {"categories": 0, "products": 0}

        categories_synced = 0
        products_synced = 0

        # 1. тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитХСтХитЦСтХд╨ТтХитХбтХитФВтХитХЫтХд╨РтХитХХтХитХг (groups)
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

        # 2. тХи╨мтХитЦСтХитФРтХитФРтХитХХтХитХЬтХитФВ тХд╨РтХитЦСтХитХЦтХитХЭтХитХбтХд╨РтХитХЫтХитЦУ тХитФдтХитХЧтХд╨Я тХд╨ТтХитХЫтХитЦУтХитЦСтХд╨РтХитХЫтХитЦУ
        size_map = {s["id"]: s["name"] for s in nomenclature.get("sizes", [])}

        # 3. тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХд╨ТтХитХЫтХитЦУтХитЦСтХд╨РтХитХЫтХитЦУ (products)
        if "products" in nomenclature:
            for p in nomenclature["products"]:
                if p.get("type") == "Service": continue # тХи╨птХд╨РтХитХЫтХитФРтХд╨УтХд╨СтХитХСтХитЦСтХитХбтХитХЭ тХд╨УтХд╨СтХитХЧтХд╨УтХитФВтХитХХ
                
                prod = session.exec(select(Product).where(Product.iiko_id == p["id"])).first()
                
                # тХи╨птХитХЫтХитХХтХд╨СтХитХС тХитХЧтХитХЫтХитХСтХитЦСтХитХЧтХд╨ЬтХитХЬтХитХЫтХитХг тХитХСтХитЦСтХд╨ТтХитХбтХитФВтХитХЫтХд╨РтХитХХтХитХХ
                category_id = None
                if p.get("parentGroup"):
                    local_cat = session.exec(select(Category).where(Category.iiko_id == p["parentGroup"])).first()
                    if local_cat: category_id = local_cat.id
                
                # тХи╨отХитФРтХд╨РтХитХбтХитФдтХитХбтХитХЧтХитХбтХитХЬтХитХХтХитХб тХитЦТтХитЦСтХитХЦтХитХЫтХитЦУтХитХЫтХитХг тХд╨ЦтХитХбтХитХЬтХд╨Ы (тХитФРтХитХбтХд╨РтХитЦУтХд╨ЫтХитХг тХитФдтХитХЫтХд╨СтХд╨ТтХд╨УтХитФРтХитХЬтХд╨ЫтХитХг тХд╨РтХитЦСтХитХЦтХитХЭтХитХбтХд╨Р)
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
                
                session.flush() # тХи╨птХитХЫтХитХЧтХд╨УтХд╨ЧтХитЦСтХитХбтХитХЭ ID тХд╨ТтХитХЫтХитЦУтХитЦСтХд╨РтХитЦС
                
                # --- тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХд╨РтХитЦСтХитХЦтХитХЭтХитХбтХд╨РтХитХЫтХитЦУ ---
                for existing_size in session.exec(select(ProductSize).where(ProductSize.product_id == prod.id)).all():
                    session.delete(existing_size)
                
                if p.get("sizePrices"):
                    for sp in p["sizePrices"]:
                        s_id = sp.get("sizeId")
                        s_name = size_map.get(s_id, "тХи╨▒тХд╨ТтХитЦСтХитХЬтХитФдтХитЦСтХд╨РтХд╨Т")
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
        """тХи╨итХитХЬтХд╨ТтХитХбтХитФВтХд╨РтХитХХтХд╨РтХитХЫтХитЦУтХитЦСтХитХЬтХитХЬтХд╨ЫтХитХг тХитХЭтХитХбтХд╨ТтХитХЫтХитФд тХитХЫтХитЦТтХд╨РтХитЦСтХитЦТтХитХЫтХд╨ТтХитХСтХитХХ тХитХЦтХитЦСтХитХСтХитЦСтХитХЦтХитЦС: тХитХСтХитХЫтХитХЬтХд╨СтХитХЫтХитХЧтХитХХтХитФдтХитХХтХд╨РтХитХЫтХитЦУтХитЦСтХитХЬтХитХЬтХитЦСтХд╨Я тХитХХ тХитХЫтХд╨ЧтХитХХтХд╨ЩтХитХбтХитХЬтХитХЬтХитЦСтХд╨Я тХитЦУтХитХбтХд╨РтХд╨СтХитХХтХд╨Я"""
        if not iiko_order_data:
            logger.warning("Received empty order data from iiko")
            return
            
        try:
            # 1. тХи╨бтХитЦСтХитХЦтХитХЫтХитЦУтХд╨ЫтХитХб тХитФдтХитЦСтХитХЬтХитХЬтХд╨ЫтХитХб тХитХЦтХитЦСтХитХСтХитЦСтХитХЦтХитЦС
            order_id_iiko = iiko_order_data.get("id")
            o_data = iiko_order_data.get("order")
            if not o_data:
                o_data = iiko_order_data
            
            if not order_id_iiko:
                order_id_iiko = o_data.get("id")

            if not order_id_iiko:
                logger.warning(f"Order data missing ID. Keys available: {list(o_data.keys())}. Full data sample: {str(o_data)[:500]}")
                return
            
            # тХи╨лтХитХЫтХитФВтХитХХтХд╨РтХд╨УтХитХбтХитХЭ тХитХЬтХитЦСтХд╨ЧтХитЦСтХитХЧтХитХЫ тХитХЫтХитЦТтХд╨РтХитЦСтХитЦТтХитХЫтХд╨ТтХитХСтХитХХ тХитФдтХитХЧтХд╨Я тХитФдтХитХХтХитЦСтХитФВтХитХЬтХитХЫтХд╨СтХд╨ТтХитХХтХитХСтХитХХ
            ext_num = o_data.get("number") or o_data.get("externalNumber")
            logger.info(f"==> Processing Iiko Order: ID={order_id_iiko}, Num={ext_num}, Status={o_data.get('status')}")
            
            settings_db = session.exec(select(IikoSettings)).first()
            city_from_settings = settings_db.city_name if settings_db else "тХи╨▓тХд╨ЮтХитХЭтХитХбтХитХЬтХд╨Ь"

            # тХи╨отХд╨ЧтХитХХтХд╨СтХд╨ТтХитХСтХитЦС тХд╨СтХд╨ТтХд╨РтХитХЫтХитХС тХитХЫтХд╨Т тХитФРтХитХЧтХитХбтХитХгтХд╨СтХд╨ХтХитХЫтХитХЧтХитФдтХитХбтХд╨РтХитХЫтХитЦУ
            def clean(v):
                if v is None: return None
                s = str(v).strip()
                # тХи╨│тХитФдтХитЦСтХитХЧтХд╨ЯтХитХбтХитХЭ тХитЦСтХд╨РтХд╨ТтХитХбтХд╨ФтХитЦСтХитХСтХд╨ТтХд╨Ы "None", "null" тХитХХ тХитФРтХд╨РтХитХЫтХд╨ЧтХитХХтХитХб тХитФРтХитХЧтХитХбтХитХгтХд╨СтХд╨ХтХитХЫтХитХЧтХитФдтХитХбтХд╨РтХд╨Ы
                if s.lower() in ["none", "null", "", "-", "--", "---", "----", "----------", ".", "undefined"]: 
                    return None
                return s

            # 2. тХи╨▒тХд╨ТтХитЦСтХд╨ТтХд╨УтХд╨С тХитХХ тХитЦУтХитХЬтХитХбтХд╨ШтХитХЬтХитХХтХитХб тХитХЬтХитХЫтХитХЭтХитХбтХд╨РтХитЦС
            raw_status = clean(o_data.get("status") or iiko_order_data.get("creationStatus"))
            raw_status_lower = raw_status.lower() if raw_status else ""
            external_number = clean(o_data.get("number") or o_data.get("externalNumber")) or None

            # 3. тХи╨▓тХитЦСтХитХгтХитХЭтХитХЦтХитХЫтХитХЬтХитЦС тХитХХ тХитЦУтХд╨РтХитХбтХитХЭтХд╨Я
            from app.core.datetime_utils import get_tz_name
            tz_name = get_tz_name(session)
            try:
                import zoneinfo
                tz = zoneinfo.ZoneInfo(tz_name)
            except Exception:
                import zoneinfo
                tz = zoneinfo.ZoneInfo("Asia/Yekaterinburg")
            
            current_time_tz = datetime.now(tz)
            
            # тХи╨птХитХЫтХитХХтХд╨СтХитХС тХитФдтХитЦСтХд╨ТтХд╨Ы тХд╨СтХитХЫтХитХЦтХитФдтХитЦСтХитХЬтХитХХтХд╨Я тХитЦУ тХд╨РтХитЦСтХитХЦтХитХЬтХд╨ЫтХд╨Х тХитХЭтХитХбтХд╨СтХд╨ТтХитЦСтХд╨Х (iiko API тХитХЭтХитХЫтХитХвтХитХбтХд╨Т тХитХЭтХитХбтХитХЬтХд╨ЯтХд╨ТтХд╨Ь тХд╨СтХд╨ТтХд╨РтХд╨УтХитХСтХд╨ТтХд╨УтХд╨РтХд╨У)
            iiko_creation_time_raw = (
                (o_data.get("creationInfo") or {}).get("creationDate") or 
                o_data.get("creationDate") or
                o_data.get("whenCreated")
            )
            iiko_creation_time = None
            if iiko_creation_time_raw:
                try:
                    # тХи╨птХд╨РтХитХХтХитХЬтХитХХтХитХЭтХитЦСтХитХбтХитХЭ тХитЦУтХд╨РтХитХбтХитХЭтХд╨Я тХитХСтХитЦСтХитХС UTC 0, тХитХбтХд╨СтХитХЧтХитХХ тХитХбтХд╨СтХд╨ТтХд╨Ь тХитФРтХитХЫтХитХЭтХитХбтХд╨ТтХитХСтХитЦС Z тХитХХтХитХЧтХитХХ тХд╨СтХитХЭтХитХбтХд╨ЩтХитХбтХитХЬтХитХХтХитХб.
                    # тХи╨╜тХд╨ТтХитХЫ тХитХХтХд╨СтХитФРтХд╨РтХитЦСтХитЦУтХитХХтХд╨Т тХитФРтХд╨РтХитХЫтХитЦТтХитХЧтХитХбтХитХЭтХд╨У 5-тХд╨ЧтХитЦСтХд╨СтХитХЫтХитЦУтХитХЫтХитФВтХитХЫ тХд╨СтХитХЭтХитХбтХд╨ЩтХитХбтХитХЬтХитХХтХд╨Я тХитЦУ тХитЦСтХитФдтХитХЭтХитХХтХитХЬтХитХСтХитХб.
                    if 'Z' in iiko_creation_time_raw or '+' in iiko_creation_time_raw or '-' in iiko_creation_time_raw[10:]:
                        # ISO тХд╨ФтХитХЫтХд╨РтХитХЭтХитЦСтХд╨Т тХд╨С Z тХитХХтХитХЧтХитХХ тХд╨СтХитХЭтХитХбтХд╨ЩтХитХбтХитХЬтХитХХтХитХбтХитХЭ тХитФРтХитЦСтХд╨РтХд╨СтХитХХтХд╨ТтХд╨СтХд╨Я тХитХСтХитЦСтХитХС aware datetime
                        dt = datetime.fromisoformat(iiko_creation_time_raw.replace('Z', '+00:00'))
                        iiko_creation_time = dt.astimezone(timezone.utc).replace(tzinfo=None)
                    else:
                        # тХи╨етХд╨СтХитХЧтХитХХ тХитЦУтХд╨РтХитХбтХитХЭтХд╨Я тХитЦТтХитХбтХитХЦ тХитФРтХитХЫтХд╨ЯтХд╨СтХитЦС (naive), тХд╨СтХд╨ЧтХитХХтХд╨ТтХитЦСтХитХбтХитХЭ тХитХбтХитФВтХитХЫ тХитХЧтХитХЫтХитХСтХитЦСтХитХЧтХд╨ЬтХитХЬтХд╨ЫтХитХЭ тХитФдтХитХЧтХд╨Я тХитХЦтХитЦСтХитЦУтХитХбтХитФдтХитХбтХитХЬтХитХХтХд╨Я
                        dt = datetime.fromisoformat(iiko_creation_time_raw)
                        iiko_creation_time = dt.replace(tzinfo=tz).astimezone(timezone.utc).replace(tzinfo=None)
                    
                    logger.info(f"Parsed iiko time (naive UTC): raw={iiko_creation_time_raw}, result={iiko_creation_time}")
                except Exception as e:
                    logger.error(f"Error parsing iiko creation time {iiko_creation_time_raw}: {e}")

            # 4. тХи╨ктХитХЧтХитХХтХитХбтХитХЬтХд╨Т
            c_data = o_data.get("customer") or {}
            c_first = clean(c_data.get("name"))
            c_last = clean(c_data.get("surname"))
            full_customer_name = f"{c_first or ''} {c_last or ''}".strip() or "тХи╨гтХитХЫтХд╨СтХд╨ТтХд╨Ь"
            phone = clean(o_data.get("phone") or c_data.get("phone"))

            # 5. тХи╨атХитФдтХд╨РтХитХбтХд╨С
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
            
            city = city or city_from_settings or "тХи╨▓тХд╨ЮтХитХЭтХитХбтХитХЬтХд╨Ь"

            # тХи╨╜тХитХСтХд╨СтХд╨ТтХд╨РтХитЦСтХитХСтХд╨ЦтХитХХтХд╨Я тХитХСтХитХЫтХитХЭтХитФРтХитХЫтХитХЬтХитХбтХитХЬтХд╨ТтХитХЫтХитЦУ тХитФдтХитХЧтХд╨Я тХи╨бтХи╨д (тХд╨СтХитХЧтХитХХтХитЦУтХитЦСтХитХбтХитХЭ тХитФдтХитЦСтХитХЬтХитХЬтХд╨ЫтХитХб тХитХХтХитХЦ address тХитХХ deliveryPoint)
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
            
            # тХи╨▒тХитХЬтХитЦСтХд╨ЧтХитЦСтХитХЧтХитЦС тХитФРтХд╨РтХитХЫтХитЦТтХд╨УтХитХбтХитХЭ тХд╨СтХитХЫтХитЦТтХд╨РтХитЦСтХд╨ТтХд╨Ь тХитЦСтХитФдтХд╨РтХитХбтХд╨С тХитХХтХитХЦ тХитХЬтХитЦСтХитХХтХитЦТтХитХЫтХитХЧтХитХбтХитХб тХитФРтХитХЫтХитХЧтХитХЬтХитХЫтХитФВтХитХЫ тХитХЫтХитЦТтХд╨ЪтХитХбтХитХСтХд╨ТтХитЦС (тХитХЫтХитЦТтХд╨ЫтХд╨ЧтХитХЬтХитХЫ тХд╨ЭтХд╨ТтХитХЫ raw_addr, тХитХЬтХитХЫ тХитХбтХд╨СтХитХЧтХитХХ тХд╨ТтХитЦСтХитХЭ тХитФРтХд╨УтХд╨СтХд╨ТтХитХЫ - raw_addr_dp)
            # тХи╨дтХитХЧтХд╨Я тХд╨ЭтХд╨ТтХитХЫтХитФВтХитХЫ тХд╨СтХитХЫтХитХЦтХитФдтХитЦСтХитХбтХитХЭ тХитЦУтХд╨РтХитХбтХитХЭтХитХбтХитХЬтХитХЬтХд╨ЫтХитХг тХитХЫтХитЦТтХд╨ЪтХитХбтХитХСтХд╨Т тХд╨СтХитХЫ тХитЦУтХд╨СтХитХбтХитХЭтХитХХ тХитФРтХитХЫтХитХЧтХд╨ЯтХитХЭтХитХХ
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
            
            # тХи╨етХд╨СтХитХЧтХитХХ тХитЦУ тХитХХтХд╨ТтХитХЫтХитФВтХитХб тХитЦСтХитФдтХд╨РтХитХбтХд╨С тХитФРтХд╨УтХд╨СтХд╨ТтХитХЫтХитХг тХитХХтХитХЧтХитХХ "тХи╨▒тХитЦСтХитХЭтХитХЫтХитЦУтХд╨ЫтХитЦУтХитХЫтХитХЦ", тХитФРтХд╨РтХитХЫтХитЦУтХитХбтХд╨РтХд╨ЯтХитХбтХитХЭ тХитФдтХд╨РтХд╨УтХитФВтХитХХтХитХб тХитФРтХитХЫтХитХЧтХд╨Я
            is_only_city = not delivery_address or delivery_address.strip() in [city, f"тХитФВ. {city}", "тХитФВ.тХи╨▓тХд╨ЮтХитХЭтХитХбтХитХЬтХд╨Ь", "тХи╨▓тХд╨ЮтХитХЭтХитХбтХитХЬтХд╨Ь"]
            
            if is_only_city:
                # тХи╨етХд╨СтХитХЧтХитХХ тХитЦУтХд╨СтХд╨б тХитХбтХд╨ЩтХитХб тХитФРтХд╨УтХд╨СтХд╨ТтХитХЫ, тХитФРтХд╨РтХитХЫтХитЦТтХд╨УтХитХбтХитХЭ deliveryAddress тХитХЬтХитЦС тХитЦУтХитХбтХд╨РтХд╨ХтХитХЬтХитХбтХитХЭ тХд╨УтХд╨РтХитХЫтХитЦУтХитХЬтХитХб
                addr_str = self.clean_str(o_data.get("deliveryAddress"))
                if addr_str and len(addr_str) > len(city or "") + 2:
                    delivery_address = addr_str
                    has_new_address = True
                else:
                    delivery_address = "тХи╨▒тХитЦСтХитХЭтХитХЫтХитЦУтХд╨ЫтХитЦУтХитХЫтХитХЦ"
            else:
                has_new_address = True
            
            # тХи╨етХд╨СтХитХЧтХитХХ тХитЦУ тХитХХтХд╨ТтХитХЫтХитФВтХитХб тХитЦУтХд╨СтХд╨б тХд╨РтХитЦСтХитЦУтХитХЬтХитХЫ тХд╨ТтХитХЫтХитХЧтХд╨ЬтХитХСтХитХЫ тХитФВтХитХЫтХд╨РтХитХЫтХитФд, тХитХЬтХитХЫ тХитХбтХд╨СтХд╨ТтХд╨Ь addressString тХитХЬтХитЦС тХитЦУтХитХбтХд╨РтХд╨ХтХитХЬтХитХбтХитХЭ тХд╨УтХд╨РтХитХЫтХитЦУтХитХЬтХитХб - тХитФРтХд╨РтХитХЫтХитЦТтХд╨УтХитХбтХитХЭ тХитХбтХитФВтХитХЫ
            if not has_new_address:
                addr_str = self.clean_str(o_data.get("deliveryAddress"))
                if addr_str and len(addr_str) > len(city or "") + 2:
                    delivery_address = addr_str
                    has_new_address = True

            # --- тХи╨нтХи╨отХи╨втХи╨атХи╨┐ тХи╨лтХи╨отХи╨гтХи╨итХи╨ктХи╨а тХи╨отХи╨птХи╨лтХи╨атХи╨▓тХи╨╗ ---
            sum_total = Decimal(str(o_data.get("sum") or 0)) # тХи╨бтХитЦСтХитХЦтХитХЫтХитЦУтХитЦСтХд╨Я тХд╨СтХд╨УтХитХЭтХитХЭтХитЦС (тХитФдтХитХЫ тХд╨СтХитХСтХитХХтХитФдтХитХЫтХитХС)
            # тХи╨▒тХд╨УтХитХЭтХитХЭтХитЦС тХитХС тХитХЫтХитФРтХитХЧтХитЦСтХд╨ТтХитХб тХитФРтХитХЫтХд╨СтХитХЧтХитХб тХитФРтХд╨РтХитХХтХитХЭтХитХбтХитХЬтХитХбтХитХЬтХитХХтХд╨Я тХд╨СтХитХСтХитХХтХитФдтХитХЫтХитХС
            total_with_discount = Decimal(str(o_data.get("totalSum") or o_data.get("total") or sum_total))
            
            # тХи╨▒тХитХСтХитХХтХитФдтХитХСтХитХХ
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
                if not pn: pn = pk or "тХи╨▓тХитХХтХитФР тХитХЫтХитФРтХитХЧтХитЦСтХд╨ТтХд╨Ы"
                
                psum = float(p.get("sum") or 0)
                
                is_processed_externally = p.get("isProcessedExternally", False) or p.get("processedExternally", False)
                is_prepay = p.get("isPrepay", False) or p.get("prepay", False)
                status_payment = p.get("status", "").lower()
                
                # тХи╨▒тХд╨ЧтХитХХтХд╨ТтХитЦСтХитХбтХитХЭ тХитФРтХитХЧтХитЦСтХд╨ТтХитХбтХитХв тХитФРтХд╨РтХитХЫтХитЦУтХитХбтХитФдтХитХбтХитХЬтХитХЬтХд╨ЫтХитХЭ
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
            
            # тХи╨│тХд╨ЧтХитХХтХд╨ТтХд╨ЫтХитЦУтХитЦСтХитХбтХитХЭ iiko Cloud processedPaymentsSum (тХитХбтХд╨СтХитХЧтХитХХ тХитХЫтХитХЬ тХитЦТтХитХЫтХитХЧтХд╨ЬтХд╨ШтХитХб тХд╨ТтХитХЫтХитФВтХитХЫ тХд╨ЧтХд╨ТтХитХЫ тХитХЭтХд╨Ы тХд╨СтХитФРтХитЦСтХд╨РтХд╨СтХитХХтХитХЧтХитХХ)
            processed_params = float(o_data.get("processedPaymentsSum") or 0)
            if processed_params > total_paid:
                total_paid = processed_params

            # тХи╨▒тХд╨ЧтХитХХтХд╨ТтХитЦСтХитХбтХитХЭ тХитХЫтХд╨СтХд╨ТтХитЦСтХд╨ТтХитХЫтХитХС
            left_to_pay = max(Decimal('0.00'), total_with_discount - Decimal(str(total_paid)))
            is_paid = (left_to_pay <= 0)
            
            payment_method = ", ".join(list(set(pm_list))) or "тХи╨нтХитХб тХд╨УтХитХСтХитЦСтХитХЦтХитЦСтХитХЬ"
            
            # тХи╨┤тХитХЫтХитХЧтХитЦТтХд╨ЭтХитХС тХд╨СтХд╨ТтХитЦСтХд╨ТтХд╨УтХд╨СтХитЦС тХитХЦтХитЦСтХитХСтХд╨РтХд╨ЫтХд╨ТтХитХЫтХитФВтХитХЫ тХитХЦтХитЦСтХитХСтХитЦСтХитХЦтХитЦС
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

            # тХи╨етХд╨СтХитХЧтХитХХ тХитХЦтХитЦСтХитХСтХитЦСтХитХЦ тХитХЦтХитЦСтХитХСтХд╨РтХд╨ЫтХд╨Т тХитЦУ iiko - тХитХЫтХитХЬ тХд╨ТтХитХЫтХд╨ЧтХитХЬтХитХЫ тХитХЫтХитФРтХитХЧтХитЦСтХд╨ЧтХитХбтХитХЬ (тХитФдтХитХЧтХд╨Я тХитХЬтХитЦСтХд╨ШтХитХбтХитХг CRM)
            if not is_paid and mapped_status in (OrderStatus.closed, OrderStatus.delivered):
                is_paid = True
                left_to_pay = Decimal('0.00')
                logger.info(f"Order {order_id_iiko}: Paid via status enforcement ('{mapped_status}')")

            # 7. тХи╨ктХд╨УтХд╨РтХд╨ЬтХитХбтХд╨Р, тХд╨ТтХитХХтХитФР тХитХХ тХитФдтХитХЫтХитФРтХитХЫтХитХЧтХитХЬтХитХХтХд╨ТтХитХбтХитХЧтХд╨ЬтХитХЬтХд╨ЫтХитХб тХитФдтХитЦСтХитХЬтХитХЬтХд╨ЫтХитХб
            courier_name = "тХи╨нтХитХб тХитХЬтХитЦСтХитХЦтХитХЬтХитЦСтХд╨ЧтХитХбтХитХЬ"
            ci = o_data.get("courierInfo") or {}
            if isinstance(ci, dict):
                c_obj = ci.get("courier") or {}
                if isinstance(c_obj, dict):
                    fn = clean(c_obj.get("firstName") or c_obj.get("name")) or ""
                    ln = clean(c_obj.get("lastName")) or ""
                    courier_name = " ".join(filter(None, [fn, ln])).strip() or clean(ci.get("courierName")) or "тХи╨нтХитХб тХитХЬтХитЦСтХитХЦтХитХЬтХитЦСтХд╨ЧтХитХбтХитХЬ"
                    # тХи╨дтХитХЫтХитФРтХитХЫтХитХЧтХитХЬтХитХХтХд╨ТтХитХбтХитХЧтХд╨ЬтХитХЬтХитЦСтХд╨Я тХитХЦтХитЦСтХд╨ЩтХитХХтХд╨ТтХитЦС тХитХЫтХд╨Т "None" тХитЦУ тХитХСтХитХЫтХитХЬтХд╨ЦтХитХб тХитХХтХитХЭтХитХбтХитХЬтХитХХ
                    if " None" in courier_name:
                        courier_name = courier_name.replace(" None", "").strip()

            stype = (clean(o_data.get("orderServiceType")) or "").lower()
            if not stype and isinstance(o_data.get("orderType"), dict):
                stype = (clean((o_data.get("orderType") or {}).get("orderServiceType")) or "").lower()
            
            order_type = "тХи╨дтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХСтХитЦС"
            if any(x in stype for x in ["pickup", "client", "тХд╨СтХитЦСтХитХЭтХитХЫ"]): 
                order_type = "тХи╨▒тХитЦСтХитХЭтХитХЫтХитЦУтХд╨ЫтХитЦУтХитХЫтХитХЦ"
            elif any(x in stype for x in ["common", "table", "тХитХЦтХитЦСтХитХЧ", "тХд╨РтХитХбтХд╨СтХд╨Т"]): 
                order_type = "тХи╨в тХд╨РтХитХбтХд╨СтХд╨ТтХитХЫтХд╨РтХитЦСтХитХЬтХитХб"

            # тХи╨нтХитХЫтХитЦУтХд╨ЫтХитХб тХитФРтХитХЫтХитХЧтХд╨Я тХитФдтХитХЧтХд╨Я тХитФРтХитХЫтХитХЧтХитХЬтХитХЫтХитХг тХитХХтХитХЬтХд╨ФтХитХЫтХд╨РтХитХЭтХитЦСтХд╨ТтХитХХтХитЦУтХитХЬтХитХЫтХд╨СтХд╨ТтХитХХ
            source = clean(o_data.get("source")) or "iiko"
            def parse_dt(dt_str):
                if not dt_str:
                    return None
                try:
                    # ISO 8601 тХд╨С Z тХитХХтХитХЧтХитХХ тХд╨СтХитХЭтХитХбтХд╨ЩтХитХбтХитХЬтХитХХтХитХбтХитХЭ
                    if 'Z' in dt_str or '+' in dt_str or '-' in dt_str[10:]:
                        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                        return dt.astimezone(timezone.utc).replace(tzinfo=None)
                    # тХи╨нтХитЦСтХитХХтХитЦУтХитХЬтХитЦСтХд╨Я тХитФдтХитЦСтХд╨ТтХитЦС - тХд╨СтХд╨ЧтХитХХтХд╨ТтХитЦСтХитХбтХитХЭ тХитХЧтХитХЫтХитХСтХитЦСтХитХЧтХд╨ЬтХитХЬтХитХЫтХитХг тХитФдтХитХЧтХд╨Я тХитХЦтХитЦСтХитЦУтХитХбтХитФдтХитХбтХитХЬтХитХХтХд╨Я
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
            
            # тХи╨┤тХитХЫтХитХЧтХитЦТтХд╨ЭтХитХС тХитХЬтХитЦС тХитЦУтХитХбтХд╨РтХд╨ХтХитХЬтХитХХтХитХг тХд╨УтХд╨РтХитХЫтХитЦУтХитХбтХитХЬтХд╨Ь тХитХЫтХитЦТтХд╨ЪтХитХбтХитХСтХд╨ТтХитЦС тХитХЦтХитЦСтХитХСтХитЦСтХитХЦтХитЦС (iiko Cloud API v2)
            if not expected_time:
                expected_time = parse_dt(o_data.get("completeBefore"))
            if not actual_time:
                actual_time = parse_dt(o_data.get("actualDate"))
            
            # 8. тХи╨┤тХитХХтХитХЬтХитЦСтХитХЧтХд╨ЬтХитХЬтХд╨ЫтХитХб тХд╨ФтХитХЧтХитЦСтХитФВтХитХХ тХитХХ тХд╨СтХитХЫтХд╨ХтХд╨РтХитЦСтХитХЬтХитХбтХитХЬтХитХХтХитХб
            delay = di.get("delayMinutes")
            admin_name = self.clean_str((o_data.get("conformationInfo") or {}).get("confirmedBy"))
            if not admin_name:
                admin_name = self.clean_str((o_data.get("confirmationInfo") or {}).get("confirmedBy"))

            # 8. тХи╨▒тХитХЫтХд╨ХтХд╨РтХитЦСтХитХЬтХитХбтХитХЬтХитХХтХитХб
            order = session.exec(select(Order).where(Order.iiko_order_id == order_id_iiko)).first()
            
            # тХи╨отХитФРтХд╨РтХитХбтХитФдтХитХбтХитХЧтХд╨ЯтХитХбтХитХЭ тХд╨ФтХитХХтХитХЧтХитХХтХитЦСтХитХЧ (branch) тХитФРтХитХЫ terminalGroupId
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
                order.status_history = [{"status": mapped_status, "time": current_time_tz.isoformat(), "comment": "тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитХХтХд╨РтХитХЫтХитЦУтХитЦСтХитХЬ"}]
            else:
                # тХи╨етХд╨СтХитХЧтХитХХ тХитХЦтХитЦСтХитХСтХитЦСтХитХЦ тХд╨УтХитХвтХитХб тХитХбтХд╨СтХд╨ТтХд╨Ь, тХитХЫтХитЦТтХитХЬтХитХЫтХитЦУтХитХЧтХд╨ЯтХитХбтХитХЭ branch_id тХитХбтХд╨СтХитХЧтХитХХ тХитХЫтХитХЬ тХитХХтХитХЦтХитХЭтХитХбтХитХЬтХитХХтХитХЧтХд╨СтХд╨Я
                order.branch_id = branch_id
            
            # --- тХи╨лтХи╨отХи╨гтХи╨итХи╨ктХи╨а тХи╨отХи╨птХи╨░тХи╨етХи╨дтХи╨етХи╨лтХи╨етХи╨нтХи╨итХи╨┐ ASAP / тХи╨птХи╨░тХи╨етХи╨дтХи╨зтХи╨атХи╨ктХи╨атХи╨з ---
            raw_comment = self.clean_str(o_data.get("comment"))
            comment_lower = (raw_comment or "").lower()
            
            # тХи╨бтХитЦСтХитХЦтХитХЫтХитЦУтХд╨ЫтХитХб тХитХЦтХитХЬтХитЦСтХд╨ЧтХитХбтХитХЬтХитХХтХд╨Я тХитХХтХитХЦ iiko (тХитФРтХд╨РтХитХХтХитХЫтХд╨РтХитХХтХд╨ТтХитХбтХд╨Т - тХд╨ФтХитХЧтХитЦСтХитФВтХд╨У isAsap)
            final_is_asap = bool(o_data.get("isAsap", True))
            
            # 1. тХи╨етХд╨СтХитХЧтХитХХ тХд╨ФтХитХЧтХитЦСтХитФВ isAsap тХд╨ЯтХитЦУтХитХЬтХитХЫ False - тХд╨ЭтХд╨ТтХитХЫ тХитФРтХд╨РтХитХбтХитФдтХитХЦтХитЦСтХитХСтХитЦСтХитХЦ
            if o_data.get("isAsap") is False:
                final_is_asap = False
            
            # 2. тХи╨етХд╨СтХитХЧтХитХХ тХитХбтХд╨СтХд╨ТтХд╨Ь тХитЦУтХд╨РтХитХбтХитХЭтХд╨Я тХитФВтХитХЫтХд╨ТтХитХЫтХитЦУтХитХЬтХитХЫтХд╨СтХд╨ТтХитХХ тХитХХ тХитХЫтХитХЬтХитХЫ тХитХЦтХитХЬтХитЦСтХд╨ЧтХитХХтХд╨ТтХитХбтХитХЧтХд╨ЬтХитХЬтХитХЫ тХитХЫтХд╨ТтХитХЧтХитХХтХд╨ЧтХитЦСтХитХбтХд╨ТтХд╨СтХд╨Я тХитХЫтХд╨Т тХитЦУтХд╨РтХитХбтХитХЭтХитХбтХитХЬтХитХХ тХд╨СтХитХЫтХитХЦтХитФдтХитЦСтХитХЬтХитХХтХд╨Я
            if expected_time and iiko_creation_time:
                diff_mins = (expected_time - iiko_creation_time).total_seconds() / 60
                # тХи╨етХд╨СтХитХЧтХитХХ тХд╨РтХитЦСтХитХЦтХитХЬтХитХХтХд╨ЦтХитЦС тХитЦТтХитХЫтХитХЧтХитХбтХитХб 90 тХитХЭтХитХХтХитХЬтХд╨УтХд╨Т - тХд╨СтХитХСтХитХЫтХд╨РтХитХбтХитХб тХитЦУтХд╨СтХитХбтХитФВтХитХЫ тХд╨ЭтХд╨ТтХитХЫ тХитФРтХд╨РтХитХбтХитФдтХитХЦтХитЦСтХитХСтХитЦСтХитХЦ (тХитХЬтХитЦС тХитЦУтХд╨РтХитХбтХитХЭтХд╨Я)
                if diff_mins > 90:
                    final_is_asap = False
            
            # 3. тХи╨дтХитХЫтХитФРтХитХЫтХитХЧтХитХЬтХитХХтХд╨ТтХитХбтХитХЧтХд╨ЬтХитХЬтХд╨ЫтХитХб тХитФРтХд╨РтХитХЫтХитЦУтХитХбтХд╨РтХитХСтХитХХ тХитФРтХитХЫ тХитХСтХитХЫтХитХЭтХитХЭтХитХбтХитХЬтХд╨ТтХитЦСтХд╨РтХитХХтХд╨Ю (тХитХбтХд╨СтХитХЧтХитХХ тХд╨ФтХитХЧтХитЦСтХитФВ тХитЦУтХд╨СтХитХб тХитХбтХд╨ЩтХитХб True)
            if final_is_asap:
                if "тХитХЬтХитЦС тХитЦУтХд╨РтХитХбтХитХЭтХд╨Я" in comment_lower or "тХитФРтХд╨РтХитХбтХитФдтХитХЦтХитЦСтХитХСтХитЦСтХитХЦ" in comment_lower:
                    final_is_asap = False
            
            # 4. тХи╨етХд╨СтХитХЧтХитХХ тХитЦУ тХитХСтХитХЫтХитХЭтХитХЭтХитХбтХитХЬтХд╨ТтХитХб тХи╨нтХи╨етХи╨▓ тХитХСтХитХЧтХд╨ЮтХд╨ЧтХитХбтХитЦУтХд╨ЫтХд╨Х тХд╨СтХитХЧтХитХЫтХитЦУ тХитФРтХд╨РтХитХбтХитФдтХитХЦтХитЦСтХитХСтХитЦСтХитХЦтХитЦС, тХитХЬтХитХЫ тХитХбтХд╨СтХд╨ТтХд╨Ь тХитФдтХд╨РтХд╨УтХитФВтХитХЫтХитХг тХд╨ТтХитХбтХитХСтХд╨СтХд╨Т, 
            # тХитХХ тХитФРтХд╨РтХитХХ тХд╨ЭтХд╨ТтХитХЫтХитХЭ тХитЦУтХд╨РтХитХбтХитХЭтХд╨Я тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХСтХитХХ тХитЦТтХитХЧтХитХХтХитХЦтХитХСтХитХЫ тХитХС тХитЦУтХд╨РтХитХбтХитХЭтХитХбтХитХЬтХитХХ тХд╨СтХитХЫтХитХЦтХитФдтХитЦСтХитХЬтХитХХтХд╨Я - тХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХЧтХд╨ЯтХитХбтХитХЭ ASAP
            elif raw_comment and "тХитХЬтХитЦС тХитЦУтХд╨РтХитХбтХитХЭтХд╨Я" not in comment_lower and "тХитФРтХд╨РтХитХбтХитФдтХитХЦтХитЦСтХитХСтХитЦСтХитХЦ" not in comment_lower:
                if expected_time and iiko_creation_time:
                    diff_mins = (expected_time - iiko_creation_time).total_seconds() / 60
                    if diff_mins < 90:
                        final_is_asap = True

            # 3. тХи╨етХд╨СтХитХЧтХитХХ тХитЦУтХд╨РтХитХбтХитХЭтХд╨Я тХитФВтХитХЫтХд╨ТтХитХЫтХитЦУтХитХЬтХитХЫтХд╨СтХд╨ТтХитХХ тХитХХтХитХЦтХитХЭтХитХбтХитХЬтХитХХтХитХЧтХитХЫтХд╨СтХд╨Ь тХитЦУ тХитФРтХд╨РтХитХЫтХд╨ЦтХитХбтХд╨СтХд╨СтХитХб (тХд╨СтХд╨РтХитЦСтХитЦУтХитХЬтХитХХтХитЦУтХитЦСтХитХбтХитХЭ тХд╨С тХд╨УтХитХвтХитХб тХд╨СтХд╨УтХд╨ЩтХитХбтХд╨СтХд╨ТтХитЦУтХд╨УтХд╨ЮтХд╨ЩтХитХХтХитХЭ тХитХЦтХитЦСтХитХСтХитЦСтХитХЦтХитХЫтХитХЭ тХитЦУ тХи╨бтХи╨д)
            if order and order.expected_time and expected_time:
                # тХи╨бтХитХбтХитХЦтХитХЫтХитФРтХитЦСтХд╨СтХитХЬтХитХЫтХитХб тХитЦУтХд╨ЫтХд╨ЧтХитХХтХд╨ТтХитЦСтХитХЬтХитХХтХитХб naive/aware
                oe = order.expected_time.replace(tzinfo=None) if order.expected_time.tzinfo else order.expected_time
                ne = expected_time.replace(tzinfo=None) if expected_time.tzinfo else expected_time
                if abs((oe - ne).total_seconds()) > 60:
                    final_is_asap = False

            # тХи╨┤тХитХХтХитХЬтХитЦСтХитХЧтХд╨ЬтХитХЬтХд╨ЫтХитХб тХд╨ФтХитХЧтХитЦСтХитФВтХитХХ
            is_asap = final_is_asap
            is_on_time = not final_is_asap

            # тХи╨втХитХЫтХд╨СтХд╨СтХд╨ТтХитЦСтХитХЬтХитЦСтХитЦУтХитХЧтХитХХтХитЦУтХитЦСтХитХбтХитХЭ тХитХЧтХитХЫтХитФВтХитХХтХитХСтХд╨У тХитХХтХд╨СтХд╨ТтХитХЫтХд╨РтХитХХтХитХХ тХд╨СтХд╨ТтХитЦСтХд╨ТтХд╨УтХд╨СтХитХЫтХитЦУ
            if order.id and order.status != mapped_status:
                h = list(order.status_history or [])
                h.append({"status": mapped_status, "time": current_time_tz.isoformat(), "comment": f"iiko: {raw_status}"})
                order.status_history = h
                sql_flag_modified(order, "status_history")

            # тХи╨мтХитЦСтХитФРтХитФРтХитХХтХитХЬтХитФВ тХитЦУтХд╨СтХитХбтХд╨Х тХитФРтХитХЫтХитХЧтХитХбтХитХг
            order.status = mapped_status
            order.external_number = external_number or order.external_number
            order.customer_name = full_customer_name
            order.customer_phone = phone
            order.courier_name = courier_name
            
            # тХи╨отХитЦТтХитХЬтХитХЫтХитЦУтХитХЧтХд╨ЯтХитХбтХитХЭ тХитЦСтХитФдтХд╨РтХитХбтХд╨СтХитХЬтХд╨ЫтХитХб тХитФРтХитХЫтХитХЧтХд╨Я тХд╨ТтХитХЫтХитХЧтХд╨ЬтХитХСтХитХЫ тХитХбтХд╨СтХитХЧтХитХХ тХитЦУ тХитХЬтХитХЫтХитЦУтХитХЫтХитХЭ тХитФРтХитЦСтХитХСтХитХбтХд╨ТтХитХб тХитХбтХд╨СтХд╨ТтХд╨Ь тХд╨РтХитХбтХитЦСтХитХЧтХд╨ЬтХитХЬтХд╨ЫтХитХг тХитЦСтХитФдтХд╨РтХитХбтХд╨С
            # тХи╨итХи╨лтХи╨и тХитХбтХд╨СтХитХЧтХитХХ тХитЦУ тХи╨бтХи╨д тХитЦСтХитФдтХд╨РтХитХбтХд╨С тХитХбтХд╨ЩтХитХб тХитХЬтХитХб тХитХЦтХитЦСтХитФРтХитХЫтХитХЧтХитХЬтХитХбтХитХЬ (тХитФВтХитХЫтХд╨РтХитХЫтХитФд тХитХЬтХитХб тХд╨СтХд╨ЧтХитХХтХд╨ТтХитЦСтХитХбтХд╨ТтХд╨СтХд╨Я тХитХЦтХитЦСтХитФРтХитХЫтХитХЧтХитХЬтХитХбтХитХЬтХитХЬтХд╨ЫтХитХЭ тХитЦСтХитФдтХд╨РтХитХбтХд╨СтХитХЫтХитХЭ)
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
            
            # тХи╨▓тХитХбтХд╨РтХитХЭтХитХХтХитХЬтХитЦСтХитХЧтХд╨ЬтХитХЬтХитЦСтХд╨Я тХитФВтХд╨РтХд╨УтХитФРтХитФРтХитЦС
            order.terminal_group_id = terminal_group_id or order.terminal_group_id
            order.terminal_group_name = terminal_group_name or order.terminal_group_name
            
            # тХи╨дтХитХЫтХитФР. тХитФРтХитХЫтХитХЧтХд╨Я
            order.source = source
            order.iiko_creation_time = iiko_creation_time or order.iiko_creation_time
            order.expected_time = expected_time or order.expected_time
            order.actual_time = actual_time or order.actual_time
            order.is_on_time = is_on_time
            order.is_asap = is_asap
            order.delay_minutes = delay
            order.admin_name = admin_name or order.admin_name

            # --- тХи╨отХитФРтХд╨РтХитХбтХитФдтХитХбтХитХЧтХитХбтХитХЬтХитХХтХитХб тХитХЦтХитХЫтХитХЬтХд╨Ы тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХСтХитХХ тХитФРтХитХЫ тХитЦСтХитФдтХд╨РтХитХбтХд╨СтХд╨У ---
            # 1. тХи╨птХд╨РтХитХЫтХитЦУтХитХбтХд╨РтХд╨ЯтХитХбтХитХЭ тХитХСтХитХЫтХитХЫтХд╨РтХитФдтХитХХтХитХЬтХитЦСтХд╨ТтХд╨Ы тХитХЬтХитЦСтХитФРтХд╨РтХд╨ЯтХитХЭтХд╨УтХд╨Ю тХитХХтХитХЦ iiko (deliveryPoint)
            coords_iiko = dp.get("coordinates", {})
            lat_iiko = coords_iiko.get("latitude")
            lng_iiko = coords_iiko.get("longitude")
            
            # тХи╨етХд╨СтХитХЧтХитХХ тХд╨ЭтХд╨ТтХитХЫ тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХСтХитЦС, тХитФРтХд╨ЫтХд╨ТтХитЦСтХитХбтХитХЭтХд╨СтХд╨Я тХитХЫтХитФРтХд╨РтХитХбтХитФдтХитХбтХитХЧтХитХХтХд╨ТтХд╨Ь тХитХЦтХитХЫтХитХЬтХд╨У
            if order_type == "тХи╨дтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХСтХитЦС":
                logger.info(f"Auto-detecting zone for order {order_id_iiko}")
                
                # тХи╨птХд╨РтХитХХтХитХЫтХд╨РтХитХХтХд╨ТтХитХбтХд╨Т 1: тХи╨ктХитХЫтХитХЫтХд╨РтХитФдтХитХХтХитХЬтХитЦСтХд╨ТтХд╨Ы тХитХХтХитХЦ iiko
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

                # тХи╨птХд╨РтХитХХтХитХЫтХд╨РтХитХХтХд╨ТтХитХбтХд╨Т 2: тХи╨гтХитХбтХитХЫтХитХСтХитХЫтХитФдтХитХбтХд╨Р (тХитХбтХд╨СтХитХЧтХитХХ тХитХЦтХитХЫтХитХЬтХитЦС тХитХбтХд╨ЩтХитХб тХитХЬтХитХб тХитХЫтХитФРтХд╨РтХитХбтХитФдтХитХбтХитХЧтХитХбтХитХЬтХитЦС)
                if not order.resolved_delivery_zone_id:
                    # тХи╨птХд╨ЫтХд╨ТтХитЦСтХитХбтХитХЭтХд╨СтХд╨Я тХитХЫтХитФРтХд╨РтХитХбтХитФдтХитХбтХитХЧтХитХХтХд╨ТтХд╨Ь тХитХЦтХитХЫтХитХЬтХд╨У тХд╨ТтХитХЫтХитХЧтХд╨ЬтХитХСтХитХЫ тХитХбтХд╨СтХитХЧтХитХХ тХитХбтХд╨СтХд╨ТтХд╨Ь тХитЦСтХитФдтХд╨РтХитХбтХд╨СтХитХЬтХд╨ЫтХитХб тХитФдтХитЦСтХитХЬтХитХЬтХд╨ЫтХитХб
                    # тХи╨▓тХитХбтХитФРтХитХбтХд╨РтХд╨Ь тХитХЭтХд╨Ы тХитЦТтХитХЫтХитХЧтХитХбтХитХб тХитХЧтХитХЫтХд╨ЯтХитХЧтХд╨ЬтХитХЬтХд╨Ы тХитХС тХитХСтХитХЫтХитХЭтХитФРтХитХЫтХитХЬтХитХбтХитХЬтХд╨ТтХитЦСтХитХЭ: тХитХбтХд╨СтХитХЧтХитХХ тХитХбтХд╨СтХд╨ТтХд╨Ь тХд╨ХтХитХЫтХд╨ТтХд╨Я тХитЦТтХд╨Ы тХд╨СтХд╨ТтХд╨РтХитХЫтХитХСтХитЦС тХитЦСтХитФдтХд╨РтХитХбтХд╨СтХитЦС
                    full_addr_str = delivery_address if (delivery_address and delivery_address != "тХи╨▒тХитЦСтХитХЭтХитХЫтХитЦУтХд╨ЫтХитЦУтХитХЫтХитХЦ") else None
                    
                    if full_addr_str or (city and street_name):
                        try:
                            # тХи╨етХд╨СтХитХЧтХитХХ тХитХСтХитХЫтХитХЭтХитФРтХитХЫтХитХЬтХитХбтХитХЬтХд╨ТтХитХЫтХитЦУ тХитХЬтХитХбтХд╨Т, тХитХЬтХитХЫ тХитХбтХд╨СтХд╨ТтХд╨Ь тХд╨СтХд╨ТтХд╨РтХитХЫтХитХСтХитЦС - iiko_service.check_address_zone 
                            # тХитЦУтХд╨СтХитХб тХд╨РтХитЦСтХитЦУтХитХЬтХитХЫ тХитФРтХитХЫтХитФРтХд╨РтХитХЫтХитЦТтХд╨УтХитХбтХд╨Т тХитФВтХитХбтХитХЫтХитХСтХитХЫтХитФдтХитХХтХд╨РтХитХЫтХитЦУтХитЦСтХд╨ТтХд╨Ь (тХитХЭтХд╨Ы тХитФРтХитХбтХд╨РтХитХбтХитФдтХитЦСтХитФдтХитХХтХитХЭ тХитХбтХитХг тХитХСтХитХЫтХитХЭтХитФРтХитХЫтХитХЬтХитХбтХитХЬтХд╨ТтХд╨Ы, тХитФдтХитЦСтХитХвтХитХб тХитХбтХд╨СтХитХЧтХитХХ тХитХЫтХитХЬтХитХХ тХитФРтХд╨УтХд╨СтХд╨ТтХд╨ЫтХитХб)
                            zone_data = await iiko_service.check_address_zone(
                                city=city or city_from_settings or "тХи╨▓тХд╨ЮтХитХЭтХитХбтХитХЬтХд╨Ь",
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
            
            elif order_type == "тХи╨▒тХитЦСтХитХЭтХитХЫтХитЦУтХд╨ЫтХитЦУтХитХЫтХитХЦ":
                order.delivery_zone = "тХд╨СтХитЦСтХитХЭтХитХЫтХитЦУтХд╨ЫтХитЦУтХитХЫтХитХЦ"
                order.resolved_delivery_zone_id = None
                logger.info(f"Order {order_id_iiko}: Type is Pickup, skipping zone detection")
            # ---------------------------------------------

            # --- тХи╨нтХи╨отХи╨втХи╨атХи╨┐ тХи╨лтХи╨отХи╨гтХи╨итХи╨ктХи╨а тХи╨▒тХи╨отХи╨▒тХи╨▓тХи╨атХи╨втХи╨а тХи╨зтХи╨атХи╨ктХи╨атХи╨зтХи╨а (тХд╨С тХитХХтХитХЭтХитХбтХитХЬтХитЦСтХитХЭтХитХХ тХитХХ тХитХЦтХитЦСтХд╨ЩтХитХХтХд╨ТтХитХЫтХитХг тХитХЫтХд╨Т тХитХЦтХитЦСтХд╨ТтХитХХтХд╨РтХитЦСтХитХЬтХитХХтХд╨Я) ---
            
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
                        
                # тХи╨дтХитХЫтХд╨СтХд╨ТтХитЦСтХитХбтХитХЭ тХитХЬтХитЦСтХитХЦтХитЦУтХитЦСтХитХЬтХитХХтХд╨Я тХитХХтХитХЦ тХитХЧтХитХЫтХитХСтХитЦСтХитХЧтХд╨ЬтХитХЬтХитХЫтХитХг тХитЦТтХитЦСтХитХЦтХд╨Ы
                db_products = session.exec(select(Product).where(Product.iiko_id.in_(product_ids))).all()
                prod_map = {p.iiko_id: p.name for p in db_products}

                # тХи╨дтХитХЫтХд╨СтХд╨ТтХитЦСтХитХбтХитХЭ тХд╨СтХд╨ТтХитЦСтХд╨РтХд╨ЫтХитХб тХитХЬтХитЦСтХитХЦтХитЦУтХитЦСтХитХЬтХитХХтХд╨Я тХитХХтХитХЦ тХд╨ТтХитХбтХитХСтХд╨УтХд╨ЩтХитХбтХитФВтХитХЫ тХд╨СтХитХЫтХд╨СтХд╨ТтХитХЫтХд╨ЯтХитХЬтХитХХтХд╨Я тХитХЦтХитЦСтХитХСтХитЦСтХитХЦтХитЦС
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
                        if old_pid and old_name and old_name != "тХи╨нтХитХбтХитХХтХитХЦтХитЦУтХитХбтХд╨СтХд╨ТтХитХЬтХд╨ЫтХитХг тХд╨ТтХитХЫтХитЦУтХитЦСтХд╨Р":
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
                            if old_mpid and old_mname and old_mname != "тХи╨мтХитХЫтХитФдтХитХХтХд╨ФтХитХХтХитХСтХитЦСтХд╨ТтХитХЫтХд╨Р":
                                old_names_map[old_mpid] = old_mname
                
                for item in raw_items:
                    enriched_item = item.copy()
                    pid = item.get("productId")
                    
                    # тХи╨птХд╨РтХитХХтХитХЫтХд╨РтХитХХтХд╨ТтХитХбтХд╨Т тХитХХтХитХЭтХитХбтХитХЬтХитХХ: product.name -> primaryComponent.product.name -> productName -> тХи╨бтХи╨д -> тХи╨итХд╨СтХд╨ТтХитХЫтХд╨РтХитХХтХд╨Я -> Fallback
                    if not enriched_item.get("name") or enriched_item.get("name") == "тХи╨нтХитХбтХитХХтХитХЦтХитЦУтХитХбтХд╨СтХд╨ТтХитХЬтХд╨ЫтХитХг тХд╨ТтХитХЫтХитЦУтХитЦСтХд╨Р":
                        enriched_item["name"] = (
                            enriched_item.get("product", {}).get("name") or 
                            enriched_item.get("primaryComponent", {}).get("product", {}).get("name") or 
                            enriched_item.get("productName") or 
                            prod_map.get(pid) or 
                            old_names_map.get(pid) or 
                            "тХи╨нтХитХбтХитХХтХитХЦтХитЦУтХитХбтХд╨СтХд╨ТтХитХЬтХд╨ЫтХитХг тХд╨ТтХитХЫтХитЦУтХитЦСтХд╨Р"
                        )
                    
                    if not enriched_item.get("sum"):
                        enriched_item["sum"] = float(enriched_item.get("amount", 0)) * float(enriched_item.get("price", 0))
                        
                    enriched_mods = []
                    for mod in (item.get("modifiers") or []):
                        if not mod: continue
                        emod = mod.copy()
                        mpid = mod.get("productId")
                        
                        if not emod.get("name") or emod.get("name") == "тХи╨мтХитХЫтХитФдтХитХХтХд╨ФтХитХХтХитХСтХитЦСтХд╨ТтХитХЫтХд╨Р":
                            emod["name"] = (
                                emod.get("product", {}).get("name") or 
                                emod.get("primaryComponent", {}).get("product", {}).get("name") or 
                                prod_map.get(mpid) or 
                                old_names_map.get(mpid) or 
                                "тХи╨мтХитХЫтХитФдтХитХХтХд╨ФтХитХХтХитХСтХитЦСтХд╨ТтХитХЫтХд╨Р"
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
            # тХи╨мтХд╨Ы тХитХЬтХитХб тХитФдтХитХбтХитХЧтХитЦСтХитХбтХитХЭ rollback тХитХЦтХитФдтХитХбтХд╨СтХд╨Ь, тХд╨ЧтХд╨ТтХитХЫтХитЦТтХд╨Ы тХитХЫтХитФдтХитХХтХитХЬ тХитЦТтХитХХтХд╨ТтХд╨ЫтХитХг тХитХЦтХитЦСтХитХСтХитЦСтХитХЦ тХитХЬтХитХб тХитХЫтХд╨ТтХитХЭтХитХбтХитХЬтХд╨ЯтХитХЧ тХитЦУтХд╨СтХд╨б, 
            # тХитХЬтХитХЫ тХитХХ тХитХЬтХитХб тХитХСтХитХЫтХитХЭтХитХЭтХитХХтХд╨ТтХитХХтХитХЭ тХд╨ЧтХитЦСтХд╨СтХд╨ТтХитХХтХд╨ЧтХитХЬтХд╨ЫтХитХб тХитФдтХитЦСтХитХЬтХитХЬтХд╨ЫтХитХб.
            try:
                session.rollback()
            except:
                pass

    async def sync_orders(self, session: Session, hours: int = 24):
        """
        тХи╨┤тХитХЫтХитХЬтХитХЫтХитЦУтХитЦСтХд╨Я тХитХЦтХитЦСтХитФдтХитЦСтХд╨ЧтХитЦС тХитХЭтХитЦСтХд╨СтХд╨СтХитХЫтХитЦУтХитХЫтХитХг тХд╨СтХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХитХХ тХитХЦтХитЦСтХитХСтХитЦСтХитХЦтХитХЫтХитЦУ.
        тХи╨итХд╨СтХитФРтХитХЫтХитХЧтХд╨ЬтХитХЦтХд╨УтХитХбтХд╨ТтХд╨СтХд╨Я тХитФдтХитХЧтХд╨Я тХитЦСтХитХСтХд╨ТтХд╨УтХитЦСтХитХЧтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХитХХ тХд╨СтХд╨ТтХитЦСтХд╨ТтХд╨УтХд╨СтХитХЫтХитЦУ (тХитХЬтХитЦС тХд╨СтХитХЧтХд╨УтХд╨ЧтХитЦСтХитХг тХитФРтХд╨РтХитХЫтХитФРтХд╨УтХд╨СтХитХСтХитЦС тХитЦУтХитХбтХитЦТтХд╨ХтХд╨УтХитХСтХитХЫтХитЦУ).
        """
        log = SyncLog(sync_type="orders", status="running")
        session.add(log)
        session.commit()
        
        try:
            settings_db = session.exec(select(IikoSettings)).first()
            if not settings_db or not settings_db.organization_id:
                logger.warning("Iiko settings not found, sync aborted")
                log.status = "error"
                log.details = "тХи╨нтХитЦСтХд╨СтХд╨ТтХд╨РтХитХЫтХитХгтХитХСтХитХХ Iiko тХитХЬтХитХб тХитХЬтХитЦСтХитХгтХитФдтХитХбтХитХЬтХд╨Ы"
                session.add(log)
                session.commit()
                return
                
            org_id = settings_db.organization_id
        
            # тХи╨отХитФРтХд╨РтХитХбтХитФдтХитХбтХитХЧтХд╨ЯтХитХбтХитХЭ тХитХХтХитХЬтХд╨ТтХитХбтХд╨РтХитЦУтХитЦСтХитХЧ тХитХЬтХитЦС тХитХЫтХд╨СтХитХЬтХитХЫтХитЦУтХитХб тХд╨ЧтХитЦСтХд╨СтХитХЫтХитЦУтХитХЫтХитФВтХитХЫ тХитФРтХитХЫтХд╨ЯтХд╨СтХитЦС тХитХХтХитХЦ тХитХЬтХитЦСтХд╨СтХд╨ТтХд╨РтХитХЫтХитХбтХитХС
            from app.core.datetime_utils import get_tz_name, get_local_now
            tz_name = get_tz_name(session)
            now = get_local_now(tz_name)
            
            # тХи╨отХитФВтХд╨РтХитЦСтХитХЬтХитХХтХд╨ЧтХитХХтХитЦУтХитЦСтХитХбтХитХЭ тХитФдтХитХХтХитЦСтХитФРтХитЦСтХитХЦтХитХЫтХитХЬ: 24 тХд╨ЧтХитЦСтХд╨СтХитЦС тХитХЬтХитЦСтХитХЦтХитЦСтХитФд тХитХХ 24 тХд╨ЧтХитЦСтХд╨СтХитЦС тХитЦУтХитФРтХитХбтХд╨РтХитХбтХитФд (тХитХХтХд╨ТтХитХЫтХитФВтХитХЫ 48 тХд╨ЧтХитЦСтХд╨СтХитХЫтХитЦУ тХд╨СтХитХЫтХитФВтХитХЧтХитЦСтХд╨СтХитХЬтХитХЫ тХд╨ТтХд╨РтХитХбтХитЦТтХитХЫтХитЦУтХитЦСтХитХЬтХитХХтХд╨Ю)
            date_from = now - timedelta(hours=24)
            date_to = now + timedelta(hours=24)
            
            logger.info(f"Mass sync starting: orders from {date_from} to {date_to} for org {org_id}")
            
            all_ids = set()

            # 0. тХи╨итХитХЬтХитХСтХд╨РтХитХбтХитХЭтХитХбтХитХЬтХд╨ТтХитЦСтХитХЧтХд╨ЬтХитХЬтХитЦСтХд╨Я тХд╨СтХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитФРтХитХЫ тХд╨РтХитХбтХитЦУтХитХХтХитХЦтХитХХтХд╨ЯтХитХЭ (тХитЦТтХд╨ЫтХд╨СтХд╨ТтХд╨РтХд╨ЫтХитХг catch-up тХитФРтХд╨РтХитХЫтХитФРтХд╨УтХд╨ЩтХитХбтХитХЬтХитХЬтХд╨ЫтХд╨Х тХитЦУтХитХбтХитЦТтХд╨ХтХд╨УтХитХСтХитХЫтХитЦУ)
            # тХи╨мтХд╨Ы тХитЦУтХитХЫтХитХЦтХитЦУтХд╨РтХитЦСтХд╨ЩтХитЦСтХитХбтХитХЭ тХитХбтХд╨б, тХд╨ТтХитЦСтХитХС тХитХСтХитЦСтХитХС тХитХЫтХитХЬтХитЦС тХитХЬтХитЦСтХитФдтХитХбтХитХвтХитХЬтХитХбтХитХб тХитФдтХитХЧтХд╨Я тХитФРтХитХЫтХитХХтХд╨СтХитХСтХитЦС тХитХХтХитХЦтХитХЭтХитХбтХитХЬтХитХбтХитХЬтХитХХтХитХг тХитЦТтХитХбтХитХЦ тХитФРтХитХбтХд╨РтХитХбтХитЦТтХитХЫтХд╨РтХитЦС тХитЦУтХд╨СтХитХбтХд╨Х тХитФдтХитЦСтХд╨Т.
            try:
                await self.sync_orders_by_revision(session, org_id)
            except Exception as rev_err:
                logger.error(f"Revision sync failed, falling back to date polling: {rev_err}")

            # 1. тХи╨итХитХЦ iiko Cloud (тХитФРтХитХЫ тХитФдтХитЦСтХд╨ТтХитЦСтХитХЭ тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХСтХитХХ) - тХитХСтХитЦСтХитХС тХд╨СтХд╨ТтХд╨РтХитЦСтХд╨ХтХитХЫтХитЦУтХитХЫтХд╨ЧтХитХЬтХд╨ЫтХитХг тХитХЭтХитХбтХд╨ХтХитЦСтХитХЬтХитХХтХитХЦтХитХЭ
            # тХи╨мтХд╨Ы тХитЦУтХд╨СтХитХбтХитФВтХитФдтХитЦС тХитХХтХд╨СтХитФРтХитХЫтХитХЧтХд╨ЬтХитХЦтХд╨УтХитХбтХитХЭ тХд╨РтХитЦСтХитХЦтХитЦТтХитХХтХитХбтХитХЬтХитХХтХитХб тХитХЬтХитЦС тХд╨ЧтХитЦСтХитХЬтХитХСтХитХХ, тХд╨ТтХитЦСтХитХС тХитХСтХитЦСтХитХС тХд╨ЭтХд╨ТтХитХЫ тХд╨СтХитЦСтХитХЭтХд╨ЫтХитХг тХитХЬтХитЦСтХитФдтХитХбтХитХвтХитХЬтХд╨ЫтХитХг тХд╨СтХитФРтХитХЫтХд╨СтХитХЫтХитЦТ тХитХХтХитХЦтХитЦТтХитХбтХитХвтХитЦСтХд╨ТтХд╨Ь TOO_MANY_DATA_REQUESTED
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
                        log_error=True # тХи╨▓тХитХбтХитФРтХитХбтХд╨РтХд╨Ь тХитХЧтХитХЫтХитФВтХитХХтХд╨РтХд╨УтХитХбтХитХЭ, тХд╨ЧтХд╨ТтХитХЫтХитЦТтХд╨Ы тХитЦУтХитХХтХитФдтХитХбтХд╨ТтХд╨Ь тХитФРтХитХЫтХд╨ЧтХитХбтХитХЭтХд╨У тХитФРтХд╨УтХд╨СтХд╨ТтХитХЫ
                    )
                    if batch:
                        logger.info(f"Fetched {len(batch)} orders for period {chunk_start} - {chunk_end}")
                        cloud_orders.extend(batch)
                    
                    # тХи╨нтХитХбтХитЦТтХитХЫтХитХЧтХд╨ЬтХд╨ШтХитЦСтХд╨Я тХитФРтХитЦСтХд╨УтХитХЦтХитЦС тХитХЭтХитХбтХитХвтХитФдтХд╨У тХд╨ЧтХитЦСтХитХЬтХитХСтХитЦСтХитХЭтХитХХ тХитФдтХитХЧтХд╨Я тХд╨СтХд╨ТтХитЦСтХитЦТтХитХХтХитХЧтХд╨ЬтХитХЬтХитХЫтХд╨СтХд╨ТтХитХХ
                    await asyncio.sleep(0.5)
                except Exception as chunk_err:
                    logger.error(f"Failed to fetch orders chunk ({chunk_start} - {chunk_end}): {chunk_err}")
                    if "429" in str(chunk_err):
                        await asyncio.sleep(5.0)
                
                chunk_start = chunk_end

            for o in cloud_orders:
                if o.get("id"): all_ids.add(o["id"])
            logger.info(f"Found {len(cloud_orders)} orders in Cloud (via date polling)")
                
            # 2. тХи╨итХитХЦ iiko Resto (тХитХбтХд╨СтХитХЧтХитХХ тХитХЬтХитЦСтХд╨СтХд╨ТтХд╨РтХитХЫтХитХбтХитХЬ)
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
                    
            # 3. тХи╨дтХитХЫтХитФРтХитХЫтХитХЧтХитХЬтХитХХтХд╨ТтХитХбтХитХЧтХд╨ЬтХитХЬтХитХЫ: тХи╨птХд╨РтХитХХтХитХЬтХд╨УтХитФдтХитХХтХд╨ТтХитХбтХитХЧтХд╨ЬтХитХЬтХитХЫ тХитФРтХд╨РтХитХЫтХитЦУтХитХбтХд╨РтХд╨ЯтХитХбтХитХЭ тХитЦУтХд╨СтХитХб тХитЦСтХитХСтХд╨ТтХитХХтХитЦУтХитХЬтХд╨ЫтХитХб тХитХЦтХитЦСтХитХСтХитЦСтХитХЦтХд╨Ы тХитХХтХитХЦ тХитХЬтХитЦСтХд╨ШтХитХбтХитХг тХи╨бтХи╨д
            # тХи╨╜тХд╨ТтХитХЫ тХитХСтХд╨РтХитХХтХд╨ТтХитХХтХд╨ЧтХитХбтХд╨СтХитХСтХитХХ тХитЦУтХитЦСтХитХвтХитХЬтХитХЫ, тХитХбтХд╨СтХитХЧтХитХХ iiko Cloud API тХитФРтХитХЫ тХитФдтХитЦСтХд╨ТтХитЦСтХитХЭ тХд╨РтХитЦСтХитЦТтХитХЫтХд╨ТтХитЦСтХитХбтХд╨Т тХитХЬтХитХбтХд╨СтХд╨ТтХитЦСтХитЦТтХитХХтХитХЧтХд╨ЬтХитХЬтХитХЫ тХитХХтХитХЧтХитХХ тХитЦУтХитХбтХитЦТтХд╨ХтХд╨УтХитХСтХитХХ тХитФРтХд╨РтХитХЫтХитФРтХд╨УтХд╨ЩтХитХбтХитХЬтХд╨Ы
            try:
                # тХи╨втХитХСтХитХЧтХд╨ЮтХд╨ЧтХитЦСтХитХбтХитХЭ тХитЦУтХд╨СтХитХб тХд╨СтХд╨ТтХитЦСтХд╨ТтХд╨УтХд╨СтХд╨Ы, тХитХСтХитХЫтХд╨ТтХитХЫтХд╨РтХд╨ЫтХитХб тХитХЬтХитХб тХд╨ЯтХитЦУтХитХЧтХд╨ЯтХд╨ЮтХд╨ТтХд╨СтХд╨Я тХд╨ФтХитХХтХитХЬтХитЦСтХитХЧтХд╨ЬтХитХЬтХд╨ЫтХитХЭтХитХХ (тХитХЦтХитЦСтХитХСтХд╨РтХд╨ЫтХд╨Т/тХитХЫтХд╨ТтХитХЭтХитХбтХитХЬтХитХбтХитХЬ)
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
                
                # тХи╨▓тХитЦСтХитХСтХитХвтХитХб тХитФдтХитХЫтХитЦТтХитЦСтХитЦУтХитХХтХитХЭ тХд╨СтХд╨ТтХд╨РтХитХЫтХитХСтХитХЫтХитЦУтХд╨ЫтХитХб тХитФРтХд╨РтХитХбтХитФдтХд╨СтХд╨ТтХитЦСтХитЦУтХитХЧтХитХбтХитХЬтХитХХтХд╨Я тХитХЬтХитЦС тХд╨СтХитХЧтХд╨УтХд╨ЧтХитЦСтХитХг, тХитХбтХд╨СтХитХЧтХитХХ тХитЦУ тХи╨бтХи╨д тХитХЦтХитЦСтХитХСтХд╨РтХитЦСтХитХЧтХитХХтХд╨СтХд╨Ь тХд╨СтХд╨ТтХитЦСтХд╨РтХд╨ЫтХитХб тХитХЦтХитХЬтХитЦСтХд╨ЧтХитХбтХитХЬтХитХХтХд╨Я
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
                    # тХи╨дтХитХЫтХитЦТтХитЦСтХитЦУтХитХЧтХд╨ЯтХитХбтХитХЭ тХитХЬтХитХбтХитЦТтХитХЫтХитХЧтХд╨ЬтХд╨ШтХд╨УтХд╨Ю тХитХЦтХитЦСтХитФдтХитХбтХд╨РтХитХвтХитХСтХд╨У, тХд╨ЧтХд╨ТтХитХЫтХитЦТтХд╨Ы тХитХЬтХитХб тХитФРтХд╨РтХитХбтХитЦУтХд╨ЫтХд╨СтХитХХтХд╨ТтХд╨Ь тХитХЧтХитХХтХитХЭтХитХХтХд╨ТтХд╨Ы API (429) 
                    if success_count > 0 and success_count % 15 == 0:
                        await asyncio.sleep(0.5)

                    # тХи╨итХд╨СтХитФРтХитХЫтХитХЧтХд╨ЬтХитХЦтХд╨УтХитХбтХитХЭ sync_order_by_id тХитФдтХитХЧтХд╨Я тХитХСтХитЦСтХитХвтХитФдтХитХЫтХитФВтХитХЫ тХитХЦтХитЦСтХитХСтХитЦСтХитХЦтХитЦС
                    # тХи╨мтХд╨Ы тХитХЬтХитХб тХд╨ХтХитХЫтХд╨ТтХитХХтХитХЭ, тХд╨ЧтХд╨ТтХитХЫтХитЦТтХд╨Ы тХитХЫтХд╨ШтХитХХтХитЦТтХитХСтХитЦС тХитЦУ тХитХЫтХитФдтХитХЬтХитХЫтХитХЭ тХитХЦтХитЦСтХитХСтХитЦСтХитХЦтХитХб тХитФРтХд╨РтХитХбтХд╨РтХитЦУтХитЦСтХитХЧтХитЦС тХитЦУтХитХбтХд╨СтХд╨Ь тХд╨ЦтХитХХтХитХСтХитХЧ
                    res = await self.sync_order_by_id(session, order_id, org_id)
                    if res: success_count += 1
                except Exception as e:
                    logger.error(f"Failed to sync order {order_id}: {e}")
                    
            logger.info(f"Mass sync finished. Total: {len(all_ids)}, Success: {success_count}")
            log.status = "success"
            log.processed_count = success_count
            log.details = f"тХи╨│тХд╨СтХитФРтХитХбтХд╨ШтХитХЬтХитХЫ тХд╨СтХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитХХтХд╨РтХитХЫтХитЦУтХитЦСтХитХЬтХитХЫ {success_count} тХитХЦтХитЦСтХитХСтХитЦСтХитХЦтХитХЫтХитЦУ тХитХХтХитХЦ {len(all_ids)}"
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
        тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитХЦтХитЦСтХитХСтХитЦСтХитХЦтХитХЫтХитЦУ тХитФРтХитХЫ тХд╨РтХитХбтХитЦУтХитХХтХитХЦтХитХХтХд╨ЯтХитХЭ (catch-up).
        тХи╨птХитХЫтХитХЦтХитЦУтХитХЫтХитХЧтХд╨ЯтХитХбтХд╨Т тХитХЬтХитЦСтХитХгтХд╨ТтХитХХ тХитХЦтХитЦСтХитХСтХитЦСтХитХЦтХд╨Ы, тХитХСтХитХЫтХд╨ТтХитХЫтХд╨РтХд╨ЫтХитХб тХитЦТтХд╨ЫтХитХЧтХитХХ тХитФРтХд╨РтХитХЫтХитФРтХд╨УтХд╨ЩтХитХбтХитХЬтХд╨Ы тХитЦУтХитХбтХитЦТтХд╨ХтХд╨УтХитХСтХитЦСтХитХЭтХитХХ, тХитХЬтХитХбтХитХЦтХитЦСтХитЦУтХитХХтХд╨СтХитХХтХитХЭтХитХЫ тХитХЫтХд╨Т тХитФдтХитЦСтХд╨ТтХд╨Ы.
        """
        # 0. тХи╨зтХитЦСтХд╨ЩтХитХХтХд╨ТтХитЦС тХитХЫтХд╨Т тХд╨СтХитХЧтХитХХтХд╨ШтХитХСтХитХЫтХитХЭ тХд╨ЧтХитЦСтХд╨СтХд╨ТтХитХЫтХитФВтХитХЫ тХитФРтХитХЫтХитХЧтХитХЧтХитХХтХитХЬтХитФВтХитЦС (тХитХЬтХитХб тХд╨ЧтХитЦСтХд╨ЩтХитХб тХд╨ЧтХитХбтХитХЭ тХд╨РтХитЦСтХитХЦ тХитЦУ 20 тХд╨СтХитХбтХитХСтХд╨УтХитХЬтХитФд)
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
            # 1. тХи╨етХд╨СтХитХЧтХитХХ тХд╨РтХитХбтХитЦУтХитХХтХитХЦтХитХХтХд╨Я 0 тХитХХтХитХЧтХитХХ тХитФРтХд╨УтХд╨СтХд╨ТтХитЦСтХд╨Я - тХитХЦтХитЦСтХитФРтХд╨УтХд╨СтХитХСтХитЦСтХитХбтХитХЭ 'Cold Start' тХитЦУтХитХЫтХд╨СтХд╨СтХд╨ТтХитЦСтХитХЬтХитХЫтХитЦУтХитХЧтХитХбтХитХЬтХитХХтХитХб
            if current_revision == 0:
                logger.warning(f"Revision 0 detected. Starting 'Cold Start' recovery for org {organization_id}...")
                
                # тХи╨а) тХи╨птХд╨РтХитХХтХитХЬтХд╨УтХитФдтХитХХтХд╨ТтХитХбтХитХЧтХд╨ЬтХитХЬтХитЦСтХд╨Я тХд╨СтХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитХЦтХитЦС тХитФРтХитХЫтХд╨СтХитХЧтХитХбтХитФдтХитХЬтХитХХтХитХб 48 тХд╨ЧтХитЦСтХд╨СтХитХЫтХитЦУ, тХд╨ЧтХд╨ТтХитХЫтХитЦТтХд╨Ы тХитХЬтХитХб тХитФРтХитХЫтХд╨ТтХитХбтХд╨РтХд╨ЯтХд╨ТтХд╨Ь тХитФдтХитЦСтХитХЬтХитХЬтХд╨ЫтХитХб
                await self.sync_orders(session, hours=48)
                
                # тХи╨б) тХи╨птХитХЫтХитХЧтХд╨УтХд╨ЧтХитЦСтХитХбтХитХЭ тХитЦСтХитХСтХд╨ТтХд╨УтХитЦСтХитХЧтХд╨ЬтХитХЬтХд╨УтХд╨Ю тХд╨РтХитХбтХитЦУтХитХХтХитХЦтХитХХтХд╨Ю тХитХХтХитХЦ Iiko тХитФдтХитХЧтХд╨Я тХитЦТтХд╨УтХитФдтХд╨УтХд╨ЩтХитХХтХд╨Х тХитХХтХитХЬтХитХСтХд╨РтХитХбтХитХЭтХитХбтХитХЬтХд╨ТтХитЦСтХитХЧтХд╨ЬтХитХЬтХд╨ЫтХд╨Х тХитХЫтХитЦТтХитХЬтХитХЫтХитЦУтХитХЧтХитХбтХитХЬтХитХХтХитХг
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

            # 2. тХи╨зтХитЦСтХитФРтХд╨РтХитЦСтХд╨ШтХитХХтХитЦУтХитЦСтХитХбтХитХЭ тХитХХтХитХЦтХитХЭтХитХбтХитХЬтХитХбтХитХЬтХитХХтХд╨Я тХд╨С тХитФРтХитХЫтХд╨СтХитХЧтХитХбтХитФдтХитХЬтХитХбтХитХг тХд╨РтХитХбтХитЦУтХитХХтХитХЦтХитХХтХитХХ
            data = await iiko_service.get_deliveries_by_revision(
                organization_id=organization_id,
                initial_revision=current_revision,
                api_login=settings_db.api_login
            )
            
            # iiko_service.get_deliveries_by_revision тХд╨ТтХитХбтХитФРтХитХбтХд╨РтХд╨Ь тХд╨СтХитЦСтХитХЭ тХд╨РтХитЦСтХд╨СтХитФРтХитЦСтХитХСтХитХЫтХитЦУтХд╨ЫтХитЦУтХитЦСтХитХбтХд╨Т ordersByOrganizations
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
                    # тХи╨отХитЦТтХд╨РтХитЦСтХитЦТтХитЦСтХд╨ТтХд╨ЫтХитЦУтХитЦСтХитХбтХитХЭ тХитХСтХитЦСтХитХвтХитФдтХд╨ЫтХитХг тХитХЦтХитЦСтХитХСтХитЦСтХитХЦ
                    await self.process_iiko_order(session, order_data, organization_id)
                    count += 1
                except Exception as e:
                    logger.error(f"Error processing order from revision: {e}")
            
            # тХи╨отХитЦТтХитХЬтХитХЫтХитЦУтХитХЧтХд╨ЯтХитХбтХитХЭ тХд╨РтХитХбтХитЦУтХитХХтХитХЦтХитХХтХд╨Ю тХитЦУ тХитХЬтХитЦСтХд╨СтХд╨ТтХд╨РтХитХЫтХитХгтХитХСтХитЦСтХд╨Х
            if max_revision:
                settings_db.last_order_revision = max_revision
                session.add(settings_db)
                session.commit()
                logger.info(f"Revision sync finished. New revision: {max_revision}, Processed: {count}")
                
        except httpx.HTTPStatusError as e:
            # 3. тХи╨отХитЦТтХд╨РтХитЦСтХитЦТтХитХЫтХд╨ТтХитХСтХитЦС тХитХЫтХд╨ШтХитХХтХитЦТтХитХСтХитХХ "TOO_OLD_REVISION" (тХи╨ктХитХЫтХитФд 400)
            if e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    if error_data.get("error") == "TOO_OLD_REVISION":
                        logger.warning(f"Revision {current_revision} is too old. Starting 'Cold Start' recovery...")
                        
                        # тХи╨▒тХитЦТтХд╨РтХитЦСтХд╨СтХд╨ЫтХитЦУтХитЦСтХитХбтХитХЭ тХд╨РтХитХбтХитЦУтХитХХтХитХЦтХитХХтХд╨Ю, тХд╨ЧтХд╨ТтХитХЫтХитЦТтХд╨Ы тХитФРтХд╨РтХитХХ тХд╨СтХитХЧтХитХбтХитФдтХд╨УтХд╨ЮтХд╨ЩтХитХбтХитХЭ тХитХЦтХитЦСтХитФРтХд╨УтХд╨СтХитХСтХитХб (тХитХХтХитХЧтХитХХ тХд╨РтХитХбтХитХСтХд╨УтХд╨РтХд╨СтХитХХтХитЦУтХитХЬтХитХЫ) тХд╨СтХд╨РтХитЦСтХитЦТтХитХЫтХд╨ТтХитЦСтХитХЧ Cold Start
                        settings_db.last_order_revision = 0
                        session.add(settings_db)
                        session.commit()
                        
                        # тХи╨зтХитЦСтХитФРтХд╨УтХд╨СтХитХСтХитЦСтХитХбтХитХЭ Cold Start тХитХЬтХитХбтХитХЭтХитХбтХитФдтХитХЧтХитХбтХитХЬтХитХЬтХитХЫ
                        await self.sync_orders_by_revision(session, organization_id)
                        return 
                except Exception as parse_err:
                    logger.error(f"Failed to handle 400 error: {parse_err}")
            
            logger.error(f"Iiko API error during revision sync: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in sync_orders_by_revision: {e}")

    async def sync_order_by_id(self, session: Session, order_id: str, organization_id: str) -> bool:
        """тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитХСтХитХЫтХитХЬтХитХСтХд╨РтХитХбтХд╨ТтХитХЬтХитХЫтХитФВтХитХЫ тХитХЦтХитЦСтХитХСтХитЦСтХитХЦтХитЦС тХитФРтХитХЫ ID (тХитЦУтХд╨ЫтХитХЦтХд╨ЫтХитЦУтХитЦСтХитХбтХд╨ТтХд╨СтХд╨Я тХитЦУтХитХбтХитЦТтХд╨ХтХд╨УтХитХСтХитЦСтХитХЭтХитХХ)"""
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
        """тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитХЦтХитХЫтХитХЬ тХитХХ тХд╨УтХд╨СтХитХЧтХитХЫтХитЦУтХитХХтХитХг тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХСтХитХХ тХитХХтХитХЦ iiko Cloud"""
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db or not settings_db.organization_id:
            return {"error": "Iiko not configured"}
            
        try:
            data = await iiko_service.get_delivery_restrictions(
                api_login=settings_db.api_login,
                organization_id=settings_db.organization_id
            )
            
            # тХи╨▒тХд╨ТтХд╨РтХд╨УтХитХСтХд╨ТтХд╨УтХд╨РтХитЦС тХитХЫтХд╨ТтХитЦУтХитХбтХд╨ТтХитЦС iiko тХитХЭтХитХЫтХитХвтХитХбтХд╨Т тХитЦТтХд╨ЫтХд╨ТтХд╨Ь {"deliveryRestrictions": [...]} тХитХХтХитХЧтХитХХ тХитФРтХд╨РтХитХЫтХд╨СтХд╨ТтХитХЫ тХд╨СтХитФРтХитХХтХд╨СтХитХЫтХитХС
            restrictions_data = []
            if isinstance(data, dict):
                restrictions_data = data.get("deliveryRestrictions", [])
            elif isinstance(data, list):
                restrictions_data = data
                
            if not restrictions_data:
                logger.warning("тХи╨нтХитХбтХд╨Т тХитФдтХитЦСтХитХЬтХитХЬтХд╨ЫтХд╨Х тХитХЫтХитЦТ тХитХЫтХитФВтХд╨РтХитЦСтХитХЬтХитХХтХд╨ЧтХитХбтХитХЬтХитХХтХд╨ЯтХд╨Х тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХСтХитХХ тХитХЫтХд╨Т iiko")
                return {"success": True, "synced": 0, "message": "No restrictions data"}

            synced_count = 0
            
            for restriction_item in restrictions_data:
                if not isinstance(restriction_item, dict):
                    continue
                    
                # 1. тХи╨нтХитЦСтХд╨ХтХитХЫтХитФдтХитХХтХитХЭ тХд╨ФтХитХХтХитХЧтХитХХтХитЦСтХитХЧ (тХд╨ТтХитХбтХд╨РтХитХЭтХитХХтХитХЬтХитЦСтХитХЧтХд╨ЬтХитХЬтХд╨УтХд╨Ю тХитФВтХд╨РтХд╨УтХитФРтХитФРтХд╨У)
                tg_id = restriction_item.get("terminalGroupId")
                if not tg_id:
                    # тХи╨етХд╨СтХитХЧтХитХХ terminalGroupId тХитХЬтХитХбтХд╨Т, тХитЦУтХитХЫтХитХЦтХитХЭтХитХЫтХитХвтХитХЬтХитХЫ тХд╨ЭтХд╨ТтХитХЫ тХитХЫтХитЦТтХд╨ЩтХитХХтХитХб тХитХЫтХитФВтХд╨РтХитЦСтХитХЬтХитХХтХд╨ЧтХитХбтХитХЬтХитХХтХд╨Я тХитФдтХитХЧтХд╨Я тХитЦУтХд╨СтХитХбтХд╨Х тХд╨ФтХитХХтХитХЧтХитХХтХитЦСтХитХЧтХитХЫтХитЦУ тХитХЫтХд╨РтХитФВтХитЦСтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХитХХ?
                    # тХи╨нтХитХЫ тХитХЫтХитЦТтХд╨ЫтХд╨ЧтХитХЬтХитХЫ тХитЦУ iiko тХитХЫтХитХЬтХитХХ тХитФРтХд╨РтХитХХтХитЦУтХд╨ЯтХитХЦтХитЦСтХитХЬтХд╨Ы тХитХС TG. 
                    # тХи╨птХитХЫтХитФРтХд╨РтХитХЫтХитЦТтХд╨УтХитХбтХитХЭ тХитХЬтХитЦСтХитХгтХд╨ТтХитХХ тХитФРтХитХбтХд╨РтХитЦУтХд╨ЫтХитХг тХд╨ФтХитХХтХитХЧтХитХХтХитЦСтХитХЧ тХитХСтХитЦСтХитХС fallback, тХитХбтХд╨СтХитХЧтХитХХ тХитХЫтХитХЬ тХитХЫтХитФдтХитХХтХитХЬ.
                    branch = session.exec(select(Branch)).first()
                    logger.warning("restriction_item missing terminalGroupId, using first branch as fallback")
                else:
                    branch = session.exec(select(Branch).where(Branch.iiko_terminal_id == tg_id)).first()
                
                if not branch:
                    logger.warning(f"тХи╨┤тХитХХтХитХЧтХитХХтХитЦСтХитХЧ тХд╨С iiko_terminal_id {tg_id} тХитХЬтХитХб тХитХЬтХитЦСтХитХгтХитФдтХитХбтХитХЬ тХитЦУ тХи╨бтХи╨д, тХитФРтХд╨РтХитХЫтХитФРтХд╨УтХд╨СтХитХСтХитЦСтХитХбтХитХЭ тХитХЫтХитФВтХд╨РтХитЦСтХитХЬтХитХХтХд╨ЧтХитХбтХитХЬтХитХХтХд╨Я")
                    continue

                # 2. тХи╨▒тХитХЫтХитЦТтХитХХтХд╨РтХитЦСтХитХбтХитХЭ тХитФРтХитХЫтХитХЧтХитХХтХитФВтХитХЫтХитХЬтХд╨Ы тХитХХтХитХЦ KML тХитФдтХитХЧтХд╨Я тХд╨ЭтХд╨ТтХитХЫтХитФВтХитХЫ тХд╨ФтХитХХтХитХЧтХитХХтХитЦСтХитХЧтХитЦС/тХитХЫтХитФВтХд╨РтХитЦСтХитХЬтХитХХтХд╨ЧтХитХбтХитХЬтХитХХтХд╨Я
                branch_polygons = {}
                map_url = restriction_item.get("deliveryRegionsMapUrl")
                if map_url:
                    logger.info(f"тХи╨нтХитЦСтХитХгтХитФдтХитХбтХитХЬтХитЦС тХд╨СтХд╨СтХд╨ЫтХитХЧтХитХСтХитЦС тХитХЬтХитЦС тХитХСтХитЦСтХд╨РтХд╨ТтХд╨У тХитФдтХитХЧтХд╨Я тХд╨ФтХитХХтХитХЧтХитХХтХитЦСтХитХЧтХитЦС {branch.name}: {map_url}. тХи╨зтХитЦСтХитФВтХд╨РтХд╨УтХитХЦтХитХСтХитЦС тХитФРтХитХЫтХитХЧтХитХХтХитФВтХитХЫтХитХЬтХитХЫтХитЦУ...")
                    try:
                        kml_zones = await iiko_service.fetch_and_parse_kml(map_url)
                        for kz in kml_zones:
                            # тХи╨▒тХитХЫтХд╨ХтХд╨РтХитЦСтХитХЬтХд╨ЯтХитХбтХитХЭ тХитФРтХитХЫтХитХЧтХитХХтХитФВтХитХЫтХитХЬ тХитФРтХитХЫ тХитХХтХитХЭтХитХбтХитХЬтХитХХ тХитХЦтХитХЫтХитХЬтХд╨Ы (тХитЦУ тХитХЬтХитХХтХитХвтХитХЬтХитХбтХитХЭ тХд╨РтХитХбтХитФВтХитХХтХд╨СтХд╨ТтХд╨РтХитХб тХитФдтХитХЧтХд╨Я тХд╨СтХитХЫтХитФРтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХЧтХитХбтХитХЬтХитХХтХд╨Я)
                            name_key = kz["name"].lower().strip()
                            branch_polygons[name_key] = kz["coordinates"]
                            logger.info(f"тХи╨зтХитЦСтХитФВтХд╨РтХд╨УтХитХвтХитХбтХитХЬтХитЦС тХитФВтХитХбтХитХЫтХитХЭтХитХбтХд╨ТтХд╨РтХитХХтХд╨Я тХитФдтХитХЧтХд╨Я тХитХЦтХитХЫтХитХЬтХд╨Ы '{kz['name']}' тХитХХтХитХЦ iiko-тХитХСтХитЦСтХд╨РтХд╨ТтХд╨Ы")
                    except Exception as e:
                        logger.error(f"тХи╨отХд╨ШтХитХХтХитЦТтХитХСтХитЦС тХитФРтХд╨РтХитХХ тХитХЦтХитЦСтХитФВтХд╨РтХд╨УтХитХЦтХитХСтХитХб тХитФРтХитХЫтХитХЧтХитХХтХитФВтХитХЫтХитХЬтХитХЫтХитЦУ тХитФдтХитХЧтХд╨Я тХд╨ФтХитХХтХитХЧтХитХХтХитЦСтХитХЧтХитЦС {branch.name}: {e}")

                # 3. тХи╨отХитЦТтХд╨РтХитЦСтХитЦТтХитЦСтХд╨ТтХд╨ЫтХитЦУтХитЦСтХитХбтХитХЭ тХитХЦтХитХЫтХитХЬтХд╨Ы тХитЦУтХитХЬтХд╨УтХд╨ТтХд╨РтХитХХ тХитХЫтХитФВтХд╨РтХитЦСтХитХЬтХитХХтХд╨ЧтХитХбтХитХЬтХитХХтХд╨Я
                for res in restriction_item.get("restrictions", []):
                    zone_name = res.get("zone")
                    if not zone_name:
                        continue
                        
                    min_sum = float(res.get("minSum") or 0)
                    delivery_cost = float(res.get("deliveryPrice") or 0)
                    
                    # тХи╨итХд╨СтХитФРтХитХЫтХитХЧтХд╨ЬтХитХЦтХд╨УтХитХбтХитХЭ zoneId тХитХХтХитХЦ iiko тХитХбтХд╨СтХитХЧтХитХХ тХитХбтХд╨СтХд╨ТтХд╨Ь, тХитХХтХитХЬтХитЦСтХд╨ЧтХитХб тХитХХтХитХЭтХд╨Я
                    iiko_zone_id = res.get("zoneId") or zone_name
                    
                    # тХи╨итХд╨ЩтХитХбтХитХЭ тХитХЦтХитХЫтХитХЬтХд╨У тХитФдтХитХЧтХд╨Я тХитХСтХитХЫтХитХЬтХитХСтХд╨РтХитХбтХд╨ТтХитХЬтХитХЫтХитФВтХитХЫ тХд╨ФтХитХХтХитХЧтХитХХтХитЦСтХитХЧтХитЦС
                    zone = session.exec(select(DeliveryZone).where(
                        (DeliveryZone.branch_id == branch.id) & 
                        ((DeliveryZone.iiko_id == iiko_zone_id) | (DeliveryZone.name == zone_name))
                    )).first()
                    
                    if not zone:
                        logger.info(f"тХи╨▒тХитХЫтХитХЦтХитФдтХитЦСтХитХЬтХитХХтХитХб тХитХЬтХитХЫтХитЦУтХитХЫтХитХг тХитХЦтХитХЫтХитХЬтХд╨Ы тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХСтХитХХ '{zone_name}' тХитФдтХитХЧтХд╨Я тХд╨ФтХитХХтХитХЧтХитХХтХитЦСтХитХЧтХитЦС {branch.name}")
                        zone = DeliveryZone(
                            name=zone_name, 
                            branch_id=branch.id, 
                            iiko_id=iiko_zone_id
                        )
                        session.add(zone)
                        session.flush() # тХи╨птХитХЫтХитХЧтХд╨УтХд╨ЧтХитЦСтХитХбтХитХЭ ID
                    
                    # тХи╨отХитЦТтХитХЬтХитХЫтХитЦУтХитХЧтХд╨ЯтХитХбтХитХЭ тХитФРтХитЦСтХд╨РтХитЦСтХитХЭтХитХбтХд╨ТтХд╨РтХд╨Ы тХитХЦтХитХЫтХитХЬтХд╨Ы
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
                    
                    # 4. тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитХХтХд╨РтХд╨УтХитХбтХитХЭ тХитФВтХитХбтХитХЫтХитХЭтХитХбтХд╨ТтХд╨РтХитХХтХд╨Ю тХитЦУ CustomPolygon
                    zone_key = zone_name.lower().strip()
                    if zone_key in branch_polygons:
                        coords = branch_polygons[zone_key]
                        # тХи╨итХд╨ЩтХитХбтХитХЭ тХд╨СтХд╨УтХд╨ЩтХитХбтХд╨СтХд╨ТтХитЦУтХд╨УтХд╨ЮтХд╨ЩтХитХХтХитХг тХитФРтХитХЫтХитХЧтХитХХтХитФВтХитХЫтХитХЬ тХитФдтХитХЧтХд╨Я тХд╨ЭтХд╨ТтХитХЫтХитХг тХитХЦтХитХЫтХитХЬтХд╨Ы
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
                            logger.info(f"тХи╨▒тХитХЫтХитХЦтХитФдтХитЦСтХитХЬ тХитХЬтХитХЫтХитЦУтХд╨ЫтХитХг тХитФРтХитХЫтХитХЧтХитХХтХитФВтХитХЫтХитХЬ тХитФдтХитХЧтХд╨Я тХитХЦтХитХЫтХитХЬтХд╨Ы '{zone.name}'")
                        else:
                            # тХи╨отХитЦТтХитХЬтХитХЫтХитЦУтХитХЧтХд╨ЯтХитХбтХитХЭ тХитХСтХитХЫтХитХЫтХд╨РтХитФдтХитХХтХитХЬтХитЦСтХд╨ТтХд╨Ы тХитХХ тХитФРтХитЦСтХд╨РтХитЦСтХитХЭтХитХбтХд╨ТтХд╨РтХд╨Ы
                            poly.coordinates = coords
                            poly.priority = zone.priority
                            poly.min_order_amount = zone.min_order_amount
                            poly.delivery_cost = zone.delivery_cost
                            poly.is_active = True
                            session.add(poly)
                            logger.info(f"тХи╨отХитЦТтХитХЬтХитХЫтХитЦУтХитХЧтХитХбтХитХЬтХитЦС тХитФВтХитХбтХитХЫтХитХЭтХитХбтХд╨ТтХд╨РтХитХХтХд╨Я тХитХХ тХитФРтХитЦСтХд╨РтХитЦСтХитХЭтХитХбтХд╨ТтХд╨РтХд╨Ы тХитФРтХитХЫтХитХЧтХитХХтХитФВтХитХЫтХитХЬтХитЦС тХитФдтХитХЧтХд╨Я тХитХЦтХитХЫтХитХЬтХд╨Ы '{zone.name}'")
                        
                        # тХи╨▒тХитХЫтХд╨ХтХд╨РтХитЦСтХитХЬтХд╨ЯтХитХбтХитХЭ тХитХХ тХитЦУ тХд╨ТтХитХбтХитХСтХд╨СтХд╨ТтХитХЫтХитЦУтХитХЫтХитХб тХитФРтХитХЫтХитХЧтХитХб тХитХЦтХитХЫтХитХЬтХд╨Ы (тХитФдтХитХЧтХд╨Я тХд╨СтХитХЫтХитЦУтХитХЭтХитХбтХд╨СтХд╨ТтХитХХтХитХЭтХитХЫтХд╨СтХд╨ТтХитХХ)
                        zone.polygon_coordinates = json.dumps(coords)
                    
                    zone.additional_info = res
                    session.add(zone)
                    synced_count += 1
                
            session.commit()
            logger.info(f"тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитХЫтХитФВтХд╨РтХитЦСтХитХЬтХитХХтХд╨ЧтХитХбтХитХЬтХитХХтХитХг тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХСтХитХХ тХитХЦтХитЦСтХитЦУтХитХбтХд╨РтХд╨ШтХитХбтХитХЬтХитЦС: {synced_count} тХитХЦтХитХЫтХитХЬ")
            return {"success": True, "synced": synced_count, "message": f"Successfully synced {synced_count} zones"}
            
        except Exception as e:
            session.rollback()
            logger.error(f"тХи╨отХд╨ШтХитХХтХитЦТтХитХСтХитЦС тХитФРтХд╨РтХитХХ тХд╨СтХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХитХХ тХитХЫтХитФВтХд╨РтХитЦСтХитХЬтХитХХтХд╨ЧтХитХбтХитХЬтХитХХтХитХг тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХСтХитХХ iiko: {e}", exc_info=True)
            return {"error": str(e)}

    async def get_available_iiko_zones(self, session: Session) -> List[Dict[str, Any]]:
        """тХи╨птХитХЫтХитХЧтХд╨УтХд╨ЧтХитХХтХд╨ТтХд╨Ь тХд╨СтХитФРтХитХХтХд╨СтХитХЫтХитХС тХитЦУтХд╨СтХитХбтХд╨Х тХитФдтХитХЫтХд╨СтХд╨ТтХд╨УтХитФРтХитХЬтХд╨ЫтХд╨Х тХитХЦтХитХЫтХитХЬ тХитХХтХитХЦ iiko Cloud (тХитЦТтХитХбтХитХЦ тХд╨СтХитХЫтХд╨ХтХд╨РтХитЦСтХитХЬтХитХбтХитХЬтХитХХтХд╨Я)"""
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
        """тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХд╨ТтХитХХтХитФРтХитХЫтХитЦУ тХитХЫтХитФРтХитХЧтХитЦСтХд╨ТтХд╨Ы тХитХХтХитХЦ iiko Cloud"""
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
            logger.info(f"тХи╨нтХитЦСтХд╨ЧтХитХХтХитХЬтХитЦСтХд╨Ю тХитХЫтХитЦТтХд╨РтХитЦСтХитЦТтХитХЫтХд╨ТтХитХСтХд╨У {len(payment_types)} тХд╨ТтХитХХтХитФРтХитХЫтХитЦУ тХитХЫтХитФРтХитХЧтХитЦСтХд╨ТтХд╨Ы тХитХХтХитХЦ iiko")
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
                        is_active=True # тХи╨отХи╨бтХи╨┐тХи╨зтХи╨атХи╨▓тХи╨етХи╨лтХи╨╝тХи╨нтХи╨о! тХи╨итХитХЬтХитЦСтХд╨ЧтХитХб тХитХЫтХитХЬтХитХХ тХитФРтХд╨РтХитХЫтХитФРтХитЦСтХитФдтХд╨УтХд╨Т тХитФРтХд╨РтХитХХ F5
                    )
                    session.add(new_pt)
                synced_count += 1
            
            logger.info(f"тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитХЦтХитЦСтХитЦУтХитХбтХд╨РтХд╨ШтХитХбтХитХЬтХитЦС. тХи╨втХд╨СтХитХбтХитФВтХитХЫ: {synced_count}")
            session.commit()
            return {"status": "success", "synced_count": synced_count}
        except Exception as e:
            logger.error(f"Payment types sync failed: {e}")
            session.rollback()
            return {"error": str(e)}


    async def sync_stop_lists(self, session: Session = None):
        """тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХд╨СтХд╨ТтХитХЫтХитФР-тХитХЧтХитХХтХд╨СтХд╨ТтХитХЫтХитЦУ"""
        # тХи╨лтХитХЫтХитФВтХитХХтХитХСтХитЦС тХд╨СтХд╨ТтХитХЫтХитФР-тХитХЧтХитХХтХд╨СтХд╨ТтХитХЫтХитЦУ
        pass

    async def sync_employees_full(self, session: Session, days: int = 7) -> None:
        """
        тХи╨птХитХЫтХитХЧтХитХЬтХитЦСтХд╨Я тХд╨СтХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХд╨СтХитХЫтХд╨ТтХд╨РтХд╨УтХитФдтХитХЬтХитХХтХитХСтХитХЫтХитЦУ тХитХХ тХитХХтХд╨Х тХд╨СтХитХЭтХитХбтХитХЬ тХд╨ЧтХитХбтХд╨РтХитХбтХитХЦ iiko RESTO (Office) API.
        """
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db or not settings_db.resto_url:
            logger.error("тХи╨нтХитЦСтХд╨СтХд╨ТтХд╨РтХитХЫтХитХгтХитХСтХитХХ iiko Resto (Office) тХитХЬтХитХб тХитХЬтХитЦСтХитХгтХитФдтХитХбтХитХЬтХд╨Ы. тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитХЫтХд╨ТтХитХЭтХитХбтХитХЬтХитХбтХитХЬтХитЦС.")
            return

        tz = self._get_tz(session)
        now_local = datetime.now(tz)
        date_from = now_local - timedelta(days=days)

        # --- тХи╨╕тХитЦСтХитФВ 1: тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитФРтХд╨РтХитХЫтХд╨ФтХитХХтХитХЧтХитХбтХитХг тХд╨СтХитХЫтХд╨ТтХд╨РтХд╨УтХитФдтХитХЬтХитХХтХитХСтХитХЫтХитЦУ ---
        # тХи╨птХитЦСтХд╨РтХитЦСтХитХЭтХитХбтХд╨ТтХд╨РтХд╨Ы тХитФРтХитХЫтХитФдтХитХСтХитХЧтХд╨ЮтХд╨ЧтХитХбтХитХЬтХитХХтХд╨Я тХитЦТтХитХбтХд╨РтХд╨бтХитХЭ тХитХХтХитХЦ тХи╨бтХи╨д, тХитЦС тХитХЬтХитХб тХитХХтХитХЦ ENV
        r_url = settings_db.resto_url
        r_login = settings_db.resto_login
        r_password = settings_db.resto_password
        try:
            logger.info("тХи╨зтХитЦСтХитФРтХд╨РтХитХЫтХд╨С тХд╨СтХитФРтХитХХтХд╨СтХитХСтХитЦС тХд╨СтХитХЫтХд╨ТтХд╨РтХд╨УтХитФдтХитХЬтХитХХтХитХСтХитХЫтХитЦУ тХитХХтХитХЦ iiko Resto...")
            iiko_employees = await iiko_service.get_resto_employees(
                resto_url=r_url, resto_login=r_login, resto_password=r_password
            )
            
            for emp in iiko_employees:
                emp_iiko_id = emp.get("id")
                if not emp_iiko_id: continue
                
                name = emp.get("name") or f"{emp.get('firstName', '')} {emp.get('lastName', '')}".strip()
                role = emp.get("role")
                rate = emp.get("salary")
                
                # тХи╨дтХитХЫтХитХСтХд╨УтХитХЭтХитХбтХитХЬтХд╨ТтХд╨Ы тХитХХ тХитФдтХитХЫтХитФР. тХитХХтХитХЬтХд╨ФтХитХЫ
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
                    return ("тХитХСтХд╨УтХд╨РтХд╨ЬтХитХбтХд╨Р" in r_l or "courier" in r_l or r_l in ["cur", "cour"]
                            or "тХитХСтХд╨УтХд╨РтХд╨ЬтХитХбтХд╨Р" in n_l or "courier" in n_l)
                def _flag_admin(r, n=""):
                    r_l = (r or "").lower()
                    return any(k in r_l for k in ["тХитЦСтХитФдтХитХЭтХитХХтХитХЬтХитХХтХд╨СтХд╨ТтХд╨РтХитЦСтХд╨ТтХитХЫтХд╨Р", "тХитХЫтХитФРтХитХбтХд╨РтХитЦСтХд╨ТтХитХЫтХд╨Р", "manager", "тХд╨СтХд╨ТтХитЦСтХд╨РтХд╨ШтХитХХтХитХг", "adm", "admin"])

                if existing:
                    existing.name = name
                    existing.role = role or existing.role
                    existing.phone = emp.get("phone") or existing.phone
                    existing.email = emp.get("email") or existing.email
                    existing.address = emp.get("address") or existing.address
                    existing.rate = rate if rate is not None else existing.rate
                    existing.document_info = doc_info
                    existing.status = "Deleted" if emp.get("deleted") else "Active"
                    existing.is_courier = _flag_courier(existing.role, existing.name)
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
            logger.info(f"╤В╨м╨Х тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитХХтХд╨РтХитХЫтХитЦУтХитЦСтХитХЬтХитХЫ {len(iiko_employees)} тХитФРтХд╨РтХитХЫтХд╨ФтХитХХтХитХЧтХитХбтХитХг тХд╨СтХитХЫтХд╨ТтХд╨РтХд╨УтХитФдтХитХЬтХитХХтХитХСтХитХЫтХитЦУ тХитХХтХитХЦ iiko Resto")
        except Exception as e:
            logger.error(f"тХи╨отХд╨ШтХитХХтХитЦТтХитХСтХитЦС тХд╨СтХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХитХХ тХитФРтХд╨РтХитХЫтХд╨ФтХитХХтХитХЧтХитХбтХитХг: {e}")
            session.rollback()

        # --- тХи╨╕тХитЦСтХитФВ 1.5: тХи╨дтХитХЫтХитФРтХитХЫтХитХЧтХитХЬтХитХбтХитХЬтХитХХтХитХб тХитФдтХитЦСтХитХЬтХитХЬтХд╨ЫтХитХЭтХитХХ тХитХХтХитХЦ iiko Cloud (тХи╨отХи╨▓тХи╨ктХи╨лтХи╨╛тХи╨╖тХи╨етХи╨нтХи╨о тХитФРтХитХЫ тХд╨ТтХд╨РтХитХбтХитЦТтХитХЫтХитЦУтХитЦСтХитХЬтХитХХтХд╨Ю тХитФРтХитХЫтХитХЧтХд╨ЬтХитХЦтХитХЫтХитЦУтХитЦСтХд╨ТтХитХбтХитХЧтХд╨Я - тХд╨СтХд╨ТтХд╨РтХитХЫтХитФВтХитХЫ Server API) ---
        # try:
        #     logger.info("тХи╨зтХитЦСтХитФРтХд╨РтХитХЫтХд╨С тХитФдтХитХЫтХитФРтХитХЫтХитХЧтХитХЬтХитХХтХд╨ТтХитХбтХитХЧтХд╨ЬтХитХЬтХд╨ЫтХд╨Х тХитФдтХитЦСтХитХЬтХитХЬтХд╨ЫтХд╨Х тХитХХтХитХЦ iiko Cloud...")
        #     cloud_employees = await iiko_service.get_employees(api_login=settings_db.api_login, organization_id=settings_db.organization_id)
        #     updated_cloud_c = 0
        #     for c_emp in cloud_employees:
        #         emp_iiko_id = c_emp.get("id")
        #         if not emp_iiko_id: continue
        #         
        #         existing = session.exec(select(Employee).where(Employee.iiko_id == emp_iiko_id)).first()
        #         # тХи╨етХд╨СтХитХЧтХитХХ тХд╨СтХитХЫтХд╨ТтХд╨РтХд╨УтХитФдтХитХЬтХитХХтХитХСтХитЦС тХитХЬтХитХбтХд╨Т тХитХХтХитХЦ Resto, тХитХЬтХитХЫ тХитХЫтХитХЬ тХитХбтХд╨СтХд╨ТтХд╨Ь тХитЦУ Cloud (тХитХЬтХитЦСтХитФРтХд╨РтХитХХтХитХЭтХитХбтХд╨Р, тХитЦУтХитХЬтХитХбтХд╨ШтХитХЬтХитХХтХитХг тХитХСтХд╨УтХд╨РтХд╨ЬтХитХбтХд╨Р)
        #         if not existing:
        #             role = ""
        #             if c_emp.get("isCourier"): role = "тХи╨ктХд╨УтХд╨РтХд╨ЬтХитХбтХд╨Р (Cloud)"
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
        #             # тХи╨дтХитХЫтХитФРтХитХЫтХитХЧтХитХЬтХд╨ЯтХитХбтХитХЭ тХитФдтХитЦСтХитХЬтХитХЬтХд╨ЫтХитХЭтХитХХ, тХитХбтХд╨СтХитХЧтХитХХ тХитХХтХд╨Х тХитХЬтХитХбтХд╨Т
        #             if c_emp.get("isCourier") and not existing.is_courier:
        #                 existing.is_courier = True
        #                 session.add(existing)
        #                 updated_cloud_c += 1
        #     session.commit()
        #     logger.info(f"╤В╨м╨Х тХи╨дтХитХЫтХитФРтХитХЫтХитХЧтХитХЬтХитХбтХитХЬтХитХЫ {updated_cloud_c} тХитФРтХд╨РтХитХЫтХд╨ФтХитХХтХитХЧтХитХбтХитХг тХитХХтХитХЦ iiko Cloud")
        # except Exception as e:
        #     logger.error(f"тХи╨отХд╨ШтХитХХтХитЦТтХитХСтХитЦС тХитФдтХитХЫтХитФРтХитХЫтХитХЧтХитХЬтХитХбтХитХЬтХитХХтХд╨Я тХитФдтХитЦСтХитХЬтХитХЬтХд╨ЫтХд╨Х тХитХХтХитХЦ Cloud: {e}")
        #     session.rollback()

        # --- тХи╨╕тХитЦСтХитФВ 2: тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитХХтХд╨СтХд╨ТтХитХЫтХд╨РтХитХХтХд╨ЧтХитХбтХд╨СтХитХСтХитХХтХд╨Х тХд╨СтХитХЭтХитХбтХитХЬ тХд╨ЧтХитХбтХд╨РтХитХбтХитХЦ Attendance API ---
        try:
            logger.info(f"тХи╨зтХитЦСтХитФРтХд╨РтХитХЫтХд╨С тХд╨ЯтХитЦУтХитХЫтХитХС (тХд╨СтХитХЭтХитХбтХитХЬ) тХд╨ЧтХитХбтХд╨РтХитХбтХитХЦ Attendance API ({date_from.date()} - {now_local.date()})...")
            attendance_records = await iiko_service.get_resto_attendance(
                resto_url=r_url, resto_login=r_login, resto_password=r_password,
                date_from=date_from, date_to=now_local,
                log_error=False
            )

            def _parse_to_utc(s):
                if not s: return None
                try:
                    # тХд╨ФтХитХЫтХд╨РтХитХЭтХитЦСтХд╨Т ISO 8601 тХд╨С тХд╨ТтХитЦСтХитХгтХитХЭтХитХЦтХитХЫтХитХЬтХитХЫтХитХг (тХитХЬтХитЦСтХитФРтХд╨РтХитХХтХитХЭтХитХбтХд╨Р 2026-04-11T10:17:00+05:00)
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
                    # logger.debug(f"Attendance: тХд╨СтХитХЫтХд╨ТтХд╨РтХд╨УтХитФдтХитХЬтХитХХтХитХС тХд╨С ID '{emp_iiko_id}' тХитХЬтХитХб тХитХЬтХитЦСтХитХгтХитФдтХитХбтХитХЬ тХитЦУ тХи╨бтХи╨д")
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

                # тХи╨отХитФВтХд╨РтХитЦСтХитХЬтХитХХтХд╨ЧтХитХХтХитЦУтХитЦСтХитХбтХитХЭ тХитЦСтХитХЬтХитХЫтХитХЭтХитЦСтХитХЧтХд╨ЬтХитХЬтХитХЫ тХитФдтХитХЧтХитХХтХитХЬтХитХЬтХд╨ЫтХитХб тХд╨СтХитХЭтХитХбтХитХЬтХд╨Ы (тХитХЭтХитЦСтХитХСтХд╨С 24 тХд╨ЧтХитЦСтХд╨СтХитЦС)
                work_hours = min(work_hours, 24.0)

                # тХи╨│тХитХЬтХитХХтХитХСтХитЦСтХитХЧтХд╨ЬтХитХЬтХд╨ЫтХитХг тХитХСтХитХЧтХд╨ЮтХд╨Ч
                shift_iiko_id = row.get("id")
                if not shift_iiko_id:
                     shift_iiko_id = f"att_{employee.id}_{date_open.strftime('%Y%m%d%H%M')}"

                # тХи╨птХитХЫтХитХХтХд╨СтХитХС тХитЦУтХд╨ЫтХд╨РтХд╨УтХд╨ЧтХитХСтХитХХ тХитФРтХд╨РтХитХХ тХитХЦтХитЦСтХитХСтХд╨РтХд╨ЫтХд╨ТтХитХХтХитХХ (тХитХХтХитХЦ тХитХЦтХитЦСтХитФВтХд╨РтХд╨УтХитХвтХитХбтХитХЬтХитХЬтХд╨ЫтХд╨Х тХитХЫтХд╨ТтХд╨ЧтХитХбтХд╨ТтХитХЫтХитЦУ OLAP)
                revenue_at_close = 0.0
                if date_close:
                    biz_date_str = date_open.astimezone(tz).strftime("%Y-%m-%d")
                    # тХи╨бтХитХбтХд╨РтХитХбтХитХЭ тХитЦУтХд╨ЫтХд╨РтХд╨УтХд╨ЧтХитХСтХд╨У тХитХЦтХитЦС тХитЦТтХитХХтХитХЦтХитХЬтХитХбтХд╨С-тХитФдтХитХбтХитХЬтХд╨Ь тХитХЫтХд╨ТтХитХСтХд╨РтХд╨ЫтХд╨ТтХитХХтХд╨Я тХд╨СтХитХЭтХитХбтХитХЬтХд╨Ы
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
                    # тХи╨отХитЦТтХитХЬтХитХЫтХитЦУтХитХЧтХд╨ЯтХитХбтХитХЭ тХитЦУтХд╨ЫтХд╨РтХд╨УтХд╨ЧтХитХСтХд╨У тХд╨ТтХитХЫтХитХЧтХд╨ЬтХитХСтХитХЫ тХитХбтХд╨СтХитХЧтХитХХ тХитХЫтХитХЬтХитЦС тХитХбтХд╨ЩтХитХб тХитХЬтХитХб тХитЦТтХд╨ЫтХитХЧтХитЦС тХд╨УтХд╨СтХд╨ТтХитЦСтХитХЬтХитХЫтХитЦУтХитХЧтХитХбтХитХЬтХитЦС
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
            logger.info(f"╤В╨м╨Х Attendance тХд╨СтХитХЭтХитХбтХитХЬтХд╨Ы: тХд╨СтХитХЫтХитХЦтХитФдтХитЦСтХитХЬтХитХЫ {created_c}, тХитХЫтХитЦТтХитХЬтХитХЫтХитЦУтХитХЧтХитХбтХитХЬтХитХЫ {updated_c} тХитХХтХитХЦ {len(attendance_records)} тХд╨СтХд╨ТтХд╨РтХитХЫтХитХС")
        except Exception as e:
            logger.error(f"тХи╨отХд╨ШтХитХХтХитЦТтХитХСтХитЦС тХд╨СтХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХитХХ Attendance тХд╨СтХитХЭтХитХбтХитХЬ: {e}", exc_info=True)
            session.rollback()

        # --- тХи╨╕тХитЦСтХитФВ 3 (тХи╨│тХитФдтХитЦСтХитХЧтХитХбтХитХЬ): тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХд╨ЧтХитХбтХд╨РтХитХбтХитХЦ personalSessions тХитХЦтХитЦСтХитХЭтХитХбтХитХЬтХитХбтХитХЬтХитЦС тХитХЬтХитЦС Attendance ---
        # тХи╨лтХитХХтХд╨ЧтХитХЬтХд╨ЫтХитХб тХд╨СтХитХЭтХитХбтХитХЬтХд╨Ы тХд╨ТтХитХбтХитФРтХитХбтХд╨РтХд╨Ь тХитФРтХитХЫтХитХЧтХитХЬтХитХЫтХд╨СтХд╨ТтХд╨ЬтХд╨Ю тХитХЫтХитЦТтХд╨РтХитЦСтХитЦТтХитЦСтХд╨ТтХд╨ЫтХитЦУтХитЦСтХд╨ЮтХд╨ТтХд╨СтХд╨Я тХитЦУ тХи╨╕тХитЦСтХитФВтХитХб 2 тХд╨ЧтХитХбтХд╨РтХитХбтХитХЦ Attendance API, 
        # тХитХСтХитХЫтХд╨ТтХитХЫтХд╨РтХд╨ЫтХитХг тХитЦУтХитХЫтХитХЦтХитЦУтХд╨РтХитЦСтХд╨ЩтХитЦСтХитХбтХд╨Т тХитХХ тХитХЫтХд╨ТтХитХСтХд╨РтХд╨ЫтХд╨ТтХд╨ЫтХитХб, тХитХХ тХитХЦтХитЦСтХитХСтХд╨РтХд╨ЫтХд╨ТтХд╨ЫтХитХб тХд╨СтХитХЭтХитХбтХитХЬтХд╨Ы тХитЦТтХитХбтХитХЦ тХитХЫтХд╨ШтХитХХтХитЦТтХитХЫтХитХС 404.
        pass

    async def get_employee_stats(self, session: Session, employee_id: int, mode: str = "calendar") -> Dict[str, Any]:
        """
        тХи╨птХитХЫтХитХЧтХд╨УтХд╨ЧтХитХбтХитХЬтХитХХтХитХб тХд╨СтХд╨ТтХитЦСтХд╨ТтХитХХтХд╨СтХд╨ТтХитХХтХитХСтХитХХ тХд╨СтХитХЫтХд╨ТтХд╨РтХд╨УтХитФдтХитХЬтХитХХтХитХСтХитЦС тХитХЦтХитЦС тХитФРтХитХбтХд╨РтХитХХтХитХЫтХитФд.
        mode: 'calendar' (тХд╨ТтХитХбтХитХСтХд╨УтХд╨ЩтХитЦСтХд╨Я тХитХЬтХитХбтХитФдтХитХбтХитХЧтХд╨Я) тХитХХтХитХЧтХитХХ 'sliding' (тХитФРтХитХЫтХд╨СтХитХЧтХитХбтХитФдтХитХЬтХитХХтХитХб 7 тХитФдтХитХЬтХитХбтХитХг)
        """
        tz = self._get_tz(session)
        now_local = datetime.now(tz)
        
        if mode == "calendar":
            # тХи╨▒ тХитФРтХитХЫтХитХЬтХитХбтХитФдтХитХбтХитХЧтХд╨ЬтХитХЬтХитХХтХитХСтХитЦС тХд╨ТтХитХбтХитХСтХд╨УтХд╨ЩтХитХбтХитХг тХитХЬтХитХбтХитФдтХитХбтХитХЧтХитХХ
            start_date = (now_local - timedelta(days=now_local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now_local
        else:
            # тХи╨птХитХЫтХд╨СтХитХЧтХитХбтХитФдтХитХЬтХитХХтХитХб 7 тХитФдтХитХЬтХитХбтХитХг
            start_date = (now_local - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now_local
            
        # тХи╨зтХитЦСтХитФВтХд╨РтХд╨УтХитХвтХитЦСтХитХбтХитХЭ тХд╨СтХитХЭтХитХбтХитХЬтХд╨Ы тХитХХтХитХЦ тХи╨бтХи╨д
        shifts = session.exec(
            select(Shift)
            .where(Shift.employee_id == employee_id)
            .where(Shift.date_open >= start_date.astimezone(timezone.utc))
            .order_by(Shift.date_open.desc())
        ).all()
        
        total_hours = sum(s.work_hours for s in shifts if s.work_hours)
        total_revenue = sum(float(s.revenue_at_close or 0) for s in shifts)
        
        # тХи╨гтХд╨РтХд╨УтХитФРтХитФРтХитХХтХд╨РтХитХЫтХитЦУтХитХСтХитЦС тХитФРтХитХЫ тХитФдтХитХЬтХд╨ЯтХитХЭ
        daily_stats = {}
        for s in shifts:
            # тХи╨птХд╨РтХитХХтХитЦУтХитХЫтХитФдтХитХХтХитХЭ тХитЦУтХд╨РтХитХбтХитХЭтХд╨Я тХитХЫтХд╨ТтХитХСтХд╨РтХд╨ЫтХд╨ТтХитХХтХд╨Я тХитХС тХитХЧтХитХЫтХитХСтХитЦСтХитХЧтХд╨ЬтХитХЬтХитХЫтХитХЭтХд╨У тХитФдтХитХЧтХд╨Я тХитФВтХд╨РтХд╨УтХитФРтХитФРтХитХХтХд╨РтХитХЫтХитЦУтХитХСтХитХХ тХитФРтХитХЫ тХитФдтХитЦСтХд╨ТтХитХб
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
            
            # тХи╨┤тХитХЫтХд╨РтХитХЭтХитХХтХд╨РтХд╨УтХитХбтХитХЭ тХитХЫтХитЦТтХд╨ЪтХитХбтХитХСтХд╨Т тХд╨СтХитХЭтХитХбтХитХЬтХд╨Ы тХитФдтХитХЧтХд╨Я тХд╨ФтХд╨РтХитХЫтХитХЬтХд╨ТтХитХбтХитХЬтХитФдтХитЦС
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
        """
        тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитФдтХитХбтХд╨ТтХитЦСтХитХЧтХд╨ЬтХитХЬтХд╨ЫтХд╨Х тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХЫтХитХС тХитХСтХд╨УтХд╨РтХд╨ЬтХитХбтХд╨РтХитХЫтХитЦУ тХитХХтХитХЦ iiko Resto OLAP.
        тХи╨зтХитЦСтХитФРтХитХЫтХитХЧтХитХЬтХд╨ЯтХитХбтХд╨Т тХд╨ТтХитЦСтХитЦТтХитХЧтХитХХтХд╨ЦтХд╨У courier_orders: тХитХЦтХитХЫтХитХЬтХд╨Ы, тХд╨СтХд╨УтХитХЭтХитХЭтХд╨Ы, тХитЦУтХд╨РтХитХбтХитХЭтХитХбтХитХЬтХитХЬтХд╨ЫтХитХб тХитХЭтХитХбтХд╨ТтХитХСтХитХХ, тХитХЦтХитЦСтХитФдтХитХбтХд╨РтХитХвтХитХСтХитХХ.
        """
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db or not settings_db.resto_url:
            logger.warning("Resto тХитХЬтХитХб тХитХЬтХитЦСтХд╨СтХд╨ТтХд╨РтХитХЫтХитХбтХитХЬ ╤В╨Р╨д тХд╨СтХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХЫтХитХС тХитФРтХд╨РтХитХЫтХитФРтХд╨УтХд╨ЩтХитХбтХитХЬтХитЦС")
            return

        tz = self._get_tz(session)
        now_local = datetime.now(tz)
        
        if not date_from:
            date_from = now_local - timedelta(days=days)
        if not date_to:
            date_to = now_local

        logger.info(f"тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХЫтХитХС тХитХСтХд╨УтХд╨РтХд╨ЬтХитХбтХд╨РтХитХЫтХитЦУ тХитХХтХитХЦ Resto OLAP ({date_from} ╤В╨Р╨д {date_to})...")

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
            logger.error(f"тХи╨отХд╨ШтХитХХтХитЦТтХитХСтХитЦС тХитФРтХитХЫтХитХЧтХд╨УтХд╨ЧтХитХбтХитХЬтХитХХтХд╨Я тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХЫтХитХС тХитХХтХитХЦ Resto OLAP: {e}")
            return

        # тХи╨ктХд╨ЭтХд╨Ш тХитХСтХд╨УтХд╨РтХд╨ЬтХитХбтХд╨РтХитХЫтХитЦУ тХитФРтХитХЫ тХитХХтХитХЭтХитХбтХитХЬтХитХХ (тХитХЬтХитХХтХитХвтХитХЬтХитХХтХитХг тХд╨РтХитХбтХитФВтХитХХтХд╨СтХд╨ТтХд╨Р)
        all_employees = session.exec(select(Employee)).all()
        courier_by_name: Dict[str, Employee] = {}
        for emp in all_employees:
            # тХи╨│тХд╨ЧтХитХХтХд╨ТтХд╨ЫтХитЦУтХитЦСтХитХбтХитХЭ тХд╨ФтХитХЧтХитЦСтХитФВ is_courier тХитХХ тХд╨РтХитЦСтХитХЦтХитХЧтХитХХтХд╨ЧтХитХЬтХд╨ЫтХитХб тХитХЬтХитЦСтХитФРтХитХХтХд╨СтХитЦСтХитХЬтХитХХтХд╨Я тХд╨РтХитХЫтХитХЧтХитХбтХитХг
            is_c = emp.is_courier or any(k in (emp.role or "").lower() for k in ["тХитХСтХд╨УтХд╨РтХд╨ЬтХитХбтХд╨Р", "courier", "cur"])
            if is_c:
                courier_by_name[(emp.name or "").lower().strip()] = emp

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

            courier_info = d.get("courierInfo") or {}
            courier_name_raw = (courier_info.get("courier") or {}).get("name") or ""
            courier_name_key = (courier_name_raw or "").lower().strip()

            courier_emp = courier_by_name.get(courier_name_key)
            if not courier_emp:
                def _get_meaningful_words(name):
                    words = (name or "").lower().split()
                    return {w for w in words if len(w) > 2 and w not in ["тХитХСтХд╨УтХд╨РтХд╨ЬтХитХбтХд╨Р", "courier", "cur"]}
                
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
                if db_order and db_order.courier_name and db_order.courier_name != "тХи╨нтХитХб тХитХЬтХитЦСтХитХЦтХитХЬтХитЦСтХд╨ЧтХитХбтХитХЬ":
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

            # тХи╨отХитЦТтХитХЫтХитФВтХитЦСтХд╨ЩтХитХбтХитХЬтХитХХтХитХб тХитЦСтХитФдтХд╨РтХитХбтХд╨СтХитЦС тХитХХтХитХЦ тХитХЫтХд╨СтХитХЬтХитХЫтХитЦУтХитХЬтХитХЫтХитХг тХд╨ТтХитЦСтХитЦТтХитХЧтХитХХтХд╨ЦтХд╨Ы тХитХЦтХитЦСтХитХСтХитЦСтХитХЦтХитХЫтХитЦУ (Cloud API тХитХХтХитХЭтХитХбтХитХбтХд╨Т тХитЦТтХитХЫтХитХЧтХитХбтХитХб тХитФдтХитХбтХд╨ТтХитЦСтХитХЧтХд╨ЬтХитХЬтХд╨ЫтХитХг JSON)
            addr_parts = d.get("address") or {}
            db_order = session.exec(select(Order).where(Order.external_number == order_num)).first()
            if db_order and db_order.address_parts:
                # тХи╨бтХитХбтХд╨РтХитХбтХитХЭ тХитФдтХитХбтХд╨ТтХитЦСтХитХЧтХд╨ЬтХитХЬтХд╨ЫтХитХг JSON тХитХХтХитХЦ Cloud API тХитХЦтХитЦСтХитХСтХитЦСтХитХЦтХитЦС
                addr_parts = db_order.address_parts
            
            city_name = settings_db.city_name if settings_db else "тХи╨▓тХд╨ЮтХитХЭтХитХбтХитХЬтХд╨Ь"
            addr_fmt = (settings_db.address_format or "components") if settings_db else "components"
            address_str = self.format_address(addr_parts, city=city_name, fmt=addr_fmt)

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
                    updated_at=datetime.now(timezone.utc)
                )
                session.add(new_order)
                created_count += 1
        
        try:
            session.commit()
            logger.info(f"тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХЫтХитХС тХитХЦтХитЦСтХитЦУтХитХбтХд╨РтХд╨ШтХитХбтХитХЬтХитЦС: {created_count} тХитХЬтХитХЫтХитЦУтХд╨ЫтХд╨Х, {updated_count} тХитХЫтХитЦТтХитХЬтХитХЫтХитЦУтХитХЧтХитХбтХитХЬтХитХЫ")
        except Exception as e:
            session.rollback()
            logger.error(f"тХи╨отХд╨ШтХитХХтХитЦТтХитХСтХитЦС тХд╨СтХитХЫтХд╨ХтХд╨РтХитЦСтХитХЬтХитХбтХитХЬтХитХХтХд╨Я тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХЫтХитХС: {e}")

    async def sync_courier_deliveries_bg(self, date_from: datetime, date_to: datetime):
        """тХи╨втХд╨СтХитФРтХитХЫтХитХЭтХитХЫтХитФВтХитЦСтХд╨ТтХитХбтХитХЧтХд╨ЬтХитХЬтХд╨ЫтХитХг тХитХЭтХитХбтХд╨ТтХитХЫтХитФд тХитФдтХитХЧтХд╨Я тХд╨ФтХитХЫтХитХЬтХитХЫтХитЦУтХитХЫтХитФВтХитХЫ тХитХЦтХитЦСтХитФРтХд╨УтХд╨СтХитХСтХитЦС тХд╨С тХд╨СтХитХЫтХитЦТтХд╨СтХд╨ТтХитЦУтХитХбтХитХЬтХитХЬтХитХЫтХитХг тХд╨СтХитХбтХд╨СтХд╨СтХитХХтХитХбтХитХг"""
        from app.core.database import SessionLocal
        with SessionLocal() as session:
            try:
                await self.sync_courier_deliveries(session, date_from=date_from, date_to=date_to)
            except Exception as e:
                logger.error(f"Error in courier deliveries background sync: {e}")
                session.rollback()


    async def sync_zones_from_external_map(self, session: Session, url: Optional[str] = None) -> Dict[str, Any]:
        """
        тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитФВтХитХбтХитХЫтХитХЭтХитХбтХд╨ТтХд╨РтХитХХтХитХХ тХитХЦтХитХЫтХитХЬ тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХСтХитХХ тХитФРтХитХЫ тХитЦУтХитХЬтХитХбтХд╨ШтХитХЬтХитХбтХитХг тХд╨СтХд╨СтХд╨ЫтХитХЧтХитХСтХитХб (Google Maps KML)
        """
        settings = session.exec(select(IikoSettings)).first()
        
        # тХи╨етХд╨СтХитХЧтХитХХ URL тХитФРтХитХбтХд╨РтХитХбтХитФдтХитЦСтХитХЬ тХд╨ЯтХитЦУтХитХЬтХитХЫ, тХд╨СтХитХЫтХд╨ХтХд╨РтХитЦСтХитХЬтХд╨ЯтХитХбтХитХЭ тХитХбтХитФВтХитХЫ тХитЦУ тХитХЬтХитЦСтХд╨СтХд╨ТтХд╨РтХитХЫтХитХгтХитХСтХитХХ
        if url:
            if settings:
                settings.delivery_zones_map_url = url
                session.add(settings)
                session.commit()
            map_url = url
        else:
            map_url = settings.delivery_zones_map_url if settings else None

        if not map_url:
            return {"success": False, "error": "тХи╨▒тХд╨СтХд╨ЫтХитХЧтХитХСтХитЦС тХитХЬтХитЦС тХитХСтХитЦСтХд╨РтХд╨ТтХд╨У тХитХЬтХитХб тХитХЦтХитЦСтХитФдтХитЦСтХитХЬтХитЦС тХитЦУ тХитХЬтХитЦСтХд╨СтХд╨ТтХд╨РтХитХЫтХитХгтХитХСтХитЦСтХд╨Х"}
        
        logger.info(f"тХи╨нтХитЦСтХд╨ЧтХитЦСтХитХЧтХитХЫ тХитХХтХитХЭтХитФРтХитХЫтХд╨РтХд╨ТтХитЦС тХитФВтХитХбтХитХЫтХитХЭтХитХбтХд╨ТтХд╨РтХитХХтХитХХ тХитХЦтХитХЫтХитХЬ тХитХХтХитХЦ: {map_url}")
        
        # 1. тХи╨зтХитЦСтХитФВтХд╨РтХд╨УтХитХвтХитЦСтХитХбтХитХЭ тХитХХ тХитФРтХитЦСтХд╨РтХд╨СтХитХХтХитХЭ KML
        try:
            from .iiko_service import iiko_service
            kml_zones = await iiko_service.fetch_and_parse_kml(settings.delivery_zones_map_url)
            if not kml_zones:
                return {"success": False, "error": "тХи╨нтХитХб тХд╨УтХитФдтХитЦСтХитХЧтХитХЫтХд╨СтХд╨Ь тХитФРтХитХЫтХитХЧтХд╨УтХд╨ЧтХитХХтХд╨ТтХд╨Ь тХитХЦтХитХЫтХитХЬтХд╨Ы тХитХХтХитХЦ тХд╨УтХитХСтХитЦСтХитХЦтХитЦСтХитХЬтХитХЬтХитХЫтХитХг тХд╨СтХд╨СтХд╨ЫтХитХЧтХитХСтХитХХ. тХи╨птХд╨РтХитХЫтХитЦУтХитХбтХд╨РтХд╨ЬтХд╨ТтХитХб тХитФдтХитХЫтХд╨СтХд╨ТтХд╨УтХитФР тХитХС тХитХСтХитЦСтХд╨РтХд╨ТтХитХб."}
        except Exception as e:
            return {"success": False, "error": f"тХи╨отХд╨ШтХитХХтХитЦТтХитХСтХитЦС тХитФРтХд╨РтХитХХ тХитХЦтХитЦСтХитФВтХд╨РтХд╨УтХитХЦтХитХСтХитХб тХитХСтХитЦСтХд╨РтХд╨ТтХд╨Ы: {str(e)}"}
            
        # 2. тХи╨▒тХитХЫтХитФРтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХЧтХд╨ЯтХитХбтХитХЭ тХитХХ тХитХЫтХитЦТтХитХЬтХитХЫтХитЦУтХитХЧтХд╨ЯтХитХбтХитХЭ
        updated_count = 0
        import json
        from app.models.company import DeliveryZone
        
        all_zones = session.exec(select(DeliveryZone)).all()
        
        for kz in kml_zones:
            name = kz["name"].strip()
            points = kz["points"]
            
            # тХи╨итХд╨ЩтХитХбтХитХЭ тХитХЦтХитХЫтХитХЬтХд╨У тХитЦУ тХи╨бтХи╨д тХитФРтХитХЫ тХитХХтХитХЭтХитХбтХитХЬтХитХХ (тХд╨РтХитХбтХитФВтХитХХтХд╨СтХд╨ТтХд╨РтХитХЫтХитХЬтХитХбтХитХЦтХитЦСтХитЦУтХитХХтХд╨СтХитХХтХитХЭтХитХЫ)
            matched_zone = next((z for z in all_zones if (z.name or "").lower() == (name or "").lower()), None)
            
            if matched_zone:
                # тХи╨▒тХитХЫтХд╨ХтХд╨РтХитЦСтХитХЬтХд╨ЯтХитХбтХитХЭ тХитХСтХитЦСтХитХС JSON тХд╨СтХд╨ТтХд╨РтХитХЫтХитХСтХд╨У (тХд╨СтХитХЫтХитФВтХитХЧтХитЦСтХд╨СтХитХЬтХитХЫ тХитХЭтХитХЫтХитФдтХитХбтХитХЧтХитХХ)
                matched_zone.polygon_coordinates = json.dumps(points)
                matched_zone.updated_at = datetime.now(timezone.utc)
                session.add(matched_zone)
                updated_count += 1
                logger.info(f"тХи╨отХитЦТтХитХЬтХитХЫтХитЦУтХитХЧтХитХбтХитХЬтХитЦС тХитФВтХитХбтХитХЫтХитХЭтХитХбтХд╨ТтХд╨РтХитХХтХд╨Я тХитФдтХитХЧтХд╨Я тХитХЦтХитХЫтХитХЬтХд╨Ы: {name}")
            else:
                logger.warning(f"тХи╨зтХитХЫтХитХЬтХитЦС тХитХХтХитХЦ KML '{name}' тХитХЬтХитХб тХитХЬтХитЦСтХитХгтХитФдтХитХбтХитХЬтХитЦС тХитЦУ тХитЦТтХитЦСтХитХЦтХитХб тХитФдтХитЦСтХитХЬтХитХЬтХд╨ЫтХд╨Х iiko")
                
        try:
            session.commit()
            # тХи╨отХд╨ЧтХитХХтХд╨ЩтХитЦСтХитХбтХитХЭ тХитХСтХд╨ЭтХд╨Ш тХитФРтХитХЫтХд╨СтХитХЧтХитХб тХитХЫтХитЦТтХитХЬтХитХЫтХитЦУтХитХЧтХитХбтХитХЬтХитХХтХд╨Я тХитХЦтХитХЫтХитХЬ (тХитХбтХд╨СтХитХЧтХитХХ тХитХХтХд╨СтХитФРтХитХЫтХитХЧтХд╨ЬтХитХЦтХд╨УтХитХбтХд╨ТтХд╨СтХд╨Я Redis тХитХХтХитХЧтХитХХ тХитХЧтХитХЫтХитХСтХитЦСтХитХЧтХд╨ЬтХитХЬтХд╨ЫтХитХг тХитХСтХд╨ЭтХд╨Ш)
            try:
                from app.core.redis import redis_client
                await redis_client.delete("delivery_zones_all")
                logger.info("тХи╨ктХд╨ЭтХд╨Ш тХитХЦтХитХЫтХитХЬ тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХСтХитХХ тХитХЫтХд╨ЧтХитХХтХд╨ЩтХитХбтХитХЬ")
            except Exception:
                pass

            return {
                "success": True, 
                "updated_count": updated_count, 
                "total_from_map": len(kml_zones),
                "message": f"тХи╨отХитЦТтХитХЬтХитХЫтХитЦУтХитХЧтХитХбтХитХЬтХитХЫ тХитХЦтХитХЫтХитХЬ: {updated_count} тХитХХтХитХЦ {len(kml_zones)}"
            }
        except Exception as e:
            session.rollback()
            logger.error(f"тХи╨отХд╨ШтХитХХтХитЦТтХитХСтХитЦС тХд╨СтХитХЫтХд╨ХтХд╨РтХитЦСтХитХЬтХитХбтХитХЬтХитХХтХд╨Я тХитФВтХитХбтХитХЫтХитХЭтХитХбтХд╨ТтХд╨РтХитХХтХитХХ тХитХЦтХитХЫтХитХЬ: {e}")
            return {"success": False, "error": f"тХи╨отХд╨ШтХитХХтХитЦТтХитХСтХитЦС тХд╨СтХитХЫтХд╨ХтХд╨РтХитЦСтХитХЬтХитХбтХитХЬтХитХХтХд╨Я тХитЦУ тХи╨бтХи╨д: {str(e)}"}


    async def sync_zones_from_kml_file(self, session: Session, kml_content: str) -> Dict[str, Any]:
        """
        тХи╨▒тХитХХтХитХЬтХд╨ХтХд╨РтХитХЫтХитХЬтХитХХтХитХЦтХитЦСтХд╨ЦтХитХХтХд╨Я тХитФВтХитХбтХитХЫтХитХЭтХитХбтХд╨ТтХд╨РтХитХХтХитХХ тХитХЦтХитХЫтХитХЬ тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХСтХитХХ тХитХХтХитХЦ тХитХЦтХитЦСтХитФВтХд╨РтХд╨УтХитХвтХитХбтХитХЬтХитХЬтХитХЫтХитФВтХитХЫ KML тХд╨ФтХитЦСтХитХгтХитХЧтХитЦС
        """
        logger.info("тХи╨нтХитЦСтХд╨ЧтХитЦСтХитХЧтХитХЫ тХитХХтХитХЭтХитФРтХитХЫтХд╨РтХд╨ТтХитЦС тХитФВтХитХбтХитХЫтХитХЭтХитХбтХд╨ТтХд╨РтХитХХтХитХХ тХитХЦтХитХЫтХитХЬ тХитХХтХитХЦ тХитХЦтХитЦСтХитФВтХд╨РтХд╨УтХитХвтХитХбтХитХЬтХитХЬтХитХЫтХитФВтХитХЫ тХд╨ФтХитЦСтХитХгтХитХЧтХитЦС")
        
        # 1. тХи╨птХитЦСтХд╨РтХд╨СтХитХХтХитХЭ KML
        try:
            from .iiko_service import iiko_service
            kml_zones = iiko_service.parse_kml_content(kml_content)
            if not kml_zones:
                return {"success": False, "error": "тХи╨в тХд╨ФтХитЦСтХитХгтХитХЧтХитХб тХитХЬтХитХб тХитХЬтХитЦСтХитХгтХитФдтХитХбтХитХЬтХитХЫ тХитФРтХитХЫтХитХЧтХитХХтХитФВтХитХЫтХитХЬтХитХЫтХитЦУ тХитХЦтХитХЫтХитХЬ тХитФдтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХСтХитХХ."}
        except Exception as e:
            return {"success": False, "error": f"тХи╨отХд╨ШтХитХХтХитЦТтХитХСтХитЦС тХитФРтХд╨РтХитХХ тХитФРтХитЦСтХд╨РтХд╨СтХитХХтХитХЬтХитФВтХитХб тХд╨ФтХитЦСтХитХгтХитХЧтХитЦС: {str(e)}"}
            
        # 2. тХи╨▒тХитХЫтХитФРтХитХЫтХд╨СтХд╨ТтХитЦСтХитЦУтХитХЧтХд╨ЯтХитХбтХитХЭ тХитХХ тХитХЫтХитЦТтХитХЬтХитХЫтХитЦУтХитХЧтХд╨ЯтХитХбтХитХЭ
        updated_count = 0
        import json
        from app.models.company import DeliveryZone
        
        all_zones = session.exec(select(DeliveryZone)).all()
        
        for kz in kml_zones:
            name = kz["name"].strip()
            points = kz["points"]
            description = kz.get("description", "")
            extended_data = kz.get("extended_data", {})
            
            # тХи╨итХд╨ЩтХитХбтХитХЭ тХитХЦтХитХЫтХитХЬтХд╨У тХитЦУ тХи╨бтХи╨д тХитФРтХитХЫ тХитХХтХитХЭтХитХбтХитХЬтХитХХ (тХд╨РтХитХбтХитФВтХитХХтХд╨СтХд╨ТтХд╨РтХитХЫтХитХЬтХитХбтХитХЦтХитЦСтХитЦУтХитХХтХд╨СтХитХХтХитХЭтХитХЫ)
            matched_zone = session.exec(select(DeliveryZone).where(func.lower(DeliveryZone.name) == (name or "").lower())).first()
            
            if matched_zone:
                matched_zone.polygon_coordinates = json.dumps(points)
                matched_zone.description = description
                matched_zone.additional_info = extended_data
                matched_zone.is_manual_override = True  # тХи╨птХд╨РтХитХХтХитХЫтХд╨РтХитХХтХд╨ТтХитХбтХд╨Т тХитФРтХитХЫтХитХЧтХд╨ЬтХитХЦтХитХЫтХитЦУтХитЦСтХд╨ТтХитХбтХитХЧтХд╨Я
                matched_zone.updated_at = datetime.now(timezone.utc)
                session.add(matched_zone)
                updated_count += 1
                logger.info(f"тХи╨отХитЦТтХитХЬтХитХЫтХитЦУтХитХЧтХитХбтХитХЬтХитЦС тХитФВтХитХбтХитХЫтХитХЭтХитХбтХд╨ТтХд╨РтХитХХтХд╨Я тХитХХ тХитХЭтХитХбтХд╨ТтХитЦСтХитФдтХитЦСтХитХЬтХитХЬтХд╨ЫтХитХб тХитФдтХитХЧтХд╨Я тХитХЦтХитХЫтХитХЬтХд╨Ы (тХитХХтХитХЦ KML): {name}")
            else:
                # тХи╨▒тХитХЫтХитХЦтХитФдтХитЦСтХитХбтХитХЭ тХитХЬтХитХЫтХитЦУтХд╨УтХд╨Ю тХитХЦтХитХЫтХитХЬтХд╨У тХитХбтХд╨СтХитХЧтХитХХ тХитХбтХд╨б тХитХЬтХитХбтХд╨Т
                logger.info(f"тХи╨▒тХитХЫтХитХЦтХитФдтХитЦСтХитХЬтХитХХтХитХб тХитХЬтХитХЫтХитЦУтХитХЫтХитХг тХитФРтХд╨РтХитХХтХитХЫтХд╨РтХитХХтХд╨ТтХитХбтХд╨ТтХитХЬтХитХЫтХитХг тХитХЦтХитХЫтХитХЬтХд╨Ы тХитХХтХитХЦ KML тХд╨ФтХитЦСтХитХгтХитХЧтХитЦС: {name}")
                from app.models.company import Branch
                branch = session.exec(select(Branch)).first()
                if branch:
                    new_zone = DeliveryZone(
                        name=name,
                        branch_id=branch.id,
                        polygon_coordinates=json.dumps(points),
                        description=description,
                        additional_info=extended_data,
                        is_manual_override=True,  # тХи╨птХд╨РтХитХХтХитХЫтХд╨РтХитХХтХд╨ТтХитХбтХд╨Т тХитФРтХитХЫтХитХЧтХд╨ЬтХитХЦтХитХЫтХитЦУтХитЦСтХд╨ТтХитХбтХитХЧтХд╨Я
                        is_active=True
                    )
                    session.add(new_zone)
                    updated_count += 1
                else:
                    logger.warning(f"тХи╨нтХитХб тХд╨УтХитФдтХитЦСтХитХЧтХитХЫтХд╨СтХд╨Ь тХд╨СтХитХЫтХитХЦтХитФдтХитЦСтХд╨ТтХд╨Ь тХитХЦтХитХЫтХитХЬтХд╨У {name}: тХд╨ФтХитХХтХитХЧтХитХХтХитЦСтХитХЧ тХитХЬтХитХб тХитХЬтХитЦСтХитХгтХитФдтХитХбтХитХЬ")
                
        try:
            session.commit()
            # тХи╨отХд╨ЧтХитХХтХд╨ЩтХитЦСтХитХбтХитХЭ тХитХСтХд╨ЭтХд╨Ш
            try:
                from app.core.redis import redis_client
                await redis_client.delete("delivery_zones_all")
            except Exception:
                pass

            return {
                "success": True, 
                "updated_count": updated_count, 
                "total_from_file": len(kml_zones),
                "message": f"тХи╨отХитЦТтХитХЬтХитХЫтХитЦУтХитХЧтХитХбтХитХЬтХитХЫ тХитХЦтХитХЫтХитХЬ тХитХХтХитХЦ тХд╨ФтХитЦСтХитХгтХитХЧтХитЦС: {updated_count} тХитХХтХитХЦ {len(kml_zones)}"
            }
        except Exception as e:
            session.rollback()
            logger.error(f"тХи╨отХд╨ШтХитХХтХитЦТтХитХСтХитЦС тХд╨СтХитХЫтХд╨ХтХд╨РтХитЦСтХитХЬтХитХбтХитХЬтХитХХтХд╨Я тХитФВтХитХбтХитХЫтХитХЭтХитХбтХд╨ТтХд╨РтХитХХтХитХХ тХитХЦтХитХЫтХитХЬ тХитХХтХитХЦ тХд╨ФтХитЦСтХитХгтХитХЧтХитЦС: {e}")
            return {"success": False, "error": f"тХи╨отХд╨ШтХитХХтХитЦТтХитХСтХитЦС тХд╨СтХитХЫтХд╨ХтХд╨РтХитЦСтХитХЬтХитХбтХитХЬтХитХХтХд╨Я тХитЦУ тХи╨бтХи╨д: {str(e)}"}


iiko_sync_service = IikoSyncService()
