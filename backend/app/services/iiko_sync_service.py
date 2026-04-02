"""
РЎРµСЂРІРёСЃ-РѕСЂРєРµСЃС‚СЂР°С‚РѕСЂ РґР»СЏ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё РґР°РЅРЅС‹С… СЃ iiko
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
from app.models.employee import Employee, Shift, Schedule
from app.models.company import Branch, Company
from app.models.customer import Customer
from app.models.vk_user import VkUser
from app.models.vk_activity import VkActivity
from app.models.vk_settings import VkSettings
from app.models.iiko_settings import IikoSettings
from app.services.vk_service import send_vk_message
from app.services.iiko_service import iiko_service

logger = logging.getLogger(__name__)


class IikoSyncService:
    """РћСЂРєРµСЃС‚СЂР°С‚РѕСЂ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё РґР°РЅРЅС‹С… РјРµР¶РґСѓ iiko Рё Р»РѕРєР°Р»СЊРЅРѕР№ Р‘Р”"""

    async def sync_menu(self, session: Session) -> Dict[str, Any]:
        """
        РџРѕР»РЅР°СЏ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РјРµРЅСЋ РёР· iiko

        Р—Р°РіСЂСѓР¶Р°РµС‚ РЅРѕРјРµРЅРєР»Р°С‚СѓСЂСѓ (РєР°С‚РµРіРѕСЂРёРё + С‚РѕРІР°СЂС‹) Рё РѕР±РЅРѕРІР»СЏРµС‚ Р»РѕРєР°Р»СЊРЅСѓСЋ Р‘Р”.
        РЎРѕРїРѕСЃС‚Р°РІР»РµРЅРёРµ РїРѕ iiko_id.
        """
        log = SyncLog(sync_type="menu", status="running")
        session.add(log)
        session.commit()

        # РџРѕР»СѓС‡Р°РµРј РЅР°СЃС‚СЂРѕР№РєРё iiko РёР· Р‘Р”
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

            # РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РєР°С‚РµРіРѕСЂРёР№ (groups)
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

            # РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ С‚РѕРІР°СЂРѕРІ (products)
            if "products" in nomenclature:
                for iiko_product in nomenclature["products"]:
                    query = select(Product).where(
                        Product.iiko_id == iiko_product["id"]
                    )
                    product = session.exec(query).first()

                    # РџРѕРёСЃРє РєР°С‚РµРіРѕСЂРёРё
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
                            size_name = size_info.get("name", "РЎС‚Р°РЅРґР°СЂС‚")
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
                                name="Р“СЂСѓРїРїР° РјРѕРґРёС„РёРєР°С‚РѕСЂРѕРІ", # To be replaced by cross-referencing products if needed, but often iiko sends it as ID pointing to another product. For now use placeholder or fetch name if available.
                                min_amount=gm.get("minAmount", 0),
                                max_amount=gm.get("maxAmount", 1),
                                is_required=gm.get("required", False)
                            )
                            # Try to find group name from nomenclature products if modifierId points to a group
                            group_product = next((p for p in nomenclature["products"] if p["id"] == gm.get("modifierId")), None)
                            if group_product:
                                mg.name = group_product.get("name", "Р“СЂСѓРїРїР° РјРѕРґРёС„РёРєР°С‚РѕСЂРѕРІ")
                                
                            session.add(mg)
                            session.flush() # get mg.id
                            
                            for child in gm.get("childModifiers", []):
                                child_product = next((p for p in nomenclature["products"] if p["id"] == child.get("modifierId")), None)
                                child_name = child_product.get("name", "РњРѕРґРёС„РёРєР°С‚РѕСЂ") if child_product else "РњРѕРґРёС„РёРєР°С‚РѕСЂ"
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

            # РћР±РЅРѕРІР»СЏРµРј Р»РѕРі
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
        РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ С‚РѕР»СЊРєРѕ С†РµРЅ РёР· iiko

        РћР±РЅРѕРІР»СЏРµС‚ С†РµРЅС‹ Сѓ СЃСѓС‰РµСЃС‚РІСѓСЋС‰РёС… С‚РѕРІР°СЂРѕРІ, СЃРѕРїРѕСЃС‚Р°РІР»СЏСЏ РїРѕ Р°СЂС‚РёРєСѓР»Сѓ (article).
        """
        log = SyncLog(sync_type="prices", status="running")
        session.add(log)
        session.commit()

        # РџРѕР»СѓС‡Р°РµРј РЅР°СЃС‚СЂРѕР№РєРё iiko РёР· Р‘Р”
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login if settings_db else None
        organization_id = settings_db.organization_id if settings_db else None

        try:
            nomenclature = await iiko_service.get_nomenclature(
                api_login=api_login,
                organization_id=organization_id
            )
            nomenclature = nomenclature or {}
            updated = 0

            if "products" in nomenclature:
                for iiko_product in nomenclature["products"]:
                    # РЎРѕРїРѕСЃС‚Р°РІР»СЏРµРј РїРѕ iiko_id
                    query = select(Product).where(
                        Product.iiko_id == iiko_product["id"]
                    )
                    product = session.exec(query).first()

                    if product:
                        price = 0
                        if iiko_product.get("sizePrices"):
                            price = (
                                iiko_product["sizePrices"][0]
                                .get("price", {})
                                .get("currentPrice", 0)
                            )
                        if product.price != price:
                            product.price = price
                            product.updated_at = datetime.utcnow()
                            updated += 1

            session.commit()

            log.status = "success"
            log.products_count = updated
            log.details = f"Updated prices for {updated} products"
            session.commit()

            return {
                "success": True,
                "products_updated": updated,
                "message": log.details
            }

        except Exception as e:
            logger.error(f"Price sync failed: {e}")
            log.status = "error"
            log.details = str(e)
            session.commit()
            raise

    async def sync_stop_lists(self, session: Session) -> Dict[str, Any]:
        """
        РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ СЃС‚РѕРї-Р»РёСЃС‚РѕРІ

        РџРѕРјРµС‡Р°РµС‚ РїРѕР·РёС†РёРё РєР°Рє РЅРµРґРѕСЃС‚СѓРїРЅС‹Рµ (is_available=False)
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

            # РЎРЅР°С‡Р°Р»Р° РїРѕРјРµС‡Р°РµРј РІСЃРµ РєР°Рє РґРѕСЃС‚СѓРїРЅС‹Рµ
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
    async def process_iiko_order(self, session: Session, iiko_order_data: Dict[str, Any], organization_id: str):
        """
        РћР±СЂР°Р±РѕС‚РєР° РґР°РЅРЅС‹С… Р·Р°РєР°Р·Р° РёР· iiko.
        РЎРѕР·РґР°РµС‚ РЅРѕРІС‹Р№ РёР»Рё РѕР±РЅРѕРІР»СЏРµС‚ СЃСѓС‰РµСЃС‚РІСѓСЋС‰РёР№ Р·Р°РєР°Р· РІ Р‘Р”.
        """
        order_id_iiko = iiko_order_data.get("id")
        logger.info(f"Processing iiko order: {order_id_iiko} for org {organization_id}")
        
        if not order_id_iiko:
            logger.warning(f"Order data missing ID: {iiko_order_data}")
            return

        # РС‰РµРј Р·Р°РєР°Р· РїРѕ iiko_order_id
        order = session.exec(select(Order).where(Order.iiko_order_id == order_id_iiko)).first()
        
        # РџС‹С‚Р°РµРјСЃСЏ Р±РµР·РѕРїР°СЃРЅРѕ РёР·РІР»РµС‡СЊ РґР°РЅРЅС‹Рµ Р·Р°РєР°Р·Р°
        o_data = iiko_order_data.get("order", iiko_order_data)
        if not isinstance(o_data, dict):
            logger.error(f"Invalid order data type: {type(o_data)}")
            return
        
        # Status mapping
        iiko_status = iiko_order_data.get("creationStatus") or o_data.get("status", "")
        mapped_status = OrderStatus.CONFIRMED
        
        # Р Р°СЃС€РёСЂРµРЅРЅС‹Р№ РјР°РїРїРёРЅРі
        status_map = {
            "New": OrderStatus.NEW,
            "WaitCooking": OrderStatus.PREPARING,
            "ReadyForCooking": OrderStatus.PREPARING,
            "CookingStarted": OrderStatus.COOKING,
            "CookingCompleted": OrderStatus.READY,
            "Waiting": OrderStatus.DELIVERING,
            "OnWay": OrderStatus.DELIVERING,
            "Delivered": OrderStatus.DELIVERED,
            "Cancelled": OrderStatus.CANCELLED,
            "Error": OrderStatus.CANCELLED,
            "NotConfirmed": OrderStatus.CANCELLED
        }
        mapped_status = status_map.get(str(iiko_status), OrderStatus.CONFIRMED)

        customer_info = o_data.get("customer") or {}
        phone = customer_info.get("phone", "")
        name = customer_info.get("name", "")

        # РџР°СЂСЃРёРЅРі РІСЂРµРјРµРЅРё
        def parse_time(ts_str):
            if not ts_str or not isinstance(ts_str, str):
                return None
            try:
                if "T" in ts_str:
                    return datetime.fromisoformat(ts_str.replace("Z", "+00:00")).replace(tzinfo=None)
                return datetime.strptime(ts_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
            except Exception:
                return None

        expected_time = parse_time(o_data.get("completeBefore"))
        actual_time = parse_time(o_data.get("actualTime"))
        creation_time = parse_time(o_data.get("creationTime"))
        
        # Расчет опоздания
        delay_minutes = 0
        if expected_time and actual_time and actual_time > expected_time:
            delta = actual_time - expected_time
            delay_minutes = int(delta.total_seconds() // 60)

        # Флаг "на время"
        is_on_time = False
        if creation_time and expected_time:
            # Если время доставки больше чем через 2 часа после создания, считаем что "на время"
            if (expected_time - creation_time).total_seconds() > 7200:
                is_on_time = True

        # Курьер
        courier_name = None
        courier_info = o_data.get("courierInfo")
        if isinstance(courier_info, dict):
            courier = courier_info.get("courier")
            if isinstance(courier, dict):
                courier_name = courier.get("name")

        # Администратор / Кассир
        admin_name = None
        conveyor_details = o_data.get("conveyorDetails")
        if isinstance(conveyor_details, dict):
            cashier = conveyor_details.get("cashier")
            if isinstance(cashier, dict):
                admin_name = cashier.get("name")

        # Адрес и зона доставки
        deliv_point = o_data.get("deliveryPoint", {})
        delivery_address = deliv_point.get("address", {}).get("street", {}).get("name", "")
        house = deliv_point.get("address", {}).get("house", "")
        flat = deliv_point.get("address", {}).get("flat", "")
        if house:
            delivery_address += f", д. {house}"
        if flat:
            delivery_address += f", кв. {flat}"
        
        if not delivery_address:
            delivery_address = o_data.get("address") or o_data.get("deliveryAddress")
            
        delivery_zone = deliv_point.get("externalCartographyId") or deliv_point.get("zone", {}).get("name")

        # Финансы (Суммы и скидки)
        sum_total = Decimal(str(o_data.get("sum", 0)))
        total_with_discount = Decimal(str(o_data.get("totalSum", sum_total)))
        total_discount = sum_total - total_with_discount
        payment_method = None
        payments = o_data.get("payments", [])
        if payments and isinstance(payments, list):
            payment_method = payments[0].get("paymentType", {}).get("name")
            
        order_type = o_data.get("orderType", {}).get("name")
        
        # Бонусы
        bonus_spent = Decimal("0")
        bonus_accrued = Decimal("0")
        if "customer" in o_data:
            cust = o_data["customer"]
            # В iiko API бонусы часто идут в payments как тип "Loyalty"
            for p in payments:
                if p.get("paymentType", {}).get("kind") == "Loyalty":
                    bonus_spent += Decimal(str(p.get("sum", 0)))

        # Поиск customer_id
        customer = session.exec(select(Customer).where(Customer.phone == phone)).first() if phone else None
        if not customer and phone:
            customer = Customer(phone=phone, name=name)
            session.add(customer)
            session.commit()
            session.refresh(customer)

        if not order:
            # Пытаемся найти branch
            terminal_group_id = iiko_order_data.get("terminalGroupId") or o_data.get("terminalGroupId")
            branch_id = None
            if terminal_group_id:
                branch = session.exec(select(Branch).where(Branch.iiko_terminal_id == terminal_group_id)).first()
                if branch:
                    branch_id = branch.id

            order = Order(
                iiko_order_id=order_id_iiko,
                customer_name=name,
                customer_phone=phone,
                customer_id=customer.id if customer else None,
                branch_id=branch_id or 1,
                total_amount=sum_total,
                status=mapped_status,
                order_items_details=o_data.get("items", []),
                discounts_details=o_data.get("discountsInfo", {}),
                customer_info_details=customer_info,
                iiko_creation_time=creation_time,
                expected_time=expected_time,
                actual_time=actual_time,
                delay_minutes=delay_minutes,
                is_on_time=is_on_time,
                admin_name=admin_name,
                order_type=order_type,
                payment_method=payment_method,
                total_with_discount=total_with_discount,
                total_discount=total_discount,
                bonus_spent=bonus_spent,
                bonus_accrued=bonus_accrued,
                courier_name=courier_name,
                delivery_address=delivery_address,
                delivery_zone=delivery_zone
            )
            session.add(order)
            session.flush() # Получаем ID заказа
        else:
            old_status = order.status
            # Обновляем существующий заказ
            order.status = mapped_status
            order.iiko_creation_time = creation_time or order.iiko_creation_time
            order.expected_time = expected_time or order.expected_time
            order.actual_time = actual_time or order.actual_time
            order.delay_minutes = delay_minutes if delay_minutes > 0 else order.delay_minutes
            order.is_on_time = is_on_time
            order.admin_name = admin_name or order.admin_name
            order.payment_method = payment_method or order.payment_method
            order.order_type = order_type or order.order_type
            order.total_amount = sum_total
            order.total_with_discount = total_with_discount
            order.total_discount = total_discount
            order.bonus_spent = bonus_spent if bonus_spent > 0 else order.bonus_spent
            order.bonus_accrued = bonus_accrued if bonus_accrued > 0 else order.bonus_accrued
            order.courier_name = courier_name or order.courier_name
            order.delivery_address = delivery_address or order.delivery_address
            order.delivery_zone = delivery_zone or order.delivery_zone
            order.order_items_details = o_data.get("items", []) or order.order_items_details
            order.discounts_details = o_data.get("discountsInfo", {}) or order.discounts_details
            
            flag_modified(order, "order_items_details")
            flag_modified(order, "discounts_details")
            session.add(order)
        
        # Синхронизация OrderItems
        items_data = o_data.get("items", [])
        if isinstance(items_data, list):
            # Удаляем старые позиции для обновления
            existing_items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
            for ei in existing_items:
                session.delete(ei)
            
            for item_data in items_data:
                product_id_iiko = item_data.get("productId")
                product_name = item_data.get("name", "Unknown Product")
                quantity = int(item_data.get("amount", 1))
                price = Decimal(str(item_data.get("price", 0)))
                total = Decimal(str(item_data.get("sum", price * quantity)))
                
                # Пытаемся найти локальный продукт по iiko_id
                product = None
                if product_id_iiko:
                    product = session.exec(select(Product).where(Product.iiko_id == product_id_iiko)).first()
                
                new_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id if product else 1,
                    product_name=product_name,
                    quantity=quantity,
                    price=price,
                    total=total
                )
                session.add(new_item)

            if old_status != mapped_status and order.customer_phone:
                vk_user = session.exec(select(VkUser).where(VkUser.phone == order.customer_phone)).first()
                if vk_user and vk_user.is_linked:
                    vk_settings = session.exec(select(VkSettings)).first()
                    bot_token = vk_settings.vk_bot_token if vk_settings else None
                    if bot_token:
                        status_text = {
                            OrderStatus.NEW: "РќРѕРІС‹Р№",
                            OrderStatus.PREPARING: "Р“РѕС‚РѕРІРёС‚СЃСЏ",
                            OrderStatus.READY: "Р“РѕС‚РѕРІ",
                            OrderStatus.DELIVERING: "Р’ РїСѓС‚Рё",
                            OrderStatus.DELIVERED: "Р”РѕСЃС‚Р°РІР»РµРЅ",
                            OrderStatus.CANCELLED: "РћС‚РјРµРЅРµРЅ",
                        }.get(mapped_status, str(mapped_status))
                        
                        msg = f"рџЌЈ РЎС‚Р°С‚СѓСЃ РІР°С€РµРіРѕ Р·Р°РєР°Р·Р° в„–{order.id} РёР·РјРµРЅРёР»СЃСЏ!\nРўРµРєСѓС‰РёР№ СЃС‚Р°С‚СѓСЃ: {status_text}"
                        if mapped_status == OrderStatus.DELIVERING and order.courier_name:
                            msg += f"\nРљСѓСЂСЊРµСЂ: {order.courier_name}"
                            
                        await send_vk_message(vk_user.vk_id, msg, bot_token)
        
        session.commit()

    async def sync_orders(self, session: Session, hours: int = 24) -> Dict[str, Any]:
        """
        РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ Р·Р°РєР°Р·РѕРІ РёР· iiko Р·Р° РїРѕСЃР»РµРґРЅРёРµ N С‡Р°СЃРѕРІ
        """
        companies = session.exec(select(Company).where(Company.iiko_organization_id != None)).all()
        
        # РџРѕР»СѓС‡Р°РµРј РіР»РѕР±Р°Р»СЊРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё РґР»СЏ Р»РѕРіРёРЅР°
        settings_db = session.exec(select(IikoSettings)).first()
        global_api_login = settings_db.api_login if settings_db else None
        global_org_id = settings_db.organization_id if settings_db else None

        if not companies:
            if not global_org_id:
                return {"success": False, "message": "No iiko organizations configured"}
            # РЎРѕР·РґР°РµРј "РІРёСЂС‚СѓР°Р»СЊРЅСѓСЋ" РєРѕРјРїР°РЅРёСЋ РґР»СЏ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё
            companies = [Company(name="Initial Sync", iiko_organization_id=global_org_id)]

        synced_count = 0
        for company in companies:
            try:
                # РћРїСЂРµРґРµР»СЏРµРј Р»РѕРіРёРЅ: РёР· РєРѕРјРїР°РЅРёРё РёР»Рё РіР»РѕР±Р°Р»СЊРЅС‹Р№
                api_login = company.iiko_api_login or global_api_login
                org_id = company.iiko_organization_id

                # 1. РЎРёРЅС…СЂРѕРЅРёР·РёСЂСѓРµРј РёСЃС‚РѕСЂРёС‡РµСЃРєРёРµ Р·Р°РєР°Р·С‹ (СЂР°Р·Р±РёРІР°РµРј РЅР° РѕРєРЅР° РїРѕ 24 С‡Р°СЃР°, С‡С‚РѕР±С‹ РёР·Р±РµР¶Р°С‚СЊ 422 Too many data)
                date_to = datetime.utcnow()
                date_from = date_to - timedelta(hours=hours)
                
                current_from = date_from
                while current_from < date_to:
                    current_to = min(current_from + timedelta(hours=24), date_to)
                    orders_by_date = await iiko_service.get_orders_by_date(
                        current_from, current_to, org_id,
                        api_login=api_login
                    )
                    logger.info(f"Fetched {len(orders_by_date)} historical orders from iiko for {current_from} to {current_to}")
                    for o in orders_by_date:
                        await self.process_iiko_order(session, o, org_id)
                        synced_count += 1
                    current_from = current_to
                
                # 2. РЎРёРЅС…СЂРѕРЅРёР·РёСЂСѓРµРј Р°РєС‚РёРІРЅС‹Рµ Р·Р°РєР°Р·С‹
                active_orders = await iiko_service.get_active_orders(
                    org_id,
                    api_login=api_login
                )
                for o in active_orders:
                    await self.process_iiko_order(session, o, org_id)
                    synced_count += 1
            except Exception as e:
                logger.error(f"Error syncing orders for company {company.name}: {e}")
                
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
        global_org_id = settings_db.organization_id
        resto_url = settings_db.resto_url
        resto_login = settings_db.resto_login
        resto_password = settings_db.resto_password

        synced_emp = 0
        synced_shifts = 0
        
        date_to = datetime.utcnow()
        date_from = date_to - timedelta(days=days)
        
        # 1. Получаем детальные данные из Resto API (если настроено)
        resto_emp_map = {}
        if resto_url and resto_login and resto_password:
            try:
                resto_employees = await iiko_service.get_resto_employees(resto_url, resto_login, resto_password)
                for re in resto_employees:
                    resto_emp_map[re.get("id")] = re
            except Exception as e:
                logger.error(f"Error fetching Resto employees: {e}")

        for company in companies:
            try:
                api_login = company.iiko_api_login or global_api_login
                org_id = company.iiko_organization_id
                
                # 2. Базовая синхронизация из Transport API
                iiko_employees = await iiko_service.get_employees(org_id, api_login=api_login)
                
                # 3. Синхронизация статистики курьеров (доставки)
                courier_stats = {}
                try:
                    c_stats = await iiko_service.get_courier_statistics(date_from, date_to, org_id, api_login=api_login)
                    for cs in c_stats:
                        courier_stats[cs["id"]] = cs["count"]
                except Exception as e:
                    logger.error(f"Error fetching courier stats: {e}")

                for emp_data in iiko_employees:
                    iiko_id = emp_data.get("id")
                    if not iiko_id: continue
                        
                    emp = session.exec(select(Employee).where(Employee.iiko_id == iiko_id)).first()
                    
                    # Обогащаем данными из Resto
                    r_data = resto_emp_map.get(iiko_id, {})
                    
                    name = emp_data.get("name", r_data.get("firstName", "") + " " + r_data.get("lastName", ""))
                    phone = emp_data.get("phone") or r_data.get("phone")
                    email = r_data.get("email")
                    role = emp_data.get("roleId") or r_data.get("role")
                    rate = r_data.get("salary")
                    address = r_data.get("address")
                    
                    # Сбор документов
                    doc_info = {
                        "inn": r_data.get("inn"),
                        "snils": r_data.get("snils"),
                        "passport": f"{r_data.get('passportSeries', '')} {r_data.get('passportNumber', '')}".strip(),
                        "medical_card": r_data.get("medicalCardNumber"),
                        "medical_expired": r_data.get("medicalCardExpired"),
                        "birthday": r_data.get("birthday"),
                        "card_number": r_data.get("cardNumber")
                    }
                    
                    status = "Active" if not emp_data.get("deleted") else "Deleted"
                    
                    if emp:
                        emp.name = name
                        emp.phone = phone or emp.phone
                        emp.email = email or emp.email
                        emp.role = role
                        emp.status = status
                        emp.rate = rate or emp.rate
                        emp.address = address or emp.address
                        emp.document_info = doc_info
                        emp.updated_at = datetime.utcnow()
                    else:
                        emp = Employee(
                            iiko_id=iiko_id,
                            name=name,
                            phone=phone,
                            email=email,
                            role=role,
                            status=status,
                            rate=rate,
                            address=address,
                            document_info=doc_info
                        )
                        session.add(emp)
                    
                    session.flush()
                    synced_emp += 1
                
                # 4. СИНХРОНИЗИРУЕМ СМЕНЫ
                iiko_shifts = await iiko_service.get_shifts(date_from, date_to, org_id, api_login=api_login)
                for shift_data in iiko_shifts:
                    shift_id = shift_data.get("id")
                    if not shift_id: continue
                        
                    emp_iiko_id = shift_data.get("employeeId")
                    emp = session.exec(select(Employee).where(Employee.iiko_id == emp_iiko_id)).first()
                    if not emp: continue 
                        
                    shift = session.exec(select(Shift).where(Shift.iiko_id == shift_id)).first()
                    
                    def parse_time(ts_str):
                        if not ts_str: return None
                        try:
                            if "T" in ts_str:
                                return datetime.fromisoformat(ts_str.replace("Z", "+00:00")).replace(tzinfo=None)
                            return datetime.strptime(ts_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
                        except: return None
                    
                    open_time = parse_time(shift_data.get("openTime"))
                    close_time = parse_time(shift_data.get("closeTime"))
                    if not open_time: continue
                        
                    new_status = "CLOSED" if close_time else "OPEN"
                    
                    # Расчет часов
                    hours = 0.0
                    if open_time and close_time:
                        hours = (close_time - open_time).total_seconds() / 3600.0
                    
                    # Кол-во доставок (если курьер)
                    delivs = courier_stats.get(emp_iiko_id, 0) if new_status == "CLOSED" else 0

                    if shift:
                        shift.date_open = open_time
                        shift.date_close = close_time
                        shift.status = new_status
                        shift.work_hours = round(hours, 2)
                        shift.deliveries_count = delivs if delivs > 0 else shift.deliveries_count
                        shift.updated_at = datetime.utcnow()
                    else:
                        shift = Shift(
                            iiko_id=shift_id,
                            employee_id=emp.id,
                            date_open=open_time,
                            date_close=close_time,
                            status=new_status,
                            work_hours=round(hours, 2),
                            deliveries_count=delivs
                        )
                        session.add(shift)
                    
                    synced_shifts += 1
                
                session.commit()
                
            except Exception as e:
                logger.error(f"Error in sync_employees_full for company {company.name}: {e}")
                session.rollback()
                
        return {"success": True, "employees": synced_emp, "shifts": synced_shifts}

    async def get_employee_stats(self, session: Session, employee_id: int, mode: str = "calendar") -> Dict[str, Any]:
        """
        Расчет статистики сотрудника: календарная неделя или последние 7 дней
        """
        now = datetime.utcnow()
        if mode == "calendar":
            # С понедельника текущей недели
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # Последние 7 дней
            start_date = now - timedelta(days=7)

        shifts = session.exec(
            select(Shift).where(Shift.employee_id == employee_id, Shift.date_open >= start_date)
        ).all()

        total_hours = sum(s.work_hours or 0 for s in shifts)
        total_deliveries = sum(s.deliveries_count for s in shifts)
        shifts_count = len(shifts)

        return {
            "period_start": start_date.isoformat(),
            "shifts_count": shifts_count,
            "total_hours": round(total_hours, 2),
            "total_deliveries": total_deliveries,
            "mode": mode
        }

    async def sync_schedules(self, session: Session, date_from: datetime, date_to: datetime, organization_id: str, api_login: Optional[str] = None):
        """
        Синхронизация запланированного графика смен
        """
        try:
            iiko_schedules = await iiko_service.get_schedules(
                date_from, date_to, organization_id,
                api_login=api_login
            )
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


# Глобальный экземпляр
iiko_sync_service = IikoSyncService()
