"""
Сервис-оркестратор для синхронизации данных с iiko
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlmodel import Session, select
from sqlalchemy.orm.attributes import flag_modified
from app.models.category import Category
from app.models.product import Product, ProductSize, ProductModifierGroup, ProductModifier
from app.models.sync_log import SyncLog
from app.models.order import Order, OrderItem, OrderStatus
from app.models.employee import Employee, Shift, Schedule, CourierOrder
from app.models.company import Branch, Company, DeliveryZone
from app.models.customer import Customer
from app.models.vk_user import VkUser
from app.models.vk_activity import VkActivity
from app.models.vk_settings import VkSettings
from app.models.iiko_settings import IikoSettings
from app.services.vk_service import send_vk_message
from app.services.iiko_service import iiko_service
from app.services.spam_service import spam_service
from app.models.payment_type import PaymentType

logger = logging.getLogger(__name__)


class IikoSyncService:

    async def sync_menu(self, session: Session) -> Dict[str, Any]:
        """Умная синхронизация меню. Использует External Menu API v2 если задан ID меню"""
        log = SyncLog(sync_type="menu", status="running")
        session.add(log)
        session.commit()
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login if settings_db else None
        org_id = settings_db.organization_id if settings_db else None
        ext_menu_id = settings_db.external_menu_id if settings_db else None
        price_cat_id = settings_db.price_category_id if settings_db else None
        try:
            if ext_menu_id:
                logger.info(f"Syncing via External Menu API (ID: {ext_menu_id}, Price Category: {price_cat_id})")
                menu_data = await iiko_service.get_external_menu_by_id(
                    ext_menu_id, 
                    price_category_id=price_cat_id,
                    api_login=api_login, 
                    organization_id=org_id
                )
                
                # Fetch nomenclature as price fallback
                logger.info("Fetching nomenclature as price fallback for v2 sync")
                nomenclature = await iiko_service.get_nomenclature(api_login=api_login, organization_id=org_id)
                
                res = await self._sync_from_external_menu(session, menu_data, log, nomenclature=nomenclature)
            else:
                logger.info("Syncing via Legacy Nomenclature API")
                nomenclature = await iiko_service.get_nomenclature(api_login=api_login, organization_id=org_id)
                res = await self._sync_from_nomenclature(session, nomenclature, log)
            session.commit()
            log.status = "success"
            log.categories_count = res.get("categories_synced", 0)
            log.products_count = res.get("products_synced", 0)
            log.details = f"Synced {log.categories_count} categories, {log.products_count} products"
            session.commit()
            return res
        except Exception as e:
            logger.error(f"Menu sync failed: {e}")
            log.status = "error"
            log.details = str(e)
            session.commit()
            raise

    async def _sync_from_external_menu(self, session: Session, menu_data: Dict[str, Any], log: SyncLog, nomenclature: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        categories_synced = 0
        products_synced = 0
        
        # Build nomenclature price map for fallback
        nom_prices = {}
        if nomenclature and "products" in nomenclature:
            for p in nomenclature["products"]:
                p_id = p.get("id")
                major_price = 0
                sz_prices = {}
                if p.get("sizePrices"):
                    major_price = p["sizePrices"][0].get("price", {}).get("currentPrice", 0)
                    for sp in p["sizePrices"]:
                        sz_prices[sp.get("sizeId") or "default"] = sp.get("price", {}).get("currentPrice", 0)
                nom_prices[p_id] = {"base": major_price, "sizes": sz_prices}

        item_categories = menu_data.get("itemCategories", [])
        for iiko_cat in item_categories:
            cat_iiko_id = iiko_cat.get("id")
            if not cat_iiko_id: continue
            category = session.exec(select(Category).where(Category.iiko_id == cat_iiko_id)).first()
            if not category:
                category = Category(name=iiko_cat.get("name", "Без названия"), iiko_id=cat_iiko_id, is_active=True)
                session.add(category)
            else:
                category.name = iiko_cat.get("name", category.name)
                category.is_active = True
                category.updated_at = datetime.utcnow()
            session.flush()
            categories_synced += 1
            for iiko_item in iiko_cat.get("items", []):
                item_iiko_id = iiko_item.get("itemId")
                if not item_iiko_id: continue

                size_prices = iiko_item.get("sizePrices", [])
                base_price = 0
                if size_prices:
                    default_size = next((sp for sp in size_prices if sp.get("isDefault")), size_prices[0])
                    base_price = default_size.get("price", {}).get("currentPrice", 0)

                # Hybrid price fallback: if v2 price is 0, use v1 price
                if base_price == 0 and item_iiko_id in nom_prices:
                    base_price = nom_prices[item_iiko_id]["base"]
                    logger.debug(f"Hybrid: using v1 base price {base_price} for {iiko_item.get('name')}")

                # КБЖУ — из nutritionPerHundredGrams
                nutrition = iiko_item.get("nutritionPerHundredGrams", {})
                kbju = {
                    "calories": nutrition.get("caloricity") or nutrition.get("calories"),
                    "proteins": nutrition.get("proteins"),
                    "fats": nutrition.get("fats"),
                    "carbohydrates": nutrition.get("carbohydrates")
                }

                product = session.exec(select(Product).where(Product.iiko_id == item_iiko_id)).first()
                if not product:
                    product = Product(
                        name=iiko_item.get("name", "Без названия"),
                        description=iiko_item.get("description"),
                        price=base_price,
                        category_id=category.id,
                        iiko_id=item_iiko_id,
                        article=iiko_item.get("sku") or iiko_item.get("code"),
                        is_available=True
                    )
                    session.add(product)
                else:
                    product.name = iiko_item.get("name", product.name)
                    product.description = iiko_item.get("description")
                    product.price = base_price
                    product.category_id = category.id
                    product.article = iiko_item.get("sku") or iiko_item.get("code")
                    product.is_available = True
                    product.updated_at = datetime.utcnow()

                # Заполняем новые поля
                product.iiko_image_id = iiko_item.get("imageId")
                product.weight_grams = iiko_item.get("weight")
                product.volume_ml = iiko_item.get("volume")
                product.calories = kbju["calories"]
                product.proteins = kbju["proteins"]
                product.fats = kbju["fats"]
                product.carbohydrates = kbju["carbohydrates"]

                img = iiko_item.get("buttonImageCroppedUrl") or (iiko_item.get("imageLinks", [None])[0] if iiko_item.get("imageLinks") else None)
                if not img and product.iiko_image_id:
                    img = f"https://api-ru.iiko.services/api/1/menu/download-image?imageId={product.iiko_image_id}"
                if img:
                    product.image_url = img
                session.flush()
                # Sizes
                for sz in session.exec(select(ProductSize).where(ProductSize.product_id == product.id)).all(): session.delete(sz)
                for sp in size_prices:
                    sp_price = sp.get("price", {}).get("currentPrice", 0)
                    sz_id = sp.get("sizeId") or "default"
                    
                    if sp_price == 0 and item_iiko_id in nom_prices:
                        # try to find exact size price, else use its base
                        sp_price = nom_prices[item_iiko_id]["sizes"].get(sz_id, nom_prices[item_iiko_id]["base"])
                        logger.debug(f"Hybrid: using v1 size price {sp_price} for {iiko_item.get('name')} size {sz_id}")
                    
                    session.add(ProductSize(product_id=product.id, iiko_id=sz_id,
                                          name=sp.get("name") or "Стандарт", price=sp_price,
                                          is_default=sp.get("isDefault", False)))
                # Modifiers
                for mg_old in session.exec(select(ProductModifierGroup).where(ProductModifierGroup.product_id == product.id)).all(): session.delete(mg_old)
                for mg_data in iiko_item.get("modifierGroups", []):
                    mg = ProductModifierGroup(product_id=product.id, iiko_id=mg_data.get("modifierGroupId", ""),
                                            name=mg_data.get("name", "Группа модификаторов"),
                                            min_amount=mg_data.get("minQuantity", 0), max_amount=mg_data.get("maxQuantity", 1),
                                            is_required=mg_data.get("required", False))
                    session.add(mg)
                    session.flush()
                    for m_data in mg_data.get("modifiers", []):
                        session.add(ProductModifier(group_id=mg.id, iiko_id=m_data.get("modifierId", ""),
                                                  name=m_data.get("name", "Модификатор"), price=m_data.get("price", 0),
                                                  default_amount=m_data.get("defaultAmount", 0),
                                                  min_amount=m_data.get("minAmount", 0), max_amount=m_data.get("maxAmount", 1)))
                products_synced += 1
        return {"success": True, "categories_synced": categories_synced, "products_synced": products_synced}

    """Оркестратор синхронизации данных между iiko и локальной БД"""

    async def _sync_from_nomenclature(self, session: Session, nomenclature: Dict[str, Any], log: SyncLog) -> Dict[str, Any]:
        """
        Полная синхронизация меню из iiko

        Загружает номенклатуру (категории + товары) и обновляет локальную БД.
        Сопоставление по iiko_id.
        """
        log = SyncLog(sync_type="menu", status="running")
        session.add(log)
        session.commit()

        # Получаем настройки iiko из БД
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login if settings_db else None
        organization_id = settings_db.organization_id if settings_db else None

        try:
            nomenclature = await iiko_service.get_nomenclature(
                api_login=api_login,
                organization_id=organization_id
            )

            categories_synced = 0
            products_synced = 0

            # Синхронизация категорий (groups)
            if "groups" in nomenclature:
                for iiko_group in nomenclature["groups"]:
                    query = select(Category).where(
                        Category.iiko_id == iiko_group["id"]
                    )
                    category = session.exec(query).first()

                    if category:
                        category.name = iiko_group["name"]
                        category.updated_at = datetime.utcnow()
                    else:
                        category = Category(
                            name=iiko_group["name"],
                            iiko_id=iiko_group["id"],
                            is_active=not iiko_group.get("isDeleted", False)
                        )
                        session.add(category)

                    categories_synced += 1

            session.commit()

            # Parsing sizes from root to map size_id to size_name
            size_map = {}
            if "sizes" in nomenclature:
                for size in nomenclature["sizes"]:
                    size_map[size["id"]] = size

            # Синхронизация товаров (products)
            if "products" in nomenclature:
                for iiko_product in nomenclature["products"]:
                    query = select(Product).where(
                        Product.iiko_id == iiko_product["id"]
                    )
                    product = session.exec(query).first()

                    # Поиск категории
                    category_id = None
                    if iiko_product.get("parentGroup"):
                        cat_query = select(Category).where(
                            Category.iiko_id == iiko_product["parentGroup"]
                        )
                        cat = session.exec(cat_query).first()
                        if cat:
                            category_id = cat.id

                    # РР·РІР»РµС‡РµРЅРёРµ С†РµРЅС‹
                    price = 0
                    if iiko_product.get("sizePrices"):
                        price = (
                            iiko_product["sizePrices"][0]
                            .get("price", {})
                            .get("currentPrice", 0)
                        )

                    # РР·РІР»РµС‡РµРЅРёРµ Р°СЂС‚РёРєСѓР»Р°
                    article = iiko_product.get("code", "")

                    if product:
                        product.name = iiko_product["name"]
                        product.description = iiko_product.get("description")
                        product.price = price
                        product.category_id = category_id
                        product.article = article
                        product.is_available = not iiko_product.get(
                            "isDeleted", False
                        )
                        product.updated_at = datetime.utcnow()
                    else:
                        product = Product(
                            name=iiko_product["name"],
                            description=iiko_product.get("description"),
                            price=price,
                            category_id=category_id,
                            iiko_id=iiko_product["id"],
                            article=article,
                            is_available=not iiko_product.get(
                                "isDeleted", False
                            )
                        )
                        session.add(product)
                        
                    session.flush() # ensure product.id is available

                    # Sync Sizes
                    # Remove existing sizes
                    for existing_size in product.sizes:
                        session.delete(existing_size)
                    product.sizes = []
                    
                    if iiko_product.get("sizePrices"):
                        for sp in iiko_product["sizePrices"]:
                            size_id = sp.get("sizeId")
                            size_price = sp.get("price", {}).get("currentPrice", 0)
                            size_info = size_map.get(size_id, {})
                            size_name = size_info.get("name", "Стандарт")
                            is_default = size_info.get("isDefault", False)
                            
                            new_size = ProductSize(
                                product_id=product.id,
                                iiko_id=size_id or "default",
                                name=size_name,
                                price=size_price,
                                is_default=is_default
                            )
                            session.add(new_size)

                    # Sync Modifier Groups
                    for existing_mg in product.modifier_groups:
                        session.delete(existing_mg)
                    product.modifier_groups = []

                    if iiko_product.get("groupModifiers"):
                        for gm in iiko_product["groupModifiers"]:
                            mg = ProductModifierGroup(
                                product_id=product.id,
                                iiko_id=gm.get("modifierId", ""),
                                name="Группа модификаторов", # To be replaced by cross-referencing products if needed, but often iiko sends it as ID pointing to another product. For now use placeholder or fetch name if available.
                                min_amount=gm.get("minAmount", 0),
                                max_amount=gm.get("maxAmount", 1),
                                is_required=gm.get("required", False)
                            )
                            # Try to find group name from nomenclature products if modifierId points to a group
                            group_product = next((p for p in nomenclature["products"] if p["id"] == gm.get("modifierId")), None)
                            if group_product:
                                mg.name = group_product.get("name", "Группа модификаторов")
                                
                            session.add(mg)
                            session.flush() # get mg.id
                            
                            for child in gm.get("childModifiers", []):
                                child_product = next((p for p in nomenclature["products"] if p["id"] == child.get("modifierId")), None)
                                child_name = child_product.get("name", "Модификатор") if child_product else "Модификатор"
                                child_price = 0
                                if child_product and child_product.get("sizePrices"):
                                    child_price = child_product["sizePrices"][0].get("price", {}).get("currentPrice", 0)
                                    
                                mod = ProductModifier(
                                    group_id=mg.id,
                                    iiko_id=child.get("modifierId", ""),
                                    name=child_name,
                                    price=child_price,
                                    default_amount=child.get("defaultAmount", 0),
                                    min_amount=child.get("minAmount", 0),
                                    max_amount=child.get("maxAmount", 1)
                                )
                                session.add(mod)

                    products_synced += 1

            session.commit()

            # Обновляем лог
            log.status = "success"
            log.categories_count = categories_synced
            log.products_count = products_synced
            log.details = f"Synced {categories_synced} categories, {products_synced} products"
            session.commit()

            return {
                "success": True,
                "categories_synced": categories_synced,
                "products_synced": products_synced,
                "message": log.details
            }

        except Exception as e:
            logger.error(f"Menu sync failed: {e}")
            log.status = "error"
            log.details = str(e)
            session.commit()
            raise

    async def sync_prices(self, session: Session) -> Dict[str, Any]:
        """
        Синхронизация только цен из iiko (с поддержкой v1, v2 и fallback)
        """
        log = SyncLog(sync_type="prices", status="running")
        session.add(log)
        session.commit()

        # Получаем настройки iiko из БД
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login if settings_db else None
        org_id = settings_db.organization_id if settings_db else None
        ext_menu_id = settings_db.external_menu_id if settings_db else None
        price_cat_id = settings_db.price_category_id if settings_db else None

        try:
            updated = 0
            sync_source = "none"
            
            # Пробуем API v2 если задано меню
            if ext_menu_id:
                logger.info(f"Syncing prices via External Menu API v2 (ID: {ext_menu_id}, PriceCat: {price_cat_id})")
                try:
                    menu_data = await iiko_service.get_external_menu_by_id(
                        ext_menu_id, 
                        price_category_id=price_cat_id,
                        api_login=api_login, 
                        organization_id=org_id
                    )
                    
                    # Fetch nomenclature as hybrid fallback
                    logger.info("Fetching nomenclature as hybrid price fallback for v2 price sync")
                    nomenclature = await iiko_service.get_nomenclature(api_login=api_login, organization_id=org_id)
                    
                    updated = await self._sync_prices_from_v2(session, menu_data, nomenclature=nomenclature)
                    sync_source = "v2"
                except Exception as e:
                    logger.warning(f"Failed to sync via API v2, falling back to v1: {e}")
                    sync_source = "v2_failed_fallback"

            # Если v2 не использовался или не обновил ничего, или мы в режиме fallback
            if sync_source in ["none", "v2_failed_fallback"] or (sync_source == "v2" and updated == 0):
                logger.info("Syncing prices via Legacy Nomenclature API (v1)")
                nomenclature = await iiko_service.get_nomenclature(api_login=api_login, organization_id=org_id)
                updated = await self._sync_prices_from_v1(session, nomenclature or {})
                sync_source = "v1" if sync_source == "none" else f"{sync_source}_v1"

            session.commit()
            log.status = "success"
            log.products_count = updated
            log.details = f"Updated prices for {updated} products using {sync_source}"
            session.commit()

            return {
                "success": True,
                "products_updated": updated,
                "source": sync_source,
                "message": log.details
            }

        except Exception as e:
            logger.error(f"Price sync failed: {e}")
            log.status = "error"
            log.details = str(e)
            session.commit()
            raise

    async def _sync_prices_from_v1(self, session: Session, nomenclature: Dict[str, Any]) -> int:
        """Вспомогательный метод синхронизации цен из номенклатуры (v1)"""
        updated = 0
        if "products" in nomenclature:
            for iiko_product in nomenclature["products"]:
                product = session.exec(select(Product).where(Product.iiko_id == iiko_product["id"])).first()
                if product:
                    price = 0
                    if iiko_product.get("sizePrices"):
                        price = iiko_product["sizePrices"][0].get("price", {}).get("currentPrice", 0)
                    
                    if product.price != price:
                        product.price = price
                        product.updated_at = datetime.utcnow()
                        updated += 1
                    
                    # Также обновляем цены размеров
                    for iiko_sp in iiko_product.get("sizePrices", []):
                        size_iiko_id = iiko_sp.get("sizeId") or "default"
                        size_price = iiko_sp.get("price", {}).get("currentPrice", 0)
                        
                        size_db = session.exec(select(ProductSize).where(
                            ProductSize.product_id == product.id,
                            ProductSize.iiko_id == size_iiko_id
                        )).first()
                        
                        if size_db and size_db.price != size_price:
                            size_db.price = size_price
                            size_db.updated_at = datetime.utcnow()
        return updated

    async def _sync_prices_from_v2(self, session: Session, menu_data: Dict[str, Any], nomenclature: Optional[Dict[str, Any]] = None) -> int:
        """Вспомогательный метод синхронизации цен из внешнего меню (v2) с гибридным фоллбеком на v1"""
        updated = 0
        
        # Build nomenclature price map for fallback
        nom_prices = {}
        if nomenclature and "products" in nomenclature:
            for p in nomenclature["products"]:
                p_id = p.get("id")
                major_price = 0
                sz_prices = {}
                if p.get("sizePrices"):
                    major_price = p["sizePrices"][0].get("price", {}).get("currentPrice", 0)
                    for sp in p["sizePrices"]:
                        sz_prices[sp.get("sizeId") or "default"] = sp.get("price", {}).get("currentPrice", 0)
                nom_prices[p_id] = {"base": major_price, "sizes": sz_prices}

        for iiko_cat in menu_data.get("itemCategories", []):
            for iiko_item in iiko_cat.get("items", []):
                item_iiko_id = iiko_item.get("itemId")
                if not item_iiko_id: continue
                
                product = session.exec(select(Product).where(Product.iiko_id == item_iiko_id)).first()
                if product:
                    size_prices = iiko_item.get("sizePrices", [])
                    if size_prices:
                        # Основная цена товара — из дефолтного размера
                        default_size = next((sp for sp in size_prices if sp.get("isDefault")), size_prices[0])
                        new_base_price = default_size.get("price", {}).get("currentPrice", 0)
                        
                        # Hybrid fallback
                        if new_base_price == 0 and item_iiko_id in nom_prices:
                            new_base_price = nom_prices[item_iiko_id]["base"]
                            logger.debug(f"Hybrid Price Sync: using v1 base price {new_base_price} for {product.name}")

                        if product.price != new_base_price:
                            product.price = new_base_price
                            product.updated_at = datetime.utcnow()
                            updated += 1
                        
                        # Детальное обновление каждого размера
                        for sp in size_prices:
                            sz_iiko_id = sp.get("sizeId") or "default"
                            sz_price = sp.get("price", {}).get("currentPrice", 0)
                            
                            # Hybrid fallback
                            if sz_price == 0 and item_iiko_id in nom_prices:
                                sz_price = nom_prices[item_iiko_id]["sizes"].get(sz_iiko_id, nom_prices[item_iiko_id]["base"])
                                logger.debug(f"Hybrid Price Sync: using v1 size price {sz_price} for {product.name} size {sz_iiko_id}")

                            size_db = session.exec(select(ProductSize).where(
                                ProductSize.product_id == product.id,
                                ProductSize.iiko_id == sz_iiko_id
                            )).first()
                            
                            if size_db and size_db.price != sz_price:
                                size_db.price = sz_price
                                size_db.updated_at = datetime.utcnow()
        return updated


    async def sync_stop_lists(self, session: Session) -> Dict[str, Any]:
        """
        Синхронизация стоп-листов

        Помечает позиции как недоступные (is_available=False)
        """
        log = SyncLog(sync_type="stop_lists", status="running")
        session.add(log)
        session.commit()

        # РџРѕР»СѓС‡Р°РµРј РЅР°СЃС‚СЂРѕР№РєРё iiko РёР· Р‘Р”
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login if settings_db else None
        organization_id = settings_db.organization_id if settings_db else None

        try:
            stop_items = await iiko_service.get_stop_lists(
                api_login=api_login,
                organization_id=organization_id
            )
            stopped_product_ids = {
                item["productId"] for item in stop_items
                if item.get("balance", 0) <= 0
            }

            # Сначала помечаем все как доступные
            all_products = session.exec(select(Product)).all()
            updated = 0
            for product in all_products:
                if product.iiko_id in stopped_product_ids:
                    if product.is_available:
                        product.is_available = False
                        updated += 1
                else:
                    if not product.is_available:
                        product.is_available = True
                        updated += 1

            session.commit()

            log.status = "success"
            log.products_count = updated
            log.details = f"Updated availability for {updated} products, {len(stopped_product_ids)} on stop-list"
            session.commit()

            return {
                "success": True,
                "products_updated": updated,
                "stopped_count": len(stopped_product_ids),
                "message": log.details
            }
        except Exception as e:
            logger.error(f"Stop-list sync failed: {e}")

    async def process_iiko_order(self, session: Session, iiko_order_data: Dict[str, Any], organization_id: str, iiko_card_data: Optional[Dict[str, Any]] = None):
        order_id_iiko = iiko_order_data.get("id")
        if not order_id_iiko: return
        if not hasattr(self, "_terminal_groups_cache"): self._terminal_groups_cache = {}
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login if settings_db else None
        if not self._terminal_groups_cache:
            try:
                tgs = await iiko_service.get_terminal_groups(api_login=api_login, organization_id=organization_id)
                for tg_entry in tgs:
                    for tg in tg_entry.get("items", []): self._terminal_groups_cache[tg["id"]] = tg["name"]
            except: pass
        order = session.exec(select(Order).where(Order.iiko_order_id == order_id_iiko)).first()
        o_data = iiko_order_data.get("order", iiko_order_data)
        raw_status = str(iiko_order_data.get("creationStatus") or o_data.get("status", "")).strip()
        
        # Маппинг статусов (регистронезависимый поиск ниже)
        status_map = {
            "new": OrderStatus.NEW, 
            "unconfirmed": OrderStatus.NEW, 
            "waitcooking": OrderStatus.CONFIRMED,
            "readyforcooking": OrderStatus.CONFIRMED, 
            "cookingstarted": OrderStatus.COOKING,
            "cookingcompleted": OrderStatus.READY, 
            "waiting": OrderStatus.READY, 
            "onway": OrderStatus.DELIVERING,
            "delivered": OrderStatus.DELIVERED, 
            "cancelled": OrderStatus.CANCELLED, 
            "error": OrderStatus.CANCELLED
        }
        
        mapped_status = status_map.get(raw_status.lower(), OrderStatus.CONFIRMED)
        print(f"DEBUG: [process_iiko_order] iiko_id={o_data.get('id')} raw_status='{raw_status}' -> mapped='{mapped_status}'")
        cancel_info = o_data.get("cancellationInfo")
        c_reason = cancel_info.get("message") if cancel_info else None
        sum_total = Decimal(str(o_data.get("sum", 0)))
        total_with_discount = Decimal(str(o_data.get("totalSum", sum_total)))
        phone = o_data.get("phone") or (o_data.get("customer") or {}).get("phone", "")
        customer = session.exec(select(Customer).where(Customer.phone == phone)).first() if phone else None
        source = o_data.get("sourceKey") or o_data.get("source")
        comment = o_data.get("comment")
        if not order:
            order = Order(iiko_order_id=order_id_iiko, status=mapped_status, total_amount=sum_total,
                         total_with_discount=total_with_discount, cancellation_reason=c_reason, 
                         customer_id=customer.id if customer else None, order_items_details=o_data.get("items", []),
                        comment=comment, source=source, branch_id=1)
            session.add(order)
        else:
            order.status = mapped_status
            order.total_amount = sum_total
            order.total_with_discount = total_with_discount
            order.cancellation_reason = c_reason or order.cancellation_reason
            order.comment = comment or order.comment
            order.order_items_details = o_data.get("items", [])
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(order, "order_items_details")
            session.add(order)
        session.flush()
        items_data = o_data.get("items", [])
        if isinstance(items_data, list):
            for ei in session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all(): session.delete(ei)
            for item in items_data:
                # Более надежный сбор модификаторов с ID
                mods = []
                for m in item.get("modifiers", []):
                    mods.append({
                        "iiko_id": m.get("productId") or m.get("id"),
                        "name": m.get("name"),
                        "amount": m.get("amount"),
                        "sum": m.get("sum")
                    })

                # Улучшенное извлечение размера (может быть объектом или строкой)
                size_data = item.get("size")
                size_name = size_data.get("name") if isinstance(size_data, dict) else size_data

                session.add(OrderItem(
                    order_id=order.id,
                    product_name=item.get("name"),
                    quantity=int(item.get("amount", 1)),
                    price=Decimal(str(item.get("price", 0))),
                    total=Decimal(str(item.get("sum", 0))),
                    size_name=size_name,
                    comment=item.get("comment"),
                    modifiers=mods
                ))
        session.commit()


    async def sync_order_by_id(self, session: Session, order_id: str, organization_id: str) -> bool:
        """
        Синхронизация конкретного заказа из iiko по его ID
        Вызывается при получении вебхука DeliveryOrderUpdate
        """
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login if settings_db else None
        
        try:
            # Получаем детальную информацию о заказе
            order_data = await iiko_service.get_order_by_id(order_id, organization_id, api_login=api_login)
            if order_data:
                # Пытаемся получить данные iiko Card
                iiko_card_data = None
                customer_phone = order_data.get("order", {}).get("customer", {}).get("phone")
                if customer_phone:
                    try:
                        iiko_card_data = await iiko_service.get_customer_info(customer_phone, api_login=api_login, organization_id=organization_id)
                    except Exception as e:
                        logger.warning(f"Failed to fetch iiko Card info for {customer_phone}: {e}")
                
                await self.process_iiko_order(session, order_data, organization_id, iiko_card_data=iiko_card_data)
                return True
        except Exception as e:
            logger.error(f"Error syncing order {order_id}: {e}")
        return False

    async def sync_payment_types(self, session: Session) -> Dict[str, Any]:
        """
        Синхронизация типов оплаты из iiko
        """
        log = SyncLog(sync_type="payment_types", status="running")
        session.add(log)
        session.commit()

        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login if settings_db else None
        org_id = settings_db.organization_id if settings_db else None

        try:
            logger.info(f"Starting payment types sync for org {org_id}")
            payment_types = await iiko_service.get_payment_types(api_login=api_login, organization_id=org_id)
            logger.info(f"Fetched {len(payment_types)} payment types from iiko Cloud")
            
            synced = 0
            for pt in payment_types:
                iiko_id = pt.get("id")
                if not iiko_id: continue
                
                name = pt.get("name", "Unknown")
                kind = pt.get("kind") or pt.get("paymentTypeKind")
                is_active = not pt.get("isDeleted", False)
                
                # В iiko v1/v2 поле может называться иначе
                if not kind and "kind" in pt: kind = pt["kind"]
                
                db_pt = session.exec(select(PaymentType).where(PaymentType.iiko_id == iiko_id)).first()
                if db_pt:
                    db_pt.name = name
                    db_pt.kind = kind
                    db_pt.is_active = is_active
                    db_pt.updated_at = datetime.utcnow()
                else:
                    db_pt = PaymentType(
                        iiko_id=iiko_id,
                        name=name,
                        kind=kind,
                        is_active=is_active
                    )
                    session.add(db_pt)
                synced += 1
            
            session.commit()
            log.status = "success"
            log.details = f"Synced {synced} payment types"
            session.commit()
            
            return {"success": True, "count": synced}
        except Exception as e:
            logger.error(f"Payment types sync failed: {e}")
            log.status = "error"
            log.details = str(e)
            session.commit()
            return {"success": False, "error": str(e)}

    async def sync_delivery_restrictions(self, session: Session) -> Dict[str, Any]:
        """
        Синхронизация зон доставки и условий (ограничений) из iiko
        """
        log = SyncLog(sync_type="delivery_zones", status="running")
        session.add(log)
        session.commit()

        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login if settings_db else None
        org_id = settings_db.organization_id if settings_db else None

        try:
            # 1. Получаем базовые данные из iiko Cloud (геометрия и условия)
            data = await iiko_service.get_delivery_restrictions(api_login=api_login, organization_id=org_id)
            restrictions_list = data.get("deliveryRestrictions", [])
            
            # Получаем филиал по умолчанию для привязки новых зон
            default_branch = session.exec(select(Branch)).first()
            branch_id = default_branch.id if default_branch else 1
            
            # 2. Получаем расширенные данные из iiko Resto (описания) если настроено
            resto_zones_map = {}
            if settings_db.resto_url and settings_db.resto_login:
                try:
                    resto_zones = await iiko_service.get_resto_delivery_zones(
                        settings_db.resto_url, settings_db.resto_login, settings_db.resto_password
                    )
                    for rz in resto_zones:
                        resto_zones_map[rz["id"]] = rz
                    logger.info(f"Fetched {len(resto_zones)} delivery zones from iiko Resto")
                except Exception as e:
                    logger.warning(f"Failed to fetch zones from iiko Resto: {e}")

            synced_zones = 0
            for rest_item in restrictions_list:
                zones = rest_item.get("deliveryZones", [])
                conditions = rest_item.get("restrictions", [])
                conditions_map = {c.get("deliveryZoneId"): c for c in conditions if c.get("deliveryZoneId")}
                
                for zone_data in zones:
                    iiko_id = zone_data.get("id")
                    if not iiko_id: continue
                    
                    name = zone_data.get("name", "Unknown Zone")
                    coords = zone_data.get("coordinates", [])
                    cond = conditions_map.get(iiko_id, {})
                    resto_data = resto_zones_map.get(iiko_id, {})

                    db_zone = session.exec(select(DeliveryZone).where(DeliveryZone.iiko_id == iiko_id)).first()
                    if not db_zone:
                        db_zone = DeliveryZone(iiko_id=iiko_id, branch_id=branch_id)
                    
                    db_zone.name = name
                    db_zone.polygon_coordinates = str(coords) # Store as string as per model
                    db_zone.min_order_amount = float(cond.get("minSum", 0))
                    db_zone.delivery_cost = float(cond.get("deliverySum", 0)) if "deliverySum" in cond else 0
                    
                    db_zone.min_delivery_time = cond.get("minDeliveryTime")
                    db_zone.max_delivery_time = cond.get("maxDeliveryTime")
                    
                    # Добавляем данные из Resto
                    if resto_data:
                        db_zone.description = resto_data.get("description")
                        # Сохраняем как список или словарь (SQLModel List/JSON)
                        db_zone.additional_info = resto_data.get("addresses", [])
                    
                    db_zone.updated_at = datetime.utcnow()
                    session.add(db_zone)
                    synced_zones += 1
            
            session.commit()
            log.status = "success"
            log.details = f"Synced {synced_zones} delivery zones (Cloud + Resto)"
            session.commit()
            return {"success": True, "count": synced_zones}
        except Exception as e:
            logger.error(f"Delivery zones sync failed: {e}")
            log.status = "error"
            log.details = str(e)
            session.commit()
            return {"success": False, "error": str(e)}

    async def sync_orders(self, session: Session, hours: int = 24) -> Dict[str, Any]:
        """
        Синхронизация заказов из iiko за последние N часов
        """
        companies = session.exec(select(Company).where(Company.iiko_organization_id != None)).all()
        
        # РџРѕР»СѓС‡Р°РµРј РіР»РѕР±Р°Р»СЊРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё РґР»СЏ Р»РѕРіРёРЅР°
        settings_db = session.exec(select(IikoSettings)).first()
        global_api_login = settings_db.api_login if settings_db else None
        global_org_id = settings_db.organization_id if settings_db else None

        if not companies:
            if not global_org_id:
                return {"success": False, "message": "No iiko organizations configured"}
            # Создаем "виртуальную" компанию для синхронизации
            companies = [Company(name="Initial Sync", iiko_organization_id=global_org_id)]

        log = SyncLog(sync_type="orders_manual", status="running")
        session.add(log)
        session.commit()

        synced_count = 0
        try:
            for company in companies:
                try:
                    # Определяем логин: из компании или глобальный
                    api_login = company.iiko_api_login or global_api_login
                    org_id = company.iiko_organization_id
    
                    # 1. Синхронизируем исторические заказы (разбиваем на окна по 24 часа, чтобы избежать 422 Too many data)
                    date_to = datetime.utcnow()
                    date_from = date_to - timedelta(hours=hours)
                    
                    current_from = date_from
                    while current_from < date_to:
                        current_to = min(current_from + timedelta(hours=24), date_to)
                        orders_by_date = await iiko_service.get_orders_by_date(
                            current_from, current_to, org_id,
                            api_login=api_login,
                            statuses=['Unconfirmed', 'WaitCooking', 'ReadyForCooking', 'CookingStarted', 'CookingCompleted', 'Waiting', 'OnWay', 'Delivered', 'Closed', 'Cancelled']
                        )
                        logger.info(f"Fetched {len(orders_by_date)} orders for range {current_from} to {current_to}")
                        
                        for o in orders_by_date:
                            await self.process_iiko_order(session, o, org_id)
                            synced_count += 1
                        current_from = current_to
                    
                    # 2. Синхронизируем активные заказы
                    active_orders = await iiko_service.get_active_orders(
                        org_id,
                        api_login=api_login
                    )
                    for o in active_orders:
                        await self.process_iiko_order(session, o, org_id)
                        synced_count += 1
                except Exception as e:
                    logger.error(f"Error syncing orders for company {company.name}: {e}")
        except Exception as e:
            logger.error(f"Critical error in sync_orders: {e}")
            log.status = "error"
            log.details = str(e)
            session.commit()
            return {"success": False, "message": str(e)}
                
        log.status = "success"
        log.details = f"Synced {synced_count} orders for last {hours} hours"
        session.commit()
        
        return {"success": True, "synced_count": synced_count}

    async def sync_employees_full(self, session: Session, days: int = 7) -> Dict[str, Any]:
        """
        Полная синхронизация сотрудников и смен (Resto + Transport)
        """
        companies = session.exec(select(Company).where(Company.iiko_organization_id != None)).all()
        settings_db = session.exec(select(IikoSettings)).first()
        
        if not settings_db:
            return {"success": False, "message": "Iiko settings not found"}

        global_api_login = settings_db.api_login
        resto_url = settings_db.resto_url
        resto_login = settings_db.resto_login
        resto_password = settings_db.resto_password

        synced_emp = 0
        synced_shifts = 0
        
        date_to = datetime.utcnow()
        date_from = date_to - timedelta(days=days)
        
        # Вспомогательный парсер дат
        def parse_dt(dt_str):
            if not dt_str: return None
            try:
                # Поддержка форматов ISO с Z или смещением
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00')).replace(tzinfo=None)
            except: 
                try:
                    # Поддержка формата iiko "yyyy-MM-dd HH:mm:ss"
                    return datetime.strptime(dt_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
                except:
                    return None

        # 1. Получаем детальные данные из Resto API один раз (если настроено)
        resto_emp_map = {}
        resto_roles_map = {}
        if resto_url and resto_login and resto_password:
            try:
                # Получаем сотрудников
                resto_employees = await iiko_service.get_resto_employees(resto_url, resto_login, resto_password)
                for re in resto_employees:
                    if re.get("id"):
                        resto_emp_map[re["id"]] = re
                
                # Получаем справочник ролей (должностей)
                resto_roles = await iiko_service.get_resto_roles(resto_url, resto_login, resto_password)
                for role in resto_roles:
                    resto_roles_map[role["code"]] = role["name"]
                logger.info(f"Fetched {len(resto_emp_map)} employees and {len(resto_roles_map)} roles from iiko Resto")
            except Exception as e:
                logger.error(f"Error fetching Resto data: {e}")

        # 2. Основной цикл по компаниям
        for company in companies:
            try:
                api_login = company.iiko_api_login or global_api_login
                org_id = company.iiko_organization_id
                
                # 2.1. Данные из Cloud API (Transport)
                cloud_employees = []
                try:
                    cloud_employees = await iiko_service.get_employees(org_id, api_login=api_login)
                except Exception as e:
                    logger.warning(f"Cloud API employees failed for {company.name} (likely 401), using Resto only: {e}")

                # 2.2. Синхронизация курьеров (статистика доставок)
                courier_stats = {}
                try:
                    courier_stats = await iiko_service.get_courier_statistics(date_from, date_to, org_id, api_login=api_login)
                    logger.info(f"Fetched delivery stats for {len(courier_stats)} couriers")
                except Exception as e:
                    logger.warning(f"Courier stats failed for {company.name}: {e}")

                # 2.2.1. Выручка курьеров из OLAP (Office)
                # Инициализируем пустым словарем, чтобы избежать NameError ниже
                courier_revenues = {}
                if resto_url and resto_login and resto_password:
                    try:
                        courier_revenues = await iiko_service.get_courier_revenue_olap(
                            date_from, date_to, resto_url, resto_login, resto_password
                        )
                        logger.info(f"Fetched OLAP revenue for {len(courier_revenues)} couriers")
                    except Exception as e:
                        logger.warning(f"Courier OLAP revenue failed: {e}")

                # 2.3. Объединяем и синхронизируем сотрудников
                cloud_ids = {e["id"] for e in cloud_employees if e.get("id")}
                # Используем всех сотрудников из Resto (с фильтрацией по организации если возможно, но для 72roll пока берем всех)
                all_ids = set(resto_emp_map.keys()).union(cloud_ids)
                
                for iiko_id in all_ids:
                    r_data = resto_emp_map.get(iiko_id, {})
                    c_data = next((e for e in cloud_employees if e.get("id") == iiko_id), {})
                    
                    if not r_data and not c_data: continue

                    # Формируем имя
                    name = r_data.get("name") or c_data.get("name")
                    if not name:
                        f_name = r_data.get("firstName") or ""
                        l_name = r_data.get("lastName") or ""
                        name = f"{f_name} {l_name}".strip() or "Неизвестный сотрудник"

                    # Определяем роль (должность) - приоритет названиям из справочника Resto
                    role_code = r_data.get("main_role_code") or r_data.get("role") or c_data.get("roleId")
                    role = resto_roles_map.get(role_code, role_code) or "Staff"
                    
                    phone = r_data.get("phone") or c_data.get("phone")
                    status = "Active" if not r_data.get("deleted") and not c_data.get("deleted") else "Deleted"

                    emp = session.exec(select(Employee).where(Employee.iiko_id == iiko_id)).first()
                    if emp:
                        emp.name = name
                        emp.phone = phone or emp.phone
                        # Обновляем роль только если она изменилась и не пустая
                        if role and role != "Staff": emp.role = role
                        emp.status = status
                        emp.updated_at = datetime.utcnow()
                        # Дополнительно сохраняем адрес если есть в Resto
                        if r_data.get("address"): emp.address = r_data["address"]
                    else:
                        emp = Employee(
                            iiko_id=iiko_id,
                            name=name,
                            phone=phone,
                            role=role,
                            status=status,
                            address=r_data.get("address")
                        )
                        session.add(emp)
                
                session.flush() # Сохраняем чтобы ID появились
                synced_emp += len(all_ids)

                # 3. СИНХРОНИЗАЦИЯ СМЕН (Явок)
                all_shifts = []
                
                # 3.1. Берем из Resto (самый детальный источник или резервный канал при 401 в Cloud)
                if resto_url and resto_login and resto_password:
                    try:
                        r_attendance = await iiko_service.get_resto_personal_sessions(
                            date_from, date_to,
                            resto_url=resto_url, 
                            resto_login=resto_login, 
                            resto_password=resto_password
                        )
                        for ra in r_attendance:
                            all_shifts.append({
                                "id": ra["id"],
                                "employee_iiko_id": ra["employeeId"],
                                "date_open": ra["openTime"],
                                "date_close": ra.get("closeTime"),
                                "source": "resto"
                            })
                    except Exception as e:
                        logger.error(f"Resto attendance (sessions) failed: {e}")

                # 3.2. Дополняем из Cloud (если есть)
                try:
                    c_shifts = await iiko_service.get_shifts(date_from, date_to, org_id, api_login=api_login)
                    for cs in c_shifts:
                        if not any(s["id"] == cs["id"] for s in all_shifts):
                            all_shifts.append({
                                "id": cs["id"],
                                "employee_iiko_id": cs["employeeId"],
                                "date_open": cs["dateOpen"],
                                "date_close": cs["dateClose"],
                                "source": "cloud"
                            })
                except Exception as e:
                    logger.warning(f"Cloud shifts failed: {e}")

                # 3.3. Сохраняем смены по одной
                for s_info in all_shifts:
                    try:
                        s_id = s_info["id"]
                        e_id = s_info["employee_iiko_id"]
                        
                        # Ищем сотрудника в нашей БД
                        db_emp = session.exec(select(Employee).where(Employee.iiko_id == e_id)).first()
                        if not db_emp: continue

                        d_open = parse_dt(s_info["date_open"])
                        d_close = parse_dt(s_info["date_close"])
                        if not d_open: continue

                        # Расчет часов
                        hours = round((d_close - d_open).total_seconds() / 3600, 2) if d_close else 0.0
                        status = "CLOSED" if d_close else "OPEN"

                        shift = session.exec(select(Shift).where(Shift.iiko_id == s_id)).first()
                        if shift:
                            shift.date_open = d_open
                            shift.date_close = d_close
                            shift.status = status
                            shift.work_hours = hours
                            
                            d_str = d_open.strftime("%Y-%m-%d")
                            # Обновляем количество доставок
                            shift.deliveries_count = courier_stats.get(e_id, {}).get(d_str, 0)
                            # Обновляем выручку курьера
                            shift.deliveries_revenue = courier_revenues.get(e_id, {}).get(d_str, 0.0)
                            
                            shift.updated_at = datetime.utcnow()
                        else:
                            shift = Shift(
                                iiko_id=s_id,
                                employee_id=db_emp.id,
                                date_open=d_open,
                                date_close=d_close,
                                status=status,
                                work_hours=hours,
                                deliveries_count=courier_stats.get(e_id, {}).get(d_open.strftime("%Y-%m-%d"), 0),
                                deliveries_revenue=courier_revenues.get(e_id, {}).get(d_open.strftime("%Y-%m-%d"), 0.0)
                            )
                            session.add(shift)
                        
                        session.flush()
                        synced_shifts += 1
                    except Exception as shift_e:
                        logger.error(f"Error syncing shift {s_info.get('id')}: {shift_e}")
                        session.rollback() # Откатываем только эту смену
                        continue

                # 4. СИНХРОНИЗАЦИЯ ДЕТАЛЬНЫХ ЗАКАЗОВ КУРЬЕРОВ
                try:
                    detailed_orders = []
                    try:
                        detailed_orders = await iiko_service.get_detailed_deliveries(date_from, date_to, org_id, api_login=api_login)
                    except Exception as cloud_e:
                        if resto_url and ("401" in str(cloud_e) or "Unauthorized" in str(cloud_e)):
                            logger.info("Cloud API 401, trying Resto for detailed deliveries...")
                            detailed_orders = await iiko_service.get_resto_detailed_deliveries(
                                date_from, date_to, org_id,
                                resto_url=resto_url, resto_login=resto_login, resto_password=resto_password
                            )
                        else:
                            raise cloud_e

                    restrictions = await iiko_service.get_delivery_restrictions(org_id, api_login=api_login)
                    
                    # Маппинг терминал -> зона
                    terminal_zones = {}
                    for restr in restrictions:
                        t_id = restr.get("deliveryTerminalId")
                        zones = restr.get("deliveryZones", [])
                        if t_id and zones:
                            terminal_zones[t_id] = zones[0].get("name")
                    
                    for order_data in detailed_orders:
                        o_id = order_data.get("id")
                        courier = order_data.get("courierInfo", {}).get("courier", {})
                        courier_iiko_id = courier.get("id")
                        
                        if not o_id or not courier_iiko_id: continue
                        
                        # Находим сотрудника
                        db_emp = session.exec(select(Employee).where(Employee.iiko_id == courier_iiko_id)).first()
                        if not db_emp: continue
                        
                        # Временные метки
                        when_created = self._parse_iiko_time(order_data.get("whenCreated"))
                        when_delivered = self._parse_iiko_time(order_data.get("whenDelivered") or order_data.get("completeTime"))
                        expected_time = self._parse_iiko_time(order_data.get("deliveryDate"))
                        when_cooking_completed = self._parse_iiko_time(order_data.get("whenCookingCompleted"))
                        
                        if not when_created: continue
                        
                        # Состав заказа
                        items = order_data.get("order", {}).get("items", [])
                        items_text = ", ".join([f"{i.get('name')} x{i.get('amount')}" for i in items])
                        
                        # Адрес
                        addr_data = order_data.get("order", {}).get("address", {})
                        address = f"{addr_data.get('street', '')} {addr_data.get('house', '')}, кв. {addr_data.get('flat', '')}".strip(", ")
                        
                        # Зона
                        zone = terminal_zones.get(order_data.get("deliveryTerminalId"))
                        
                        # Расчет опозданий
                        is_late = False
                        if when_delivered and expected_time:
                            is_late = when_delivered > expected_time
                            
                        cooking_late = False
                        if when_cooking_completed and expected_time:
                            # Опоздание кухни - если готовность позже ожидаемого времени доставки (или по своей логике)
                            cooking_late = when_cooking_completed > expected_time
                            
                        # Находим смену
                        shift_obj = session.exec(
                            select(Shift)
                            .where(Shift.employee_id == db_emp.id)
                            .where(Shift.date_open <= (when_delivered or when_created))
                            .order_by(Shift.date_open.desc())
                        ).first()
                        
                        db_order = session.exec(select(CourierOrder).where(CourierOrder.iiko_id == o_id)).first()
                        if db_order:
                            db_order.actual_delivery_time = when_delivered
                            db_order.is_late = is_late
                            db_order.cooking_late = cooking_late
                            db_order.updated_at = datetime.utcnow()
                        else:
                            db_order = CourierOrder(
                                iiko_id=o_id,
                                employee_id=db_emp.id,
                                shift_id=shift_obj.id if shift_obj else None,
                                address=address,
                                items_summary=items_text[:500],
                                delivery_zone=zone,
                                created_at_iiko=when_created,
                                cooking_completed_at=when_cooking_completed,
                                expected_delivery_time=expected_time,
                                actual_delivery_time=when_delivered,
                                is_late=is_late,
                                cooking_late=cooking_late
                            )
                            session.add(db_order)
                    
                    logger.info(f"Synced {len(detailed_orders)} detailed courier orders for {company.name}")
                except Exception as e:
                    logger.error(f"Error syncing detailed courier orders for {company.name}: {e}")

                # 5. СИНХРОНИЗАЦИЯ ГРАФИКОВ
                try:
                    await self.sync_schedules(
                        session, date_from, date_to, org_id, 
                        api_login=api_login,
                        resto_url=resto_url,
                        resto_login=resto_login,
                        resto_password=resto_password
                    )
                except Exception as e:
                    logger.warning(f"Schedules failed: {e}")

                session.commit() # Фиксируем всё по компании
                
            except Exception as company_e:
                logger.error(f"Error in sync_employees_full for company {company.name}: {company_e}")
                session.rollback()
                
        return {"success": True, "employees": synced_emp, "shifts": synced_shifts}

    async def get_employee_stats(self, session: Session, employee_id: int, mode: str = "calendar") -> Dict[str, Any]:
        """
        Расчет статистики сотрудника: группировка по дням, чистая выручка и детализация доставок.
        """
        from app.models.order import Order # Импорт внутри для избежания циклической зависимости
        
        now = datetime.utcnow()
        if mode == "calendar":
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = now - timedelta(days=7)

        # 1. Получаем смены
        shifts = session.exec(
            select(Shift).where(Shift.employee_id == employee_id, Shift.date_open >= start_date).order_by(Shift.date_open.desc())
        ).all()
        
        db_emp = session.get(Employee, employee_id)
        # Уточненное условие для курьера: роль курьера ИЛИ наличие доставок в истории
        has_delivery_history = session.exec(
            select(Order).where(Order.courier_name == db_emp.name).limit(1)
        ).first() is not None if db_emp else False
        
        is_courier_role = db_emp.role in ["Courier", "CUR", "курьер", "Delivery"] if db_emp else False
        show_deliveries = is_courier_role or has_delivery_history

        # 2. Получаем выручку из iiko OLAP (чистая выручка = Сумма - Скидки)
        revenue_data = {}
        try:
            revenue_data = await iiko_service.get_daily_revenue_olap(start_date, now)
        except Exception as e:
            logger.error(f"Error fetching revenue OLAP: {e}")

        total_hours = sum(s.work_hours or 0 for s in shifts)
        total_deliveries_count = sum(s.deliveries_count or 0 for s in shifts)
        
        # 3. Группировка по дням
        daily_stats = {}
        for s in shifts:
            day_key = s.date_open.strftime("%Y-%m-%d")
            if day_key not in daily_stats:
                day_fin = revenue_data.get(day_key, {"revenue": 0.0, "discounts": 0.0})
                daily_stats[day_key] = {
                    "date": day_key,
                    "shifts": [],
                    "total_hours": 0.0,
                    "total_deliveries": 0,
                    "financials": {
                        "revenue": day_fin["revenue"],
                        "discounts": day_fin["discounts"],
                        "net_revenue": round(day_fin["revenue"] - day_fin["discounts"], 2)
                    },
                    "deliveries": [] # Сюда добавим детали
                }
            
            daily_stats[day_key]["shifts"].append({
                "id": s.id,
                "open": s.date_open.isoformat(),
                "close": s.date_close.isoformat() if s.date_close else None,
                "status": s.status,
                "hours": round(s.work_hours or 0, 2),
                "deliveries": s.deliveries_count or 0
            })
            daily_stats[day_key]["total_hours"] += (s.work_hours or 0)
            daily_stats[day_key]["total_deliveries"] += (s.deliveries_count or 0)

        # 4. Если нужно показывать доставки
        if show_deliveries and db_emp:
            # Ищем заказы за период по имени курьера
            orders = session.exec(
                select(Order).where(
                    Order.courier_name == db_emp.name, 
                    Order.created_at >= start_date
                ).order_by(Order.created_at.desc())
            ).all()
            
            for o in orders:
                day_key = o.created_at.strftime("%Y-%m-%d")
                if day_key in daily_stats:
                    daily_stats[day_key]["deliveries"].append({
                        "id": o.iiko_order_id,
                        "amount": float(o.total_with_discount),
                        "address": o.delivery_address,
                        "zone": o.delivery_zone,
                        "departure": o.iiko_creation_time.isoformat() if o.iiko_creation_time else None,
                        "arrival": o.actual_time.isoformat() if o.actual_time else None,
                        "target_time": o.expected_time.isoformat() if o.expected_time else None,
                        "delay": o.delay_minutes or 0
                    })

        sorted_days = sorted(daily_stats.values(), key=lambda x: x["date"], reverse=True)
        for day in sorted_days:
            day["total_hours"] = round(day["total_hours"], 2)

        return {
            "period_start": start_date.isoformat(),
            "total_shifts": len(shifts),
            "total_hours_period": round(total_hours, 2),
            "total_deliveries_period": total_deliveries_count,
            "daily_stats": sorted_days,
            "is_courier": show_deliveries,
            "mode": mode
        }

    async def sync_schedules(
        self, session: Session, date_from: datetime, date_to: datetime, organization_id: str,
        api_login: Optional[str] = None,
        resto_url: Optional[str] = None,
        resto_login: Optional[str] = None,
        resto_password: Optional[str] = None
    ):
        """
        Синхронизация запланированного графика смен
        """
        try:
            iiko_schedules = []
            try:
                iiko_schedules = await iiko_service.get_schedules(
                    date_from, date_to, organization_id,
                    api_login=api_login
                )
            except Exception as cloud_e:
                if resto_url and ("401" in str(cloud_e) or "Unauthorized" in str(cloud_e)):
                    logger.info("Cloud API 401, trying Resto for schedules...")
                    iiko_schedules = await iiko_service.get_resto_schedules(
                        date_from, date_to,
                        resto_url=resto_url, resto_login=resto_login, resto_password=resto_password
                    )
                else:
                    logger.error(f"Cloud schedules failed: {cloud_e}")
                    raise cloud_e
            for item in iiko_schedules:
                iiko_id = item.get("id")
                if not iiko_id:
                    continue
                
                emp_iiko_id = item.get("employeeId")
                emp = session.exec(select(Employee).where(Employee.iiko_id == emp_iiko_id)).first()
                if not emp:
                    continue
                
                def parse_time(ts_str):
                    if not ts_str: return None
                    try:
                        return datetime.fromisoformat(ts_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    except:
                        return None
                
                start_time = parse_time(item.get("dateFrom"))
                end_time = parse_time(item.get("dateTo"))
                
                if not start_time or not end_time:
                    continue
                    
                schedule = session.exec(select(Schedule).where(Schedule.iiko_id == iiko_id)).first()
                if schedule:
                    schedule.date_from = start_time
                    schedule.date_to = end_time
                    schedule.updated_at = datetime.utcnow()
                else:
                    schedule = Schedule(
                        iiko_id=iiko_id,
                        employee_id=emp.id,
                        date_from=start_time,
                        date_to=end_time
                    )
                    session.add(schedule)
            
            session.flush()
        except Exception as e:
            logger.error(f"Error in sync_schedules: {e}")
            raise

    async def sync_vk_loyalty(self, session: Session) -> Dict[str, Any]:
        """
        Синхронизация баллов из VK в iikoCard.
        Находит все несинхронизированные активности, группирует по пользователям
        и отправляет начисление в iiko.
        """
        # Find all unsynced activities
        unsynced = session.exec(select(VkActivity).where(VkActivity.is_synced == False)).all()
        if not unsynced:
            return {"success": True, "synced_activities": 0, "message": "No new activities to sync"}
            
        # Group points by vk_id
        points_by_user = {}
        activities_by_user = {}
        for activity in unsynced:
            points_by_user[activity.vk_id] = points_by_user.get(activity.vk_id, 0) + activity.points
            if activity.vk_id not in activities_by_user:
                activities_by_user[activity.vk_id] = []
            activities_by_user[activity.vk_id].append(activity)
            
        synced_count = 0
        error_count = 0
        
        # Получаем глобальные настройки для логина
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login if settings_db else None
        org_id = settings_db.organization_id if settings_db else None

        for vk_id, total_points in points_by_user.items():
            if total_points <= 0:
                continue
                
            # Get VkUser
            vk_user = session.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
            if not vk_user or not vk_user.is_linked or not vk_user.phone:
                continue
                
            try:
                # Find customer in iikoCard to get customerId and walletId
                customer_info = await iiko_service.get_customer_info(
                    vk_user.phone,
                    api_login=api_login,
                    organization_id=org_id
                )
                if str(customer_info.get("found", "")).lower() == "false":
                    logger.warning(f"Could not find iikoCard for phone {vk_user.phone}")
                    continue
                    
                customer_id = customer_info.get("id")
                wallets = customer_info.get("walletBalances", [])
                if not wallets:
                    # Sometimes the response format is different or they don't have a wallet yet.
                    # We might need to just use the default wallet logic or create one, but usually get_customer_info returns it if they exist.
                    logger.warning(f"No wallets found for customer {vk_user.phone}")
                    continue
                    
                # Get the first active wallet
                wallet_id = wallets[0].get("wallet", {}).get("id")
                if not wallet_id or not customer_id:
                    continue
                    
                # Accrue points
                await iiko_service.add_customer_balance(
                    customer_id=customer_id,
                    wallet_id=wallet_id,
                    amount=float(total_points),
                    api_login=api_login,
                    organization_id=org_id
                )
                
                # Mark as synced
                for act in activities_by_user[vk_id]:
                    act.is_synced = True
                    act.synced_at = datetime.utcnow()
                    session.add(act)
                    synced_count += 1
                    
                # Deduct from local balance as they are now in iiko
                vk_user.vk_bonus_balance -= total_points
                if vk_user.vk_bonus_balance < 0:
                    vk_user.vk_bonus_balance = 0
                session.add(vk_user)
                
                # Send success message to VK
                vk_settings = session.exec(select(VkSettings)).first()
                bot_token = vk_settings.vk_bot_token if vk_settings else None
                if bot_token:
                    await send_vk_message(
                        vk_id,
                        f"🎉 Ваши баллы за активность ({total_points}) успешно переведены на iikoCard!",
                        bot_token
                    )
                
            except Exception as e:
                logger.error(f"Error syncing loyalty for VK user {vk_id}: {e}")
                error_count += 1
                
        session.commit()
        
        return {
            "success": True, 
            "synced_activities": synced_count,
            "errors": error_count
        }


    def _parse_iiko_time(self, timestr: Optional[str]) -> Optional[datetime]:
        """Парсинг времени из iiko (формат '2024-03-27 15:30:00.000' или ISO)"""
        if not timestr:
            return None
        try:
            # iiko Cloud часто присылает '2024-03-27 15:30:00.000'
            if " " in timestr and "." in timestr:
                return datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S.%f")
            if " " in timestr:
                return datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S")
            return datetime.fromisoformat(timestr.replace("Z", "+00:00"))
        except:
            return None


    async def sync_categories_only(self, session: Session) -> Dict[str, Any]:
        """Синхронизация только категорий из iiko External Menu API v2"""
        from app.models.category import Category
        log = SyncLog(sync_type="categories", status="running")
        session.add(log)
        session.commit()
        
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db or not settings_db.external_menu_id:
            log.status = "error"
            log.details = "External Menu ID не настроен"
            session.commit()
            raise Exception("External Menu ID не настроен в settings iiko")
            
        try:
            menu_data = await iiko_service.get_external_menu_by_id(
                settings_db.external_menu_id,
                api_login=settings_db.api_login,
                organization_id=settings_db.organization_id
            )
            
            categories_synced = 0
            for cat_data in menu_data.get("itemCategories", []):
                cat_iiko_id = cat_data.get("id")
                cat_name = cat_data.get("name", "")
                cat_image_id = cat_data.get("imageId")
                items_in_cat = cat_data.get("items", [])
                
                if not cat_iiko_id:
                    continue
                    
                category = session.exec(
                    select(Category).where(Category.iiko_id == cat_iiko_id)
                ).first()
                
                if not category:
                    category = Category(iiko_id=cat_iiko_id, name=cat_name)
                    session.add(category)
                
                category.name = cat_name
                category.iiko_image_id = cat_image_id
                if cat_image_id:
                    category.image_url = f"https://api-ru.iiko.services/api/1/menu/download-image?imageId={cat_image_id}"
                
                category.is_active = True
                category.products_count = len(items_in_cat)
                category.modifiers_count = sum(
                    len(item.get("itemModifierGroups", [])) for item in items_in_cat
                )
                category.updated_at = datetime.utcnow()
                categories_synced += 1
                
            session.commit()
            log.status = "success"
            log.details = f"Синхронизировано {categories_synced} категорий"
            session.commit()
            return {"success": True, "categories_synced": categories_synced, "message": log.details}
        except Exception as e:
            log.status = "error"
            log.details = str(e)
            session.commit()
            raise

# Глобальный экземпляр
iiko_sync_service = IikoSyncService()
