"""
РЎРµСЂРІРёСЃ-РѕСЂРєРµСЃС‚СЂР°С‚РѕСЂ РґР»СЏ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё РґР°РЅРЅС‹С… СЃ iiko Cloud
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
from app.models.company import Branch, Company, DeliveryZone
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

    def format_address(self, addr_obj: Dict[str, Any], city: Optional[str] = None, fmt: str = "components") -> str:
        """
        РЈРЅРёРІРµСЂСЃР°Р»СЊРЅРѕРµ С„РѕСЂРјР°С‚РёСЂРѕРІР°РЅРёРµ Р°РґСЂРµСЃР° РёР· РѕР±СЉРµРєС‚Р° iiko.
        fmt: 'components' (СЃРѕР±СЂР°С‚СЊ РёР· РїРѕР»РµР№) РёР»Рё 'line1' (РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ РіРѕС‚РѕРІСѓСЋ СЃС‚СЂРѕРєСѓ)
        """
        if not addr_obj or not isinstance(addr_obj, dict):
            return city or "РўСЋРјРµРЅСЊ"

        clean = self.clean_str
        
        # РР·РІР»РµРєР°РµРј РєРѕРјРїРѕРЅРµРЅС‚С‹
        s_obj = addr_obj.get("street")
        street = None
        if isinstance(s_obj, dict):
            street = clean(s_obj.get("name"))
        else:
            street = clean(s_obj)

        # РРіРЅРѕСЂРёСЂСѓРµРј РїР»РµР№СЃС…РѕР»РґРµСЂС‹
        if street and all(char in "-. " for char in street):
            street = None
            
        house = clean(addr_obj.get("house"))
        if house and all(char in "-. " for char in house): house = None
        
        flat = clean(addr_obj.get("flat"))
        if flat and all(char in "-. " for char in flat): flat = None
        
        entrance = clean(addr_obj.get("entrance"))
        floor = clean(addr_obj.get("floor"))
        doorphone = clean(addr_obj.get("doorphone"))

        # РР·РІР»РµС‡РµРЅРёРµ РіРѕСЂРѕРґР°
        city_from_obj = ""
        city_val = addr_obj.get("city")
        if city_val:
            if isinstance(city_val, dict):
                city_from_obj = clean(city_val.get("name"))
            else:
                city_from_obj = clean(city_val)
        
        final_city = clean(city_from_obj or city or "РўСЋРјРµРЅСЊ")
        if not final_city or final_city == "None":
            final_city = "РўСЋРјРµРЅСЊ"

        # Р•СЃР»Рё РІС‹Р±СЂР°РЅ С„РѕСЂРјР°С‚ line1, РїСЂРѕР±СѓРµРј РµРіРѕ
        if fmt == "line1":
            l1 = clean(addr_obj.get("line1") or addr_obj.get("addressString"))
            # Р•СЃР»Рё line1 СЃРѕРґРµСЂР¶РёС‚ Р±РѕР»СЊС€Рµ С‡РµРј РїСЂРѕСЃС‚Рѕ РіРѕСЂРѕРґ, РІРѕР·РІСЂР°С‰Р°РµРј РµРіРѕ
            if l1 and len(l1) > len(final_city) + 2 and not all(char in "-. " for char in l1):
                # РџСЂРѕРІРµСЂСЏРµРј, РµСЃС‚СЊ Р»Рё РІ l1 СѓРїРѕРјРёРЅР°РЅРёСЏ РєРІР°СЂС‚РёСЂС‹ РёР»Рё РґСЂСѓРіРёС… РїРѕР»РµР№
                # Р•СЃР»Рё РёС… РЅРµС‚ РІ СЃС‚СЂРѕРєРµ, РЅРѕ РѕРЅРё РµСЃС‚СЊ РІ РѕР±СЉРµРєС‚Рµ - РґРѕРєР»РµРёРІР°РµРј
                extra = []
                l1_lower = l1.lower()
                
                # РџСЂРёРІРѕРґРёРј РєРѕРјРїРѕРЅРµРЅС‚С‹ Рє СЃС‚СЂРѕРєР°Рј РґР»СЏ РїРѕРёСЃРєР°
                s_flat = clean(flat)
                s_entrance = clean(entrance)
                s_floor = clean(floor)
                s_doorphone = clean(doorphone)

                if s_flat and s_flat != "0" and f"РєРІ. {s_flat.lower()}" not in l1_lower and f"РєРІ {s_flat.lower()}" not in l1_lower:
                    extra.append(f"РєРІ. {s_flat}")
                if s_entrance and s_entrance != "0" and "РїРѕРґ." not in l1_lower and "РїРѕРґСЉРµР·Рґ" not in l1_lower:
                    extra.append(f"РїРѕРґ. {s_entrance}")
                if s_floor and s_floor != "0" and "СЌС‚." not in l1_lower and "СЌС‚Р°Р¶" not in l1_lower:
                    extra.append(f"СЌС‚. {s_floor}")
                if s_doorphone and s_doorphone != "0" and "РґРѕРјРѕС„РѕРЅ" not in l1_lower:
                    extra.append(f"РґРѕРјРѕС„РѕРЅ: {s_doorphone}")
                
                if extra:
                    return f"{l1}, {', '.join(extra)}"
                return l1
        
        # РЎР±РѕСЂРєР° РёР· РєРѕРјРїРѕРЅРµРЅС‚РѕРІ (РљР»Р°СЃСЃРёС‡РµСЃРєРёР№ / Fallback)
        parts = []
        if street or house:
            if street:
                if not any(pref in street.lower() for pref in ["СѓР».", "РїСЂ.", "РїРµСЂ.", "Р±-СЂ"]):
                    parts.append(f"СѓР». {street}")
                else:
                    parts.append(street)
            
            if house and house != "0":
                parts.append(f"Рґ. {house}")
            
            if flat: parts.append(f"РєРІ. {flat}")
            if entrance: parts.append(f"РїРѕРґ. {entrance}")
            if floor: parts.append(f"СЌС‚. {floor}")
            if doorphone: parts.append(f"РґРѕРјРѕС„РѕРЅ: {doorphone}")
            
            addr_str = ", ".join(parts)
            # Р”РѕР±Р°РІР»СЏРµРј РіРѕСЂРѕРґ РµСЃР»Рё РµРіРѕ РЅРµС‚ РІ СЃС‚СЂРѕРєРµ
            if final_city and final_city.lower() not in addr_str.lower():
                return f"Рі. {final_city}, {addr_str}"
            return addr_str

        # Р•СЃР»Рё РєРѕРјРїРѕРЅРµРЅС‚РѕРІ РЅРµС‚, РїСЂРѕР±СѓРµРј line1 РєР°Рє РїРѕСЃР»РµРґРЅРёР№ С€Р°РЅСЃ
        l1 = clean(addr_obj.get("line1") or addr_obj.get("addressString"))
        if l1 and len(l1) > 2 and not all(char in "-. " for char in l1):
            if final_city and final_city.lower() not in l1.lower():
                return f"Рі. {final_city}, {l1}"
            return l1

        return f"Рі. {final_city}"

    def _get_tz(self, session: Session):
        """РџРѕР»СѓС‡РµРЅРёРµ С‡Р°СЃРѕРІРѕРіРѕ РїРѕСЏСЃР° РёР· РЅР°СЃС‚СЂРѕРµРє"""
        from app.core.datetime_utils import get_tz
        return get_tz(session)

    async def sync_menu(self, session: Session) -> Dict[str, Any]:
        """РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РєР°С‚Р°Р»РѕРіР° РјРµРЅСЋ (РєР°С‚РµРіРѕСЂРёРё + С‚РѕРІР°СЂС‹)"""
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
            
            # Р“Р°СЂР°РЅС‚РёСЂСѓРµРј РЅР°Р»РёС‡РёРµ success Рё РїРѕР»РµР№ РґР»СЏ СЃС…РµРјС‹
            response = {
                "success": True,
                "categories_synced": res.get("categories", 0),
                "products_synced": res.get("products", 0),
                "message": f"РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ Р·Р°РІРµСЂС€РµРЅР° СѓСЃРїРµС€РЅРѕ: {res.get('categories', 0)} РєР°С‚РµРіРѕСЂРёР№, {res.get('products', 0)} С‚РѕРІР°СЂРѕРІ"
            }
            
            log.status = "success"
            log.details = response["message"]
            session.add(log)
            session.commit()
            
            # Р”РѕР±Р°РІР»СЏРµРј Р·Р°РїРёСЃСЊ РІ Р°СѓРґРёС‚
            log_audit(action="manual_sync", resource_type="menu", message=response["message"])
            
            return response
        except Exception as e:
            logger.error(f"Menu sync failed: {e}", exc_info=True)
            log.status = "error"
            log.details = str(e)
            session.add(log)
            session.commit()
            
            # Р”РѕР±Р°РІР»СЏРµРј Р·Р°РїРёСЃСЊ РІ Р°СѓРґРёС‚ РѕР± РѕС€РёР±РєРµ
            log_audit(action="manual_sync_failed", resource_type="menu", message=str(e))
            
            return {
                "success": False,
                "error": str(e),
                "message": f"РћС€РёР±РєР° СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё: {str(e)}"
            }

    async def sync_categories_only(self, session: Session) -> Dict[str, Any]:
        """РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ С‚РѕР»СЊРєРѕ РєР°С‚РµРіРѕСЂРёР№ РёР· iiko (РІС‹Р·С‹РІР°РµС‚ РїРѕР»РЅСѓСЋ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЋ РјРµРЅСЋ)"""
        res = await self.sync_menu(session)
        return {
            "success": res.get("success", False),
            "categories_synced": res.get("categories_synced", 0),
            "message": f"РЎРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°РЅРѕ РєР°С‚РµРіРѕСЂРёР№: {res.get('categories_synced', 0)}"
        }

    async def _sync_from_external_menu(self, session: Session, menu_data: Dict[str, Any], log: SyncLog) -> Dict[str, Any]:
        """Р›РѕРіРёРєР° РѕР±СЂР°Р±РѕС‚РєРё РІРЅРµС€РЅРµРіРѕ РјРµРЅСЋ iiko (API v2 /menu/by_id)"""
        if not menu_data:
            return {"categories": 0, "products": 0}
        
        categories_synced = 0
        products_synced = 0

        # 1. РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РєР°С‚РµРіРѕСЂРёР№
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

        # 2. РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ С‚РѕРІР°СЂРѕРІ
        # Р’ v2 С‚РѕРІР°СЂС‹ СЃРіСЂСѓРїРїРёСЂРѕРІР°РЅС‹ РїРѕ РєР°С‚РµРіРѕСЂРёСЏРј РІ itemCategories
        for cat_data in cats_list:
            iiko_cat_id = cat_data.get("id")
            local_cat = session.exec(select(Category).where(Category.iiko_id == iiko_cat_id)).first()
            category_id = local_cat.id if local_cat else None
            
            items_list = cat_data.get("items") or cat_data.get("products") or []
            for item_data in items_list:
                item_id = item_data.get("itemId") or item_data.get("id")
                if not item_id: continue
                
                prod = session.exec(select(Product).where(Product.iiko_id == item_id)).first()
                
                # РР·РІР»РµРєР°РµРј РґР°РЅРЅС‹Рµ РёР· РїРµСЂРІРѕРіРѕ СЂР°Р·РјРµСЂР° РґР»СЏ Р±Р°Р·РѕРІС‹С… РїРѕР»РµР№ С‚РѕРІР°СЂР°
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
                
                session.flush() # РџРѕР»СѓС‡Р°РµРј ID

                # --- РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ СЂР°Р·РјРµСЂРѕРІ ---
                for existing_size in session.exec(select(ProductSize).where(ProductSize.product_id == prod.id)).all():
                    session.delete(existing_size)
                
                if sizes:
                    for s_data in sizes:
                        s_price = 0
                        if s_data.get("prices"): s_price = s_data["prices"][0].get("price", 0)
                        
                        session.add(ProductSize(
                            product_id=prod.id,
                            iiko_id=s_data.get("sizeId") or item_id,
                            name=s_data.get("sizeName") or "РЎС‚Р°РЅРґР°СЂС‚",
                            price=float(s_price or 0),
                            is_default=s_data.get("isDefault", False)
                        ))
                else:
                    session.add(ProductSize(
                        product_id=prod.id,
                        iiko_id=item_id,
                        name="РЎС‚Р°РЅРґР°СЂС‚",
                        price=float(price or 0),
                        is_default=True
                    ))

                # --- РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РјРѕРґРёС„РёРєР°С‚РѕСЂРѕРІ ---
                # Р‘РµСЂРµРј РјРѕРґРёС„РёРєР°С‚РѕСЂС‹ РёР· РґРµС„РѕР»С‚РЅРѕРіРѕ СЂР°Р·РјРµСЂР° (РёР»Рё РїРµСЂРІРѕРіРѕ РґРѕСЃС‚СѓРїРЅРѕРіРѕ)
                target_size = next((s for s in sizes if s.get("isDefault")), sizes[0] if sizes else None)
                if target_size:
                    # РћС‡РёС‰Р°РµРј СЃС‚Р°СЂС‹Рµ РіСЂСѓРїРїС‹ РјРѕРґРёС„РёРєР°С‚РѕСЂРѕРІ
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
        """РћР±СЂР°Р±РѕС‚РєР° РєР»Р°СЃСЃРёС‡РµСЃРєРѕР№ РЅРѕРјРµРЅРєР»Р°С‚СѓСЂС‹ iiko (groups + products + sizes)"""
        if not nomenclature:
            return {"categories": 0, "products": 0}

        categories_synced = 0
        products_synced = 0

        # 1. РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РєР°С‚РµРіРѕСЂРёР№ (groups)
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

        # 2. РњР°РїРїРёРЅРі СЂР°Р·РјРµСЂРѕРІ РґР»СЏ С‚РѕРІР°СЂРѕРІ
        size_map = {s["id"]: s["name"] for s in nomenclature.get("sizes", [])}

        # 3. РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ С‚РѕРІР°СЂРѕРІ (products)
        if "products" in nomenclature:
            for p in nomenclature["products"]:
                if p.get("type") == "Service": continue # РџСЂРѕРїСѓСЃРєР°РµРј СѓСЃР»СѓРіРё
                
                prod = session.exec(select(Product).where(Product.iiko_id == p["id"])).first()
                
                # РџРѕРёСЃРє Р»РѕРєР°Р»СЊРЅРѕР№ РєР°С‚РµРіРѕСЂРёРё
                category_id = None
                if p.get("parentGroup"):
                    local_cat = session.exec(select(Category).where(Category.iiko_id == p["parentGroup"])).first()
                    if local_cat: category_id = local_cat.id
                
                # РћРїСЂРµРґРµР»РµРЅРёРµ Р±Р°Р·РѕРІРѕР№ С†РµРЅС‹ (РїРµСЂРІС‹Р№ РґРѕСЃС‚СѓРїРЅС‹Р№ СЂР°Р·РјРµСЂ)
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
                
                session.flush() # РџРѕР»СѓС‡Р°РµРј ID С‚РѕРІР°СЂР°
                
                # --- РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ СЂР°Р·РјРµСЂРѕРІ ---
                for existing_size in session.exec(select(ProductSize).where(ProductSize.product_id == prod.id)).all():
                    session.delete(existing_size)
                
                if p.get("sizePrices"):
                    for sp in p["sizePrices"]:
                        s_id = sp.get("sizeId")
                        s_name = size_map.get(s_id, "РЎС‚Р°РЅРґР°СЂС‚")
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
        """РРЅС‚РµРіСЂРёСЂРѕРІР°РЅРЅС‹Р№ РјРµС‚РѕРґ РѕР±СЂР°Р±РѕС‚РєРё Р·Р°РєР°Р·Р°: РєРѕРЅСЃРѕР»РёРґРёСЂРѕРІР°РЅРЅР°СЏ Рё РѕС‡РёС‰РµРЅРЅР°СЏ РІРµСЂСЃРёСЏ"""
        if not iiko_order_data:
            logger.warning("Received empty order data from iiko")
            return
            
        try:
            # 1. Р‘Р°Р·РѕРІС‹Рµ РґР°РЅРЅС‹Рµ Р·Р°РєР°Р·Р°
            order_id_iiko = iiko_order_data.get("id")
            o_data = iiko_order_data.get("order")
            if not o_data:
                o_data = iiko_order_data
            
            if not order_id_iiko:
                order_id_iiko = o_data.get("id")

            if not order_id_iiko:
                logger.warning(f"Order data missing ID. Keys available: {list(o_data.keys())}. Full data sample: {str(o_data)[:500]}")
                return
            
            # Р›РѕРіРёСЂСѓРµРј РЅР°С‡Р°Р»Рѕ РѕР±СЂР°Р±РѕС‚РєРё РґР»СЏ РґРёР°РіРЅРѕСЃС‚РёРєРё
            ext_num = o_data.get("number") or o_data.get("externalNumber")
            logger.info(f"==> Processing Iiko Order: ID={order_id_iiko}, Num={ext_num}, Status={o_data.get('status')}")
            
            settings_db = session.exec(select(IikoSettings)).first()
            city_from_settings = settings_db.city_name if settings_db else "РўСЋРјРµРЅСЊ"

            # РћС‡РёСЃС‚РєР° СЃС‚СЂРѕРє РѕС‚ РїР»РµР№СЃС…РѕР»РґРµСЂРѕРІ
            def clean(v):
                if v is None: return None
                s = str(v).strip()
                # РЈРґР°Р»СЏРµРј Р°СЂС‚РµС„Р°РєС‚С‹ "None", "null" Рё РїСЂРѕС‡РёРµ РїР»РµР№СЃС…РѕР»РґРµСЂС‹
                if s.lower() in ["none", "null", "", "-", "--", "---", "----", "----------", ".", "undefined"]: 
                    return None
                return s

            # 2. РЎС‚Р°С‚СѓСЃ Рё РІРЅРµС€РЅРёРµ РЅРѕРјРµСЂР°
            raw_status = clean(o_data.get("status") or iiko_order_data.get("creationStatus"))
            raw_status_lower = raw_status.lower() if raw_status else ""
            external_number = clean(o_data.get("number") or o_data.get("externalNumber")) or None

            # 3. РўР°Р№РјР·РѕРЅР° Рё РІСЂРµРјСЏ
            from app.core.datetime_utils import get_tz_name
            tz_name = get_tz_name(session)
            try:
                import zoneinfo
                tz = zoneinfo.ZoneInfo(tz_name)
            except Exception:
                import zoneinfo
                tz = zoneinfo.ZoneInfo("Asia/Yekaterinburg")
            
            current_time_tz = datetime.now(tz)
            
            # РџРѕРёСЃРє РґР°С‚С‹ СЃРѕР·РґР°РЅРёСЏ РІ СЂР°Р·РЅС‹С… РјРµСЃС‚Р°С… (iiko API РјРѕР¶РµС‚ РјРµРЅСЏС‚СЊ СЃС‚СЂСѓРєС‚СѓСЂСѓ)
            iiko_creation_time_raw = (
                (o_data.get("creationInfo") or {}).get("creationDate") or 
                o_data.get("creationDate") or
                o_data.get("whenCreated")
            )
            iiko_creation_time = None
            if iiko_creation_time_raw:
                try:
                    # РџСЂРёРЅРёРјР°РµРј РІСЂРµРјСЏ РєР°Рє UTC 0, РµСЃР»Рё РµСЃС‚СЊ РїРѕРјРµС‚РєР° Z РёР»Рё СЃРјРµС‰РµРЅРёРµ.
                    # Р­С‚Рѕ РёСЃРїСЂР°РІРёС‚ РїСЂРѕР±Р»РµРјСѓ 5-С‡Р°СЃРѕРІРѕРіРѕ СЃРјРµС‰РµРЅРёСЏ РІ Р°РґРјРёРЅРєРµ.
                    if 'Z' in iiko_creation_time_raw or '+' in iiko_creation_time_raw or '-' in iiko_creation_time_raw[10:]:
                        # ISO С„РѕСЂРјР°С‚ СЃ Z РёР»Рё СЃРјРµС‰РµРЅРёРµРј РїР°СЂСЃРёС‚СЃСЏ РєР°Рє aware datetime
                        dt = datetime.fromisoformat(iiko_creation_time_raw.replace('Z', '+00:00'))
                        iiko_creation_time = dt.astimezone(timezone.utc).replace(tzinfo=None)
                    else:
                        # Р•СЃР»Рё РІСЂРµРјСЏ Р±РµР· РїРѕСЏСЃР° (naive), СЃС‡РёС‚Р°РµРј РµРіРѕ Р»РѕРєР°Р»СЊРЅС‹Рј РґР»СЏ Р·Р°РІРµРґРµРЅРёСЏ
                        dt = datetime.fromisoformat(iiko_creation_time_raw)
                        iiko_creation_time = dt.replace(tzinfo=tz).astimezone(timezone.utc).replace(tzinfo=None)
                    
                    logger.info(f"Parsed iiko time (naive UTC): raw={iiko_creation_time_raw}, result={iiko_creation_time}")
                except Exception as e:
                    logger.error(f"Error parsing iiko creation time {iiko_creation_time_raw}: {e}")

            # 4. РљР»РёРµРЅС‚
            c_data = o_data.get("customer") or {}
            c_first = clean(c_data.get("name"))
            c_last = clean(c_data.get("surname"))
            full_customer_name = f"{c_first or ''} {c_last or ''}".strip() or "Р“РѕСЃС‚СЊ"
            phone = clean(o_data.get("phone") or c_data.get("phone"))

            # 5. РђРґСЂРµСЃ
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
            
            city = city or city_from_settings or "РўСЋРјРµРЅСЊ"

            # Р­РєСЃС‚СЂР°РєС†РёСЏ РєРѕРјРїРѕРЅРµРЅС‚РѕРІ РґР»СЏ Р‘Р” (СЃР»РёРІР°РµРј РґР°РЅРЅС‹Рµ РёР· address Рё deliveryPoint)
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
            
            # РЎРЅР°С‡Р°Р»Р° РїСЂРѕР±СѓРµРј СЃРѕР±СЂР°С‚СЊ Р°РґСЂРµСЃ РёР· РЅР°РёР±РѕР»РµРµ РїРѕР»РЅРѕРіРѕ РѕР±СЉРµРєС‚Р° (РѕР±С‹С‡РЅРѕ СЌС‚Рѕ raw_addr, РЅРѕ РµСЃР»Рё С‚Р°Рј РїСѓСЃС‚Рѕ - raw_addr_dp)
            # Р”Р»СЏ СЌС‚РѕРіРѕ СЃРѕР·РґР°РµРј РІСЂРµРјРµРЅРЅС‹Р№ РѕР±СЉРµРєС‚ СЃРѕ РІСЃРµРјРё РїРѕР»СЏРјРё
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
            
            delivery_address = self.format_address(merged_addr_obj, city=city, fmt=addr_fmt)
            
            # Р•СЃР»Рё РІ РёС‚РѕРіРµ Р°РґСЂРµСЃ РїСѓСЃС‚РѕР№ РёР»Рё "РЎР°РјРѕРІС‹РІРѕР·", РїСЂРѕРІРµСЂСЏРµРј РґСЂСѓРіРёРµ РїРѕР»СЏ
            is_only_city = not delivery_address or delivery_address.strip() in [city, f"Рі. {city}", "Рі.РўСЋРјРµРЅСЊ", "РўСЋРјРµРЅСЊ"]
            
            if is_only_city:
                # Р•СЃР»Рё РІСЃС‘ РµС‰Рµ РїСѓСЃС‚Рѕ, РїСЂРѕР±СѓРµРј deliveryAddress РЅР° РІРµСЂС…РЅРµРј СѓСЂРѕРІРЅРµ
                addr_str = self.clean_str(o_data.get("deliveryAddress"))
                if addr_str and len(addr_str) > len(city or "") + 2:
                    delivery_address = addr_str
                    has_new_address = True
                else:
                    delivery_address = "РЎР°РјРѕРІС‹РІРѕР·"
            else:
                has_new_address = True
            
            # Р•СЃР»Рё РІ РёС‚РѕРіРµ РІСЃС‘ СЂР°РІРЅРѕ С‚РѕР»СЊРєРѕ РіРѕСЂРѕРґ, РЅРѕ РµСЃС‚СЊ addressString РЅР° РІРµСЂС…РЅРµРј СѓСЂРѕРІРЅРµ - РїСЂРѕР±СѓРµРј РµРіРѕ
            if not has_new_address:
                addr_str = self.clean_str(o_data.get("deliveryAddress"))
                if addr_str and len(addr_str) > len(city or "") + 2:
                    delivery_address = addr_str
                    has_new_address = True

            # --- РќРћР’РђРЇ Р›РћР“РРљРђ РћРџР›РђРўР« ---
            sum_total = Decimal(str(o_data.get("sum") or 0)) # Р‘Р°Р·РѕРІР°СЏ СЃСѓРјРјР° (РґРѕ СЃРєРёРґРѕРє)
            # РЎСѓРјРјР° Рє РѕРїР»Р°С‚Рµ РїРѕСЃР»Рµ РїСЂРёРјРµРЅРµРЅРёСЏ СЃРєРёРґРѕРє
            total_with_discount = Decimal(str(o_data.get("totalSum") or o_data.get("total") or sum_total))
            
            # РЎРєРёРґРєРё
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
                if not pn: pn = pk or "РўРёРї РѕРїР»Р°С‚С‹"
                
                psum = float(p.get("sum") or 0)
                
                is_processed_externally = p.get("isProcessedExternally", False) or p.get("processedExternally", False)
                is_prepay = p.get("isPrepay", False) or p.get("prepay", False)
                status_payment = p.get("status", "").lower()
                
                # РЎС‡РёС‚Р°РµРј РїР»Р°С‚РµР¶ РїСЂРѕРІРµРґРµРЅРЅС‹Рј
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
            
            # РЈС‡РёС‚С‹РІР°РµРј iiko Cloud processedPaymentsSum (РµСЃР»Рё РѕРЅ Р±РѕР»СЊС€Рµ С‚РѕРіРѕ С‡С‚Рѕ РјС‹ СЃРїР°СЂСЃРёР»Рё)
            processed_params = float(o_data.get("processedPaymentsSum") or 0)
            if processed_params > total_paid:
                total_paid = processed_params

            # РЎС‡РёС‚Р°РµРј РѕСЃС‚Р°С‚РѕРє
            left_to_pay = max(Decimal('0.00'), total_with_discount - Decimal(str(total_paid)))
            is_paid = (left_to_pay <= 0)
            
            payment_method = ", ".join(list(set(pm_list))) or "РќРµ СѓРєР°Р·Р°РЅ"
            
            # Р¤РѕР»Р±СЌРє СЃС‚Р°С‚СѓСЃР° Р·Р°РєСЂС‹С‚РѕРіРѕ Р·Р°РєР°Р·Р°
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

            # Р•СЃР»Рё Р·Р°РєР°Р· Р·Р°РєСЂС‹С‚ РІ iiko - РѕРЅ С‚РѕС‡РЅРѕ РѕРїР»Р°С‡РµРЅ (РґР»СЏ РЅР°С€РµР№ CRM)
            if not is_paid and mapped_status in (OrderStatus.closed, OrderStatus.delivered):
                is_paid = True
                left_to_pay = Decimal('0.00')
                logger.info(f"Order {order_id_iiko}: Paid via status enforcement ('{mapped_status}')")

            # 7. РљСѓСЂСЊРµСЂ, С‚РёРї Рё РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Рµ РґР°РЅРЅС‹Рµ
            courier_name = "РќРµ РЅР°Р·РЅР°С‡РµРЅ"
            ci = o_data.get("courierInfo") or {}
            if isinstance(ci, dict):
                c_obj = ci.get("courier") or {}
                if isinstance(c_obj, dict):
                    fn = clean(c_obj.get("firstName") or c_obj.get("name")) or ""
                    ln = clean(c_obj.get("lastName")) or ""
                    courier_name = " ".join(filter(None, [fn, ln])).strip() or clean(ci.get("courierName")) or "РќРµ РЅР°Р·РЅР°С‡РµРЅ"
                    # Р”РѕРїРѕР»РЅРёС‚РµР»СЊРЅР°СЏ Р·Р°С‰РёС‚Р° РѕС‚ "None" РІ РєРѕРЅС†Рµ РёРјРµРЅРё
                    if " None" in courier_name:
                        courier_name = courier_name.replace(" None", "").strip()

            stype = (clean(o_data.get("orderServiceType")) or "").lower()
            if not stype and isinstance(o_data.get("orderType"), dict):
                stype = (clean((o_data.get("orderType") or {}).get("orderServiceType")) or "").lower()
            
            order_type = "Р”РѕСЃС‚Р°РІРєР°"
            if any(x in stype for x in ["pickup", "client", "СЃР°РјРѕ"]): 
                order_type = "РЎР°РјРѕРІС‹РІРѕР·"
            elif any(x in stype for x in ["common", "table", "Р·Р°Р»", "СЂРµСЃС‚"]): 
                order_type = "Р’ СЂРµСЃС‚РѕСЂР°РЅРµ"

            # РќРѕРІС‹Рµ РїРѕР»СЏ РґР»СЏ РїРѕР»РЅРѕР№ РёРЅС„РѕСЂРјР°С‚РёРІРЅРѕСЃС‚Рё
            source = clean(o_data.get("source")) or "iiko"
            def parse_dt(dt_str):
                if not dt_str:
                    return None
                try:
                    # ISO 8601 СЃ Z РёР»Рё СЃРјРµС‰РµРЅРёРµРј
                    if 'Z' in dt_str or '+' in dt_str or '-' in dt_str[10:]:
                        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                        return dt.astimezone(timezone.utc).replace(tzinfo=None)
                    # РќР°РёРІРЅР°СЏ РґР°С‚Р° - СЃС‡РёС‚Р°РµРј Р»РѕРєР°Р»СЊРЅРѕР№ РґР»СЏ Р·Р°РІРµРґРµРЅРёСЏ
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
            
            # Р¤РѕР»Р±СЌРє РЅР° РІРµСЂС…РЅРёР№ СѓСЂРѕРІРµРЅСЊ РѕР±СЉРµРєС‚Р° Р·Р°РєР°Р·Р° (iiko Cloud API v2)
            if not expected_time:
                expected_time = parse_dt(o_data.get("completeBefore"))
            if not actual_time:
                actual_time = parse_dt(o_data.get("actualDate"))
            
            # 8. Р¤РёРЅР°Р»СЊРЅС‹Рµ С„Р»Р°РіРё Рё СЃРѕС…СЂР°РЅРµРЅРёРµ
            delay = di.get("delayMinutes")
            admin_name = self.clean_str((o_data.get("conformationInfo") or {}).get("confirmedBy"))
            if not admin_name:
                admin_name = self.clean_str((o_data.get("confirmationInfo") or {}).get("confirmedBy"))

            # 8. РЎРѕС…СЂР°РЅРµРЅРёРµ
            order = session.exec(select(Order).where(Order.iiko_order_id == order_id_iiko)).first()
            
            # РћРїСЂРµРґРµР»СЏРµРј С„РёР»РёР°Р» (branch) РїРѕ terminalGroupId
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
                order.status_history = [{"status": mapped_status, "time": current_time_tz.isoformat(), "comment": "РЎРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°РЅ"}]
            else:
                # Р•СЃР»Рё Р·Р°РєР°Р· СѓР¶Рµ РµСЃС‚СЊ, РѕР±РЅРѕРІР»СЏРµРј branch_id РµСЃР»Рё РѕРЅ РёР·РјРµРЅРёР»СЃСЏ
                order.branch_id = branch_id
            
            # --- Р›РћР“РРљРђ РћРџР Р•Р”Р•Р›Р•РќРРЇ ASAP / РџР Р•Р”Р—РђРљРђР— ---
            raw_comment = self.clean_str(o_data.get("comment"))
            comment_lower = (raw_comment or "").lower()
            
            # Р‘Р°Р·РѕРІС‹Рµ Р·РЅР°С‡РµРЅРёСЏ РёР· iiko (РїСЂРёРѕСЂРёС‚РµС‚ - С„Р»Р°РіСѓ isAsap)
            final_is_asap = bool(o_data.get("isAsap", True))
            
            # 1. Р•СЃР»Рё С„Р»Р°Рі isAsap СЏРІРЅРѕ False - СЌС‚Рѕ РїСЂРµРґР·Р°РєР°Р·
            if o_data.get("isAsap") is False:
                final_is_asap = False
            
            # 2. Р•СЃР»Рё РµСЃС‚СЊ РІСЂРµРјСЏ РіРѕС‚РѕРІРЅРѕСЃС‚Рё Рё РѕРЅРѕ Р·РЅР°С‡РёС‚РµР»СЊРЅРѕ РѕС‚Р»РёС‡Р°РµС‚СЃСЏ РѕС‚ РІСЂРµРјРµРЅРё СЃРѕР·РґР°РЅРёСЏ
            if expected_time and iiko_creation_time:
                diff_mins = (expected_time - iiko_creation_time).total_seconds() / 60
                # Р•СЃР»Рё СЂР°Р·РЅРёС†Р° Р±РѕР»РµРµ 90 РјРёРЅСѓС‚ - СЃРєРѕСЂРµРµ РІСЃРµРіРѕ СЌС‚Рѕ РїСЂРµРґР·Р°РєР°Р· (РЅР° РІСЂРµРјСЏ)
                if diff_mins > 90:
                    final_is_asap = False
            
            # 3. Р”РѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Рµ РїСЂРѕРІРµСЂРєРё РїРѕ РєРѕРјРјРµРЅС‚Р°СЂРёСЋ (РµСЃР»Рё С„Р»Р°Рі РІСЃРµ РµС‰Рµ True)
            if final_is_asap:
                if "РЅР° РІСЂРµРјСЏ" in comment_lower or "РїСЂРµРґР·Р°РєР°Р·" in comment_lower:
                    final_is_asap = False
            
            # 4. Р•СЃР»Рё РІ РєРѕРјРјРµРЅС‚Рµ РќР•Рў РєР»СЋС‡РµРІС‹С… СЃР»РѕРІ РїСЂРµРґР·Р°РєР°Р·Р°, РЅРѕ РµСЃС‚СЊ РґСЂСѓРіРѕР№ С‚РµРєСЃС‚, 
            # Рё РїСЂРё СЌС‚РѕРј РІСЂРµРјСЏ РґРѕСЃС‚Р°РІРєРё Р±Р»РёР·РєРѕ Рє РІСЂРµРјРµРЅРё СЃРѕР·РґР°РЅРёСЏ - РѕСЃС‚Р°РІР»СЏРµРј ASAP
            elif raw_comment and "РЅР° РІСЂРµРјСЏ" not in comment_lower and "РїСЂРµРґР·Р°РєР°Р·" not in comment_lower:
                if expected_time and iiko_creation_time:
                    diff_mins = (expected_time - iiko_creation_time).total_seconds() / 60
                    if diff_mins < 90:
                        final_is_asap = True

            # 3. Р•СЃР»Рё РІСЂРµРјСЏ РіРѕС‚РѕРІРЅРѕСЃС‚Рё РёР·РјРµРЅРёР»РѕСЃСЊ РІ РїСЂРѕС†РµСЃСЃРµ (СЃСЂР°РІРЅРёРІР°РµРј СЃ СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓСЋС‰РёРј Р·Р°РєР°Р·РѕРј РІ Р‘Р”)
            if order and order.expected_time and expected_time:
                # Р‘РµР·РѕРїР°СЃРЅРѕРµ РІС‹С‡РёС‚Р°РЅРёРµ naive/aware
                oe = order.expected_time.replace(tzinfo=None) if order.expected_time.tzinfo else order.expected_time
                ne = expected_time.replace(tzinfo=None) if expected_time.tzinfo else expected_time
                if abs((oe - ne).total_seconds()) > 60:
                    final_is_asap = False

            # Р¤РёРЅР°Р»СЊРЅС‹Рµ С„Р»Р°РіРё
            is_asap = final_is_asap
            is_on_time = not final_is_asap

            # Р’РѕСЃСЃС‚Р°РЅР°РІР»РёРІР°РµРј Р»РѕРіРёРєСѓ РёСЃС‚РѕСЂРёРё СЃС‚Р°С‚СѓСЃРѕРІ
            if order.id and order.status != mapped_status:
                h = list(order.status_history or [])
                h.append({"status": mapped_status, "time": current_time_tz.isoformat(), "comment": f"iiko: {raw_status}"})
                order.status_history = h
                sql_flag_modified(order, "status_history")

            # РњР°РїРїРёРЅРі РІСЃРµС… РїРѕР»РµР№
            order.status = mapped_status
            order.external_number = external_number or order.external_number
            order.customer_name = full_customer_name
            order.customer_phone = phone
            order.courier_name = courier_name
            
            # РћР±РЅРѕРІР»СЏРµРј Р°РґСЂРµСЃРЅС‹Рµ РїРѕР»СЏ С‚РѕР»СЊРєРѕ РµСЃР»Рё РІ РЅРѕРІРѕРј РїР°РєРµС‚Рµ РµСЃС‚СЊ СЂРµР°Р»СЊРЅС‹Р№ Р°РґСЂРµСЃ
            # РР›Р РµСЃР»Рё РІ Р‘Р” Р°РґСЂРµСЃ РµС‰Рµ РЅРµ Р·Р°РїРѕР»РЅРµРЅ (РіРѕСЂРѕРґ РЅРµ СЃС‡РёС‚Р°РµС‚СЃСЏ Р·Р°РїРѕР»РЅРµРЅРЅС‹Рј Р°РґСЂРµСЃРѕРј)
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
            
            # РўРµСЂРјРёРЅР°Р»СЊРЅР°СЏ РіСЂСѓРїРїР°
            order.terminal_group_id = terminal_group_id or order.terminal_group_id
            order.terminal_group_name = terminal_group_name or order.terminal_group_name
            
            # Р”РѕРї. РїРѕР»СЏ
            order.source = source
            order.iiko_creation_time = iiko_creation_time or order.iiko_creation_time
            order.expected_time = expected_time or order.expected_time
            order.actual_time = actual_time or order.actual_time
            order.is_on_time = is_on_time
            order.is_asap = is_asap
            order.delay_minutes = delay
            order.admin_name = admin_name or order.admin_name

            # --- РћРїСЂРµРґРµР»РµРЅРёРµ Р·РѕРЅС‹ РґРѕСЃС‚Р°РІРєРё РїРѕ Р°РґСЂРµСЃСѓ ---
            if order_type == "Р”РѕСЃС‚Р°РІРєР°" and city and street_name and house:
                try:
                    zone_data = await iiko_service.check_address_zone(
                        organization_id=organization_id,
                        city=city,
                        street=street_name,
                        house=house,
                        api_login=settings_db.api_login
                    )
                    if zone_data and zone_data.get("zone"):
                        order.delivery_zone = zone_data.get("zone")
                        logger.info(f"Order {order_id_iiko}: Auto-detected zone: {order.delivery_zone}")
                except Exception as e:
                    logger.warning(f"Could not auto-detect zone: {e}")
            # ---------------------------------------------

            # --- РќРћР’РђРЇ Р›РћР“РРљРђ РЎРћРЎРўРђР’Рђ Р—РђРљРђР—Рђ (СЃ РёРјРµРЅР°РјРё Рё Р·Р°С‰РёС‚РѕР№ РѕС‚ Р·Р°С‚РёСЂР°РЅРёСЏ) ---
            
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
                        
                # Р”РѕСЃС‚Р°РµРј РЅР°Р·РІР°РЅРёСЏ РёР· Р»РѕРєР°Р»СЊРЅРѕР№ Р±Р°Р·С‹
                db_products = session.exec(select(Product).where(Product.iiko_id.in_(product_ids))).all()
                prod_map = {p.iiko_id: p.name for p in db_products}

                # Р”РѕСЃС‚Р°РµРј СЃС‚Р°СЂС‹Рµ РЅР°Р·РІР°РЅРёСЏ РёР· С‚РµРєСѓС‰РµРіРѕ СЃРѕСЃС‚РѕСЏРЅРёСЏ Р·Р°РєР°Р·Р°
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
                        if old_pid and old_name and old_name != "РќРµРёР·РІРµСЃС‚РЅС‹Р№ С‚РѕРІР°СЂ":
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
                            if old_mpid and old_mname and old_mname != "РњРѕРґРёС„РёРєР°С‚РѕСЂ":
                                old_names_map[old_mpid] = old_mname
                
                for item in raw_items:
                    enriched_item = item.copy()
                    pid = item.get("productId")
                    
                    # РџСЂРёРѕСЂРёС‚РµС‚ РёРјРµРЅРё: product.name -> primaryComponent.product.name -> productName -> Р‘Р” -> РСЃС‚РѕСЂРёСЏ -> Fallback
                    if not enriched_item.get("name") or enriched_item.get("name") == "РќРµРёР·РІРµСЃС‚РЅС‹Р№ С‚РѕРІР°СЂ":
                        enriched_item["name"] = (
                            enriched_item.get("product", {}).get("name") or 
                            enriched_item.get("primaryComponent", {}).get("product", {}).get("name") or 
                            enriched_item.get("productName") or 
                            prod_map.get(pid) or 
                            old_names_map.get(pid) or 
                            "РќРµРёР·РІРµСЃС‚РЅС‹Р№ С‚РѕРІР°СЂ"
                        )
                    
                    if not enriched_item.get("sum"):
                        enriched_item["sum"] = float(enriched_item.get("amount", 0)) * float(enriched_item.get("price", 0))
                        
                    enriched_mods = []
                    for mod in (item.get("modifiers") or []):
                        if not mod: continue
                        emod = mod.copy()
                        mpid = mod.get("productId")
                        
                        if not emod.get("name") or emod.get("name") == "РњРѕРґРёС„РёРєР°С‚РѕСЂ":
                            emod["name"] = (
                                emod.get("product", {}).get("name") or 
                                emod.get("primaryComponent", {}).get("product", {}).get("name") or 
                                prod_map.get(mpid) or 
                                old_names_map.get(mpid) or 
                                "РњРѕРґРёС„РёРєР°С‚РѕСЂ"
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
            # РњС‹ РЅРµ РґРµР»Р°РµРј rollback Р·РґРµСЃСЊ, С‡С‚РѕР±С‹ РѕРґРёРЅ Р±РёС‚С‹Р№ Р·Р°РєР°Р· РЅРµ РѕС‚РјРµРЅСЏР» РІСЃС‘, 
            # РЅРѕ Рё РЅРµ РєРѕРјРјРёС‚РёРј С‡Р°СЃС‚РёС‡РЅС‹Рµ РґР°РЅРЅС‹Рµ.
            try:
                session.rollback()
            except:
                pass

    async def sync_orders(self, session: Session, hours: int = 24):
        """
        Р¤РѕРЅРѕРІР°СЏ Р·Р°РґР°С‡Р° РјР°СЃСЃРѕРІРѕР№ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё Р·Р°РєР°Р·РѕРІ.
        РСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ РґР»СЏ Р°РєС‚СѓР°Р»РёР·Р°С†РёРё СЃС‚Р°С‚СѓСЃРѕРІ (РЅР° СЃР»СѓС‡Р°Р№ РїСЂРѕРїСѓСЃРєР° РІРµР±С…СѓРєРѕРІ).
        """
        log = SyncLog(sync_type="orders", status="running")
        session.add(log)
        session.commit()
        
        try:
            settings_db = session.exec(select(IikoSettings)).first()
            if not settings_db or not settings_db.organization_id:
                logger.warning("Iiko settings not found, sync aborted")
                log.status = "error"
                log.details = "РќР°СЃС‚СЂРѕР№РєРё Iiko РЅРµ РЅР°Р№РґРµРЅС‹"
                session.add(log)
                session.commit()
                return
                
            org_id = settings_db.organization_id
        
            # РћРїСЂРµРґРµР»СЏРµРј РёРЅС‚РµСЂРІР°Р» РЅР° РѕСЃРЅРѕРІРµ С‡Р°СЃРѕРІРѕРіРѕ РїРѕСЏСЃР° РёР· РЅР°СЃС‚СЂРѕРµРє
            from app.core.datetime_utils import get_tz_name, get_local_now
            tz_name = get_tz_name(session)
            now = get_local_now(tz_name)
            
            # РћРіСЂР°РЅРёС‡РёРІР°РµРј РґРёР°РїР°Р·РѕРЅ: 24 С‡Р°СЃР° РЅР°Р·Р°Рґ Рё 24 С‡Р°СЃР° РІРїРµСЂРµРґ (РёС‚РѕРіРѕ 48 С‡Р°СЃРѕРІ СЃРѕРіР»Р°СЃРЅРѕ С‚СЂРµР±РѕРІР°РЅРёСЋ)
            date_from = now - timedelta(hours=24)
            date_to = now + timedelta(hours=24)
            
            logger.info(f"Mass sync starting: orders from {date_from} to {date_to} for org {org_id}")
            
            all_ids = set()

            # 0. РРЅРєСЂРµРјРµРЅС‚Р°Р»СЊРЅР°СЏ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РїРѕ СЂРµРІРёР·РёСЏРј (Р±С‹СЃС‚СЂС‹Р№ catch-up РїСЂРѕРїСѓС‰РµРЅРЅС‹С… РІРµР±С…СѓРєРѕРІ)
            # РњС‹ РІРѕР·РІСЂР°С‰Р°РµРј РµС‘, С‚Р°Рє РєР°Рє РѕРЅР° РЅР°РґРµР¶РЅРµРµ РґР»СЏ РїРѕРёСЃРєР° РёР·РјРµРЅРµРЅРёР№ Р±РµР· РїРµСЂРµР±РѕСЂР° РІСЃРµС… РґР°С‚.
            try:
                await self.sync_orders_by_revision(session, org_id)
            except Exception as rev_err:
                logger.error(f"Revision sync failed, falling back to date polling: {rev_err}")

            # 1. РР· iiko Cloud (РїРѕ РґР°С‚Р°Рј РґРѕСЃС‚Р°РІРєРё) - РєР°Рє СЃС‚СЂР°С…РѕРІРѕС‡РЅС‹Р№ РјРµС…Р°РЅРёР·Рј
            # РњС‹ РІСЃРµРіРґР° РёСЃРїРѕР»СЊР·СѓРµРј СЂР°Р·Р±РёРµРЅРёРµ РЅР° С‡Р°РЅРєРё, С‚Р°Рє РєР°Рє СЌС‚Рѕ СЃР°РјС‹Р№ РЅР°РґРµР¶РЅС‹Р№ СЃРїРѕСЃРѕР± РёР·Р±РµР¶Р°С‚СЊ TOO_MANY_DATA_REQUESTED
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
                        log_error=True # РўРµРїРµСЂСЊ Р»РѕРіРёСЂСѓРµРј, С‡С‚РѕР±С‹ РІРёРґРµС‚СЊ РїРѕС‡РµРјСѓ РїСѓСЃС‚Рѕ
                    )
                    if batch:
                        logger.info(f"Fetched {len(batch)} orders for period {chunk_start} - {chunk_end}")
                        cloud_orders.extend(batch)
                    
                    # РќРµР±РѕР»СЊС€Р°СЏ РїР°СѓР·Р° РјРµР¶РґСѓ С‡Р°РЅРєР°РјРё РґР»СЏ СЃС‚Р°Р±РёР»СЊРЅРѕСЃС‚Рё
                    await asyncio.sleep(0.5)
                except Exception as chunk_err:
                    logger.error(f"Failed to fetch orders chunk ({chunk_start} - {chunk_end}): {chunk_err}")
                    if "429" in str(chunk_err):
                        await asyncio.sleep(5.0)
                
                chunk_start = chunk_end

            for o in cloud_orders:
                if o.get("id"): all_ids.add(o["id"])
            logger.info(f"Found {len(cloud_orders)} orders in Cloud (via date polling)")
                
            # 2. РР· iiko Resto (РµСЃР»Рё РЅР°СЃС‚СЂРѕРµРЅ)
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
                    
            # 3. Р”РѕРїРѕР»РЅРёС‚РµР»СЊРЅРѕ: РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ РїСЂРѕРІРµСЂСЏРµРј РІСЃРµ Р°РєС‚РёРІРЅС‹Рµ Р·Р°РєР°Р·С‹ РёР· РЅР°С€РµР№ Р‘Р”
            # Р­С‚Рѕ РєСЂРёС‚РёС‡РµСЃРєРё РІР°Р¶РЅРѕ, РµСЃР»Рё iiko Cloud API РїРѕ РґР°С‚Р°Рј СЂР°Р±РѕС‚Р°РµС‚ РЅРµСЃС‚Р°Р±РёР»СЊРЅРѕ РёР»Рё РІРµР±С…СѓРєРё РїСЂРѕРїСѓС‰РµРЅС‹
            try:
                # Р’РєР»СЋС‡Р°РµРј РІСЃРµ СЃС‚Р°С‚СѓСЃС‹, РєРѕС‚РѕСЂС‹Рµ РЅРµ СЏРІР»СЏСЋС‚СЃСЏ С„РёРЅР°Р»СЊРЅС‹РјРё (Р·Р°РєСЂС‹С‚/РѕС‚РјРµРЅРµРЅ)
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
                
                # РўР°РєР¶Рµ РґРѕР±Р°РІРёРј СЃС‚СЂРѕРєРѕРІС‹Рµ РїСЂРµРґСЃС‚Р°РІР»РµРЅРёСЏ РЅР° СЃР»СѓС‡Р°Р№, РµСЃР»Рё РІ Р‘Р” Р·Р°РєСЂР°Р»РёСЃСЊ СЃС‚Р°СЂС‹Рµ Р·РЅР°С‡РµРЅРёСЏ
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
                    # Р”РѕР±Р°РІР»СЏРµРј РЅРµР±РѕР»СЊС€СѓСЋ Р·Р°РґРµСЂР¶РєСѓ, С‡С‚РѕР±С‹ РЅРµ РїСЂРµРІС‹СЃРёС‚СЊ Р»РёРјРёС‚С‹ API (429) 
                    if success_count > 0 and success_count % 15 == 0:
                        await asyncio.sleep(0.5)

                    # РСЃРїРѕР»СЊР·СѓРµРј sync_order_by_id РґР»СЏ РєР°Р¶РґРѕРіРѕ Р·Р°РєР°Р·Р°
                    # РњС‹ РЅРµ С…РѕС‚РёРј, С‡С‚РѕР±С‹ РѕС€РёР±РєР° РІ РѕРґРЅРѕРј Р·Р°РєР°Р·Рµ РїСЂРµСЂРІР°Р»Р° РІРµСЃСЊ С†РёРєР»
                    res = await self.sync_order_by_id(session, order_id, org_id)
                    if res: success_count += 1
                except Exception as e:
                    logger.error(f"Failed to sync order {order_id}: {e}")
                    
            logger.info(f"Mass sync finished. Total: {len(all_ids)}, Success: {success_count}")
            log.status = "success"
            log.processed_count = success_count
            log.details = f"РЈСЃРїРµС€РЅРѕ СЃРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°РЅРѕ {success_count} Р·Р°РєР°Р·РѕРІ РёР· {len(all_ids)}"
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
        РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ Р·Р°РєР°Р·РѕРІ РїРѕ СЂРµРІРёР·РёСЏРј (catch-up).
        РџРѕР·РІРѕР»СЏРµС‚ РЅР°Р№С‚Рё Р·Р°РєР°Р·С‹, РєРѕС‚РѕСЂС‹Рµ Р±С‹Р»Рё РїСЂРѕРїСѓС‰РµРЅС‹ РІРµР±С…СѓРєР°РјРё, РЅРµР·Р°РІРёСЃРёРјРѕ РѕС‚ РґР°С‚С‹.
        """
        # 0. Р—Р°С‰РёС‚Р° РѕС‚ СЃР»РёС€РєРѕРј С‡Р°СЃС‚РѕРіРѕ РїРѕР»Р»РёРЅРіР° (РЅРµ С‡Р°С‰Рµ С‡РµРј СЂР°Р· РІ 20 СЃРµРєСѓРЅРґ)
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
            # 1. Р•СЃР»Рё СЂРµРІРёР·РёСЏ 0 РёР»Рё РїСѓСЃС‚Р°СЏ - Р·Р°РїСѓСЃРєР°РµРј 'Cold Start' РІРѕСЃСЃС‚Р°РЅРѕРІР»РµРЅРёРµ
            if current_revision == 0:
                logger.warning(f"Revision 0 detected. Starting 'Cold Start' recovery for org {organization_id}...")
                
                # Рђ) РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅР°СЏ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ Р·Р° РїРѕСЃР»РµРґРЅРёРµ 48 С‡Р°СЃРѕРІ, С‡С‚РѕР±С‹ РЅРµ РїРѕС‚РµСЂСЏС‚СЊ РґР°РЅРЅС‹Рµ
                await self.sync_orders(session, hours=48)
                
                # Р‘) РџРѕР»СѓС‡Р°РµРј Р°РєС‚СѓР°Р»СЊРЅСѓСЋ СЂРµРІРёР·РёСЋ РёР· Iiko РґР»СЏ Р±СѓРґСѓС‰РёС… РёРЅРєСЂРµРјРµРЅС‚Р°Р»СЊРЅС‹С… РѕР±РЅРѕРІР»РµРЅРёР№
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

            # 2. Р—Р°РїСЂР°С€РёРІР°РµРј РёР·РјРµРЅРµРЅРёСЏ СЃ РїРѕСЃР»РµРґРЅРµР№ СЂРµРІРёР·РёРё
            data = await iiko_service.get_deliveries_by_revision(
                organization_id=organization_id,
                initial_revision=current_revision,
                api_login=settings_db.api_login
            )
            
            # iiko_service.get_deliveries_by_revision С‚РµРїРµСЂСЊ СЃР°Рј СЂР°СЃРїР°РєРѕРІС‹РІР°РµС‚ ordersByOrganizations
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
                    # РћР±СЂР°Р±Р°С‚С‹РІР°РµРј РєР°Р¶РґС‹Р№ Р·Р°РєР°Р·
                    await self.process_iiko_order(session, order_data, organization_id)
                    count += 1
                except Exception as e:
                    logger.error(f"Error processing order from revision: {e}")
            
            # РћР±РЅРѕРІР»СЏРµРј СЂРµРІРёР·РёСЋ РІ РЅР°СЃС‚СЂРѕР№РєР°С…
            if max_revision:
                settings_db.last_order_revision = max_revision
                session.add(settings_db)
                session.commit()
                logger.info(f"Revision sync finished. New revision: {max_revision}, Processed: {count}")
                
        except httpx.HTTPStatusError as e:
            # 3. РћР±СЂР°Р±РѕС‚РєР° РѕС€РёР±РєРё "TOO_OLD_REVISION" (РљРѕРґ 400)
            if e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    if error_data.get("error") == "TOO_OLD_REVISION":
                        logger.warning(f"Revision {current_revision} is too old. Starting 'Cold Start' recovery...")
                        
                        # РЎР±СЂР°СЃС‹РІР°РµРј СЂРµРІРёР·РёСЋ, С‡С‚РѕР±С‹ РїСЂРё СЃР»РµРґСѓСЋС‰РµРј Р·Р°РїСѓСЃРєРµ (РёР»Рё СЂРµРєСѓСЂСЃРёРІРЅРѕ) СЃСЂР°Р±РѕС‚Р°Р» Cold Start
                        settings_db.last_order_revision = 0
                        session.add(settings_db)
                        session.commit()
                        
                        # Р—Р°РїСѓСЃРєР°РµРј Cold Start РЅРµРјРµРґР»РµРЅРЅРѕ
                        await self.sync_orders_by_revision(session, organization_id)
                        return 
                except Exception as parse_err:
                    logger.error(f"Failed to handle 400 error: {parse_err}")
            
            logger.error(f"Iiko API error during revision sync: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in sync_orders_by_revision: {e}")

    async def sync_order_by_id(self, session: Session, order_id: str, organization_id: str) -> bool:
        """РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РєРѕРЅРєСЂРµС‚РЅРѕРіРѕ Р·Р°РєР°Р·Р° РїРѕ ID (РІС‹Р·С‹РІР°РµС‚СЃСЏ РІРµР±С…СѓРєР°РјРё)"""
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
        """РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ Р·РѕРЅ Рё СѓСЃР»РѕРІРёР№ РґРѕСЃС‚Р°РІРєРё РёР· iiko Cloud"""
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db or not settings_db.organization_id:
            return {"error": "Iiko not configured"}
            
        try:
            data = await iiko_service.get_delivery_restrictions(
                api_login=settings_db.api_login,
                organization_id=settings_db.organization_id
            )
            
            # Р‘РµСЂРµРј РїРµСЂРІС‹Р№ С„РёР»РёР°Р» РєР°Рє С†РµР»РµРІРѕР№ (РІ С‚РµРєСѓС‰РµР№ Р»РѕРіРёРєРµ Р‘Р”)
            branch = session.exec(select(Branch)).first()
            if not branch:
                return {"error": "No branch found in DB"}

            synced_count = 0
            # РЎС‚СЂСѓРєС‚СѓСЂР° РѕС‚РІРµС‚Р° iiko РјРѕР¶РµС‚ Р±С‹С‚СЊ {"deliveryRestrictions": [...]} РёР»Рё РїСЂРѕСЃС‚Рѕ СЃРїРёСЃРѕРє
            restrictions_data = []
            if isinstance(data, dict):
                restrictions_data = data.get("deliveryRestrictions", [])
            elif isinstance(data, list):
                restrictions_data = data
                
            if not restrictions_data:
                logger.warning("РќРµС‚ РґР°РЅРЅС‹С… РѕР± РѕРіСЂР°РЅРёС‡РµРЅРёСЏС… РґРѕСЃС‚Р°РІРєРё РѕС‚ iiko")
                return {"success": True, "synced": 0, "message": "No restrictions data"}

            # РЎРѕР±РёСЂР°РµРј РІСЃРµ РїРѕР»РёРіРѕРЅС‹ РёР· KML
            all_polygons = {}
            for org_data in restrictions_data:
                if not isinstance(org_data, dict):
                    continue
                map_url = org_data.get("deliveryRegionsMapUrl")
                if map_url:
                    logger.info(f"РќР°Р№РґРµРЅР° СЃСЃС‹Р»РєР° РЅР° РєР°СЂС‚Сѓ РІ iiko: {map_url}. Р—Р°РіСЂСѓР·РєР° РїРѕР»РёРіРѕРЅРѕРІ...")
                    try:
                        kml_zones = await iiko_service.fetch_and_parse_kml(map_url)
                        for kz in kml_zones:
                            # РЎРѕС…СЂР°РЅСЏРµРј РїРѕР»РёРіРѕРЅ РїРѕ РёРјРµРЅРё Р·РѕРЅС‹ (РІ РЅРёР¶РЅРµРј СЂРµРіРёСЃС‚СЂРµ РґР»СЏ СЃРѕРїРѕСЃС‚Р°РІР»РµРЅРёСЏ)
                            name_key = kz["name"].lower().strip()
                            all_polygons[name_key] = kz["points"]
                            logger.info(f"Р—Р°РіСЂСѓР¶РµРЅР° РіРµРѕРјРµС‚СЂРёСЏ РґР»СЏ Р·РѕРЅС‹ РёР· iiko-РєР°СЂС‚С‹: {name_key}")
                    except Exception as e:
                        logger.error(f"РћС€РёР±РєР° РїСЂРё Р·Р°РіСЂСѓР·РєРµ РїРѕР»РёРіРѕРЅРѕРІ РїРѕ СЃСЃС‹Р»РєРµ РёР· iiko: {e}")

            for org_data in restrictions_data:
                if not isinstance(org_data, dict):
                    continue
                for res in org_data.get("restrictions", []):
                    zone_name = res.get("zone")
                    if not zone_name:
                        continue
                        
                    min_sum = float(res.get("minSum") or 0)
                    delivery_cost = float(res.get("deliveryPrice") or 0)
                    
                    # РСЃРїРѕР»СЊР·СѓРµРј zoneId РёР· iiko РµСЃР»Рё РµСЃС‚СЊ, РёРЅР°С‡Рµ РёРјСЏ
                    iiko_zone_id = res.get("zoneId") or zone_name
                    
                    # РС‰РµРј Р’РЎР• Р·РѕРЅС‹, РїСЂРёРІСЏР·Р°РЅРЅС‹Рµ Рє СЌС‚РѕРјСѓ ID РёР»Рё СЃ С‚Р°РєРёРј Р¶Рµ РёРјРµРЅРµРј
                    zones = session.exec(select(DeliveryZone).where(
                        (DeliveryZone.iiko_id == iiko_zone_id) | 
                        (DeliveryZone.name == zone_name)
                    )).all()
                    
                    if not zones:
                        logger.info(f"РЎРѕР·РґР°РЅРёРµ РЅРѕРІРѕР№ Р·РѕРЅС‹ РґРѕСЃС‚Р°РІРєРё: {zone_name}")
                        new_zone = DeliveryZone(name=zone_name, branch_id=branch.id, iiko_id=iiko_zone_id)
                        session.add(new_zone)
                        zones = [new_zone]
                    
                    for zone in zones:
                        # РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ РѕР±РЅРѕРІР»СЏРµРј iiko_id РµСЃР»Рё РѕРЅ РЅРµ Р±С‹Р» Р·Р°РґР°РЅ РёР»Рё РёР·РјРµРЅРёР»СЃСЏ
                        if zone.iiko_id != iiko_zone_id:
                            zone.iiko_id = iiko_zone_id
                            
                        # Р•СЃР»Рё Р·РѕРЅР° Р±С‹Р»Р° РёР·РјРµРЅРµРЅР° СЂСѓРєР°РјРё - РјС‹ РІСЃРµ СЂР°РІРЅРѕ РѕР±РЅРѕРІР»СЏРµРј РµС‘ РїСЂРё СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё, 
                        # С‚Р°Рє РєР°Рє СЌС‚Рѕ СЏРІРЅРѕРµ РґРµР№СЃС‚РІРёРµ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ "РЎРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°С‚СЊ"
                        # РќРѕ РµСЃР»Рё С…РѕС‚РёРј Р·Р°С‰РёС‚РёС‚СЊ - РјРѕР¶РЅРѕ РґРѕР±Р°РІРёС‚СЊ РїСЂРѕРІРµСЂРєСѓ. 
                        # РџРѕРєР° СѓР±РёСЂР°РµРј РїСЂРѕРїСѓСЃРє, С‡С‚РѕР±С‹ СЃРѕРїРѕСЃС‚Р°РІР»РµРЅРёРµ СЂР°Р±РѕС‚Р°Р»Рѕ.
                        
                        zone.min_order_amount = min_sum
                        zone.delivery_cost = delivery_cost
                        zone.min_delivery_time = res.get("minDeliveryTime")
                        zone.max_delivery_time = res.get("maxDeliveryTime")
                        zone.free_delivery_sum = float(res.get("freeDeliverySum") or 0) if res.get("freeDeliverySum") is not None else None
                        zone.priority = int(res.get("priority") or 0)
                        zone.is_default = bool(res.get("isDefault"))
                        zone.updated_at = datetime.now(timezone.utc)
                        
                        # Р”РѕР±Р°РІР»СЏРµРј РєРѕРѕСЂРґРёРЅР°С‚С‹ РµСЃР»Рё РЅР°С€Р»Рё РёС… РІ KML Рё Сѓ Р·РѕРЅС‹ РµС‰С‘ РЅРµС‚ РєРѕРѕСЂРґРёРЅР°С‚
                        if not zone.polygon_coordinates or zone.polygon_coordinates == '[]':
                            zone_key = (zone_name or "").lower().strip()
                            if zone_key in all_polygons:
                                zone.polygon_coordinates = json.dumps(all_polygons[zone_key])
                                logger.info(f"РџСЂРёРјРµРЅРµРЅР° РіРµРѕРјРµС‚СЂРёСЏ РґР»СЏ Р·РѕРЅС‹ {zone.name} РёР· KML-РєР°СЂС‚С‹ iiko")
                        
                        session.add(zone)
                        synced_count += 1


                    
                    # Р”РѕР±Р°РІР»СЏРµРј РєРѕРѕСЂРґРёРЅР°С‚С‹ РµСЃР»Рё РЅР°С€Р»Рё РёС… РІ KML
                    zone_key = zone_name.lower().strip()
                    if zone_key in all_polygons:
                        import json
                        new_poly = json.dumps(all_polygons[zone_key])
                        # РћР±РЅРѕРІР»СЏРµРј С‚РѕР»СЊРєРѕ РµСЃР»Рё РєРѕРѕСЂРґРёРЅР°С‚С‹ РёР·РјРµРЅРёР»РёСЃСЊ РёР»Рё РёС… РЅРµС‚
                        if zone.polygon_coordinates != new_poly:
                            logger.info(f"РћР±РЅРѕРІР»РµРЅРёРµ РїРѕР»РёРіРѕРЅР° РґР»СЏ Р·РѕРЅС‹: {zone.name}")
                            zone.polygon_coordinates = new_poly
                    elif not zone.polygon_coordinates or zone.polygon_coordinates == "[]":
                        # Р•СЃР»Рё РєРѕРѕСЂРґРёРЅР°С‚ РЅРµС‚ Рё РІ Р‘Р” РїСѓСЃС‚Рѕ, СЃС‚Р°РІРёРј РїСѓСЃС‚РѕР№ РјР°СЃСЃРёРІ
                        zone.polygon_coordinates = "[]"
                    # РРЅР°С‡Рµ (РµСЃР»Рё РІ Р‘Р” СѓР¶Рµ РµСЃС‚СЊ РєРѕРѕСЂРґРёРЅР°С‚С‹, Р° РІ KML СЃРµР№С‡Р°СЃ РЅРµС‚) - РћРЎРўРђР’Р›РЇР•Рњ РЎРўРђР Р«Р•
                    
                    # Р”РѕРїРѕР»РЅРёС‚РµР»СЊРЅР°СЏ РёРЅС„Р°
                    zone.additional_info = res
                    
                    session.add(zone)
                    synced_count += 1
            
            session.commit()
            logger.info(f"РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ Р·РѕРЅ Р·Р°РІРµСЂС€РµРЅР°: {synced_count} Р·РѕРЅ")
            return {"status": "success", "synced_zones": synced_count, "polygons_found": len(all_polygons)}
        except Exception as e:
            logger.error(f"Delivery zones sync failed: {e}")
            session.rollback()
            return {"error": str(e)}

    async def get_available_iiko_zones(self, session: Session) -> List[Dict[str, Any]]:
        """РџРѕР»СѓС‡РёС‚СЊ СЃРїРёСЃРѕРє РІСЃРµС… РґРѕСЃС‚СѓРїРЅС‹С… Р·РѕРЅ РёР· iiko Cloud (Р±РµР· СЃРѕС…СЂР°РЅРµРЅРёСЏ)"""
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
        """РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ С‚РёРїРѕРІ РѕРїР»Р°С‚С‹ РёР· iiko Cloud"""
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
            logger.info(f"РќР°С‡РёРЅР°СЋ РѕР±СЂР°Р±РѕС‚РєСѓ {len(payment_types)} С‚РёРїРѕРІ РѕРїР»Р°С‚С‹ РёР· iiko")
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
                        is_active=True # РћР‘РЇР—РђРўР•Р›Р¬РќРћ! РРЅР°С‡Рµ РѕРЅРё РїСЂРѕРїР°РґСѓС‚ РїСЂРё F5
                    )
                    session.add(new_pt)
                synced_count += 1
            
            logger.info(f"РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ Р·Р°РІРµСЂС€РµРЅР°. Р’СЃРµРіРѕ: {synced_count}")
            session.commit()
            return {"status": "success", "synced_count": synced_count}
        except Exception as e:
            logger.error(f"Payment types sync failed: {e}")
            session.rollback()
            return {"error": str(e)}


    async def sync_stop_lists(self, session: Session = None):
        """РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ СЃС‚РѕРї-Р»РёСЃС‚РѕРІ"""
        # Р›РѕРіРёРєР° СЃС‚РѕРї-Р»РёСЃС‚РѕРІ
        pass

    async def sync_employees_full(self, session: Session, days: int = 7) -> None:
        """
        РџРѕР»РЅР°СЏ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ СЃРѕС‚СЂСѓРґРЅРёРєРѕРІ Рё РёС… СЃРјРµРЅ С‡РµСЂРµР· iiko RESTO (Office) API.
        """
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db or not settings_db.resto_url:
            logger.error("РќР°СЃС‚СЂРѕР№РєРё iiko Resto (Office) РЅРµ РЅР°Р№РґРµРЅС‹. РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РѕС‚РјРµРЅРµРЅР°.")
            return

        tz = self._get_tz(session)
        now_local = datetime.now(tz)
        date_from = now_local - timedelta(days=days)

        # --- РЁР°Рі 1: РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РїСЂРѕС„РёР»РµР№ СЃРѕС‚СЂСѓРґРЅРёРєРѕРІ ---
        # РџР°СЂР°РјРµС‚СЂС‹ РїРѕРґРєР»СЋС‡РµРЅРёСЏ Р±РµСЂС‘Рј РёР· Р‘Р”, Р° РЅРµ РёР· ENV
        r_url = settings_db.resto_url
        r_login = settings_db.resto_login
        r_password = settings_db.resto_password
        try:
            logger.info("Р—Р°РїСЂРѕСЃ СЃРїРёСЃРєР° СЃРѕС‚СЂСѓРґРЅРёРєРѕРІ РёР· iiko Resto...")
            iiko_employees = await iiko_service.get_resto_employees(
                resto_url=r_url, resto_login=r_login, resto_password=r_password
            )
            
            for emp in iiko_employees:
                emp_iiko_id = emp.get("id")
                if not emp_iiko_id: continue
                
                name = emp.get("name") or f"{emp.get('firstName', '')} {emp.get('lastName', '')}".strip()
                role = emp.get("role")
                rate = emp.get("salary")
                
                # Р”РѕРєСѓРјРµРЅС‚С‹ Рё РґРѕРї. РёРЅС„Рѕ
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
                    return ("РєСѓСЂСЊРµСЂ" in r_l or "courier" in r_l or r_l in ["cur", "cour"]
                            or "РєСѓСЂСЊРµСЂ" in n_l or "courier" in n_l)
                def _flag_admin(r, n=""):
                    r_l = (r or "").lower()
                    return any(k in r_l for k in ["Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂ", "РѕРїРµСЂР°С‚РѕСЂ", "manager", "СЃС‚Р°СЂС€РёР№", "adm", "admin"])

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
            logger.info(f"вњ… РЎРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°РЅРѕ {len(iiko_employees)} РїСЂРѕС„РёР»РµР№ СЃРѕС‚СЂСѓРґРЅРёРєРѕРІ РёР· iiko Resto")
        except Exception as e:
            logger.error(f"РћС€РёР±РєР° СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё РїСЂРѕС„РёР»РµР№: {e}")
            session.rollback()

        # --- РЁР°Рі 1.5: Р”РѕРїРѕР»РЅРµРЅРёРµ РґР°РЅРЅС‹РјРё РёР· iiko Cloud (РћРўРљР›Р®Р§Р•РќРћ РїРѕ С‚СЂРµР±РѕРІР°РЅРёСЋ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ - СЃС‚СЂРѕРіРѕ Server API) ---
        # try:
        #     logger.info("Р—Р°РїСЂРѕСЃ РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹С… РґР°РЅРЅС‹С… РёР· iiko Cloud...")
        #     cloud_employees = await iiko_service.get_employees(api_login=settings_db.api_login, organization_id=settings_db.organization_id)
        #     updated_cloud_c = 0
        #     for c_emp in cloud_employees:
        #         emp_iiko_id = c_emp.get("id")
        #         if not emp_iiko_id: continue
        #         
        #         existing = session.exec(select(Employee).where(Employee.iiko_id == emp_iiko_id)).first()
        #         # Р•СЃР»Рё СЃРѕС‚СЂСѓРґРЅРёРєР° РЅРµС‚ РёР· Resto, РЅРѕ РѕРЅ РµСЃС‚СЊ РІ Cloud (РЅР°РїСЂРёРјРµСЂ, РІРЅРµС€РЅРёР№ РєСѓСЂСЊРµСЂ)
        #         if not existing:
        #             role = ""
        #             if c_emp.get("isCourier"): role = "РљСѓСЂСЊРµСЂ (Cloud)"
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
        #             # Р”РѕРїРѕР»РЅСЏРµРј РґР°РЅРЅС‹РјРё, РµСЃР»Рё РёС… РЅРµС‚
        #             if c_emp.get("isCourier") and not existing.is_courier:
        #                 existing.is_courier = True
        #                 session.add(existing)
        #                 updated_cloud_c += 1
        #     session.commit()
        #     logger.info(f"вњ… Р”РѕРїРѕР»РЅРµРЅРѕ {updated_cloud_c} РїСЂРѕС„РёР»РµР№ РёР· iiko Cloud")
        # except Exception as e:
        #     logger.error(f"РћС€РёР±РєР° РґРѕРїРѕР»РЅРµРЅРёСЏ РґР°РЅРЅС‹С… РёР· Cloud: {e}")
        #     session.rollback()

        # --- РЁР°Рі 2: РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РёСЃС‚РѕСЂРёС‡РµСЃРєРёС… СЃРјРµРЅ С‡РµСЂРµР· Attendance API ---
        try:
            logger.info(f"Р—Р°РїСЂРѕСЃ СЏРІРѕРє (СЃРјРµРЅ) С‡РµСЂРµР· Attendance API ({date_from.date()} - {now_local.date()})...")
            attendance_records = await iiko_service.get_resto_attendance(
                resto_url=r_url, resto_login=r_login, resto_password=r_password,
                date_from=date_from, date_to=now_local,
                log_error=False
            )

            def _parse_to_utc(s):
                if not s: return None
                try:
                    # С„РѕСЂРјР°С‚ ISO 8601 СЃ С‚Р°Р№РјР·РѕРЅРѕР№ (РЅР°РїСЂРёРјРµСЂ 2026-04-11T10:17:00+05:00)
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
                    # logger.debug(f"Attendance: СЃРѕС‚СЂСѓРґРЅРёРє СЃ ID '{emp_iiko_id}' РЅРµ РЅР°Р№РґРµРЅ РІ Р‘Р”")
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

                # РћРіСЂР°РЅРёС‡РёРІР°РµРј Р°РЅРѕРјР°Р»СЊРЅРѕ РґР»РёРЅРЅС‹Рµ СЃРјРµРЅС‹ (РјР°РєСЃ 24 С‡Р°СЃР°)
                work_hours = min(work_hours, 24.0)

                # РЈРЅРёРєР°Р»СЊРЅС‹Р№ РєР»СЋС‡
                shift_iiko_id = row.get("id")
                if not shift_iiko_id:
                     shift_iiko_id = f"att_{employee.id}_{date_open.strftime('%Y%m%d%H%M')}"

                # РџРѕРёСЃРє РІС‹СЂСѓС‡РєРё РїСЂРё Р·Р°РєСЂС‹С‚РёРё (РёР· Р·Р°РіСЂСѓР¶РµРЅРЅС‹С… РѕС‚С‡РµС‚РѕРІ OLAP)
                revenue_at_close = 0.0
                if date_close:
                    biz_date_str = date_open.astimezone(tz).strftime("%Y-%m-%d")
                    # Р‘РµСЂРµРј РІС‹СЂСѓС‡РєСѓ Р·Р° Р±РёР·РЅРµСЃ-РґРµРЅСЊ РѕС‚РєСЂС‹С‚РёСЏ СЃРјРµРЅС‹
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
                    # РћР±РЅРѕРІР»СЏРµРј РІС‹СЂСѓС‡РєСѓ С‚РѕР»СЊРєРѕ РµСЃР»Рё РѕРЅР° РµС‰Рµ РЅРµ Р±С‹Р»Р° СѓСЃС‚Р°РЅРѕРІР»РµРЅР°
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
            logger.info(f"вњ… Attendance СЃРјРµРЅС‹: СЃРѕР·РґР°РЅРѕ {created_c}, РѕР±РЅРѕРІР»РµРЅРѕ {updated_c} РёР· {len(attendance_records)} СЃС‚СЂРѕРє")
        except Exception as e:
            logger.error(f"РћС€РёР±РєР° СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё Attendance СЃРјРµРЅ: {e}", exc_info=True)
            session.rollback()

        # --- РЁР°Рі 3 (РЈРґР°Р»РµРЅ): РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ С‡РµСЂРµР· personalSessions Р·Р°РјРµРЅРµРЅР° РЅР° Attendance ---
        # Р›РёС‡РЅС‹Рµ СЃРјРµРЅС‹ С‚РµРїРµСЂСЊ РїРѕР»РЅРѕСЃС‚СЊСЋ РѕР±СЂР°Р±Р°С‚С‹РІР°СЋС‚СЃСЏ РІ РЁР°РіРµ 2 С‡РµСЂРµР· Attendance API, 
        # РєРѕС‚РѕСЂС‹Р№ РІРѕР·РІСЂР°С‰Р°РµС‚ Рё РѕС‚РєСЂС‹С‚С‹Рµ, Рё Р·Р°РєСЂС‹С‚С‹Рµ СЃРјРµРЅС‹ Р±РµР· РѕС€РёР±РѕРє 404.
        pass

    async def get_employee_stats(self, session: Session, employee_id: int, mode: str = "calendar") -> Dict[str, Any]:
        """
        РџРѕР»СѓС‡РµРЅРёРµ СЃС‚Р°С‚РёСЃС‚РёРєРё СЃРѕС‚СЂСѓРґРЅРёРєР° Р·Р° РїРµСЂРёРѕРґ.
        mode: 'calendar' (С‚РµРєСѓС‰Р°СЏ РЅРµРґРµР»СЏ) РёР»Рё 'sliding' (РїРѕСЃР»РµРґРЅРёРµ 7 РґРЅРµР№)
        """
        tz = self._get_tz(session)
        now_local = datetime.now(tz)
        
        if mode == "calendar":
            # РЎ РїРѕРЅРµРґРµР»СЊРЅРёРєР° С‚РµРєСѓС‰РµР№ РЅРµРґРµР»Рё
            start_date = (now_local - timedelta(days=now_local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now_local
        else:
            # РџРѕСЃР»РµРґРЅРёРµ 7 РґРЅРµР№
            start_date = (now_local - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now_local
            
        # Р—Р°РіСЂСѓР¶Р°РµРј СЃРјРµРЅС‹ РёР· Р‘Р”
        shifts = session.exec(
            select(Shift)
            .where(Shift.employee_id == employee_id)
            .where(Shift.date_open >= start_date.astimezone(timezone.utc))
            .order_by(Shift.date_open.desc())
        ).all()
        
        total_hours = sum(s.work_hours for s in shifts if s.work_hours)
        total_revenue = sum(float(s.revenue_at_close or 0) for s in shifts)
        
        # Р“СЂСѓРїРїРёСЂРѕРІРєР° РїРѕ РґРЅСЏРј
        daily_stats = {}
        for s in shifts:
            # РџСЂРёРІРѕРґРёРј РІСЂРµРјСЏ РѕС‚РєСЂС‹С‚РёСЏ Рє Р»РѕРєР°Р»СЊРЅРѕРјСѓ РґР»СЏ РіСЂСѓРїРїРёСЂРѕРІРєРё РїРѕ РґР°С‚Рµ
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
            
            # Р¤РѕСЂРјРёСЂСѓРµРј РѕР±СЉРµРєС‚ СЃРјРµРЅС‹ РґР»СЏ С„СЂРѕРЅС‚РµРЅРґР°
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
        РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РґРµС‚Р°Р»СЊРЅС‹С… РґРѕСЃС‚Р°РІРѕРє РєСѓСЂСЊРµСЂРѕРІ РёР· iiko Resto OLAP.
        Р—Р°РїРѕР»РЅСЏРµС‚ С‚Р°Р±Р»РёС†Сѓ courier_orders: Р·РѕРЅС‹, СЃСѓРјРјС‹, РІСЂРµРјРµРЅРЅС‹Рµ РјРµС‚РєРё, Р·Р°РґРµСЂР¶РєРё.
        """
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db or not settings_db.resto_url:
            logger.warning("Resto РЅРµ РЅР°СЃС‚СЂРѕРµРЅ вЂ” СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РґРѕСЃС‚Р°РІРѕРє РїСЂРѕРїСѓС‰РµРЅР°")
            return

        tz = self._get_tz(session)
        now_local = datetime.now(tz)
        
        if not date_from:
            date_from = now_local - timedelta(days=days)
        if not date_to:
            date_to = now_local

        logger.info(f"РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РґРѕСЃС‚Р°РІРѕРє РєСѓСЂСЊРµСЂРѕРІ РёР· Resto OLAP ({date_from} вЂ” {date_to})...")

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
            logger.error(f"РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ РґРѕСЃС‚Р°РІРѕРє РёР· Resto OLAP: {e}")
            return

        # РљСЌС€ РєСѓСЂСЊРµСЂРѕРІ РїРѕ РёРјРµРЅРё (РЅРёР¶РЅРёР№ СЂРµРіРёСЃС‚СЂ)
        all_employees = session.exec(select(Employee)).all()
        courier_by_name: Dict[str, Employee] = {}
        for emp in all_employees:
            # РЈС‡РёС‚С‹РІР°РµРј С„Р»Р°Рі is_courier Рё СЂР°Р·Р»РёС‡РЅС‹Рµ РЅР°РїРёСЃР°РЅРёСЏ СЂРѕР»РµР№
            is_c = emp.is_courier or any(k in (emp.role or "").lower() for k in ["РєСѓСЂСЊРµСЂ", "courier", "cur"])
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
                    return {w for w in words if len(w) > 2 and w not in ["РєСѓСЂСЊРµСЂ", "courier", "cur"]}
                
                target_words = _get_meaningful_words(courier_name_raw)
                for key, emp in courier_by_name.items():
                    emp_words = _get_meaningful_words(emp.name)
                    if target_words and emp_words and (target_words & emp_words):
                        courier_emp = emp
                        break

            if not courier_emp:
                from app.models.order import Order
                db_order = session.exec(
                    select(Order).where(Order.external_number == order_num)
                ).first()
                if db_order and db_order.courier_name and db_order.courier_name != "РќРµ РЅР°Р·РЅР°С‡РµРЅ":
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

            # РћР±РѕРіР°С‰РµРЅРёРµ Р°РґСЂРµСЃР° РёР· РѕСЃРЅРѕРІРЅРѕР№ С‚Р°Р±Р»РёС†С‹ Р·Р°РєР°Р·РѕРІ (Cloud API РёРјРµРµС‚ Р±РѕР»РµРµ РґРµС‚Р°Р»СЊРЅС‹Р№ JSON)
            addr_parts = d.get("address") or {}
            db_order = session.exec(select(Order).where(Order.external_number == order_num)).first()
            if db_order and db_order.address_parts:
                # Р‘РµСЂРµРј РґРµС‚Р°Р»СЊРЅС‹Р№ JSON РёР· Cloud API Р·Р°РєР°Р·Р°
                addr_parts = db_order.address_parts
            
            city_name = settings_db.city_name if settings_db else "РўСЋРјРµРЅСЊ"
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
            logger.info(f"РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РґРѕСЃС‚Р°РІРѕРє Р·Р°РІРµСЂС€РµРЅР°: {created_count} РЅРѕРІС‹С…, {updated_count} РѕР±РЅРѕРІР»РµРЅРѕ")
        except Exception as e:
            session.rollback()
            logger.error(f"РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ РґРѕСЃС‚Р°РІРѕРє: {e}")

    async def sync_courier_deliveries_bg(self, date_from: datetime, date_to: datetime):
        """Р’СЃРїРѕРјРѕРіР°С‚РµР»СЊРЅС‹Р№ РјРµС‚РѕРґ РґР»СЏ С„РѕРЅРѕРІРѕРіРѕ Р·Р°РїСѓСЃРєР° СЃ СЃРѕР±СЃС‚РІРµРЅРЅРѕР№ СЃРµСЃСЃРёРµР№"""
        from app.core.database import SessionLocal
        with SessionLocal() as session:
            try:
                await self.sync_courier_deliveries(session, date_from=date_from, date_to=date_to)
            except Exception as e:
                logger.error(f"Error in courier deliveries background sync: {e}")
                session.rollback()


    async def sync_zones_from_external_map(self, session: Session, url: Optional[str] = None) -> Dict[str, Any]:
        """
        РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РіРµРѕРјРµС‚СЂРёРё Р·РѕРЅ РґРѕСЃС‚Р°РІРєРё РїРѕ РІРЅРµС€РЅРµР№ СЃСЃС‹Р»РєРµ (Google Maps KML)
        """
        settings = session.exec(select(IikoSettings)).first()
        
        # Р•СЃР»Рё URL РїРµСЂРµРґР°РЅ СЏРІРЅРѕ, СЃРѕС…СЂР°РЅСЏРµРј РµРіРѕ РІ РЅР°СЃС‚СЂРѕР№РєРё
        if url:
            if settings:
                settings.delivery_zones_map_url = url
                session.add(settings)
                session.commit()
            map_url = url
        else:
            map_url = settings.delivery_zones_map_url if settings else None

        if not map_url:
            return {"success": False, "error": "РЎСЃС‹Р»РєР° РЅР° РєР°СЂС‚Сѓ РЅРµ Р·Р°РґР°РЅР° РІ РЅР°СЃС‚СЂРѕР№РєР°С…"}
        
        logger.info(f"РќР°С‡Р°Р»Рѕ РёРјРїРѕСЂС‚Р° РіРµРѕРјРµС‚СЂРёРё Р·РѕРЅ РёР·: {map_url}")
        
        # 1. Р—Р°РіСЂСѓР¶Р°РµРј Рё РїР°СЂСЃРёРј KML
        try:
            from .iiko_service import iiko_service
            kml_zones = await iiko_service.fetch_and_parse_kml(settings.delivery_zones_map_url)
            if not kml_zones:
                return {"success": False, "error": "РќРµ СѓРґР°Р»РѕСЃСЊ РїРѕР»СѓС‡РёС‚СЊ Р·РѕРЅС‹ РёР· СѓРєР°Р·Р°РЅРЅРѕР№ СЃСЃС‹Р»РєРё. РџСЂРѕРІРµСЂСЊС‚Рµ РґРѕСЃС‚СѓРї Рє РєР°СЂС‚Рµ."}
        except Exception as e:
            return {"success": False, "error": f"РћС€РёР±РєР° РїСЂРё Р·Р°РіСЂСѓР·РєРµ РєР°СЂС‚С‹: {str(e)}"}
            
        # 2. РЎРѕРїРѕСЃС‚Р°РІР»СЏРµРј Рё РѕР±РЅРѕРІР»СЏРµРј
        updated_count = 0
        import json
        from app.models.company import DeliveryZone
        
        all_zones = session.exec(select(DeliveryZone)).all()
        
        for kz in kml_zones:
            name = kz["name"].strip()
            points = kz["points"]
            
            # РС‰РµРј Р·РѕРЅСѓ РІ Р‘Р” РїРѕ РёРјРµРЅРё (СЂРµРіРёСЃС‚СЂРѕРЅРµР·Р°РІРёСЃРёРјРѕ)
            matched_zone = next((z for z in all_zones if (z.name or "").lower() == (name or "").lower()), None)
            
            if matched_zone:
                # РЎРѕС…СЂР°РЅСЏРµРј РєР°Рє JSON СЃС‚СЂРѕРєСѓ (СЃРѕРіР»Р°СЃРЅРѕ РјРѕРґРµР»Рё)
                matched_zone.polygon_coordinates = json.dumps(points)
                matched_zone.updated_at = datetime.now(timezone.utc)
                session.add(matched_zone)
                updated_count += 1
                logger.info(f"РћР±РЅРѕРІР»РµРЅР° РіРµРѕРјРµС‚СЂРёСЏ РґР»СЏ Р·РѕРЅС‹: {name}")
            else:
                logger.warning(f"Р—РѕРЅР° РёР· KML '{name}' РЅРµ РЅР°Р№РґРµРЅР° РІ Р±Р°Р·Рµ РґР°РЅРЅС‹С… iiko")
                
        try:
            session.commit()
            # РћС‡РёС‰Р°РµРј РєСЌС€ РїРѕСЃР»Рµ РѕР±РЅРѕРІР»РµРЅРёСЏ Р·РѕРЅ (РµСЃР»Рё РёСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ Redis РёР»Рё Р»РѕРєР°Р»СЊРЅС‹Р№ РєСЌС€)
            try:
                from app.core.redis import redis_client
                await redis_client.delete("delivery_zones_all")
                logger.info("РљСЌС€ Р·РѕРЅ РґРѕСЃС‚Р°РІРєРё РѕС‡РёС‰РµРЅ")
            except Exception:
                pass

            return {
                "success": True, 
                "updated_count": updated_count, 
                "total_from_map": len(kml_zones),
                "message": f"РћР±РЅРѕРІР»РµРЅРѕ Р·РѕРЅ: {updated_count} РёР· {len(kml_zones)}"
            }
        except Exception as e:
            session.rollback()
            logger.error(f"РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ РіРµРѕРјРµС‚СЂРёРё Р·РѕРЅ: {e}")
            return {"success": False, "error": f"РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ РІ Р‘Р”: {str(e)}"}


    async def sync_zones_from_kml_file(self, session: Session, kml_content: str) -> Dict[str, Any]:
        """
        РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РіРµРѕРјРµС‚СЂРёРё Р·РѕРЅ РґРѕСЃС‚Р°РІРєРё РёР· Р·Р°РіСЂСѓР¶РµРЅРЅРѕРіРѕ KML С„Р°Р№Р»Р°
        """
        logger.info("РќР°С‡Р°Р»Рѕ РёРјРїРѕСЂС‚Р° РіРµРѕРјРµС‚СЂРёРё Р·РѕРЅ РёР· Р·Р°РіСЂСѓР¶РµРЅРЅРѕРіРѕ С„Р°Р№Р»Р°")
        
        # 1. РџР°СЂСЃРёРј KML
        try:
            from .iiko_service import iiko_service
            kml_zones = iiko_service.parse_kml_content(kml_content)
            if not kml_zones:
                return {"success": False, "error": "Р’ С„Р°Р№Р»Рµ РЅРµ РЅР°Р№РґРµРЅРѕ РїРѕР»РёРіРѕРЅРѕРІ Р·РѕРЅ РґРѕСЃС‚Р°РІРєРё."}
        except Exception as e:
            return {"success": False, "error": f"РћС€РёР±РєР° РїСЂРё РїР°СЂСЃРёРЅРіРµ С„Р°Р№Р»Р°: {str(e)}"}
            
        # 2. РЎРѕРїРѕСЃС‚Р°РІР»СЏРµРј Рё РѕР±РЅРѕРІР»СЏРµРј
        updated_count = 0
        import json
        from app.models.company import DeliveryZone
        
        all_zones = session.exec(select(DeliveryZone)).all()
        
        for kz in kml_zones:
            name = kz["name"].strip()
            points = kz["points"]
            description = kz.get("description", "")
            extended_data = kz.get("extended_data", {})
            
            # РС‰РµРј Р·РѕРЅСѓ РІ Р‘Р” РїРѕ РёРјРµРЅРё (СЂРµРіРёСЃС‚СЂРѕРЅРµР·Р°РІРёСЃРёРјРѕ)
            matched_zone = session.exec(select(DeliveryZone).where(func.lower(DeliveryZone.name) == (name or "").lower())).first()
            
            if matched_zone:
                matched_zone.polygon_coordinates = json.dumps(points)
                matched_zone.description = description
                matched_zone.additional_info = extended_data
                matched_zone.is_manual_override = True  # РџСЂРёРѕСЂРёС‚РµС‚ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ
                matched_zone.updated_at = datetime.now(timezone.utc)
                session.add(matched_zone)
                updated_count += 1
                logger.info(f"РћР±РЅРѕРІР»РµРЅР° РіРµРѕРјРµС‚СЂРёСЏ Рё РјРµС‚Р°РґР°РЅРЅС‹Рµ РґР»СЏ Р·РѕРЅС‹ (РёР· KML): {name}")
            else:
                # РЎРѕР·РґР°РµРј РЅРѕРІСѓСЋ Р·РѕРЅСѓ РµСЃР»Рё РµС‘ РЅРµС‚
                logger.info(f"РЎРѕР·РґР°РЅРёРµ РЅРѕРІРѕР№ РїСЂРёРѕСЂРёС‚РµС‚РЅРѕР№ Р·РѕРЅС‹ РёР· KML С„Р°Р№Р»Р°: {name}")
                from app.models.company import Branch
                branch = session.exec(select(Branch)).first()
                if branch:
                    new_zone = DeliveryZone(
                        name=name,
                        branch_id=branch.id,
                        polygon_coordinates=json.dumps(points),
                        description=description,
                        additional_info=extended_data,
                        is_manual_override=True,  # РџСЂРёРѕСЂРёС‚РµС‚ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ
                        is_active=True
                    )
                    session.add(new_zone)
                    updated_count += 1
                else:
                    logger.warning(f"РќРµ СѓРґР°Р»РѕСЃСЊ СЃРѕР·РґР°С‚СЊ Р·РѕРЅСѓ {name}: С„РёР»РёР°Р» РЅРµ РЅР°Р№РґРµРЅ")
                
        try:
            session.commit()
            # РћС‡РёС‰Р°РµРј РєСЌС€
            try:
                from app.core.redis import redis_client
                await redis_client.delete("delivery_zones_all")
            except Exception:
                pass

            return {
                "success": True, 
                "updated_count": updated_count, 
                "total_from_file": len(kml_zones),
                "message": f"РћР±РЅРѕРІР»РµРЅРѕ Р·РѕРЅ РёР· С„Р°Р№Р»Р°: {updated_count} РёР· {len(kml_zones)}"
            }
        except Exception as e:
            session.rollback()
            logger.error(f"РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ РіРµРѕРјРµС‚СЂРёРё Р·РѕРЅ РёР· С„Р°Р№Р»Р°: {e}")
            return {"success": False, "error": f"РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ РІ Р‘Р”: {str(e)}"}


iiko_sync_service = IikoSyncService()

