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
from app.models.employee import Employee, Shift, Schedule
from app.models.company import Branch, Company
from app.models.customer import Customer
from app.models.vk_user import VkUser
from app.models.vk_activity import VkActivity
from app.models.vk_settings import VkSettings
from app.models.iiko_settings import IikoSettings
from app.services.vk_service import send_vk_message
from app.services.iiko_service import iiko_service
from app.models.payment_type import PaymentType

logger = logging.getLogger(__name__)


class IikoSyncService:
    """Оркестратор синхронизации данных между iiko и локальной БД"""

    async def sync_menu(self, session: Session) -> Dict[str, Any]:
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
        Синхронизация только цен из iiko

        Обновляет цены у существующих товаров, сопоставляя по артикулу (article).
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
                    # Сопоставляем по iiko_id
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
        """
        Обработка данных заказа из iiko.
        Создает новый или обновляет существующий заказ в БД.
        """
        order_id_iiko = iiko_order_data.get("id")
        logger.info(f"Processing iiko order: {order_id_iiko} for org {organization_id}")
        
        if not order_id_iiko:
            logger.warning(f"Order data missing ID: {iiko_order_data}")
            return

        # Получаем терминальные группы для названий (кэшируем в объекте если нужно)
        if not hasattr(self, "_terminal_groups_cache"):
            self._terminal_groups_cache = {}
            
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login if settings_db else None
        
        # Если кэш пуст или старый, обновляем
        if not self._terminal_groups_cache:
            try:
                tgs = await iiko_service.get_terminal_groups(api_login=api_login, organization_id=organization_id)
                for tg_entry in tgs:
                    for tg in tg_entry.get("items", []):
                        self._terminal_groups_cache[tg["id"]] = tg["name"]
                logger.info(f"Terminal groups cache updated: {len(self._terminal_groups_cache)} groups")
            except Exception as e:
                logger.error(f"Failed to fetch terminal groups for naming: {e}")

        # Ищем заказ по iiko_order_id
        order = session.exec(select(Order).where(Order.iiko_order_id == order_id_iiko)).first()
        
        # Пытаемся безопасно извлечь данные заказа
        o_data = iiko_order_data.get("order", iiko_order_data)
        if not isinstance(o_data, dict):
            logger.error(f"Invalid order data type: {type(o_data)}")
            return
        
        # Status mapping
        iiko_status = iiko_order_data.get("creationStatus") or o_data.get("status", "")
        mapped_status = OrderStatus.CONFIRMED
        
        # Расширенный маппинг
        status_map = {
            "New": OrderStatus.NEW,
            "Unconfirmed": OrderStatus.NEW,
            "WaitCooking": OrderStatus.CONFIRMED,
            "ReadyForCooking": OrderStatus.CONFIRMED,
            "CookingStarted": OrderStatus.COOKING,
            "CookingCompleted": OrderStatus.READY,
            "Waiting": OrderStatus.READY,
            "OnWay": OrderStatus.DELIVERING,
            "Delivered": OrderStatus.DELIVERED,
            "Cancelled": OrderStatus.CANCELLED,
            "Error": OrderStatus.CANCELLED,
            "NotConfirmed": OrderStatus.CANCELLED
        }
        mapped_status = status_map.get(str(iiko_status), OrderStatus.CONFIRMED)

        customer_info = o_data.get("customer") or {}
        phone = customer_info.get("phone", "")
        firstname = customer_info.get("name", "")
        surname = customer_info.get("surname", "")
        name = f"{firstname} {surname}".strip() or firstname
        if not name:
            name = customer_info.get("nicName") or "Гость"

        # Парсинг времени
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

        # Курьер (извлекаем ID и имя для привязки)
        courier_name = None
        courier_iiko_id = None
        courier_info = o_data.get("courierInfo")
        if isinstance(courier_info, dict):
            courier = courier_info.get("courier")
            if isinstance(courier, dict):
                courier_name = courier.get("name")
                courier_iiko_id = courier.get("id")

        # Администратор / Кассир
        admin_name = None
        conveyor_details = o_data.get("conveyorDetails")
        if isinstance(conveyor_details, dict):
            cashier = conveyor_details.get("cashier")
            if isinstance(cashier, dict):
                admin_name = cashier.get("name")

        # Адрес и зона доставки
        deliv_point = o_data.get("deliveryPoint", {})
        address_info = deliv_point.get("address", {})
        
        # Собираем адрес
        street_data = address_info.get("street")
        street_name = ""
        if isinstance(street_data, dict):
            street_name = street_data.get("name", "")
        elif isinstance(street_data, str):
            street_name = street_data
            
        city_data = address_info.get("city")
        city_name = ""
        if isinstance(city_data, dict):
            city_name = city_data.get("name", "")
        elif isinstance(city_data, str):
            city_name = city_data
            
        house = address_info.get("house", "")
        flat = address_info.get("flat", "")
        entrance = address_info.get("entrance", "")
        floor = address_info.get("floor", "")
        
        delivery_address = ""
        if city_name:
            delivery_address += f"г. {city_name}, "
        
        if street_name:
            delivery_address += street_name
        
        if house:
            delivery_address += f", д. {house}"
        if entrance:
            delivery_address += f", под. {entrance}"
        if floor:
            delivery_address += f", эт. {floor}"
        if flat:
            delivery_address += f", кв. {flat}"
        
        # Если delivery_address пустой, пробуем собрать из плоских полей или взять готовое
        if not delivery_address.replace(f"г. {city_name}, ", "").strip():
            flat_address = o_data.get("address") or o_data.get("deliveryAddress")
            if flat_address:
                delivery_address = flat_address
            
        # Зона доставки
        delivery_zone = None
        zone_info = deliv_point.get("zone")
        if isinstance(zone_info, dict):
            delivery_zone = zone_info.get("name")
        
        if not delivery_zone:
            delivery_zone = deliv_point.get("externalCartographyId")

        # Тип заказа
        order_type_data = o_data.get("orderType")
        order_type = None
        if isinstance(order_type_data, dict):
            order_type = order_type_data.get("name")
        elif isinstance(order_type_data, str):
            order_type = order_type_data

        # Финансы (Суммы и скидки)
        sum_total = Decimal(str(o_data.get("sum", 0)))
        total_with_discount = Decimal(str(o_data.get("totalSum", sum_total)))
        total_discount = sum_total - total_with_discount
        payment_method = None
        payments = o_data.get("payments", [])
        if payments and isinstance(payments, list):
            payment_method = payments[0].get("paymentType", {}).get("name")
            
        # Извлекаем дополнительные поля
        external_number = o_data.get("externalNumber") or o_data.get("orderNumber")
        source = o_data.get("sourceKey") or o_data.get("source")
        comment = o_data.get("comment")

        # Бонусы
        bonus_spent = Decimal("0")
        bonus_accrued = Decimal("0")
        
        # В iiko API бонусы часто идут в payments как тип "Loyalty"
        is_paid = False
        total_payments_sum = Decimal("0")
        for p in payments:
            pay_sum = Decimal(str(p.get("sum", 0)))
            total_payments_sum += pay_sum
            if p.get("paymentType", {}).get("kind") == "Loyalty":
                bonus_spent += pay_sum
        
        if total_payments_sum >= total_with_discount and total_with_discount > 0:
            is_paid = True
        
        # Если есть информация по бонусам в отдельном поле (зависит от версии API)
        loyalty_info = o_data.get("loyaltyInfo", {})
        if loyalty_info:
            bonus_accrued = Decimal(str(loyalty_info.get("accruedBonuses", 0)))
            
        # Используем данные iiko Card если переданы
        if iiko_card_data and iiko_card_data.get("walletBalances"):
            # Мы можем сохранить баланс клиента в customer_info_details
            if not customer_info:
                customer_info = {}
            customer_info["loyalty_balance"] = iiko_card_data.get("walletBalances")

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
            terminal_group_name = self._terminal_groups_cache.get(terminal_group_id) if terminal_group_id else None
            
            branch_id = None
            if terminal_group_id:
                branch = session.exec(select(Branch).where(Branch.iiko_terminal_id == terminal_group_id)).first()
                if branch:
                    branch_id = branch.id

            order = Order(
                iiko_order_id=order_id_iiko,
                external_number=external_number,
                terminal_group_id=terminal_group_id,
                terminal_group_name=terminal_group_name,
                source=source,
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
                comment=comment,
                payment_method=payment_method,
                is_paid=is_paid,
                city=city_name,
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
            terminal_group_id = iiko_order_data.get("terminalGroupId") or o_data.get("terminalGroupId")
            if terminal_group_id:
                order.terminal_group_id = terminal_group_id
                order.terminal_group_name = self._terminal_groups_cache.get(terminal_group_id) or order.terminal_group_name
                
            order.status = mapped_status
            order.external_number = external_number or order.external_number
            order.source = source or order.source
            order.iiko_creation_time = creation_time or order.iiko_creation_time
            order.expected_time = expected_time or order.expected_time
            order.actual_time = actual_time or order.actual_time
            order.delay_minutes = delay_minutes if delay_minutes > 0 else order.delay_minutes
            order.is_on_time = is_on_time
            order.admin_name = admin_name or order.admin_name
            order.payment_method = payment_method or order.payment_method
            order.is_paid = is_paid
            order.city = city_name or order.city
            order.order_type = order_type or order.order_type
            order.comment = comment or order.comment
            order.total_amount = sum_total
            order.total_with_discount = total_with_discount
            order.total_discount = total_discount
            order.bonus_spent = bonus_spent if bonus_spent > 0 else order.bonus_spent
            order.bonus_accrued = bonus_accrued if bonus_accrued > 0 else order.bonus_accrued
            
            if courier_name:
                if order.courier_name != courier_name:
                    logger.info(f"Обновление курьера для заказа {order.id}: {order.courier_name} -> {courier_name}")
                order.courier_name = courier_name
            
            order.delivery_address = delivery_address or order.delivery_address
            order.delivery_zone = delivery_zone or order.delivery_zone
            order.order_items_details = o_data.get("items", []) or order.order_items_details
            order.discounts_details = o_data.get("discountsInfo", {}) or order.discounts_details
            order.customer_info_details = customer_info or order.customer_info_details
            
            flag_modified(order, "order_items_details")
            flag_modified(order, "discounts_details")
            flag_modified(order, "customer_info_details")
            session.add(order)
        
        # Синхронизация OrderItems
        items_data = o_data.get("items", [])
        if isinstance(items_data, list):
            # Удаляем старые позиции для обновления
            existing_items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
            for ei in existing_items:
                session.delete(ei)
            
            for item_data in items_data:
                product_name = item_data.get("name")
                if not product_name:
                    # Попытка найти во вложенном объекте или использовать заглушку
                    product_name = item_data.get("productName", "Unknown Product")
                
                quantity = int(item_data.get("amount", 1))
                price = Decimal(str(item_data.get("price", 0)))
                total = Decimal(str(item_data.get("sum", price * quantity)))
                
                # Пытаемся найти локальный продукт по iiko_id
                product = None
                p_id_iiko = item_data.get("productId")
                if p_id_iiko:
                    product = session.exec(select(Product).where(Product.iiko_id == p_id_iiko)).first()
                
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
                            OrderStatus.NEW: "Новый",
                            OrderStatus.PREPARING: "Готовится",
                            OrderStatus.READY: "Готов",
                            OrderStatus.DELIVERING: "В пути",
                            OrderStatus.DELIVERED: "Доставлен",
                            OrderStatus.CANCELLED: "Отменен",
                        }.get(mapped_status, str(mapped_status))
                        
                        msg = f"🍣 Статус вашего заказа №{order.id} изменился!\nТекущий статус: {status_text}"
                        if mapped_status == OrderStatus.DELIVERING and order.courier_name:
                            msg += f"\nКурьер: {order.courier_name}"
                            
                        await send_vk_message(vk_user.vk_id, msg, bot_token)
        
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
                        db_zone = DeliveryZone(iiko_id=iiko_id)
                    
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
                    c_stats = await iiko_service.get_courier_statistics(date_from, date_to, org_id, api_login=api_login)
                    for cs in c_stats:
                        courier_stats[cs["id"]] = cs["count"]
                except Exception as e:
                    logger.warning(f"Courier stats failed for {company.name}: {e}")

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
                
                # 3.1. Берем из Resto (самый детальный источник)
                if resto_url and resto_login and resto_password:
                    try:
                        r_attendance = await iiko_service.get_resto_attendance(resto_url, resto_login, resto_password, date_from, date_to)
                        for ra in r_attendance:
                            all_shifts.append({
                                "id": ra["id"],
                                "employee_iiko_id": ra["employeeId"],
                                "date_open": ra["dateOpen"],
                                "date_close": ra["dateClose"],
                                "source": "resto"
                            })
                    except Exception as e:
                        logger.error(f"Resto attendance failed: {e}")

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
                            shift.updated_at = datetime.utcnow()
                        else:
                            shift = Shift(
                                iiko_id=s_id,
                                employee_id=db_emp.id,
                                date_open=d_open,
                                date_close=d_close,
                                status=status,
                                work_hours=hours,
                                deliveries_count=courier_stats.get(e_id, 0)
                            )
                            session.add(shift)
                        
                        session.flush()
                        synced_shifts += 1
                    except Exception as shift_e:
                        logger.error(f"Error syncing shift {s_info.get('id')}: {shift_e}")
                        session.rollback() # Откатываем только эту смену
                        continue

                # 4. СИНХРОНИЗАЦИЯ ГРАФИКОВ
                try:
                    await self.sync_schedules(session, date_from, date_to, org_id, api_login=api_login)
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
