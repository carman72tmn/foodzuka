"""
Синхронизация данных с iiko Cloud
"""
# -*- coding: utf-8 -*-
# Encoding: UTF-8 (Strictly required for FoodTech project)
import logging
import asyncio
import json
import re
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
import zoneinfo
from decimal import Decimal
from sqlmodel import Session, select, delete, update
from sqlalchemy import func
from app.models.category import Category
from app.models.product import Product, ProductSize, ProductModifierGroup, ProductModifier
from app.models.sync_log import SyncLog
# Order, OrderItem, OrderStatus импортируются локально для предотвращения циклических зависимостей
from app.models.employee import Employee, Shift, Schedule, CourierOrder
from app.models.company import Branch, Company, DeliveryZone, CustomPolygon
from app.models.customer import Customer
from app.models.iiko_settings import IikoSettings
from app.models.iiko_loyalty import IikoLoyaltyItem
from app.models.olap_revenue import OlapRevenueRecord
from app.models.role import Role, Permission
from app.models.user import User
from app.core.config import settings
from app.services.iiko_service import iiko_service
from app.utils.phone_utils import normalize_phone
from app.core.logging_utils import log_audit
from app.services.vk_notification_router import vk_notification_router
from app.services.order_status_history_service import append_order_status_history

logger = logging.getLogger(__name__)

class IikoSyncService:
    def __init__(self):
        self.iiko = iiko_service
        self._terminal_groups_cache = {}
        self._last_rev_sync = {} # {org_id: last_time}

    def send_websocket_broadcast_safe(self, payload: dict):
        """Безопасная рассылка WebSocket сообщений из любого контекста (синхронного/асинхронного)"""
        try:
            from app.api.chat import manager
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            if loop.is_running():
                loop.create_task(manager.broadcast(payload))
            else:
                loop.run_until_complete(manager.broadcast(payload))
        except Exception as e:
            logger.error(f"Failed to send websocket broadcast in safe mode: {e}")

    def send_websocket_personal_safe(self, payload: dict, user_id: int):
        """Безопасная персональная отправка WebSocket сообщения из любого контекста"""
        try:
            from app.api.chat import manager
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            if loop.is_running():
                loop.create_task(manager.send_personal_message(payload, user_id))
            else:
                loop.run_until_complete(manager.send_personal_message(payload, user_id))
        except Exception as e:
            logger.error(f"Failed to send websocket personal message in safe mode: {e}")

    async def _sync_addresses_from_local_orders(self, session: Session, customer_id: int, phone: str, days: int = 365):
        """Извлечение адресов из локальной таблицы заказов за последние X дней"""
        from app.models.order import Order
        from app.models.customer import GuestAddress, ClientAddressHistory
        
        def _sync_db_logic():
            date_limit = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Ищем заказы по номеру телефона
            query = select(Order).where(
                Order.customer_phone == phone,
                Order.created_at >= date_limit
            ).order_by(Order.created_at.desc())
            
            orders = session.exec(query).all()
            added_count = 0
            
            for order in orders:
                addr_str = order.delivery_address
                if not addr_str or addr_str == "Самовывоз" or len(addr_str) < 5:
                    continue
                    
                # Проверяем наличие в GuestAddress
                existing = session.exec(
                    select(GuestAddress).where(
                        GuestAddress.customer_id == customer_id,
                        GuestAddress.address == addr_str
                    )
                ).first()
                
                if not existing:
                    new_addr = GuestAddress(
                        customer_id=customer_id,
                        address=addr_str,
                        is_main=False
                    )
                    session.add(new_addr)
                    added_count += 1
                    
                # Также обновляем историю адресов (Laravel)
                if order.street or addr_str:
                    city = order.city or "Тюмень"
                    street = order.street
                    house = order.house
                    
                    if street:
                        existing_history = session.exec(
                            select(ClientAddressHistory).where(
                                ClientAddressHistory.client_id == customer_id,
                                ClientAddressHistory.city == city,
                                ClientAddressHistory.street == street,
                                ClientAddressHistory.house == house
                            )
                        ).first()
                        
                        if not existing_history:
                            new_history = ClientAddressHistory(
                                client_id=customer_id,
                                city=city,
                                settlement=None, # В заказах пока нет отдельного поля для населенного пункта
                                street=street,
                                house=house,
                                entrance=order.entrance,
                                floor=order.floor,
                                apartment=order.flat,
                                doorphone=order.doorphone,
                                address=addr_str,
                                last_used_at=order.created_at.replace(tzinfo=None),
                                orders_count=1
                            )
                            session.add(new_history)
            
            if added_count > 0:
                logger.info(f"Extracted {added_count} new addresses from local orders for customer {customer_id}")
                
                # [FIX] Обновляем поле addresses в основной таблице customers для фронтенда
                # Мы берем все адреса из GuestAddress для этого клиента
                all_guest_addrs = session.exec(
                    select(GuestAddress).where(GuestAddress.customer_id == customer_id)
                ).all()
                if all_guest_addrs:
                    addr_strings = [a.address for a in all_guest_addrs if a.address]
                    # Убираем дубликаты
                    seen = set()
                    unique_addrs = [x for x in addr_strings if not (x in seen or seen.add(x))]
                    
                    # Обновляем объект Customer
                    cust = session.get(Customer, customer_id)
                    if cust:
                        cust.addresses = json.dumps(unique_addrs, ensure_ascii=False)
                        session.add(cust)
            
            return added_count

        return await asyncio.to_thread(_sync_db_logic)

    async def sync_single_customer(
        self, 
        session: Session, 
        phone: str, 
        organization_id: Optional[str] = None, 
        order_id: Optional[int] = None, 
        fast_sync: bool = False,
        bypass_cache: bool = False
    ) -> bool:
        """
        Синхронизация одного клиента из iiko Cloud.
        Если передан order_id, создается снимок данных клиента в заказе.
        """
        from app.models.order import Order
        from app.models.customer import Customer
        
        clean_phone = normalize_phone(phone)
        if not clean_phone:
            return False

        logger.info(f"Syncing single customer: {clean_phone} (Order ID: {order_id})")
        
        def _get_order_and_customer():
            ord_obj = session.get(Order, order_id) if order_id else None
            cust_obj = session.exec(select(Customer).where(Customer.phone == clean_phone)).first()
            return ord_obj, cust_obj

        order, customer = await asyncio.to_thread(_get_order_and_customer)

        try:
            # 1. Данные из Cloud API (iiko Card)
            iiko_data = None
            
            # Если у нас есть ID, пробуем сначала по нему
            if customer and customer.iiko_customer_id:
                try:
                    iiko_data = await self.iiko.get_customer_info(customer_id=customer.iiko_customer_id, organization_id=organization_id)
                except Exception as e:
                    logger.warning(f"Sync by iiko_id {customer.iiko_customer_id} failed: {e}. Falling back to phone search.")
            
            # Если по ID не нашли или его нет - ищем по номеру телефона
            if not iiko_data or not isinstance(iiko_data, dict) or not iiko_data.get("id"):
                iiko_data = await self.iiko.get_customer_info(phone=clean_phone, organization_id=organization_id)
            
            # Финальная проверка типа данных iiko_data
            if not isinstance(iiko_data, dict):
                logger.warning(f"iiko_data is not a dict for {clean_phone}: {iiko_data}")
                iiko_data = {"found": False, "id": None}
            
            if not customer:
                def _create_customer():
                    new_cust = Customer(phone=clean_phone, is_new_guest=True)
                    session.add(new_cust)
                    session.flush()
                    return new_cust
                customer = await asyncio.to_thread(_create_customer)

            if iiko_data and iiko_data.get("id"):
                customer.iiko_customer_id = iiko_data.get("id")
                customer.uid = iiko_data.get("id")
                customer.iiko_id = iiko_data.get("id")
                
                iiko_name = iiko_data.get("name", "")
                iiko_surname = iiko_data.get("surname", "")
                
                is_iiko_name_empty = not iiko_name.strip() or iiko_name.strip().lower() in ("не задано", "гость")
                
                from app.models.vk_user import VkUser
                vk_user = session.exec(
                    select(VkUser)
                    .where((VkUser.phone == clean_phone) | (VkUser.vk_id == customer.vk_user_id))
                    .where(VkUser.is_linked == True)
                ).first()
                
                if is_iiko_name_empty and vk_user and (vk_user.first_name or vk_user.last_name):
                    new_name = vk_user.first_name or "Гость"
                    new_surname = vk_user.last_name or ""
                    
                    customer.name = new_name
                    customer.first_name = new_name
                    customer.surname = new_surname
                    customer.last_name = new_surname
                    
                    logger.info(f"Auto-updating empty/placeholder name for customer {clean_phone} from linked VK profile: {new_name} {new_surname}")
                    
                    try:
                        iiko_payload = {
                            "phone": clean_phone,
                            "name": new_name,
                            "surName": new_surname
                        }
                        if customer.iiko_customer_id:
                            iiko_payload["id"] = customer.iiko_customer_id
                            
                        await self.iiko.create_or_update_customer(iiko_payload)
                        logger.info(f"Successfully synced VK name/surname to iiko for {clean_phone}")
                    except Exception as e:
                        logger.error(f"Error syncing VK name to iiko for {clean_phone}: {e}")
                else:
                    if iiko_data.get("name"):
                        customer.name = iiko_data["name"]
                        customer.first_name = iiko_data["name"]
                    if iiko_data.get("surname"):
                        customer.surname = iiko_data["surname"]
                        customer.last_name = iiko_data["surname"]
                if iiko_data.get("middleName"):
                    customer.middle_name = iiko_data["middleName"]
                if iiko_data.get("email"):
                    customer.email = iiko_data["email"]
                
                # Пол (0: Не указан, 1: Мужской, 2: Женский)
                sex_val = iiko_data.get("sex", 0)
                if sex_val == 1: customer.gender = "Мужской"
                elif sex_val == 2: customer.gender = "Женский"
                else: customer.gender = "Не указан"

                # Бонусы
                if "walletBalances" in iiko_data:
                    total_bonuses = sum(float(b.get("balance", 0)) for b in iiko_data["walletBalances"])
                    customer.bonus_points = Decimal(str(total_bonuses))
                    customer.wallet_balances = iiko_data["walletBalances"]
                
                # Карты лояльности
                cards = iiko_data.get("cards", [])
                if cards:
                    # Берем первую карту как основную
                    customer.card_number = cards[0].get("number")
                    # Сохраняем все номера карт
                    customer.iiko_card_numbers = [c.get("number") for c in cards if c.get("number")]
                
                # Категории
                if "categories" in iiko_data:
                    category_names = [c["name"] for c in iiko_data["categories"] if isinstance(c, dict) and c.get("name")]
                    customer.loyalty_categories = json.dumps(category_names, ensure_ascii=False)
                    customer.iiko_categories = category_names
                
                # Комментарий iiko
                customer.iiko_comment = iiko_data.get("comment")



                # Флаг риска - обновляем только если поле есть в ответе, чтобы не затереть локальный статус
                # Проверяем возможные варианты названия поля в iiko
                risk_keys = ["shouldBeCheckedForRisk", "isHighRisk", "checkedForRisk"]
                risk_found = False
                for rk in risk_keys:
                    if rk in iiko_data:
                        customer.is_high_risk = bool(iiko_data.get(rk))
                        risk_found = True
                        logger.info(f"Customer {clean_phone} risk status updated from iiko field '{rk}': {customer.is_high_risk}")
                        break
                
                if not risk_found:
                    # Если ни одного поля нет, проверяем категории (иногда риск это категория)
                    risk_in_categories = any("риск" in str(cat).lower() or "risk" in str(cat).lower() for cat in (customer.iiko_categories or []))
                    if risk_in_categories:
                        customer.is_high_risk = True
                        logger.info(f"Customer {clean_phone} marked as high risk based on categories: {customer.iiko_categories}")
                    else:
                        logger.debug(f"Customer {clean_phone} risk status not found in iiko data, keeping local value: {customer.is_high_risk}")
                
            # 2. Аналитика из OLAP (количество заказов)
            # При fast_sync пропускаем тяжелые OLAP запросы
            if not fast_sync:
                try:
                    analytics = await self.iiko.get_customer_analytics_olap(clean_phone, session, organization_id=organization_id, bypass_cache=bypass_cache)
                    if analytics and not analytics.get("error"):
                        customer.total_orders_count = analytics.get("orders_count", analytics.get("total_count", 0))
                        customer.total_orders_amount = Decimal(str(analytics.get("total_revenue", analytics.get("total_sum", 0))))
                        customer.total_purchases_sum = customer.total_orders_amount
                        
                        # [NEW] Сохраняем расширенную аналитику в БД
                        customer.total_discount = Decimal(str(analytics.get("total_discount", 0)))
                        customer.total_items = float(analytics.get("total_items", 0))
                        customer.average_check = Decimal(str(analytics.get("average_check", 0)))
                        customer.frequency_days = float(analytics.get("frequency_days", 0))
                        customer.days_since_last_order = analytics.get("days_since_last_order")
                        
                        if analytics.get("first_order_date"):
                            try:
                                customer.first_order_date = datetime.fromisoformat(analytics["first_order_date"])
                            except: pass
                        if analytics.get("last_order_date"):
                            try:
                                customer.last_order_date = datetime.fromisoformat(analytics["last_order_date"])
                            except: pass
                        
                        customer.last_olap_sync_at = datetime.now()
                except Exception as e:
                    logger.warning(f"OLAP sync failed for {clean_phone}: {e}")

            # 3. Адреса
            await self._sync_addresses_from_local_orders(session, customer.id, clean_phone)

            customer.updated_at = datetime.now()
            
            def _save_customer():
                session.add(customer)
                session.flush()
            
            await asyncio.to_thread(_save_customer)

            # --- Создание Snapshot для заказа ---
            if order:
                # Если у клиента в базе 0 заказов или 1 (этот), считаем его новым
                is_new_guest_snap = (customer.total_orders_count or 0) <= 1
                
                snapshot = {
                    "name": f"{customer.first_name or ''} {customer.last_name or ''}".strip() or customer.name or "Гость",
                    "is_new_guest": is_new_guest_snap,
                    "is_high_risk": bool(customer.is_high_risk),
                    "total_orders_count": customer.total_orders_count or 0,
                    "bonus_balance": float(customer.bonus_points or 0),
                    "bonus_points": float(customer.bonus_points or 0),  # Синоним
                    "iiko_notes": customer.iiko_comment or "",
                    "notes": customer.notes or "",  # Заметки
                    "phone": customer.phone or clean_phone or "",  # Телефон
                    "categories": customer.iiko_categories or [],  # Категории
                    "sync_date": datetime.now(timezone.utc).isoformat(),
                    "sync_status": "success"
                }
                if order.customer_id != customer.id:
                    order.customer_id = customer.id
                    logger.info(f"Updated customer_id to {customer.id} for order {order.id} during customer sync")
                order.customer_info_details = snapshot
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(order, "customer_info_details")
                session.add(order)
                logger.info(f"Created customer snapshot for order {order_id}")

            await asyncio.to_thread(session.commit)
            return True

        except Exception as e:
            logger.error(f"Error in sync_single_customer for {phone}: {e}")
            if order:
                order.customer_info_details = {
                    "sync_error": True, 
                    "error_msg": str(e),
                    "sync_date": datetime.now(timezone.utc).isoformat()
                }
                def _save_err():
                    session.add(order)
                    session.commit()
                await asyncio.to_thread(_save_err)
            return False

    @staticmethod
    def clean_str(val):
        if val is None:
            return ""
        
        # Если это не строка, преобразуем в строку
        s = str(val).strip()
        
        # Проверка на служебные значения, которые iiko может присылать как строки
        if s.lower() in ("none", "null", "", "-", "--", ".", "undefined", "nan"):
            return ""
            
        # Защита от mojibake: если строка случайно декодирована как ISO-8859-1 вместо UTF-8
        # (Обычно это выглядит как РђРђРђРђРђ...)
        try:
            # Если в строке много символов из расширенной латиницы, но нет кириллицы
            # это может быть неверно декодированный UTF-8
            if any(ord(c) > 127 and ord(c) < 255 for c in s) and not any(1040 <= ord(c) <= 1103 for c in s):
                test_s = s.encode('latin-1').decode('utf-8')
                if any(1040 <= ord(c) <= 1103 for c in test_s):
                    return test_s
        except Exception:
            pass
            
        return s

    def format_address(self, address_data: Any, city: Optional[str] = None, fmt: str = "components") -> str:
        """
        Форматирует адрес iiko. 
        Приоритет: line1 (если fmt='line1' или 'line3'), иначе сборка по компонентам.
        Всегда гарантирует наличие указанных клиентом подъезда, этажа, квартиры и кода домофона.
        """
        if not address_data:
            return ""

        if not isinstance(address_data, dict):
            return str(address_data)

        # 1. Извлекаем компоненты с очисткой
        line1 = self.clean_str(address_data.get('line1'))
        city_val = self.clean_str(address_data.get('city') or city)
        street_val = address_data.get('street')
        street = street_val.get('name') if isinstance(street_val, dict) else self.clean_str(street_val)
        
        house = self.clean_str(address_data.get('house'))
        if house in ["0", "-", "None", "null"]:
            house = None
        flat = self.clean_str(address_data.get('flat'))
        if flat in ["0", "-", "None", "null"]:
            flat = None
        entrance = self.clean_str(address_data.get('entrance'))
        if entrance in ["0", "-", "None", "null"]:
            entrance = None
        floor = self.clean_str(address_data.get('floor'))
        if floor in ["0", "-", "None", "null"]:
            floor = None
        door_phone = self.clean_str(address_data.get('doorphone'))
        if door_phone in ["0", "-", "None", "null"]:
            door_phone = None
        building = self.clean_str(address_data.get('building'))
        if building in ["0", "-", "None", "null"]:
            building = None

        # 2. Логика для fmt="line1" / "line3" (одной строкой)
        if fmt in ["line1", "line3"] and line1:
            addr = self.clean_str(line1)
            # Интеллектуальное добавление отсутствующих элементов через regex
            extras = []
            if entrance:
                # Проверяем, есть ли уже указание подъезда с данным номером
                has_ent = bool(re.search(rf'(?i)(?:под(?:ъезд|\.|\s*)|(?<=[,\s])п\.\s*)\s*{re.escape(str(entrance))}\b', addr))
                if not has_ent:
                    extras.append(f"под. {entrance}")
            if floor:
                # Проверяем, есть ли уже указание этажа с данным номером
                has_fl = bool(re.search(rf'(?i)(?:эт(?:аж|\.|\s*)|(?<=[,\s])э\.\s*)\s*{re.escape(str(floor))}\b', addr))
                if not has_fl:
                    extras.append(f"эт. {floor}")
            if flat:
                # Проверяем, есть ли уже указание квартиры/офиса с данным номером
                has_flt = bool(re.search(rf'(?i)(?:кв(?:артира|\.|\s*)|оф(?:ис|\.|\s*)|пом(?:ещение|\.|\s*))\s*{re.escape(str(flat))}\b', addr))
                if not has_flt:
                    extras.append(f"кв. {flat}")
            if door_phone:
                # Проверяем, есть ли уже указание домофона с данным кодом
                has_dp = bool(re.search(rf'(?i)(?:код|домофон|д\/ф|код\s*домофона)\s*[:#]?\s*{re.escape(str(door_phone))}\b', addr))
                if not has_dp:
                    extras.append(f"код {door_phone}")
                
            if extras:
                addr = f"{addr}, {', '.join(extras)}"
            return addr

        # 3. Классическая сборка (город, улица, дом, корпус, подъезд, этаж, квартира, домофон)
        if not street and not house and line1:
            return line1

        parts = []
        if city_val:
            c = self.clean_str(city_val)
            parts.append(c if c.lower().startswith("г.") else f"г. {c}")
            
        if street:
            s = self.clean_str(street)
            if not any(p in s.lower() for p in ["улица", "ул.", "пр.", "пер.", "бул.", "проезд", "тракт", "шоссе"]):
                s = f"ул. {s}"
            parts.append(s)
            
        if house: parts.append(f"д. {house}")
        if building: parts.append(f"корп. {building}")
        if entrance: parts.append(f"под. {entrance}")
        if floor: parts.append(f"эт. {floor}")
        if flat: parts.append(f"кв. {flat}")
        if door_phone: parts.append(f"код {door_phone}")

        return ", ".join(parts) if parts else (line1 or "Адрес не указан")

    def _get_tz(self, session: Session):
        """Получение часового пояса из настроек"""
        from app.core.datetime_utils import get_tz
        return get_tz(session)

    async def sync_menu(self, session: Session) -> Dict[str, Any]:
        """Полная синхронизация меню (Категории + Товары)"""
        def _init_log():
            log = SyncLog(
                sync_type="menu",
                status="running",
                details="Запуск синхронизации меню",
                created_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            session.add(log)
            session.commit()
            session.refresh(log)
            return log

        log = await asyncio.to_thread(_init_log)
        
        try:
            from app.services.iiko_service import iiko_service
            
            def _get_settings():
                return session.exec(select(IikoSettings)).first()
            
            settings = await asyncio.to_thread(_get_settings)
            api_login = settings.api_login if settings else None
            org_id = settings.organization_id if settings else None
            
            # 1. Получаем данные из API (асинхронно)
            res = None
            use_fallback = False
            
            if settings and settings.use_v2_menu:
                logger.info("Syncing from Cloud Menu (API v2)")
                
                # Получаем резервные цены из классической номенклатуры
                nomenclature_prices = {}
                try:
                    logger.info("Fetching fallback nomenclature prices...")
                    nomenclature = await iiko_service.get_nomenclature(api_login=api_login, organization_id=org_id)
                    for prod_data in nomenclature.get("products", []):
                        prod_id = prod_data.get("id")
                        if not prod_id:
                            continue
                        if "price" in prod_data and prod_data["price"] is not None:
                            nomenclature_prices[(prod_id, None)] = float(prod_data["price"])
                        for sp in prod_data.get("sizePrices", []):
                            size_id = sp.get("sizeId")
                            price_val = sp.get("price", {}).get("currentPrice") if isinstance(sp.get("price"), dict) else sp.get("price")
                            if price_val is not None:
                                nomenclature_prices[(prod_id, size_id)] = float(price_val)
                except Exception as e:
                    logger.warning(f"Failed to fetch fallback nomenclature prices: {e}")
                    nomenclature_prices = {}

                price_cat_id = None if settings.price_source == "menu" else settings.price_category_id
                logger.info(f"get_menu_v2 with price_category_id={price_cat_id} (source={settings.price_source})")

                try:
                    menu_data = await iiko_service.get_menu_v2(
                        api_login=api_login, 
                        organization_id=org_id,
                        external_menu_id=settings.external_menu_id,
                        price_category_id=price_cat_id
                    )
                    
                    # Проверяем, пустое ли меню
                    cats_list = menu_data.get("itemCategories") or menu_data.get("groups") or []
                    has_items = False
                    for cat in cats_list:
                        if cat.get("items") or cat.get("products"):
                            has_items = True
                            break
                            
                    if not has_items:
                        logger.warning("External Menu v2 returned 0 items. Fallback to Classic Nomenclature.")
                        use_fallback = True
                    else:
                        # 2. Обрабатываем в БД (выносим в поток)
                        res = await asyncio.to_thread(self._sync_from_external_menu_sync, session, menu_data, log.id, nomenclature_prices)
                except Exception as menu_err:
                    logger.error(f"Error fetching V2 menu: {menu_err}. Fallback to Classic Nomenclature.")
                    use_fallback = True
            
            if not settings or not settings.use_v2_menu or use_fallback:
                logger.info("Syncing from Nomenclature (Classic API)")
                nomenclature = await iiko_service.get_nomenclature(api_login=api_login, organization_id=org_id)
                # 2. Обрабатываем в БД (выносим в поток)
                res = await asyncio.to_thread(self._sync_from_nomenclature_sync, session, nomenclature, log.id)
            
            def _final_update():
                session.refresh(log)
                msg = f"Синхронизация завершена успешно: {res.get('categories', 0)} категорий, {res.get('products', 0)} товаров"
                log.status = "success"
                log.details = msg
                session.add(log)
                session.commit()
                return msg

            message = await asyncio.to_thread(_final_update)
            
            response = {
                "success": True,
                "categories_synced": res.get("categories", 0),
                "products_synced": res.get("products", 0),
                "message": f"Синхронизация завершена успешно: {res.get('categories', 0)} категорий, {res.get('products', 0)} товаров"
            }
            
            def _final_success():
                log.status = "success"
                log.details = response["message"]
                session.add(log)
                session.commit()
                log_audit(action="manual_sync", resource_type="menu", message=response["message"])

            await asyncio.to_thread(_final_success)
            
            # Запуск фонового скачивания изображений товаров
            try:
                from app.tasks.general_tasks import download_product_images_task
                download_product_images_task.delay()
                logger.info("Запущена фоновая задача скачивания картинок товаров")
            except Exception as task_err:
                logger.error(f"Не удалось запустить задачу скачивания картинок: {task_err}")
                
            return response

        except Exception as e:
            logger.error(f"Menu sync failed: {e}", exc_info=True)
            
            def _final_error():
                log.status = "error"
                log.details = str(e)
                session.add(log)
                session.commit()
                log_audit(action="manual_sync_failed", resource_type="menu", message=str(e))

            await asyncio.to_thread(_final_error)
            
            return {
                "success": False,
                "error": str(e),
                "message": f"Ошибка синхронизации: {str(e)}"
            }

    async def sync_categories_only(self, session: Session) -> Dict[str, Any]:
        """Синхронизация только категорий из iiko (вызывает полную синхронизацию меню)"""
        res = await self.sync_menu(session)
        return {
            "success": res.get("success", False),
            "categories_synced": res.get("categories_synced", 0),
            "message": f"Синхронизировано категорий: {res.get('categories_synced', 0)}"
        }

    async def sync_prices(self, session: Session) -> Dict[str, Any]:
        """Синхронизация только цен товаров из iiko"""
        try:
            from app.services.iiko_service import iiko_service
            def _get_settings():
                return session.exec(select(IikoSettings)).first()
            
            settings = await asyncio.to_thread(_get_settings)
            api_login = settings.api_login if settings else None
            org_id = settings.organization_id if settings else None
            
            res = None
            use_fallback = False
            
            if settings and settings.use_v2_menu:
                # Получаем резервные цены из классической номенклатуры
                nomenclature_prices = {}
                try:
                    logger.info("Fetching fallback nomenclature prices...")
                    nomenclature = await iiko_service.get_nomenclature(api_login=api_login, organization_id=org_id)
                    for prod_data in nomenclature.get("products", []):
                        prod_id = prod_data.get("id")
                        if not prod_id:
                            continue
                        if "price" in prod_data and prod_data["price"] is not None:
                            nomenclature_prices[(prod_id, None)] = float(prod_data["price"])
                        for sp in prod_data.get("sizePrices", []):
                            size_id = sp.get("sizeId")
                            price_val = sp.get("price", {}).get("currentPrice") if isinstance(sp.get("price"), dict) else sp.get("price")
                            if price_val is not None:
                                nomenclature_prices[(prod_id, size_id)] = float(price_val)
                except Exception as e:
                    logger.warning(f"Failed to fetch fallback nomenclature prices: {e}")
                    nomenclature_prices = {}

                price_cat_id = None if settings.price_source == "menu" else settings.price_category_id
                logger.info(f"get_menu_v2 with price_category_id={price_cat_id} (source={settings.price_source})")

                try:
                    menu_data = await iiko_service.get_menu_v2(
                        api_login=api_login, 
                        organization_id=org_id,
                        external_menu_id=settings.external_menu_id,
                        price_category_id=price_cat_id
                    )
                    
                    # Проверяем, пустое ли меню
                    cats_list = menu_data.get("itemCategories") or menu_data.get("groups") or []
                    has_items = False
                    for cat in cats_list:
                        if cat.get("items") or cat.get("products"):
                            has_items = True
                            break
                            
                    if not has_items:
                        logger.warning("External Menu v2 returned 0 items. Fallback to Classic Nomenclature for prices.")
                        use_fallback = True
                    else:
                        res = await asyncio.to_thread(self._update_prices_from_v2, session, menu_data, nomenclature_prices)
                except Exception as menu_err:
                    logger.error(f"Error fetching V2 menu for prices: {menu_err}. Fallback to Classic Nomenclature.")
                    use_fallback = True
                    
            if not settings or not settings.use_v2_menu or use_fallback:
                nomenclature = await iiko_service.get_nomenclature(api_login=api_login, organization_id=org_id)
                res = await asyncio.to_thread(self._update_prices_from_nomenclature, session, nomenclature)
            
            return {
                "success": True,
                "prices_synced": res.get("count", 0),
                "message": f"Цены обновлены для {res.get('count', 0)} товаров"
            }
        except Exception as e:
            logger.error(f"Price sync failed: {e}")
            return {"success": False, "error": str(e), "prices_synced": 0}

    async def sync_stop_lists(self, session: Session) -> Dict[str, Any]:
        """Синхронизация стоп-листов"""
        try:
            from app.services.iiko_service import iiko_service
            def _get_settings():
                return session.exec(select(IikoSettings)).first()
            
            settings = await asyncio.to_thread(_get_settings)
            org_id = settings.organization_id if settings else None
            
            stop_lists = await iiko_service.get_stop_lists(organization_id=org_id)
            res = await asyncio.to_thread(self._process_stop_lists, session, stop_lists)
            
            return {
                "success": True, 
                "message": f"Стоп-листы обновлены. На стопе: {res.get('count', 0)} позиций",
                "stopped_count": res.get("count", 0)
            }
        except Exception as e:
            logger.error(f"Stop-list sync failed: {e}")
            return {"success": False, "error": str(e), "stopped_count": 0}

    async def sync_payment_types(self, session: Session) -> Dict[str, Any]:
        """Синхронизация типов оплаты"""
        try:
            from app.services.iiko_service import iiko_service
            from app.models.payment_type import PaymentType
            
            def _get_settings():
                return session.exec(select(IikoSettings)).first()
            
            settings = await asyncio.to_thread(_get_settings)
            api_login = settings.api_login if settings else None
            org_id = settings.organization_id if settings else None
            
            types = await iiko_service.get_payment_types(api_login=api_login, organization_id=org_id)
            
            def _db_update():
                count = 0
                for t_data in types:
                    pt_id = t_data.get("id")
                    if not pt_id: continue
                    
                    pt = session.exec(select(PaymentType).where(PaymentType.iiko_id == pt_id)).first()
                    if pt:
                        pt.name = t_data.get("name", pt.name)
                        pt.kind = t_data.get("paymentTypeKind", pt.kind)
                        pt.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    else:
                        pt = PaymentType(
                            iiko_id=pt_id,
                            name=t_data.get("name"),
                            kind=t_data.get("paymentTypeKind"),
                            is_active=True
                        )
                        session.add(pt)
                    count += 1
                session.commit()
                return count
            
            count = await asyncio.to_thread(_db_update)
            return {"success": True, "count": count, "message": f"Синхронизировано {count} типов оплаты"}
        except Exception as e:
            logger.error(f"Payment types sync failed: {e}")
            return {"success": False, "error": str(e)}

    async def sync_roles(self, session: Session) -> Dict[str, Any]:
        """Синхронизация ролей (должностей) из iiko Resto"""
        try:
            # Получаем настройки iiko для Resto API
            def _get_settings():
                return session.exec(select(IikoSettings)).first()
            
            settings_db = await asyncio.to_thread(_get_settings)
            if not settings_db or not settings_db.resto_url:
                return {"success": False, "error": "Настройки iiko Resto не найдены"}
            
            # Получаем роли из iiko
            iiko_roles = await self.iiko.get_resto_roles(
                resto_url=settings_db.resto_url,
                resto_login=settings_db.resto_login,
                resto_password=settings_db.resto_password
            )
            
            if not iiko_roles:
                return {"success": False, "error": "Не удалось получить роли из iiko"}
            
            count = 0
            for r_data in iiko_roles:
                # Ищем по внешнему ID или коду
                iiko_id = r_data.get("id")
                name = r_data.get("name")
                code = r_data.get("code") or iiko_id # Если кода нет, используем ID
                
                # Ищем существующую роль
                existing = session.exec(
                    select(Role).where((Role.code == code) | (Role.iiko_id == iiko_id))
                ).first()
                
                if not existing:
                    # Создаем новую роль (не системную)
                    new_role = Role(
                        name=name,
                        code=code,
                        iiko_id=iiko_id,
                        description=f"Импортировано из iiko: {name}",
                        is_system=False
                    )
                    session.add(new_role)
                    count += 1
                else:
                    # Обновляем имя, если это не системная роль
                    if not existing.is_system:
                        existing.name = name
                        existing.iiko_id = iiko_id
                        session.add(existing)
            
            session.commit()
            return {"success": True, "count": count, "message": f"Синхронизировано {count} новых ролей"}
            
        except Exception as e:
            logger.error(f"Roles sync failed: {e}")
            return {"success": False, "error": str(e)}


    def _update_prices_from_v2(self, session: Session, menu_data: Dict[str, Any], nomenclature_prices: Optional[Dict[tuple, float]] = None) -> Dict[str, Any]:
        count = 0
        if nomenclature_prices is None:
            nomenclature_prices = {}
        cats = menu_data.get("itemCategories") or menu_data.get("groups") or []
        for cat in cats:
            for item in (cat.get("items") or cat.get("products") or []):
                item_id = item.get("itemId") or item.get("id")
                sizes = item.get("itemSizes", [])
                price = 0
                if sizes:
                    p = sizes[0].get("prices", [])
                    if p: price = p[0].get("price", 0)
                elif "price" in item:
                    price = item["price"]
                
                # Применяем fallback
                size0_id = sizes[0].get("sizeId") if sizes else None
                fallback_price = nomenclature_prices.get((item_id, size0_id))
                if (price is None or price == 0) and fallback_price is not None:
                    price = fallback_price

                prod = session.exec(select(Product).where(Product.iiko_id == item_id)).first()
                if prod:
                    prod.price = float(price or 0)
                    prod.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    count += 1
                    
                    # Обновляем цены размеров
                    if sizes:
                        for s_data in sizes:
                            s_id = s_data.get("sizeId") or item_id
                            s_price = 0
                            if s_data.get("prices"): 
                                s_price = s_data["prices"][0].get("price", 0)
                            
                            # Fallback для размера
                            fallback_size_price = nomenclature_prices.get((item_id, s_data.get("sizeId")))
                            if (s_price is None or s_price == 0) and fallback_size_price is not None:
                                s_price = fallback_size_price
                                
                            psize = session.exec(select(ProductSize).where(ProductSize.product_id == prod.id, ProductSize.iiko_id == s_id)).first()
                            if psize:
                                psize.price = float(s_price or 0)
                                session.add(psize)
        session.commit()
        return {"count": count}

    def _update_prices_from_nomenclature(self, session: Session, nomenclature: Dict[str, Any]) -> Dict[str, Any]:
        count = 0
        products = nomenclature.get("products", [])
        for p_data in products:
            p_id = p_data.get("id")
            price = 0
            if p_data.get("sizePrices"):
                price = p_data["sizePrices"][0].get("price", {}).get("currentPrice", 0)
            
            prod = session.exec(select(Product).where(Product.iiko_id == p_id)).first()
            if prod:
                prod.price = float(price)
                prod.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                count += 1
        session.commit()
        return {"count": count}

    def _process_stop_lists(self, session: Session, stop_lists: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка стоп-листов: двусторонняя синхронизация (постановка и автоматическое снятие со стопа)"""
        if isinstance(stop_lists, list):
            stop_lists = stop_lists[0] if stop_lists else {}
            
        terminal_stop_lists = stop_lists.get("terminalGroupStopLists", []) if isinstance(stop_lists, dict) else []
        stopped_ids = set()
        
        for t_sl in terminal_stop_lists:
            for item in t_sl.get("items", []):
                p_id = item.get("productId")
                if p_id:
                    stopped_ids.add(str(p_id))
        
        now_dt = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Находим товары по прямому iiko_id или через ProductSize
        stopped_prod_ids = set()
        if stopped_ids:
            stopped_prods = session.exec(select(Product).where(Product.iiko_id.in_(list(stopped_ids)))).all()
            for p in stopped_prods:
                stopped_prod_ids.add(p.id)
            
            stopped_sizes = session.exec(select(ProductSize).where(ProductSize.iiko_id.in_(list(stopped_ids)))).all()
            for s in stopped_sizes:
                if s.product_id:
                    stopped_prod_ids.add(s.product_id)

        # 1. ПОСТАНОВКА НА СТОП
        placed_count = 0
        if stopped_prod_ids:
            for p in session.exec(select(Product).where(Product.id.in_(list(stopped_prod_ids)))).all():
                if not p.is_stopped or p.is_available:
                    p.is_stopped = True
                    p.is_available = False
                    p.stopped_at = now_dt
                    p.updated_at = now_dt
                    session.add(p)
                    placed_count += 1

        # 2. АВТОМАТИЧЕСКОЕ СНЯТИЕ СО СТОПА (для позиций, ушедших из стоп-листа iiko)
        unstopped_query = select(Product).where(Product.is_stopped == True)
        if stopped_prod_ids:
            unstopped_query = unstopped_query.where(~Product.id.in_(list(stopped_prod_ids)))
        
        unstopped_prods = session.exec(unstopped_query).all()
        released_count = 0
        for p in unstopped_prods:
            p.is_stopped = False
            p.is_available = True
            p.stopped_at = None
            p.updated_at = now_dt
            session.add(p)
            released_count += 1

        session.commit()
        logger.info(f"Stop-lists processed: {len(stopped_prod_ids)} in iiko, {placed_count} placed on stop, {released_count} released from stop")
        return {
            "count": len(stopped_prod_ids),
            "placed_count": placed_count,
            "released_count": released_count
        }

    def _sync_from_external_menu_sync(self, session: Session, menu_data: Dict[str, Any], log_id: int, nomenclature_prices: Optional[Dict[tuple, float]] = None) -> Dict[str, Any]:
        """Логика обработки внешнего меню iiko (Синхронная версия для потока)"""
        if not menu_data:
            return {"categories": 0, "products": 0}
        
        if nomenclature_prices is None:
            nomenclature_prices = {}

        categories_synced = 0
        products_synced = 0

        # Рекурсивный сбор всех категорий и подкатегорий из дерева меню
        def _collect_categories(cat_nodes, parent_iiko_id=None):
            collected = []
            for c in cat_nodes:
                c_id = c.get("id")
                if not c_id:
                    continue
                c_copy = dict(c)
                c_copy["_parent_iiko_id"] = parent_iiko_id
                collected.append(c_copy)
                sub = c.get("groups") or c.get("itemCategories") or c.get("categories") or []
                if sub:
                    collected.extend(_collect_categories(sub, parent_iiko_id=c_id))
            return collected

        root_cats = menu_data.get("itemCategories") or menu_data.get("groups") or []
        all_cats = _collect_categories(root_cats)

        # 1. Синхронизация категорий (Проход 1: Создание/Обновление полей)
        for cat_data in all_cats:
            cat_id = cat_data.get("id")
            if not cat_id: continue
            
            cat = session.exec(select(Category).where(Category.iiko_id == cat_id)).first()
            if cat:
                if not getattr(cat, "lock_name", False):
                    cat.name = cat_data["name"]
                cat.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            else:
                cat = Category(
                    iiko_id=cat_id,
                    name=cat_data["name"],
                    is_active=True
                )
                session.add(cat)
            categories_synced += 1
        session.commit()

        # Проход 2: Синхронизация иерархии (parent_id)
        for cat_data in all_cats:
            cat_id = cat_data.get("id")
            if not cat_id: continue
            
            parent_iiko_id = cat_data.get("_parent_iiko_id") or cat_data.get("parentGroupId") or cat_data.get("parentId")
            cat = session.exec(select(Category).where(Category.iiko_id == cat_id)).first()
            if cat and not getattr(cat, "lock_parent", False):
                if parent_iiko_id:
                    parent_cat = session.exec(select(Category).where(Category.iiko_id == parent_iiko_id)).first()
                    cat.parent_id = parent_cat.id if parent_cat else None
                else:
                    cat.parent_id = None
        session.commit()

        # 2. Синхронизация товаров (из категорий и корневых элементов)
        processed_item_ids = set()
        items_to_process = []

        # Сбор элементов из всех категорий
        for cat_data in all_cats:
            iiko_cat_id = cat_data.get("id")
            local_cat = session.exec(select(Category).where(Category.iiko_id == iiko_cat_id)).first()
            category_id = local_cat.id if local_cat else None
            
            c_items = cat_data.get("items") or cat_data.get("products") or []
            for item_data in c_items:
                items_to_process.append((item_data, category_id))

        # Сбор элемента из корня меню (если применимо)
        root_items = menu_data.get("products") or menu_data.get("items") or []
        for item_data in root_items:
            cat_iiko_id = item_data.get("categoryId") or item_data.get("groupId")
            local_cat = session.exec(select(Category).where(Category.iiko_id == cat_iiko_id)).first() if cat_iiko_id else None
            category_id = local_cat.id if local_cat else None
            items_to_process.append((item_data, category_id))

        for item_data, category_id in items_to_process:
            item_id = item_data.get("itemId") or item_data.get("id")
            if not item_id or item_id in processed_item_ids:
                continue
            processed_item_ids.add(item_id)
            
            prod = session.exec(select(Product).where(Product.iiko_id == item_id)).first()
            
            sizes = item_data.get("itemSizes", [])
            price = 0
            nutritions = {}
            weight = None
            
            # Определяем размер по умолчанию или первый размер с ненулевой ценой
            target_size = None
            if sizes:
                target_size = next((s for s in sizes if s.get("isDefault") or s.get("default")), None)
                if not target_size:
                    for s in sizes:
                        s_pr = 0
                        if s.get("prices"): s_pr = s["prices"][0].get("price", 0)
                        if s_pr > 0:
                            target_size = s
                            break
                if not target_size:
                    target_size = sizes[0]

            if target_size:
                prices = target_size.get("prices", [])
                if prices: price = prices[0].get("price", 0)
                nutritions = target_size.get("nutritionPerHundredGrams") or target_size.get("nutritions") or {}
                weight = target_size.get("portionWeightGrams")
            elif "price" in item_data: 
                price = item_data["price"]

            # Fallback цены из классической номенклатуры
            target_size_id = target_size.get("sizeId") if target_size else None
            fallback_price = nomenclature_prices.get((item_id, target_size_id)) or nomenclature_prices.get((item_id, None))
            if (price is None or price == 0) and fallback_price is not None:
                price = fallback_price

            # Если цена все еще 0, но в других размерах есть цена > 0 - берем минимальную положительную
            if (price is None or price == 0) and sizes:
                positive_prices = []
                for s in sizes:
                    sp_list = s.get("prices", [])
                    if sp_list and sp_list[0].get("price", 0) > 0:
                        positive_prices.append(float(sp_list[0]["price"]))
                    elif nomenclature_prices.get((item_id, s.get("sizeId"))):
                        positive_prices.append(float(nomenclature_prices[(item_id, s.get("sizeId"))]))
                if positive_prices:
                    price = min(positive_prices)

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
                "image_url": item_data.get("buttonImageUrl") or (sizes[0].get("buttonImageUrl") if sizes else None),
                "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
            }

            if prod:
                for key, val in updated_data.items(): setattr(prod, key, val)
            else:
                prod = Product(iiko_id=item_id, **updated_data)
                session.add(prod)
            
            session.flush()

            # Размеры
            session.exec(delete(ProductSize).where(ProductSize.product_id == prod.id))
            
            if sizes:
                has_default = any(s_data.get("isDefault", False) or s_data.get("default", False) for s_data in sizes)
                for idx, s_data in enumerate(sizes):
                    s_price = 0
                    if s_data.get("prices"): s_price = s_data["prices"][0].get("price", 0)
                    
                    fallback_size_price = nomenclature_prices.get((item_id, s_data.get("sizeId")))
                    if (s_price is None or s_price == 0) and fallback_size_price is not None:
                        s_price = fallback_size_price

                    is_def = s_data.get("isDefault", False) or s_data.get("default", False)
                    if not has_default and idx == 0:
                        is_def = True

                    s_weight = s_data.get("portionWeightGrams")

                    session.add(ProductSize(
                        product_id=prod.id,
                        iiko_id=s_data.get("sizeId") or item_id,
                        name=s_data.get("sizeName") or "Стандарт",
                        price=float(s_price or 0),
                        weight_grams=int(s_weight) if s_weight else None,
                        is_default=is_def
                    ))
            else:
                session.add(ProductSize(
                    product_id=prod.id,
                    iiko_id=item_id,
                    name="Стандарт",
                    price=float(price or 0),
                    weight_grams=int(weight) if weight else None,
                    is_default=True
                ))

            # Модификаторы
            target_size = next((s for s in sizes if s.get("isDefault") or s.get("default")), sizes[0] if sizes else None)
            mod_groups = []
            if target_size and (target_size.get("itemModifierGroups") or target_size.get("modifierGroups")):
                mod_groups = target_size.get("itemModifierGroups") or target_size.get("modifierGroups") or []
            elif item_data.get("itemModifierGroups") or item_data.get("modifierGroups"):
                mod_groups = item_data.get("itemModifierGroups") or item_data.get("modifierGroups") or []

            if mod_groups:
                old_groups = session.exec(select(ProductModifierGroup).where(ProductModifierGroup.product_id == prod.id)).all()
                old_group_ids = [g.id for g in old_groups]
                if old_group_ids:
                    session.exec(delete(ProductModifier).where(ProductModifier.group_id.in_(old_group_ids)))
                
                session.exec(delete(ProductModifierGroup).where(ProductModifierGroup.product_id == prod.id))
                
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
                        
                        fallback_modifier_price = nomenclature_prices.get((m_item["itemId"], None))
                        if (m_price is None or m_price == 0) and fallback_modifier_price is not None:
                            m_price = fallback_modifier_price

                        session.add(ProductModifier(
                            group_id=new_group.id,
                            iiko_id=m_item["itemId"],
                            name=m_item["name"],
                            price=float(m_price or 0),
                            min_amount=m_item.get("minAmount", 0),
                            max_amount=m_item.get("maxAmount", 1),
                            default_amount=m_item.get("defaultAmount", 0)
                        ))
            products_synced += 1
        
        session.commit()
        return {"categories": categories_synced, "products": products_synced}

    def _sync_from_nomenclature_sync(self, session: Session, nomenclature: Dict[str, Any], log_id: int) -> Dict[str, Any]:
        """Обработка классической номенклатуры iiko (Синхронная версия для потока)"""
        if not nomenclature:
            return {"categories": 0, "products": 0}

        categories_synced = 0
        products_synced = 0

        # 1. Категории (Проход 1: Создание/Обновление полей, кроме иерархии)
        if "groups" in nomenclature:
            for g in nomenclature["groups"]:
                if g.get("isDeleted"): continue
                cat = session.exec(select(Category).where(Category.iiko_id == g["id"])).first()
                if cat:
                    if not getattr(cat, "lock_name", False):
                        cat.name = g["name"]
                    cat.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                else:
                    session.add(Category(iiko_id=g["id"], name=g["name"], is_active=True))
                categories_synced += 1
            session.commit()

            # Проход 2: Иерархия (parent_id) с учетом lock_parent
            for g in nomenclature["groups"]:
                if g.get("isDeleted"): continue
                cat_id = g["id"]
                parent_iiko_id = g.get("parentGroup")
                if parent_iiko_id:
                    parent_cat = session.exec(select(Category).where(Category.iiko_id == parent_iiko_id)).first()
                    if parent_cat:
                        cat = session.exec(select(Category).where(Category.iiko_id == cat_id)).first()
                        if cat and not getattr(cat, "lock_parent", False):
                            cat.parent_id = parent_cat.id
                else:
                    cat = session.exec(select(Category).where(Category.iiko_id == cat_id)).first()
                    if cat and not getattr(cat, "lock_parent", False):
                        cat.parent_id = None
            session.commit()

        # 2. Товары
        size_map = {s["id"]: s["name"] for s in nomenclature.get("sizes", [])}
        if "products" in nomenclature:
            for p in nomenclature["products"]:
                if p.get("type") == "Service": continue
                prod = session.exec(select(Product).where(Product.iiko_id == p["id"])).first()
                
                category_id = None
                if p.get("parentGroup"):
                    local_cat = session.exec(select(Category).where(Category.iiko_id == p["parentGroup"])).first()
                    if local_cat: category_id = local_cat.id
                
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
                    "image_url": p.get("buttonImageUrl") or (p.get("imageLinks")[0] if p.get("imageLinks") else None),
                    "updated_at": datetime.now(timezone.utc).replace(tzinfo=None)
                }

                if prod:
                    for key, val in updated_data.items(): setattr(prod, key, val)
                else:
                    prod = Product(iiko_id=p["id"], **updated_data)
                    session.add(prod)
                
                session.flush()
                
                # Размеры
                session.exec(delete(ProductSize).where(ProductSize.product_id == prod.id))
                if p.get("sizePrices"):
                    for sp in p["sizePrices"]:
                        s_id = sp.get("sizeId")
                        session.add(ProductSize(
                            product_id=prod.id,
                            iiko_id=s_id or "default",
                            name=size_map.get(s_id, "Стандарт"),
                            price=float(sp.get("price", {}).get("currentPrice", 0)),
                            is_default=(len(p["sizePrices"]) == 1 or sp.get("isDefault", False))
                        ))
                products_synced += 1
            session.commit()
        return {"categories": categories_synced, "products": products_synced}

    async def ensure_customer_from_order(
        self, 
        session: Session, 
        phone: str, 
        name: Optional[str] = None, 
        surname: Optional[str] = None, 
        order_info: Optional[str] = None, 
        order_date: Optional[datetime] = None, 
        telegram_id: Optional[int] = None,
        order_status: Optional[str] = None,
        address: Optional[str] = None,
        email: Optional[str] = None,
        loyalty_data: Optional[Dict[str, Any]] = None,
        order_id_iiko: Optional[str] = None,
        city: Optional[str] = None,
        street: Optional[str] = None,
        house: Optional[str] = None,
        flat: Optional[str] = None,
        total_sum: float = 0,
        order_db_id: Optional[int] = None
    ):
        """
        Проверка существования гостя по номеру телефона и создание/обновление карточки.
        Используется при поступлении заказа (webhook или API).
        """
        from app.models.order import OrderStatus
        
        # Очистка и нормализация номера телефона (РФ формат +7XXXXXXXXXX)
        clean_phone = normalize_phone(phone)
        
        if not clean_phone:
            logger.warning(f"Attempted to ensure customer with empty phone: {phone}")
            return None

        logger.info(f"==> Customer Sync Trigger: Phone={clean_phone}, Order={order_info}")

        def _find_customer():
            cust = session.exec(select(Customer).where(Customer.phone == clean_phone)).first()
            if not cust:
                from app.models.customer import GuestPhone
                gp = session.exec(select(GuestPhone).where(GuestPhone.phone == clean_phone)).first()
                if gp:
                    cust = session.get(Customer, gp.customer_id)
            return cust

        customer = await asyncio.to_thread(_find_customer)

        # Работа с датами (приведение к UTC без TZ для БД)
        current_order_time = order_date or datetime.now(timezone.utc).replace(tzinfo=None)
        if current_order_time.tzinfo:
            current_order_time = current_order_time.astimezone(timezone.utc).replace(tzinfo=None)
        
        # Формирование детальной информации о заказе для заметок
        if not order_info:
            order_info = f"Заказ от {current_order_time.strftime('%d.%m.%Y %H:%M')}"
            if total_sum > 0:
                order_info += f" на сумму {total_sum:.0f} руб."
            if address:
                order_info += f" (Адрес: {address})"
        
        # Добавление данных программы лояльности
        if loyalty_data:
            extra_info = []
            if loyalty_data.get("discount_total"):
                extra_info.append(f"Скидка: {loyalty_data['discount_total']}р")
            if loyalty_data.get("free_products"):
                extra_info.append(f"Подарки: {', '.join(loyalty_data['free_products'])}")
            if loyalty_data.get("errors"):
                extra_info.append(f"Ошибки лоял.: {', '.join(loyalty_data['errors'])}")
            
            if extra_info:
                if "(" in order_info:
                    order_info = order_info.rstrip(")") + "; " + "; ".join(extra_info) + ")"
                else:
                    order_info += " (" + "; ".join(extra_info) + ")"

        if not customer:
            # Регистрация НОВОГО гостя
            logger.info(f"==> REGISTRATION: New guest phone {clean_phone}. Name: {name} {surname or ''}")
            customer = Customer(
                phone=clean_phone,
                name=name or "Гость",
                surname=surname,
                first_name=name,
                last_name=surname,
                email=email,
                telegram_id=telegram_id,
                last_order_date=current_order_time,
                last_iiko_order_id=order_id_iiko,
                is_new_guest=True,
                # Считаем выполненным заказом только если статус подходящий
                total_orders_count=1 if order_status in (OrderStatus.closed, OrderStatus.delivered) else 0,
                total_orders_amount=Decimal(str(total_sum)) if order_status in (OrderStatus.closed, OrderStatus.delivered) else Decimal("0"),
                total_purchases_sum=Decimal(str(total_sum)) if order_status in (OrderStatus.closed, OrderStatus.delivered) else Decimal("0"),
                updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            def _create_customer():
                session.add(customer)
                session.flush()
                return customer.id

            await asyncio.to_thread(_create_customer)
            logger.info(f"Created new customer card: ID={customer.id}, Phone={clean_phone}")
        else:
            # ОБНОВЛЕНИЕ существующей карточки
            logger.info(f"==> UPDATE: Customer ID={customer.id} found. Processing order info.")
            
            # Заполняем имя/фамилию если они пустые
            if name and (not customer.name or customer.name == "Гость"):
                customer.name = name
                customer.first_name = name
            if surname and (not customer.surname or customer.surname == ""):
                customer.surname = surname
                customer.last_name = surname
            
            def _update_stats():
                # Обновляем статистику если это новый заказ
                is_new_order_data = (customer.last_iiko_order_id != order_id_iiko)
                
                if not customer.last_order_date or current_order_time >= customer.last_order_date:
                    if is_new_order_data and order_status in (OrderStatus.closed, OrderStatus.delivered):
                        customer.total_orders_count = (customer.total_orders_count or 0) + 1
                        customer.total_orders_amount = (customer.total_orders_amount or Decimal("0")) + Decimal(str(total_sum))
                        customer.total_purchases_sum = (customer.total_purchases_sum or Decimal("0")) + Decimal(str(total_sum))
                    
                    customer.last_order_date = current_order_time
                    customer.last_iiko_order_id = order_id_iiko
                
                # Снимаем флаг нового гостя
                if order_status in (OrderStatus.closed, OrderStatus.delivered):
                    customer.is_new_guest = False
            
            await asyncio.to_thread(_update_stats)

        # Сохранение адресов (поддержка старой схемы и Laravel)
        if address and address != "Самовывоз":
            def _save_addresses():
                from app.models.customer import GuestAddress, ClientAddressHistory
                
                # Legacy GuestAddress
                existing_addr = session.exec(
                    select(GuestAddress).where(
                        GuestAddress.customer_id == customer.id,
                        GuestAddress.address == address
                    )
                ).first()
                if not existing_addr:
                    session.add(GuestAddress(customer_id=customer.id, address=address, is_main=False))
                
                # Laravel ClientAddressHistory
                if city or street or house:
                    existing_history = session.exec(
                        select(ClientAddressHistory).where(
                            ClientAddressHistory.client_id == customer.id,
                            ClientAddressHistory.city == city,
                            ClientAddressHistory.street == street,
                            ClientAddressHistory.house == house
                        )
                    ).first()
                    
                    if not existing_history:
                        session.add(ClientAddressHistory(
                            client_id=customer.id,
                            city=city,
                            street=street,
                            house=house,
                            apartment=flat,
                            last_used_at=datetime.now(timezone.utc).replace(tzinfo=None)
                        ))
                    else:
                        existing_history.last_used_at = datetime.now(timezone.utc).replace(tzinfo=None)
                        if flat and not existing_history.apartment:
                            existing_history.apartment = flat
                        session.add(existing_history)

                customer.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                session.add(customer)
                session.commit()

            await asyncio.to_thread(_save_addresses)
        else:
            def _commit_customer():
                customer.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                session.add(customer)
                session.commit()
            await asyncio.to_thread(_commit_customer)
        
        try:
            # Получаем ID организации для API
            from app.models.iiko_settings import IikoSettings
            def _get_settings():
                return session.exec(select(IikoSettings)).first()
            settings_db = await asyncio.to_thread(_get_settings)
            org_id = settings_db.organization_id if settings_db else None
            
            # Запуск синхронизации лояльности через Celery фоновую задачу во избежание таймаутов БД сессии
            from app.tasks.customer_tasks import sync_single_customer_task
            sync_single_customer_task.delay(clean_phone, order_id=order_db_id, fast_sync=True)
            logger.info(f"Dispatched background customer sync for phone {clean_phone} during order creation")
        except Exception as sync_err:
            logger.warning(f"Synchronous sync failed for {clean_phone}: {sync_err}. Falling back to background task if possible.")
            # Если прямой вызов упал, на всякий случай пробуем в фоне
            try:
                from app.tasks.customer_tasks import sync_single_customer_task
                sync_single_customer_task.delay(clean_phone, order_id=order_db_id, fast_sync=True)
            except:
                pass
        
        # Запускаем фоновое принудительное обновление аналитики со сбросом кэша при любом получении заказа
        try:
            from app.tasks.customer_tasks import sync_single_customer_task
            sync_single_customer_task.delay(clean_phone, fast_sync=False, bypass_cache=True)
            logger.info(f"Triggered background full-sync for phone {clean_phone} during order creation")
        except Exception as bg_err:
            logger.warning(f"Failed to trigger background full-sync for phone {clean_phone}: {bg_err}")

        # Автоматический поиск и привязка аккаунта MAX для клиента без max_user_id
        if customer and customer.phone and not customer.max_user_id:
            try:
                from app.tasks.customer_tasks import link_customer_max_task
                link_customer_max_task.delay(customer.id)
                logger.info(f"Triggered link_customer_max_task for customer #{customer.id} ({customer.phone})")
            except Exception as max_task_err:
                logger.warning(f"Failed to trigger link_customer_max_task: {max_task_err}")
            
        return customer

    async def process_iiko_order(self, session: Session, iiko_order_data: Dict[str, Any], organization_id: str, iiko_card_data: Optional[Dict[str, Any]] = None):
        from app.models.order import Order, OrderItem, OrderStatus # Локальный импорт для предотвращения UnboundLocalError и циклических зависимостей
        from sqlalchemy.orm.attributes import flag_modified as sql_flag_modified
        """Интегрированный метод обработки заказа: консолидированная и очищенная версия"""
        if not iiko_order_data:
            logger.warning("Received empty order data from iiko")
            return

        # Игнорируем ошибки создания заказа (creationStatus == "Error" или order == null)
        creation_status = iiko_order_data.get("creationStatus")
        o_data = iiko_order_data.get("order")
        if creation_status in ("Error", "Fail") or ("order" in iiko_order_data and iiko_order_data["order"] is None):
            order_id = iiko_order_data.get("id") or (o_data.get("id") if o_data else None)
            ext_num = iiko_order_data.get("externalNumber") or (o_data.get("number") if o_data else None)
            logger.warning(f"Игнорируем обработку заказа {order_id} (внешний № {ext_num}) из-за статуса ошибки создания (creationStatus: {creation_status})")
            return
            
        try:
            is_new = False
            is_status_changed = False
            
            # 1. Базовые данные заказа
            order_id_iiko = iiko_order_data.get("id")
            o_data = iiko_order_data.get("order")
            if not o_data:
                o_data = iiko_order_data
            
            if not order_id_iiko:
                order_id_iiko = o_data.get("id")

            if not order_id_iiko:
                logger.warning(f"Order data missing ID. Keys available: {list(o_data.keys())}. Full data sample: {str(o_data)[:500]}")
                return
            
            # Логируем начало обработки для диагностики
            ext_num = o_data.get("number") or o_data.get("externalNumber")
            logger.info(f"==> Processing Iiko Order: ID={order_id_iiko}, Num={ext_num}, Status={o_data.get('status')}")
            
            settings_db = await asyncio.to_thread(lambda: session.exec(select(IikoSettings)).first())
            city_from_settings = settings_db.city_name if settings_db else "Тюмень"

            # Очистка строк (используем глобальный метод класса для защиты кодировки)
            clean = self.clean_str

            # 2. Статус и внешние номера
            raw_status = clean(o_data.get("status") or iiko_order_data.get("creationStatus"))
            raw_status_lower = raw_status.lower() if raw_status else ""
            external_number = clean(o_data.get("number") or o_data.get("externalNumber")) or None

            # 3. Таймзона и время
            from app.core.datetime_utils import get_tz_name
            tz_name = await asyncio.to_thread(get_tz_name, session)
            try:
                import zoneinfo
                tz = zoneinfo.ZoneInfo(tz_name)
            except Exception:
                import zoneinfo
                tz = zoneinfo.ZoneInfo("Asia/Yekaterinburg")
            
            current_time_tz = datetime.now(tz)
            
            # Поиск даты создания в разных местах (iiko API может менять структуру)
            iiko_creation_time_raw = (
                (o_data.get("creationInfo") or {}).get("creationDate") or 
                o_data.get("creationDate") or
                o_data.get("whenCreated")
            )
            iiko_creation_time = None
            if iiko_creation_time_raw:
                try:
                    # Принимаем время как UTC 0, если есть пометка Z или смещение.
                    # Это исправит проблему 5-часового смещения в админке.
                    if 'Z' in iiko_creation_time_raw or '+' in iiko_creation_time_raw or '-' in iiko_creation_time_raw[10:]:
                        # ISO формат с Z или смещением парсится как aware datetime
                        dt = datetime.fromisoformat(iiko_creation_time_raw.replace('Z', '+00:00'))
                        iiko_creation_time = dt.astimezone(timezone.utc).replace(tzinfo=None)
                    else:
                        # Если время без пояса (naive), считаем его локальным для заведения
                        dt = datetime.fromisoformat(iiko_creation_time_raw)
                        iiko_creation_time = dt.replace(tzinfo=tz).astimezone(timezone.utc).replace(tzinfo=None)
                    
                    logger.info(f"Parsed iiko time (naive UTC): raw={iiko_creation_time_raw}, result={iiko_creation_time}")
                except Exception as e:
                    logger.error(f"Error parsing iiko creation time {iiko_creation_time_raw}: {e}")

            # 4. Клиент
            c_data = o_data.get("customer") or {}
            c_first = clean(c_data.get("name"))
            c_last = clean(c_data.get("surname"))
            full_customer_name = f"{c_first or ''} {c_last or ''}".strip() or "Гость"
            phone = clean(o_data.get("phone") or c_data.get("phone"))


            # 5. Адрес
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
            
            city = city or city_from_settings or "Тюмень"

            # Экстракция компонентов для БД (сливаем данные из address и deliveryPoint)
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

            # 6. РАСЧЕТ ОПЛАТЫ И ЛОЯЛЬНОСТИ (для передачи в карточку клиента)
            sum_total = Decimal(str(o_data.get("sum") or 0))
            total_with_discount = Decimal(str(o_data.get("totalSum") or o_data.get("total") or sum_total))
            disc_list = o_data.get("discounts") or o_data.get("concessions") or []
            total_discount = sum([Decimal(str((d or {}).get("sum") or 0)) for d in disc_list if isinstance(d, dict)])
            
            loyalty_payload = {
                "discount_total": o_data.get("discountTotal") or float(total_discount),
                "discounts": disc_list,
                "errors": o_data.get("loyaltyProgramErrors") or [],
                "free_products": o_data.get("freeProducts") or [],
                "lost_gift": o_data.get("lostGift") or []
            }

            # 7. ФОРМИРОВАНИЕ АДРЕСА
            addr_fmt = (settings_db.address_format or "components") if settings_db else "components"
            building = clean(raw_addr.get("building")) or clean(raw_addr_dp.get("building"))
            line1_raw = clean(raw_addr.get("line1")) or clean(raw_addr_dp.get("line1")) or clean(raw_addr.get("line3")) or clean(raw_addr_dp.get("line3")) or clean(raw_addr.get("addressString")) or clean(raw_addr_dp.get("addressString"))
            addr_comment = clean(dp.get("comment")) or clean(raw_addr.get("comment")) or clean(raw_addr_dp.get("comment"))

            merged_addr_obj = {
                "city": city,
                "street": {"name": street_name} if street_name else None,
                "house": house,
                "building": building,
                "flat": flat,
                "entrance": entrance,
                "floor": floor,
                "doorphone": doorphone,
                "line1": line1_raw,
                "comment": addr_comment
            }
            
            try:
                delivery_address = self.format_address(merged_addr_obj, city=city, fmt=addr_fmt)
            except TypeError as e:
                logger.error(f"Address formatting failed: {e}. Falling back to default.")
                delivery_address = self.format_address(merged_addr_obj, fmt=addr_fmt)
            
            # Если в итоге адрес пустой или "Самовывоз", проверяем другие поля
            is_only_city = not delivery_address or delivery_address.strip() in [city, f"г. {city}", "г.Тюмень", "Тюмень"]
            
            if is_only_city:
                # Если все еще пусто, пробуем deliveryAddress на внешнем уровне
                addr_str = self.clean_str(o_data.get("deliveryAddress"))
                if addr_str and len(addr_str) > len(city or "") + 2:
                    delivery_address = addr_str
                    has_new_address = True
                else:
                    delivery_address = "Самовывоз"
            else:
                has_new_address = True
            
            # Если в итоге все равно только город, но есть addressString на внешнем уровне - пробуем его
            if not has_new_address:
                addr_str = self.clean_str(o_data.get("deliveryAddress"))
                if addr_str and len(addr_str) > len(city or "") + 2:
                    delivery_address = addr_str
                    has_new_address = True

            # 8. Резервируем базовые данные (клиент будет создан/обновлен ниже в п.10 с полным составом заказа)
            order_info_short = f"Заказ #{external_number or order_id_iiko[:8]}"

            # 9. ОБРАБОТКА ПЛАТЕЖЕЙ
            payments = o_data.get("payments") or []
            total_paid = 0
            pm_list_detailed = []
            pm_list = []
            
            bonus_spent_from_payments = 0
            for p in payments:
                if not isinstance(p, dict): continue
                pt = p.get("paymentType") or {}
                pn = pt.get("name") if isinstance(pt, dict) else clean(pt)
                pk = (clean(p.get("paymentTypeKind") or p.get("kind") or (pt.get("kind") if isinstance(pt, dict) else "") or "") or "").lower()
                if not pn: pn = pk or "Тип оплаты"
                
                psum = float(p.get("sum") or 0)
                
                is_processed_externally = bool(p.get("isProcessedExternally", False) or p.get("processedExternally", False))
                is_prepay = bool(p.get("isPrepay", False) or p.get("prepay", False))
                status_payment = p.get("status", "").lower()
                
                # Считаем платеж проведенным строго по подтверждению от iiko:
                # - либо подтвержден внешней платежной системой (isProcessedExternally)
                # - либо проведен как предоплата (isPrepay)
                # - либо статус платежа в iiko явно processed/closed/success
                # - либо заказ полностью закрыт в кассе iiko (closed)
                is_processed = bool(
                    is_processed_externally 
                    or is_prepay 
                    or status_payment in ["processed", "closed", "success"]
                    or raw_status_lower == "closed"
                )
                
                # Платежи iikoCard (бонусы)
                if pk == "iikocard" or "бонус" in (pn or "").lower():
                    bonus_spent_from_payments += psum
                elif is_processed:
                    # Только реальные проведенные денежные оплаты идут в сумму оплаченного
                    total_paid += psum
                
                pm_list_detailed.append({
                    "name": pn,
                    "kind": pk,
                    "sum": psum,
                    "is_processed": is_processed,
                    "is_prepay": is_prepay
                })
                if pn: pm_list.append(pn)
            
            # Учитываем iiko Cloud processedPaymentsSum (сумма подтвержденных кассой iiko платежей)
            processed_params = float(o_data.get("processedPaymentsSum") or 0)
            if processed_params > total_paid:
                total_paid = processed_params

            # Считаем остаток к оплате
            left_to_pay = max(Decimal('0.00'), total_with_discount - Decimal(str(round(total_paid, 2))))
            
            # СТРОГИЙ ПРИОРИТЕТ IIKO ДЛЯ СТАТУСА ОПЛАТЫ:
            # 1. Если заказ закрыт в кассе iiko - он всегда 100% оплачен полностью
            if raw_status_lower == "closed":
                is_paid = True
                total_paid = float(total_with_discount)
                left_to_pay = Decimal('0.00')
                payment_status = "paid"
                payment_status_label = "Оплачен (iiko)"
            # 2. Если сумма проведенных кассой оплат покрывает заказ
            elif total_with_discount > 0 and left_to_pay <= Decimal('0.00') and total_paid >= float(total_with_discount):
                is_paid = True
                left_to_pay = Decimal('0.00')
                payment_status = "paid"
                payment_status_label = "Оплачен (iiko)"
            # 3. Частичная оплата (внесена часть суммы, остаток > 0)
            elif total_paid > 0 and left_to_pay > 0:
                is_paid = False
                payment_status = "partially_paid"
                payment_status_label = "Частично оплачен"
            # 4. Не оплачен
            else:
                is_paid = False
                payment_status = "unpaid"
                payment_status_label = "Не оплачен"
            
            payment_method = ", ".join(list(set(pm_list))) or "Не указан"

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

            # Если заказ закрыт в iiko - он точно оплачен (для нашей CRM)
            if not is_paid and mapped_status == OrderStatus.closed:
                is_paid = True
                left_to_pay = Decimal('0.00')
                logger.info(f"Order {order_id_iiko}: Paid via status enforcement ('{mapped_status}')")


            # 7. Курьер, тип и дополнительные данные
            courier_name = "Не назначен"
            courier_iiko_id = None
            ci = o_data.get("courierInfo") or {}
            if isinstance(ci, dict):
                c_obj = ci.get("courier") or {}
                if isinstance(c_obj, dict):
                    fn = clean(c_obj.get("firstName") or c_obj.get("name")) or ""
                    ln = clean(c_obj.get("lastName")) or ""
                    courier_name = " ".join(filter(None, [fn, ln])).strip() or clean(ci.get("courierName")) or "Не назначен"
                    courier_iiko_id = c_obj.get("id")
                    # Дополнительная защита от "None" в конце имени
                    if " None" in courier_name:
                        courier_name = courier_name.replace(" None", "").strip()

                    # Сопоставление с локальным справочником сотрудников Employee
                    from app.models.employee import Employee
                    if courier_iiko_id:
                        def _get_emp_by_iiko():
                            return session.exec(select(Employee).where(Employee.iiko_id == str(courier_iiko_id))).first()
                        emp_match = await asyncio.to_thread(_get_emp_by_iiko)
                        if emp_match and emp_match.name:
                            courier_name = emp_match.name
                    elif courier_name and courier_name != "Не назначен":
                        def _get_emp_by_name():
                            emp_direct = session.exec(select(Employee).where(Employee.name == courier_name)).first()
                            if emp_direct:
                                return emp_direct
                            target_words = {w for w in courier_name.lower().split() if len(w) > 2 and w not in ["курьер", "courier"]}
                            if target_words:
                                for e_item in session.exec(select(Employee)).all():
                                    e_words = {w for w in (e_item.name or "").lower().split() if len(w) > 2}
                                    if target_words & e_words:
                                        return e_item
                            return None
                        emp_match = await asyncio.to_thread(_get_emp_by_name)
                        if emp_match and emp_match.name:
                            courier_name = emp_match.name
                            courier_iiko_id = emp_match.iiko_id

            stype = (clean(o_data.get("orderServiceType")) or "").lower()
            if not stype and isinstance(o_data.get("orderType"), dict):
                stype = (clean((o_data.get("orderType") or {}).get("orderServiceType")) or "").lower()
            
            order_type = "Доставка"
            if any(x in stype for x in ["pickup", "client", "самовывоз"]): 
                order_type = "Самовывоз"
            elif any(x in stype for x in ["common", "table", "зале", "ресторане"]): 
                order_type = "В ресторане"

            # Новые поля для полной информативности
            source = clean(o_data.get("source")) or "iiko"
            def parse_dt(dt_str):
                if not dt_str:
                    return None
                try:
                    # ISO 8601 с Z или смещением
                    if 'Z' in dt_str or '+' in dt_str or '-' in dt_str[10:]:
                        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                        return dt.astimezone(timezone.utc).replace(tzinfo=None)
                    # Наивное время - считаем локальным для заведения
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
            
            # Фолбэк на верхний уровень объекта заказа (iiko Cloud API v2)
            if not expected_time:
                expected_time = parse_dt(o_data.get("completeBefore"))
            if not actual_time:
                actual_time = parse_dt(o_data.get("actualDate"))
            
            # 8. Финальные флаги и сохранение
            delay = di.get("delayMinutes")
            admin_name = None
            op = o_data.get("operator")
            if isinstance(op, dict):
                admin_name = self.clean_str(op.get("name"))
            if not admin_name:
                admin_name = self.clean_str((o_data.get("conformationInfo") or {}).get("confirmedBy"))
            if not admin_name:
                admin_name = self.clean_str((o_data.get("confirmationInfo") or {}).get("confirmedBy"))

            # 8. Сохранение
            def _get_order():
                return session.exec(select(Order).where(Order.iiko_order_id == order_id_iiko)).first()
            order = await asyncio.to_thread(_get_order)

            # ЗАПРЕТ ОБНОВЛЕНИЯ СТАТУСА ДЛЯ ЗАКРЫТЫХ ЗАКАЗОВ (но разрешаем обновление деталей для учета лояльности)
            if order and order.status in (OrderStatus.closed, OrderStatus.cancelled, OrderStatus.delivered):
                # Если в БД заказ уже закрыт/доставлен/отменен, а из iiko приходит промежуточный статус (waiting/cooking/etc),
                # мы НЕ откатываем статус назад в активный.
                if mapped_status not in (OrderStatus.closed, OrderStatus.cancelled, OrderStatus.delivered):
                    mapped_status = order.status
                elif order.status != mapped_status:
                    logger.info(f"Order {order.id}: Status update ({order.status} -> {mapped_status})")
                    order.status = mapped_status
                    append_order_status_history(
                        order=order,
                        new_status=mapped_status,
                        comment=f"iiko: {raw_status} (terminal update)",
                        custom_time=current_time_tz,
                        tz=tz
                    )
                if mapped_status == OrderStatus.closed:
                    is_paid = True
                    left_to_pay = Decimal('0.00')
                # Продолжаем выполнение для обновления деталей (discounts, items, bonus_spent)


            # Сохраняем старые значения для уведомлений об изменениях
            old_amount = float(getattr(order, 'total_with_discount', 0)) if order else 0
            old_items_count = len(getattr(order, 'order_items_details', []) or []) if order else 0
            old_time = getattr(order, 'expected_time', None) if order else None
            old_address = getattr(order, 'delivery_address', None) if order else None
            old_courier = getattr(order, 'courier_name', None) if order else None
            old_cooking_time = getattr(order, 'cooking_time_minutes', None) if order else None
            old_payments_details = getattr(order, 'payments_details', None) if order else None
            old_order_type = getattr(order, 'order_type', None) if order else None
            old_status = getattr(order, 'status', None) if order else None

            # Определяем филиал (branch) по terminalGroupId
            terminal_group_id = o_data.get("terminalGroupId")
            branch_id = 1 # Fallback
            terminal_group_name = None
            
            if terminal_group_id:
                def _get_branch():
                    return session.exec(select(Branch).where(Branch.iiko_terminal_id == terminal_group_id)).first()
                branch = await asyncio.to_thread(_get_branch)
                if branch:
                    branch_id = branch.id
                    terminal_group_name = branch.name
            
            if not order:
                is_new = True
                order = Order(iiko_order_id=order_id_iiko, branch_id=branch_id)
                order.iiko_creation_time = iiko_creation_time
                append_order_status_history(
                    order=order,
                    new_status=mapped_status,
                    comment=f"iiko: {raw_status}" if raw_status else "Синхронизирован",
                    custom_time=current_time_tz,
                    tz=tz
                )
            else:
                # Если заказ уже есть, обновляем branch_id если он изменился
                order.branch_id = branch_id
                if order.status != mapped_status:
                    is_status_changed = True
            
            # --- ЛОГИКА ОПРЕДЕЛЕНИЯ ASAP / ПРЕДЗАКАЗ ---
            raw_comment = self.clean_str(o_data.get("comment"))
            comment_lower = (raw_comment or "").lower()
            
            # Базовые значения из iiko (приоритет - флагу isAsap)
            final_is_asap = bool(o_data.get("isAsap", True))
            
            # 1. Если флаг isAsap явно False - это предзаказ
            if o_data.get("isAsap") is False:
                final_is_asap = False
            
            # 2. Если есть время готовности и оно значительно отличается от времени создания
            if expected_time and iiko_creation_time:
                diff_mins = (expected_time - iiko_creation_time).total_seconds() / 60
                # Если разница более 90 минут - скорее всего это предзаказ (на время)
                if diff_mins > 90:
                    final_is_asap = False
            
            # 3. Дополнительные проверки по комментарию (если флаг все еще True)
            if final_is_asap:
                if "на время" in comment_lower or "предзаказ" in comment_lower:
                    final_is_asap = False
            
            # 4. Если в комментарии НЕТ ключевых слов предзаказа, но есть другой текст, 
            # и при этом время доставки близко к времени создания - оставляем ASAP
            elif raw_comment and "на время" not in comment_lower and "предзаказ" not in comment_lower:
                if expected_time and iiko_creation_time:
                    diff_mins = (expected_time - iiko_creation_time).total_seconds() / 60
                    if diff_mins < 90:
                        final_is_asap = True

            # 3. Если время готовности изменилось в процессе (сравниваем с уже существующим заказом в БД)
            if order and order.expected_time and expected_time:
                # Безопасное вычитание naive/aware
                oe = order.expected_time.replace(tzinfo=None) if order.expected_time.tzinfo else order.expected_time
                ne = expected_time.replace(tzinfo=None) if expected_time.tzinfo else expected_time
                if abs((oe - ne).total_seconds()) > 60:
                    final_is_asap = False

            # Финальные флаги
            is_asap = final_is_asap
            is_on_time = not final_is_asap

            # Восстанавливаем логику истории статусов
            if order.id and order.status != mapped_status:
                append_order_status_history(
                    order=order,
                    new_status=mapped_status,
                    comment=f"iiko: {raw_status}",
                    custom_time=current_time_tz,
                    tz=tz
                )

            # Маппинг всех полей
            order.status = mapped_status
            order.external_number = external_number or order.external_number
            order.customer_name = full_customer_name
            order.customer_phone = phone
            order.courier_name = courier_name
            
            # Обновляем адресные поля только если в новом пакете есть реальный адрес
            # ИЛИ если в БД адрес еще не заполнен (город не считается заполненным адресом)
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
                order.address_parts = merged_addr_obj
                sql_flag_modified(order, "address_parts")
            
            # Извлекаем примечание к адресу
            address_comment_raw = dp.get("comment") or raw_addr.get("comment") or raw_addr_dp.get("comment")
            
            # Извлекаем дополнительную информацию и прочее из верхнего уровня или externalData
            additional_info_raw = o_data.get("additionalInfo")
            other_info_raw = o_data.get("otherInfo") or o_data.get("other")
            
            ext_data = o_data.get("externalData") or []
            for item in ext_data:
                if isinstance(item, dict):
                    k = (item.get("key") or "").lower().strip()
                    v = item.get("value")
                    if not additional_info_raw and any(x in k for x in ["доп", "additional"]):
                        additional_info_raw = v
                    if not other_info_raw and any(x in k for x in ["проч", "other"]):
                        other_info_raw = v

            order.address_comment = clean(address_comment_raw) or None
            order.additional_info = clean(additional_info_raw) or None
            order.other_info = clean(other_info_raw) or None

            orig_comment = clean(o_data.get("comment"))
            if bonus_spent_from_payments > 0:
                bonus_note = f"[Оплата бонусами: {bonus_spent_from_payments:.0f} руб.]"
                order.comment = f"{orig_comment} {bonus_note}" if orig_comment else bonus_note
            else:
                order.comment = orig_comment or None
            
            # Статус оплаты берется строго из кассы iiko (приоритетные значения iiko).
            # Не сбрасываем в оплачен только на основании доставки, пока нет подтверждения кассы/платежа.
            order.total_amount, order.total_with_discount, order.total_discount = sum_total, total_with_discount, total_discount
            order.total_paid = Decimal(str(round(total_paid, 2)))
            order.left_to_pay = left_to_pay
            order.is_paid, order.payment_method, order.order_type = is_paid, payment_method, order_type
            order.payments_details = {
                "items": pm_list_detailed, 
                "total_paid": float(total_paid),
                "left_to_pay": float(left_to_pay),
                "payment_status": payment_status,
                "payment_status_label": payment_status_label,
                "processed_payments_sum": float(processed_params)
            }

            # Терминальная группа
            order.terminal_group_id = terminal_group_id or order.terminal_group_id
            order.terminal_group_name = terminal_group_name or order.terminal_group_name
            
            # Доп. поля
            order.source = source
            order.iiko_creation_time = iiko_creation_time or order.iiko_creation_time
            order.expected_time = expected_time or order.expected_time
            order.actual_time = actual_time or order.actual_time
            order.is_on_time = is_on_time
            order.is_asap = is_asap
            order.delay_minutes = delay
            order.admin_name = admin_name or order.admin_name

            # Сбрасываем флаг модификации для JSON полей
            sql_flag_modified(order, "payments_details")

            # --- ОПРЕДЕЛЕНИЕ ЗОНЫ ДОСТАВКИ ПО АДРЕСУ ---
            # 1. Проверяем координаты напрямую из iiko (deliveryPoint)
            coords_iiko = dp.get("coordinates", {})
            lat_iiko = coords_iiko.get("latitude")
            lng_iiko = coords_iiko.get("longitude")
            
            # Если это доставка, пытаемся определить зону
            if order_type == "Доставка":
                logger.info(f"Auto-detecting zone for order {order_id_iiko}")
                
                # Приоритет 1: Координаты из iiko
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

                # Приоритет 2: Геокодер (если зона еще не определена)
                if not order.resolved_delivery_zone_id:
                    # Пытаемся определить зону только если есть адресные данные
                    # Теперь мы более лояльны к компонентам: если есть хотя бы строка адреса
                    full_addr_str = delivery_address if (delivery_address and delivery_address != "Самовывоз") else None
                    
                    if full_addr_str or (city and street_name):
                        try:
                            # Если компонентов нет, но есть строка - iiko_service.check_address_zone 
                            # все равно попробует геокодировать (мы передадим ей компоненты, даже если они пустые)
                            zone_data = await iiko_service.check_address_zone(
                                city=city or city_from_settings or "Тюмень",
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
            
            elif order_type == "Самовывоз":
                order.delivery_zone = "самовывоз"
                order.resolved_delivery_zone_id = None
                logger.info(f"Order {order_id_iiko}: Type is Pickup, skipping zone detection")
            # ---------------------------------------------

            # --- НОВАЯ ЛОГИКА СОСТАВА ЗАКАЗА (с именами и защитой от затирания) ---
            prod_obj_map = {}
            
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
                        
                # Достаем названия и картинки из локальной базы
                def _get_products():
                    return session.exec(select(Product).where(Product.iiko_id.in_(product_ids))).all()
                db_products = await asyncio.to_thread(_get_products)
                prod_map = {p.iiko_id: p.name for p in db_products}
                prod_img_map = {p.iiko_id: p.image_url for p in db_products}
                prod_obj_map = {p.iiko_id: p for p in db_products}

                # Достаем старые названия из текущего состояния заказа
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
                        if old_pid and old_name and old_name != "Неизвестный товар":
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
                            if old_mpid and old_mname and old_mname != "Модификатор":
                                old_names_map[old_mpid] = old_mname
                
                for item in raw_items:
                    enriched_item = item.copy()
                    pid = item.get("productId")
                    
                    # Приоритет имени: product.name -> primaryComponent.product.name -> productName -> БД -> История -> Fallback
                    if not enriched_item.get("name") or enriched_item.get("name") == "Неизвестный товар":
                        enriched_item["name"] = (
                            enriched_item.get("product", {}).get("name") or 
                            enriched_item.get("primaryComponent", {}).get("product", {}).get("name") or 
                            enriched_item.get("productName") or 
                            prod_map.get(pid) or 
                            old_names_map.get(pid) or 
                            "Неизвестный товар"
                        )
                    
                    # Записываем ссылку на картинку
                    enriched_item["image_url"] = prod_img_map.get(pid) or enriched_item.get("image_url")
                    
                    if not enriched_item.get("sum"):
                        enriched_item["sum"] = float(enriched_item.get("amount", 0)) * float(enriched_item.get("price", 0))
                        
                    enriched_mods = []
                    for mod in (item.get("modifiers") or []):
                        if not mod: continue
                        emod = mod.copy()
                        mpid = mod.get("productId")
                        
                        if not emod.get("name") or emod.get("name") == "Неизвестный товар":
                            emod["name"] = (
                                emod.get("product", {}).get("name") or 
                                emod.get("primaryComponent", {}).get("product", {}).get("name") or 
                                prod_map.get(mpid) or 
                                old_names_map.get(mpid) or 
                                "Неизвестный товар"
                            )
                        
                        if not emod.get("sum"):
                            emod["sum"] = float(emod.get("amount", 0)) * float(emod.get("price", 0))
                            
                        enriched_mods.append(emod)
                    
                    enriched_item["modifiers"] = enriched_mods
                    enriched_items.append(enriched_item)

                # Расчет честного подытога (сумма всех позиций по базовым ценам)
                calculated_base_sum = 0
                for e_item in enriched_items:
                    # Сумма самой позиции
                    item_qty = float(e_item.get("amount") or e_item.get("quantity") or 0)
                    item_price = float(e_item.get("price") or 0)
                    calculated_base_sum += item_qty * item_price
                    
                    # Сумма модификаторов
                    for e_mod in (e_item.get("modifiers") or []):
                        mod_qty = float(e_mod.get("amount") or e_mod.get("quantity") or 0)
                        mod_price = float(e_mod.get("price") or 0)
                        calculated_base_sum += mod_qty * mod_price

                order.total_amount = Decimal(str(round(calculated_base_sum, 2)))
                order.order_items_details = enriched_items
                sql_flag_modified(order, "order_items_details")
            else:
                logger.info(f"Order {order_id_iiko}: No valid items in webhook payload, skipping items update to prevent data loss")

            # --- ОБРАБОТКА ЛОЯЛЬНОСТИ, СКИДОК, АКЦИЙ, КУПОНОВ И ПОДАРКОВ IIKO ---
            loyalty_info = o_data.get("loyaltyInfo") or {}
            coupon_code = loyalty_info.get("coupon")
            dynamic_discounts = loyalty_info.get("dynamicDiscounts") or []
            applied_manual = loyalty_info.get("appliedManualConditions") or []
            free_products_raw = o_data.get("freeProducts") or loyalty_info.get("freeProducts") or []

            # Предварительно загружаем все элементы лояльности для обогащения
            def _get_all_loyalty():
                return {item.iiko_id: item for item in session.exec(select(IikoLoyaltyItem)).all()}
            loyalty_cache = await asyncio.to_thread(_get_all_loyalty)
            
            bonus_spent_from_discounts = 0
            enriched_discounts = []
            gifts_list = []

            # 1. Выделение подарков (Free Products) из iiko
            for fp in free_products_raw:
                if not isinstance(fp, dict): continue
                fp_id = fp.get("id") or fp.get("productId")
                fp_name = prod_map.get(fp_id) or fp.get("name") or fp.get("code") or "Подарочное блюдо"
                g_item = {
                    "name": f"Подарок к заказу: {fp_name}",
                    "sum": 0.0,
                    "type": "free_product",
                    "is_gift": True,
                    "product_id": fp_id,
                    "product_name": fp_name
                }
                gifts_list.append(g_item)
                enriched_discounts.append(g_item)

            # Проверяем позиции состава заказа: если у позиции цена 0, это подарок по акции
            for e_item in enriched_items:
                i_price = float(e_item.get("price") or 0)
                i_sum = float(e_item.get("sum") or 0)
                if i_price == 0 and i_sum == 0 and not e_item.get("is_modifier"):
                    e_item["is_gift"] = True
                    g_name = e_item.get("name") or "Подарок к заказу"
                    if not any(g.get("product_name") == g_name for g in gifts_list):
                        g_item = {
                            "name": f"Подарок к заказу: {g_name}",
                            "sum": 0.0,
                            "type": "free_product",
                            "is_gift": True,
                            "product_name": g_name
                        }
                        gifts_list.append(g_item)
                        enriched_discounts.append(g_item)

            # 2. Обработка скидок и акций
            for d in disc_list:
                if not isinstance(d, dict): continue
                ed = d.copy()
                d_sum = float(d.get("sum") or 0)
                
                dtype = d.get("discountType") or {}
                dtype_id = dtype.get("id") if isinstance(dtype, dict) else d.get("discountTypeId")
                dtype_name = dtype.get("name") if isinstance(dtype, dict) else clean(dtype)
                
                # Поиск названия в динамических скидках или справочнике лояльности
                resolved_name = None
                resolved_type = "discount"
                
                # Проверяем dynamicDiscounts
                for dyn in dynamic_discounts:
                    if isinstance(dyn, dict):
                        mc_id = dyn.get("manualConditionId")
                        if mc_id and mc_id in loyalty_cache:
                            l_obj = loyalty_cache[mc_id]
                            resolved_name = l_obj.name
                            resolved_type = l_obj.type or "promotion"
                            break
                        if dyn.get("name"):
                            resolved_name = dyn.get("name")
                            resolved_type = "promotion"
                            break

                # Проверяем кэш базы данных по discountType.id
                if not resolved_name and dtype_id and dtype_id in loyalty_cache:
                    l_it = loyalty_cache[dtype_id]
                    resolved_name = l_it.name
                    resolved_type = l_it.type or "discount"
                elif not resolved_name and dtype_name and dtype_name != "iikoCard":
                    resolved_name = dtype_name

                # Проверка: является ли это ДЕЙСТВИТЕЛЬНО списанием бонусов
                is_real_bonus = False
                check_name = (resolved_name or dtype_name or "").lower()
                
                if "списание бонус" in check_name or "оплата бонус" in check_name:
                    is_real_bonus = True
                elif bonus_spent_from_payments > 0 and ("бонус" in check_name or dtype_id == "30ee9e91-36d4-a868-e087-15892defe17c"):
                    # Привязка к факту списания бонусов в платежах
                    is_real_bonus = True

                if is_real_bonus:
                    ed["name"] = resolved_name or "Списание бонусов iikoCard"
                    ed["type"] = "bonus_spending"
                    ed["is_bonus"] = True
                    bonus_spent_from_discounts += d_sum
                else:
                    # Это АКЦИЯ, СКИДКА или КУПОН, а НЕ бонусы!
                    ed["is_bonus"] = False
                    if coupon_code:
                        ed["name"] = f"Промокод ({coupon_code})"
                        ed["type"] = "coupon_series"
                        ed["coupon"] = coupon_code
                    elif resolved_name:
                        ed["name"] = resolved_name
                        ed["type"] = resolved_type
                    else:
                        ed["name"] = "Скидка по акции iikoCard"
                        ed["type"] = "promotion"

                enriched_discounts.append(ed)

            # Начисленные бонусы (если переданы)
            bonus_accrued = 0
            if iiko_card_data and isinstance(iiko_card_data, dict):
                bonus_accrued = float(iiko_card_data.get("bonus_accrued") or 0)
            
            # Суммируем реальные бонусы
            final_bonus_spent = max(bonus_spent_from_payments, bonus_spent_from_discounts)
            if bonus_spent_from_payments > 0 and bonus_spent_from_discounts > 0:
                final_bonus_spent = bonus_spent_from_payments

            order.base_amount = sum_total
            order.left_to_pay = left_to_pay
            order.total_paid = Decimal(str(round(total_paid, 2)))
            order.bonus_spent = Decimal(str(round(final_bonus_spent, 2)))
            if bonus_accrued > 0:
                order.bonus_accrued = Decimal(str(round(bonus_accrued, 2)))

            order.payments_details = {
                "items": pm_list_detailed, 
                "total_paid": float(total_paid),
                "left_to_pay": float(left_to_pay),
                "payment_status": payment_status,
                "payment_status_label": payment_status_label,
                "processed_payments_sum": float(processed_params)
            }
            order.discounts_details = {
                "items": enriched_discounts,
                "gifts": gifts_list,
                "bonus_spent": float(final_bonus_spent)
            }
            order.updated_at = datetime.now(timezone.utc)
            
            sql_flag_modified(order, "order_items_details")
            sql_flag_modified(order, "discounts_details")
            sql_flag_modified(order, "payments_details")
            def _save_order_intermediate():
                session.add(order)
                session.flush() # Получаем ID для последующей синхронизации
            await asyncio.to_thread(_save_order_intermediate)

            # --- Авто-сопоставление безналичного платежа заказа с реальной банковской проводкой Т-Банка ---
            # Сопоставление с выпиской Т-Банка выполняем СТРОГО если платеж или заказ реально оплачен в iiko!
            try:
                from app.models.tbank_settings import TBankAccountStatement
                from app.api.chat import manager
                
                if is_paid or (float(total_paid) > 0 and raw_status_lower in ["closed", "delivered"]):
                    for p_item in pm_list_detailed:
                        pn_lower = (p_item.get("name") or "").lower()
                        is_cash_item = "налич" in pn_lower
                        pay_sum = float(p_item.get("sum", 0) or 0)
                        p_processed = p_item.get("is_processed", False)
                        
                        if not is_cash_item and pay_sum > 0 and (p_processed or is_paid):
                            comm_lower = (order.comment or "").lower()
                            # Определение точного метода оплаты
                            if any(w in pn_lower for w in ["сбп", "qr"]) or any(w in comm_lower for w in ["сбп", "sbp"]):
                                det_method = "СБП"
                            elif any(w in pn_lower for w in ["tpay", "t-pay"]) or any(w in comm_lower for w in ["tpay", "t-pay", "t pay"]):
                                det_method = "T-Pay"
                            elif "приложении" in comm_lower or "приложение" in comm_lower:
                                det_method = "СБП (T-Pay)"
                            elif "курьер" in pn_lower:
                                det_method = "Картой курьеру"
                            else:
                                det_method = "Эквайринг"

                            # 1. Проверяем, не сопоставлен ли этот заказ уже с реальной проводкой Т-Банка
                            def _check_already_matched():
                                return session.exec(
                                    select(TBankAccountStatement).where(
                                        TBankAccountStatement.matched_order_id == order.id
                                    )
                                ).first()

                            already_matched = await asyncio.to_thread(_check_already_matched)
                            if already_matched:
                                # Заказ уже привязан к банковской операции, дублировать не нужно
                                continue

                            # 2. Ищем реальную непривязанную проводку Т-Банка по сумме и времени (с учетом времени создания и закрытия)
                            def _find_matching_statement():
                                tx_time = iiko_creation_time or order.created_at or datetime.now()
                                if hasattr(tx_time, 'tzinfo') and tx_time.tzinfo is not None:
                                    tx_time = tx_time.replace(tzinfo=None)
                                up_time = order.updated_at
                                if up_time is not None and hasattr(up_time, 'tzinfo') and up_time.tzinfo is not None:
                                    up_time = up_time.replace(tzinfo=None)
                                from datetime import timedelta
                                time_min = tx_time - timedelta(hours=2)
                                end_bound = up_time if (up_time and up_time > tx_time) else tx_time
                                time_max = end_bound + timedelta(hours=3)
                                return session.exec(
                                    select(TBankAccountStatement).where(
                                        TBankAccountStatement.amount == pay_sum,
                                        TBankAccountStatement.charge_date >= time_min,
                                        TBankAccountStatement.charge_date <= time_max,
                                        TBankAccountStatement.matched_order_id == None
                                    )
                                ).first()
                                
                            matched_stmt = await asyncio.to_thread(_find_matching_statement)
                            if matched_stmt:
                                matched_stmt.matched_order_id = order.id
                                def _save_matched_statement():
                                    session.add(matched_stmt)
                                    session.flush()
                                await asyncio.to_thread(_save_matched_statement)
                                logger.info(f"[T-Bank Match] Заказ #{order.id} успешно сопоставлен с реальной проводкой Т-Банка #{matched_stmt.id} (RRN: {matched_stmt.payer_account})")

                                # Мгновенная отправка в WebSocket шину Redis Pub/Sub для LIVE-монитора Т-Банка ТОЛЬКО при реальном сопоставлении проводки
                                try:
                                    ws_payload = {
                                        "type": "new_bank_payment",
                                        "amount": pay_sum,
                                        "method": det_method,
                                        "customer": order.customer_name or "Клиент",
                                        "order_id": order.id,
                                        "rrn": str(matched_stmt.payer_account or f"ORD{order.id:06d}")
                                    }
                                    manager.broadcast_sync(ws_payload)
                                except Exception as ws_e:
                                    logger.warning(f"Failed to broadcast new_bank_payment from iiko_sync: {ws_e}")
            except Exception as tbank_err:
                logger.error(f"Ошибка при сопоставлении платежа Т-Банка: {tbank_err}")

            # --- АВТО-СОЗДАНИЕ КАРТОЧКИ КЛИЕНТА ---
            if phone:
                try:
                    # Генерируем состав заказа для заметок
                    items_list = []
                    for item in (order.order_items_details or []):
                        name = item.get("name", "Товар")
                        amount = item.get("amount", 1)
                        items_list.append(f"{name} x{amount}")
                    order_items_text = ", ".join(items_list)
                    
                    # Формируем расширенную информацию для заметок
                    display_time = iiko_creation_time or datetime.now(timezone.utc).replace(tzinfo=None)
                    full_order_info = f"Заказ #{ext_num or 'б/н'} от {display_time.strftime('%d.%m.%Y %H:%M')}"
                    full_order_info += f" на сумму {total_with_discount:.0f} руб."
                    
                    # Добавляем адрес в описание
                    if delivery_address:
                        full_order_info += f"\nАдрес: {delivery_address}"
                    
                    if order_items_text:
                        # Ограничиваем длину
                        if len(order_items_text) > 300:
                            order_items_text = order_items_text[:297] + "..."
                        full_order_info += f"\nСостав: {order_items_text}"
                    
                    # Добавляем инфо о подарках в расширенное описание состава
                    if loyalty_payload.get("free_products"):
                        full_order_info += f"\nПодарки: {', '.join(loyalty_payload['free_products'])}"
                    if loyalty_payload.get("errors"):
                        full_order_info += f"\nОшибки лояльности: {', '.join(loyalty_payload['errors'])}"

                    customer_obj = await self.ensure_customer_from_order(
                        session=session,
                        phone=phone,
                        name=c_first,
                        surname=c_last,
                        order_info=full_order_info,
                        order_date=iiko_creation_time,
                        order_status=mapped_status,
                        loyalty_data=loyalty_payload,
                        order_id_iiko=order_id_iiko,
                        city=city,
                        street=street_name,
                        house=house,
                        flat=flat,
                        total_sum=float(total_with_discount),
                        order_db_id=order.id
                    )
                    
                    if customer_obj and order.customer_id != customer_obj.id:
                        order.customer_id = customer_obj.id
                        session.add(order)
                        logger.info(f"Linked order {order.id} to customer {customer_obj.id}")

                    # --- ЛОГИКА "ПЕРВЫЙ ЗАКАЗ" ---
                    if is_new and customer_obj:
                        # Если iiko говорит что гость новый ИЛИ в нашей базе это единственный заказ
                        is_iiko_new = getattr(customer_obj, 'is_new_guest', False)
                        
                        # Проверяем количество ЛОКАЛЬНЫХ заказов (кроме текущего)
                        def _get_local_orders_count():
                            return session.exec(
                                select(func.count(Order.id)).where(
                                    Order.customer_phone == phone,
                                    Order.iiko_order_id != order_id_iiko
                                )
                            ).one()
                        local_orders_count = await asyncio.to_thread(_get_local_orders_count)
                        
                        if is_iiko_new or local_orders_count == 0:
                            order.is_first_order = True
                            logger.info(f"Order {order_id_iiko}: Marked as IS_FIRST_ORDER (New Guest)")
                except Exception as cust_err:
                    logger.error(f"Error in auto-creating customer for order {order_id_iiko}: {cust_err}")

            # --- СИНХРОНИЗАЦИЯ ПОЗИЦИЙ ЗАКАЗА (order_items) ДЛЯ КУХНИ (KDS) ---
            try:
                def _sync_order_items():
                    # Загружаем существующие OrderItem для этого заказа
                    existing_items = session.exec(
                        select(OrderItem).where(OrderItem.order_id == order.id)
                    ).all()
                    
                    # Группируем существующие OrderItem по product_id
                    existing_by_prod = {}
                    for ei in existing_items:
                        existing_by_prod.setdefault(ei.product_id, []).append(ei)
                        
                    items_to_keep = set()
                    
                    # Проходим по позициям из iiko
                    for item_data in (order.order_items_details or []):
                        pid_iiko = item_data.get("productId")
                        if not pid_iiko:
                            continue
                            
                        prod = prod_obj_map.get(pid_iiko)
                        prod_id = prod.id if prod else None
                        
                        # Ищем существующий OrderItem
                        matched_item = None
                        if prod_id and prod_id in existing_by_prod and existing_by_prod[prod_id]:
                            matched_item = existing_by_prod[prod_id].pop(0)
                            
                        qty = int(float(item_data.get("amount") or item_data.get("quantity") or 1))
                        price = Decimal(str(item_data.get("price") or 0))
                        total = Decimal(str(item_data.get("sum") or (qty * float(price))))
                        size_val = item_data.get("size_name") or item_data.get("size")
                        if isinstance(size_val, dict):
                            size_name = size_val.get("name")
                        else:
                            size_name = size_val
                        comment = item_data.get("comment")
                        modifiers = item_data.get("modifiers")
                        
                        # Определяем зону приготовления (цех)
                        k_zone_id = item_data.get("kitchen_zone_id") or (prod.kitchen_zone_id if prod else None)
                        
                        if matched_item:
                            # Обновляем существующий
                            matched_item.product_name = item_data.get("name") or "Неизвестный товар"
                            matched_item.quantity = qty
                            matched_item.price = price
                            matched_item.total = total
                            matched_item.size_name = size_name
                            matched_item.comment = comment
                            matched_item.modifiers = modifiers
                            if k_zone_id is not None:
                                matched_item.kitchen_zone_id = k_zone_id
                            
                            session.add(matched_item)
                            items_to_keep.add(matched_item.id)
                        else:
                            # Создаем новый
                            new_item = OrderItem(
                                order_id=order.id,
                                product_id=prod_id,
                                product_name=item_data.get("name") or "Неизвестный товар",
                                quantity=qty,
                                price=price,
                                total=total,
                                size_name=size_name,
                                comment=comment,
                                modifiers=modifiers,
                                kitchen_status="pending",
                                kitchen_zone_id=k_zone_id
                            )
                            session.add(new_item)
                            session.flush() # Получаем ID
                            items_to_keep.add(new_item.id)
                            
                    # Удаляем старые, которых больше нет в iiko
                    for ei in existing_items:
                        if ei.id not in items_to_keep:
                            session.delete(ei)
                            
                await asyncio.to_thread(_sync_order_items)
            except Exception as items_sync_err:
                logger.error(f"Error syncing order items for order {order_id_iiko}: {items_sync_err}")

            await asyncio.to_thread(session.commit)
            logger.info(f"Order {order_id_iiko} ({external_number}) synced. Status={mapped_status}, Paid={is_paid}")

            # Проверка изменений для уведомлений (только для существующих заказов)
            old_cook = int(old_cooking_time or 0)
            new_cook = int(order.cooking_time_minutes or 0)
            is_cooking_time_set = not is_new and (old_cook <= 0 and new_cook > 0)
            is_cooking_time_rechanged = not is_new and (old_cook > 0 and new_cook > 0 and old_cook != new_cook)
            is_cooking_time_changed = not is_new and (old_cook != new_cook)

            is_amount_changed = not is_new and abs(old_amount - float(total_with_discount)) > 0.01
            is_address_changed = not is_new and old_address != order.delivery_address and has_new_address
            is_items_changed = not is_new and old_items_count != len(order.order_items_details or [])
            is_payment_changed = not is_new and old_payments_details != order.payments_details
            
            is_time_changed = False
            if not is_new and old_time and order.expected_time:
                try:
                    ot = old_time.replace(tzinfo=None)
                    nt = order.expected_time.replace(tzinfo=None)
                    if abs((ot - nt).total_seconds()) > 60:
                        is_time_changed = True
                except: pass

            # Повторная синхронизация гостя при завершении или отмене заказа для обновления статистики
            if phone and mapped_status in (OrderStatus.closed, OrderStatus.cancelled, OrderStatus.delivered):
                try:
                    from app.tasks.customer_tasks import sync_single_customer_task
                    sync_single_customer_task.delay(phone, fast_sync=True)
                    logger.info(f"Triggered re-sync for customer {phone} due to order status {mapped_status}")
                except Exception as e:
                    logger.warning(f"Failed to trigger re-sync for customer {phone}: {e}")

            # Отправка уведомлений
            if is_new:
                # 1. Общее событие "Новый заказ" для всех заказов (доставка, самовывоз, зал)
                await self._send_order_vk_notification(order, "order_new_all", session=session)
                
                # 2. Событие "Новый заказ на доставку" для цепочек курьера
                ord_type_str = str(order.order_type or "").lower()
                is_pickup_order = "самовывоз" in ord_type_str or "pickup" in ord_type_str
                if not is_pickup_order:
                    await self.check_and_send_order_new_to_courier(order, session=session)
                
                # Отправка WebSocket уведомления в админку
                try:
                    from app.api.chat import manager
                    ws_payload = {
                        "type": "new_order",
                        "order_id": order.id,
                        "iiko_order_id": order.iiko_order_id,
                        "order_number": external_number,
                        "total_sum": float(total_with_discount),
                        "customer_name": order.customer_name or "Гость"
                    }
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(manager.broadcast(ws_payload))
                except Exception as e:
                    logger.error(f"Failed to send websocket order notification: {e}")
                
                # Отправка пуш-уведомления администраторам
                try:
                    cust_name = order.customer_name or "Гость"
                    await self.send_admin_push_notification(
                        session=session,
                        title="Новый заказ!",
                        body=f"Сумма: {total_with_discount} ₽ | Клиент: {cust_name} | Заказ #{external_number or order.id}",
                        url="/admin/orders",
                        event_type="new_order",
                        tag=f"order-{order.id}"
                    )
                except Exception as e:
                    logger.error(f"Failed to send admin push notification: {e}")

                # НОВАЯ ДОСТАВКА БЕЗ НАЗНАЧЕННОГО КУРЬЕРА
                if order_type == "Доставка" and (not courier_name or courier_name == "Не назначен"):
                    try:
                        ws_unassigned = {
                            "type": "delivery_unassigned",
                            "order_id": order.id,
                            "order_number": external_number,
                            "total_sum": float(total_with_discount),
                            "address": order.delivery_address,
                            "customer_name": order.customer_name or "Гость"
                        }
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            loop.create_task(manager.broadcast(ws_unassigned))
                        
                        await self.send_admin_push_notification(
                            session=session,
                            title="Новая доставка (свободная)!",
                            body=f"Сумма: {total_with_discount} ₽ | Адрес: {order.delivery_address} | Заказ #{external_number or order.id}",
                            url="/admin/orders",
                            event_type="delivery_unassigned",
                            tag=f"unassigned-{order.id}"
                        )
                    except Exception as e:
                        logger.error(f"Failed to send delivery_unassigned notifications: {e}")

            # ОТСЛЕЖИВАНИЕ ИЗМЕНЕНИЙ КУРЬЕРА (назначение, переназначение или снятие)
            is_courier_assigned_now = False
            is_courier_unassigned_now = False
            is_courier_reassigned = False
            
            # Проверка терминального статуса заказа (доставлен, закрыт, отменен)
            is_order_finished = bool(
                mapped_status in (OrderStatus.closed, OrderStatus.cancelled, OrderStatus.delivered) or
                (order and getattr(order, 'status', None) in (OrderStatus.closed, OrderStatus.cancelled, OrderStatus.delivered)) or
                str(getattr(order, 'status', '')).lower() in ("closed", "cancelled", "delivered", "доставлен", "закрыт", "отменен")
            )
            
            # Назначение курьера и пуш-уведомления активны ТОЛЬКО для активных незавершенных заказов
            if not is_order_finished:
                if is_new and courier_name and courier_name != "Не назначен":
                    is_courier_assigned_now = True
                elif not is_new and old_courier != courier_name:
                    if courier_name and courier_name != "Не назначен":
                        is_courier_assigned_now = True
                        if old_courier and old_courier != "Не назначен":
                            is_courier_reassigned = True
                    if old_courier and old_courier != "Не назначен" and (not courier_name or courier_name == "Не назначен"):
                        is_courier_unassigned_now = True

            if is_courier_assigned_now:
                # 0. При переназначении курьера обязательно сбрасываем статус подтверждения
                if is_courier_reassigned:
                    order.courier_notification_status = None
                    order.courier_accepted_at = None
                    order.courier_accepted_source = None
                    order.courier_read_at = None
                    order.updated_at = datetime.now(timezone.utc)
                    session.add(order)

                # 1. Широковещательное обновление для админки (/orders) и панели курьера (/pers/courier)
                now_ts = int(datetime.now(timezone.utc).timestamp() * 1000)
                ws_order_changed = {
                    "type": "order_changed",
                    "order_id": order.id,
                    "order_number": external_number or str(order.id),
                    "status": order.status,
                    "customer_name": order.customer_name or "Гость",
                    "order_type": order.order_type,
                    "courier_name": order.courier_name,
                    "courier_notification_status": order.courier_notification_status,
                    "timestamp": now_ts
                }
                ws_courier_status = {
                    "type": "courier_status_changed",
                    "order_id": order.id,
                    "order_num": external_number or str(order.id),
                    "courier_name": order.courier_name,
                    "courier_notification_status": order.courier_notification_status,
                    "status": "reassigned" if is_courier_reassigned else "assigned",
                    "timestamp": now_ts
                }
                self.send_websocket_broadcast_safe(ws_order_changed)
                self.send_websocket_broadcast_safe(ws_courier_status)

                # 2. Отправка системного уведомления назначенному курьеру по цепочке шага 1 (order_new) или courier_assigned
                sent_order_new = await self.check_and_send_order_new_to_courier(
                    order, 
                    session=session, 
                    is_reassigned=is_courier_reassigned, 
                    old_courier=old_courier, 
                    new_courier=courier_name
                )
                if not sent_order_new:
                    try:
                        await self._send_order_vk_notification(
                            order, 
                            "courier_assigned", 
                            session=session,
                            is_reassigned=is_courier_reassigned,
                            old_courier=old_courier,
                            new_courier=courier_name
                        )
                        if is_courier_reassigned:
                            logger.info(f"Order #{order.external_number or order.id} was REASSIGNED from '{old_courier}' to '{courier_name}'. Notification 'courier_assigned' sent to new courier.")
                    except Exception as notif_err:
                        logger.error(f"Failed to send courier_assigned notification: {notif_err}")

                # 3. WebSocket и Push для приложения сотрудника
                try:
                    courier_user = None
                    if courier_iiko_id:
                        def _get_courier_user():
                            return session.exec(select(User).where(User.iiko_id == str(courier_iiko_id))).first()
                        courier_user = await asyncio.to_thread(_get_courier_user)
                    
                    if not courier_user and courier_name:
                        def _get_courier_user_by_name():
                            return session.exec(select(User).where(User.full_name == courier_name)).first()
                        courier_user = await asyncio.to_thread(_get_courier_user_by_name)
                        
                    if courier_user:
                        ws_assigned = {
                            "type": "delivery_assigned",
                            "order_id": order.id,
                            "order_number": external_number,
                            "address": order.delivery_address,
                            "amount": float(total_with_discount),
                            "target_user_id": courier_user.id
                        }
                        self.send_websocket_broadcast_safe(ws_assigned)
                        # Примечание: персональный Web Push курьеру отправляется ниже через send_courier_notification
                        # (событие courier_order_assigned), чтобы исключить дублирование пушей.
                except Exception as e:
                    logger.error(f"Failed to send courier delivery assignment notifications: {e}")

            if is_courier_unassigned_now:
                try:
                    # Ищем пользователя старого курьера, чтобы отправить ему уведомление
                    old_courier_user = None
                    if old_courier:
                        def _get_old_courier_user():
                            from app.models.employee import Employee
                            employee = session.exec(select(Employee).where(Employee.name == old_courier)).first()
                            if employee:
                                return session.exec(select(User).where(User.iiko_id == str(employee.iiko_id))).first()
                            return None
                        old_courier_user = await asyncio.to_thread(_get_old_courier_user)
                    
                    ws_unassigned = {
                        "type": "delivery_unassigned",
                        "order_id": order.id,
                        "order_number": external_number,
                        "total_sum": float(total_with_discount),
                        "address": order.delivery_address,
                        "customer_name": order.customer_name or "Гость"
                    }
                    self.send_websocket_broadcast_safe(ws_unassigned)
                    
                    if old_courier_user:
                        self.send_websocket_personal_safe(ws_unassigned, old_courier_user.id)
                        await self.send_admin_push_notification(
                            session=session,
                            title="Доставка отменена",
                            body=f"С вас снята доставка заказа #{external_number or order.id}",
                            url="/pers/courier",
                            event_type="delivery_unassigned",
                            target_user_id=old_courier_user.id,
                            tag=f"unassigned-{order.id}"
                        )
                except Exception as e:
                    logger.error(f"Failed to send courier delivery unassignment notifications: {e}")

            if is_status_changed:
                from app.models.order import OrderStatus
                event = "order_cancelled" if mapped_status == OrderStatus.cancelled else "order_status_update"
                await self._send_order_vk_notification(order, event, session=session)
                
                # WebSocket оповещение о смене статуса заказа в реальном времени
                try:
                    ws_type = "order_cancelled" if mapped_status == OrderStatus.cancelled else "order_changed"
                    ws_payload = {
                        "type": ws_type,
                        "order_id": order.id,
                        "order_number": external_number or str(order.id),
                        "status": mapped_status,
                        "customer_name": order.customer_name or "Гость",
                        "order_type": order.order_type,
                        "courier_name": order.courier_name
                    }
                    self.send_websocket_broadcast_safe(ws_payload)
                    
                    # Если курьер назначен, то также отправим ему лично
                    if order.courier_name:
                        try:
                            from app.models.employee import Employee
                            def _get_courier_user():
                                employee = session.exec(select(Employee).where(Employee.name == order.courier_name)).first()
                                if employee:
                                    return session.exec(select(User).where(User.iiko_id == str(employee.iiko_id))).first()
                                return None
                            courier_user = await asyncio.to_thread(_get_courier_user)
                            if courier_user:
                                self.send_websocket_personal_safe(ws_payload, courier_user.id)
                        except Exception as e_c:
                            logger.warning(f"Failed to find courier for personal status update WS: {e_c}")
                except Exception as e:
                    logger.error(f"Failed to send websocket status change notification: {e}")
                    
                # Push-уведомление администраторам о смене статуса
                try:
                    ws_type = "order_cancelled" if mapped_status == OrderStatus.cancelled else "order_changed"
                    title = "Заказ отменен" if mapped_status == OrderStatus.cancelled else "Статус заказа изменен"
                    body = f"Заказ #{external_number or order.id} отменен" if mapped_status == OrderStatus.cancelled else f"Заказ #{external_number or order.id} переведен в статус '{mapped_status}'"
                    await self.send_admin_push_notification(
                        session=session,
                        title=title,
                        body=body,
                        url="/admin/orders",
                        event_type=ws_type,
                        tag=f"order-status-{order.id}",
                        order=order
                    )
                except Exception as e:
                    logger.error(f"Failed to send admin push for status change: {e}")

                # Специальное уведомление "Доставка заказа" (заказ доставлен курьером)
                is_delivery_order = (
                    "самовывоз" not in str(order.order_type or "").lower() and 
                    "pickup" not in str(order.order_type or "").lower() and
                    "зал" not in str(order.order_type or "").lower()
                )
                already_notified_delivered = False
                if order.change_indicators and isinstance(order.change_indicators, dict):
                    already_notified_delivered = bool(order.change_indicators.get("order_delivered_notified"))

                if mapped_status == OrderStatus.delivered and is_delivery_order and not already_notified_delivered:
                    try:
                        from app.core.datetime_utils import format_local_time
                        deliv_time_str = format_local_time(order.actual_time) if order.actual_time else ""
                        ws_delivered = {
                            "type": "order_delivered",
                            "order_id": order.id,
                            "order_number": external_number or str(order.id),
                            "courier_name": order.courier_name or "Курьер",
                            "delivery_address": order.delivery_address or "---",
                            "total_amount": float(total_with_discount),
                            "customer_name": order.customer_name or "Гость",
                            "actual_time": deliv_time_str,
                            "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000)
                        }
                        self.send_websocket_broadcast_safe(ws_delivered)
                        
                        await self.send_admin_push_notification(
                            session=session,
                            title="Заказ доставлен!",
                            body=f"Заказ #{external_number or order.id} успешно доставлен! Курьер: {order.courier_name or 'Курьер'} | Адрес: {order.delivery_address or '---'}",
                            url="/admin/orders",
                            event_type="order_delivered",
                            tag=f"delivered-{order.id}",
                            order=order
                        )
                        
                        if not order.change_indicators or not isinstance(order.change_indicators, dict):
                            order.change_indicators = {}
                        order.change_indicators["order_delivered_notified"] = True
                        from sqlalchemy.orm.attributes import flag_modified
                        flag_modified(order, "change_indicators")
                        session.add(order)
                        logger.info(f"Order #{external_number or order.id} delivered notification broadcasted and flagged.")
                    except Exception as deliv_err:
                        logger.error(f"Failed to send order_delivered notification: {deliv_err}")
            
            # Уведомления об изменениях
            if not is_new:
                if is_amount_changed:
                    await self._send_order_vk_notification(
                        order, "order_amount_changed", session=session,
                        is_amount_changed=True, old_amount=old_amount, new_amount=float(total_with_discount)
                    )
                if is_items_changed:
                    await self._send_order_vk_notification(
                        order, "order_items_changed", session=session,
                        is_items_changed=True, old_items_count=old_items_count, new_items_count=len(order.order_items_details or [])
                    )
                if is_time_changed:
                    await self._send_order_vk_notification(
                        order, "order_time_changed", session=session,
                        is_time_changed=True, old_time=old_time, new_time=order.expected_time
                    )
                if is_address_changed:
                    await self._send_order_vk_notification(
                        order, "order_address_changed", session=session,
                        is_address_changed=True, old_address=old_address, new_address=order.delivery_address
                    )
                
                # WebSocket и Web Push уведомления об изменениях в заказе
                try:
                    from app.api.chat import manager
                    loop = asyncio.get_event_loop()
                    
                    # 1. Изменение времени готовности
                    if is_cooking_time_changed:
                        if loop.is_running():
                            loop.create_task(manager.broadcast({
                                "type": "change_cooking_time",
                                "order_id": order.id,
                                "order_number": external_number,
                                "cooking_time_minutes": order.cooking_time_minutes,
                                "order_type": order.order_type,
                                "courier_name": order.courier_name
                            }))
                        await self.send_admin_push_notification(
                            session=session,
                            title="Изменение времени готовности",
                            body=f"Заказ #{external_number or order.id} | Время на кухне: {order.cooking_time_minutes} мин.",
                            url="/admin/orders",
                            event_type="change_cooking_time",
                            tag=f"cooking-time-{order.id}",
                            order=order
                        )
                        
                        # 1.1. Если время кухни задано впервые (>0 мин), проверяем досылку шага 1 (order_new) назначенному курьеру
                        if is_cooking_time_set and not is_order_finished:
                            await self.check_and_send_order_new_to_courier(order, session=session)

                        # 1.2. Отправка уведомления change_cooking_time (роутер проверит require_cooking_time_changed)
                        try:
                            await self._send_order_vk_notification(
                                order, 
                                "change_cooking_time", 
                                session=session,
                                is_cooking_time_set=is_cooking_time_set,
                                is_cooking_time_rechanged=is_cooking_time_rechanged,
                                old_cooking_time=old_cook,
                                new_cooking_time=new_cook
                            )
                        except Exception as notif_err:
                            logger.error(f"Failed to send change_cooking_time notification: {notif_err}")
                        
                    # 2. Изменение состава заказа
                    if is_items_changed:
                        if loop.is_running():
                            loop.create_task(manager.broadcast({
                                "type": "change_items",
                                "order_id": order.id,
                                "order_number": external_number,
                                "order_type": order.order_type,
                                "courier_name": order.courier_name
                            }))
                        await self.send_admin_push_notification(
                            session=session,
                            title="Изменение состава заказа",
                            body=f"Состав заказа #{external_number or order.id} был изменен",
                            url="/admin/orders",
                            event_type="change_items",
                            tag=f"items-change-{order.id}",
                            order=order
                        )
                        
                    # 3. Изменение суммы оплаты
                    if is_amount_changed:
                        if loop.is_running():
                            loop.create_task(manager.broadcast({
                                "type": "change_amount",
                                "order_id": order.id,
                                "order_number": external_number,
                                "amount": float(total_with_discount),
                                "order_type": order.order_type,
                                "courier_name": order.courier_name
                            }))
                        await self.send_admin_push_notification(
                            session=session,
                            title="Изменение суммы заказа",
                            body=f"Сумма заказа #{external_number or order.id} изменена: {total_with_discount} ₽",
                            url="/admin/orders",
                            event_type="change_amount",
                            tag=f"amount-change-{order.id}",
                            order=order
                        )
                        
                    # 4. Изменение способа оплаты
                    if is_payment_changed:
                        pay_name = "не указан"
                        if order.payments_details and isinstance(order.payments_details, dict):
                            items = order.payments_details.get("items", [])
                            if items:
                                pay_name = ", ".join([it.get("paymentType", {}).get("name", "") for it in items])
                        if loop.is_running():
                            loop.create_task(manager.broadcast({
                                "type": "change_payment",
                                "order_id": order.id,
                                "order_number": external_number,
                                "payment_method": pay_name,
                                "order_type": order.order_type,
                                "courier_name": order.courier_name
                            }))
                        await self.send_admin_push_notification(
                            session=session,
                            title="Изменение способа оплаты",
                            body=f"Способ оплаты заказа #{external_number or order.id} изменен: {pay_name}",
                            url="/admin/orders",
                            event_type="change_payment",
                            tag=f"payment-change-{order.id}",
                            order=order
                        )
                        
                    # 5. Изменение адреса доставки
                    if is_address_changed:
                        if loop.is_running():
                            loop.create_task(manager.broadcast({
                                "type": "change_address",
                                "order_id": order.id,
                                "order_number": external_number,
                                "address": order.delivery_address,
                                "order_type": order.order_type,
                                "courier_name": order.courier_name
                            }))
                        await self.send_admin_push_notification(
                            session=session,
                            title="Изменение адреса доставки",
                            body=f"Адрес доставки заказа #{external_number or order.id} изменен: {order.delivery_address}",
                            url="/admin/orders",
                            event_type="change_address",
                            tag=f"address-change-{order.id}",
                            order=order
                        )
                        
                except Exception as e:
                    logger.error(f"Failed to send order change notifications: {e}")
            
            # =========================================================================
            # ПЕРСОНАЛЬНЫЕ PUSH И BROWSER УВЕДОМЛЕНИЯ КУРЬЕРУ (10 ВЫДЕЛЕННЫХ СОБЫТИЙ)
            # =========================================================================
            try:
                courier_user = self.find_courier_user(session, courier_name, courier_iiko_id)
                old_courier_user = self.find_courier_user(session, old_courier) if old_courier else None

                # 1. Назначен заказ на доставку
                if is_courier_assigned_now and courier_user:
                    await self.send_courier_notification(
                        session=session,
                        courier_user_id=courier_user.id,
                        event_type="courier_order_assigned",
                        title="Назначен заказ на доставку",
                        body=f"Вам назначен заказ #{external_number or order.id} | Сумма: {float(total_with_discount):.0f} ₽ | Адрес: {order.delivery_address}",
                        order_id=order.id,
                        order_number=external_number or order.id,
                        url="/pers/courier",
                        extra_data={
                            "amount": float(total_with_discount),
                            "address": order.delivery_address,
                            "customer_name": order.customer_name or "Гость",
                            "cooking_time_minutes": order.cooking_time_minutes
                        },
                        order=order
                    )

                # 2. Установление времени приготовления заказа
                if not is_new and (old_cooking_time is None or old_cooking_time == 0) and order.cooking_time_minutes and order.cooking_time_minutes > 0 and courier_user:
                    await self.send_courier_notification(
                        session=session,
                        courier_user_id=courier_user.id,
                        event_type="courier_cooking_time_set",
                        title="Установлено время приготовления",
                        body=f"Заказ #{external_number or order.id}. Время на кухне: {order.cooking_time_minutes} мин.",
                        order_id=order.id,
                        order_number=external_number or order.id,
                        url="/pers/courier",
                        extra_data={
                            "cooking_time_minutes": order.cooking_time_minutes,
                            "amount": float(total_with_discount),
                            "address": order.delivery_address
                        },
                        order=order
                    )

                # 3. Изменение времени приготовления заказа
                if not is_new and old_cooking_time and old_cooking_time > 0 and order.cooking_time_minutes and old_cooking_time != order.cooking_time_minutes and courier_user:
                    await self.send_courier_notification(
                        session=session,
                        courier_user_id=courier_user.id,
                        event_type="courier_cooking_time_changed",
                        title="Изменено время приготовления",
                        body=f"Заказ #{external_number or order.id}. Новое время кухни: {order.cooking_time_minutes} мин. (было: {old_cooking_time} мин.)",
                        order_id=order.id,
                        order_number=external_number or order.id,
                        url="/pers/courier",
                        extra_data={
                            "cooking_time_minutes": order.cooking_time_minutes,
                            "old_cooking_time": old_cooking_time,
                            "amount": float(total_with_discount),
                            "address": order.delivery_address
                        },
                        order=order
                    )

                # 4. Изменение статуса заказа (только готов или отменен)
                if is_status_changed and courier_user:
                    if mapped_status in (OrderStatus.ready, "cooking_finished", "ready", "Готов"):
                        await self.send_courier_notification(
                            session=session,
                            courier_user_id=courier_user.id,
                            event_type="courier_status_changed",
                            title="Заказ готов к выдаче!",
                            body=f"Заказ #{external_number or order.id} приготовлен кухней. Можно забирать!",
                            order_id=order.id,
                            order_number=external_number or order.id,
                            url="/pers/courier",
                            extra_data={
                                "status": "ready",
                                "amount": float(total_with_discount),
                                "address": order.delivery_address
                            },
                            order=order
                        )
                    elif mapped_status in (OrderStatus.cancelled, "cancelled", "отменен"):
                        await self.send_courier_notification(
                            session=session,
                            courier_user_id=courier_user.id,
                            event_type="courier_status_changed",
                            title="Заказ отменен!",
                            body=f"Заказ #{external_number or order.id} был отменен!",
                            order_id=order.id,
                            order_number=external_number or order.id,
                            url="/pers/courier",
                            extra_data={
                                "status": "cancelled",
                                "amount": float(total_with_discount),
                                "address": order.delivery_address
                            },
                            order=order
                        )

                # 5. Изменение суммы заказа
                if not is_new and is_amount_changed and courier_user:
                    await self.send_courier_notification(
                        session=session,
                        courier_user_id=courier_user.id,
                        event_type="courier_amount_changed",
                        title="Изменение суммы заказа",
                        body=f"Сумма заказа #{external_number or order.id} изменена: {float(total_with_discount):.0f} ₽ (было: {old_amount:.0f} ₽)",
                        order_id=order.id,
                        order_number=external_number or order.id,
                        url="/pers/courier",
                        extra_data={
                            "amount": float(total_with_discount),
                            "old_amount": old_amount,
                            "address": order.delivery_address
                        },
                        order=order
                    )

                # 6. Изменение адреса доставки
                if not is_new and is_address_changed and courier_user:
                    await self.send_courier_notification(
                        session=session,
                        courier_user_id=courier_user.id,
                        event_type="courier_address_changed",
                        title="Изменение адреса доставки",
                        body=f"Адрес заказа #{external_number or order.id} изменен: {order.delivery_address}",
                        order_id=order.id,
                        order_number=external_number or order.id,
                        url="/pers/courier",
                        extra_data={
                            "address": order.delivery_address,
                            "old_address": old_address,
                            "amount": float(total_with_discount)
                        },
                        order=order
                    )

                # 7. Изменение способа доставки заказа (изменили на самовывоз)
                if not is_new and old_order_type == "Доставка" and order.order_type in ("Самовывоз", "В ресторане"):
                    target_u = old_courier_user or courier_user
                    if target_u:
                        await self.send_courier_notification(
                            session=session,
                            courier_user_id=target_u.id,
                            event_type="courier_changed_to_pickup",
                            title="Заказ переведен на самовывоз!",
                            body=f"Заказ #{external_number or order.id} изменен на самовывоз. Доставка отменена.",
                            order_id=order.id,
                            order_number=external_number or order.id,
                            url="/pers/courier",
                            extra_data={
                                "order_type": order.order_type,
                                "amount": float(total_with_discount)
                            },
                            order=order
                        )

                # 8. Заказ убран из доставки
                if not is_new and (old_order_type == "Доставка" or order.order_type == "Доставка") and mapped_status in (OrderStatus.cancelled, "cancelled", "отменен"):
                    target_u = courier_user or old_courier_user
                    if target_u:
                        await self.send_courier_notification(
                            session=session,
                            courier_user_id=target_u.id,
                            event_type="courier_removed_from_delivery",
                            title="Заказ убран из доставки!",
                            body=f"Заказ #{external_number or order.id} снят с доставки.",
                            order_id=order.id,
                            order_number=external_number or order.id,
                            url="/pers/courier",
                            extra_data={
                                "amount": float(total_with_discount)
                            },
                            order=order
                        )

                # 9. Заказ убран из списка доставок выбранного курьера
                if (is_courier_unassigned_now or is_courier_reassigned) and old_courier_user:
                    await self.send_courier_notification(
                        session=session,
                        courier_user_id=old_courier_user.id,
                        event_type="courier_unassigned",
                        title="Заказ снят с ваших доставок",
                        body=f"Заказ #{external_number or order.id} убран из вашего списка доставок.",
                        order_id=order.id,
                        order_number=external_number or order.id,
                        url="/pers/courier",
                        extra_data={
                            "amount": float(total_with_discount),
                            "address": order.delivery_address
                        },
                        order=order
                    )

                # 10. Изменение времени доставки заказа
                if not is_new and is_time_changed and courier_user:
                    time_str = order.expected_time.strftime("%H:%M") if order.expected_time else "---"
                    await self.send_courier_notification(
                        session=session,
                        courier_user_id=courier_user.id,
                        event_type="courier_delivery_time_changed",
                        title="Изменение времени доставки",
                        body=f"Время доставки заказа #{external_number or order.id} изменено: ожидается к {time_str}",
                        order_id=order.id,
                        order_number=external_number or order.id,
                        url="/pers/courier",
                        extra_data={
                            "expected_time": order.expected_time.isoformat() if order.expected_time else None,
                            "amount": float(total_with_discount),
                            "address": order.delivery_address
                        },
                        order=order
                    )
            except Exception as courier_notif_err:
                logger.error(f"Error sending dedicated courier notifications: {courier_notif_err}")
            
        except Exception as e:
            import traceback
            logger.error(f"CRITICAL Error processing order {iiko_order_data.get('id', 'unknown')}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Мы не делаем rollback полностью, чтобы один кривой заказ не останавливал весь цикл, 
            # но и не коммитим частично сломанные данные.
            try:
                await asyncio.to_thread(session.rollback)
            except:
                pass

    async def check_and_send_order_new_to_courier(
        self, 
        order, 
        session: Session = None, 
        is_reassigned: bool = False, 
        old_courier: str = None, 
        new_courier: str = None
    ) -> bool:
        """
        Проверяет готовность заказа для отправки по цепочке "order_new" (Шаг 1 «Новый заказ курьеру»):
        - Заказ не является самовывозом
        - Курьер назначен на заказ (если в цепочке включено require_courier_assigned)
        - Время готовности на кухне задано (>0 мин), если в цепочке включено require_cooking_time_set
        - Заказ не был ранее отправлен текущему курьеру (или разрешен повтор resend_on_courier_reassigned при смене курьера)
        """
        try:
            if not order:
                return False

            # 0. Завершенный / закрытый / доставленный / отмененный заказ курьеру как "новый" не отправляется
            st_lower = str(getattr(order, 'status', '') or '').lower()
            if st_lower in ("delivered", "closed", "cancelled", "доставлен", "закрыт", "отменен") or getattr(order, 'is_closed', False):
                logger.debug(f"Order #{getattr(order, 'external_number', order.id)}: order_new suppressed because status is terminal '{st_lower}'")
                return False

            # 1. Самовывоз курьеру не отправляется
            ord_type_str = str(getattr(order, 'order_type', '') or '').lower()
            if "самовывоз" in ord_type_str or "pickup" in ord_type_str:
                return False

            # 2. Проверка назначенного курьера
            c_name = getattr(order, 'courier_name', None) or new_courier
            has_assigned_courier = bool(c_name and str(c_name).strip() not in ("", "Не назначен", "---"))

            # 3. Проверка активности шаблона order_new в БД
            from app.models.vk_bot import VkTemplate
            from app.core.database import engine
            def _get_template():
                s = session if session else Session(engine)
                try:
                    return s.exec(select(VkTemplate).where(VkTemplate.event_type == "order_new")).first()
                finally:
                    if not session:
                        s.close()

            tpl = await asyncio.to_thread(_get_template)
            if not tpl or not getattr(tpl, 'is_active', True):
                return False

            chain_config_obj = {}
            if tpl and tpl.chain_config:
                try:
                    import json
                    if isinstance(tpl.chain_config, str):
                        chain_config_obj = json.loads(tpl.chain_config)
                    elif isinstance(tpl.chain_config, dict):
                        chain_config_obj = tpl.chain_config
                except Exception:
                    chain_config_obj = {}

            # Если требуется назначенный курьер, а курьер не назначен — ждем
            if chain_config_obj.get("require_courier_assigned", True) and not has_assigned_courier:
                logger.debug(f"Order #{order.external_number or order.id}: order_new pending assigned courier")
                return False

            # 4. Проверка требования времени готовности кухни
            if chain_config_obj.get("require_cooking_time_set"):
                cook_mins = int(getattr(order, 'cooking_time_minutes', 0) or 0)
                if cook_mins <= 0:
                    logger.debug(f"Order #{order.external_number or order.id}: order_new pending cooking time > 0 (current: {cook_mins})")
                    return False

            # 5. Проверка требования "только неоплаченные"
            if chain_config_obj.get("only_unpaid") and getattr(order, 'is_paid', False):
                logger.debug(f"Order #{order.external_number or order.id}: order_new requires unpaid, but order is paid")
                return False

            # 6. Проверка: отправлялся ли уже order_new текущему курьеру
            change_indicators = dict(getattr(order, 'change_indicators', None) or {})
            already_sent_courier = change_indicators.get("order_new_sent_courier")

            if has_assigned_courier:
                if already_sent_courier and already_sent_courier == c_name:
                    # Уже отправлялся этому курьеру
                    return False

                if already_sent_courier and already_sent_courier != c_name:
                    # Курьер сменился (переназначение)
                    resend_on_reassign = chain_config_obj.get("resend_on_courier_reassigned", True)
                    if not resend_on_reassign:
                        logger.info(f"Order #{order.external_number or order.id}: courier changed from '{already_sent_courier}' to '{c_name}', but resend_on_courier_reassigned is False")
                        return False
            else:
                if change_indicators.get("order_new_sent_unassigned"):
                    return False

            # 7. Отправляем order_new назначенному курьеру
            logger.info(f"Dispatching step 1 'order_new' to courier '{c_name or 'все'}' for order #{order.external_number or order.id} (cooking_time={getattr(order, 'cooking_time_minutes', 0)} min)")
            await self._send_order_vk_notification(
                order,
                "order_new",
                session=session,
                is_reassigned=is_reassigned,
                old_courier=old_courier or already_sent_courier,
                new_courier=c_name
            )

            # 8. Фиксируем отправку в change_indicators
            if has_assigned_courier:
                change_indicators["order_new_sent_courier"] = c_name
            else:
                change_indicators["order_new_sent_unassigned"] = True
            change_indicators["order_new_sent_at"] = datetime.now(timezone.utc).isoformat()
            order.change_indicators = change_indicators
            if session:
                session.add(order)
                await asyncio.to_thread(session.commit)

            return True
        except Exception as e:
            logger.error(f"Error in check_and_send_order_new_to_courier for order {getattr(order, 'id', None)}: {e}")
            return False

    async def send_order_notification(self, order, event_type: str, session: Session = None, **extra_flags):
        """Публичный метод для отправки уведомлений о заказах"""
        await self._send_order_vk_notification(order, event_type, session=session, **extra_flags)

    async def _send_order_vk_notification(self, order, event_type: str, session: Session = None, **extra_flags):
        """Вспомогательный метод для отправки уведомлений о заказах в ВК"""
        try:
            # --- Каскадное уведомление Гостя ---
            try:
                from app.services.mailing_cascade_service import mailing_cascade_service
                cust_id = getattr(order, 'customer_id', None)
                if cust_id:
                    await mailing_cascade_service.trigger_cascade(
                        customer_id=cust_id,
                        event_type=event_type,
                        order_id=getattr(order, 'id', None)
                    )
            except Exception as ce:
                logger.error(f"Error in mailing cascade: {ce}")

            # --- Уведомление Сотрудников (через Router) ---
            from app.models.order import OrderStatus
            status_text = {
                OrderStatus.new: "Новый заказ",
                OrderStatus.unconfirmed: "Не подтвержден",
                OrderStatus.confirmed: "Подтвержден",
                OrderStatus.cooking: "Готовится",
                OrderStatus.ready: "Готов",
                OrderStatus.ready_for_pickup: "Готов к выдаче",
                OrderStatus.delivering: "В пути",
                OrderStatus.delivered: "Доставлен",
                OrderStatus.closed: "Закрыт",
                OrderStatus.cancelled: "ОТМЕНЕН ❌"
            }.get(order.status, str(order.status))

            # Формируем контекст данных для шаблона
            order_items_text = ""
            # Сначала пробуем из order_items_details (JSON), так как там самые свежие данные из вебхука
            if order and hasattr(order, 'order_items_details') and order.order_items_details:
                items_list = []
                for item in order.order_items_details:
                    name = item.get('name', 'Товар')
                    amount = item.get('amount', 1)
                    price = item.get('price', 0)
                    items_list.append(f"• {name} x{amount} ({float(price)*float(amount):.0f} ₽)")
                order_items_text = "\n".join(items_list)
            # Фолбэк на связанные объекты
            elif order and hasattr(order, 'items') and order.items:
                items_list = []
                for item in order.items:
                    items_list.append(f"• {item.product_name} x{item.quantity} ({float(item.total):.0f} ₽)")
                order_items_text = "\n".join(items_list)

            # Создаем расширенный объект контекста с отформатированными полями
            # Чтобы в шаблоне можно было писать {{ order.total_amount }} и получать красивую строку
            from datetime import timedelta
            from app.core.datetime_utils import get_tz_name, to_local, utc_now

            tz_name = get_tz_name(session) if session else "Asia/Yekaterinburg"
            addr_str = getattr(order, 'delivery_address', '---') or '---'
            exp_time_str = getattr(order, 'expected_time', '').strftime('%d.%m %H:%M') if getattr(order, 'expected_time', None) else '---'
            
            cooking_mins = int(getattr(order, 'cooking_time_minutes', 0) or 0)
            cooking_updated_at = getattr(order, 'cooking_time_updated_at', None)
            if cooking_updated_at:
                local_cooking_dt = to_local(cooking_updated_at, tz_name)
            else:
                local_cooking_dt = to_local(utc_now(), tz_name)

            cooking_set_time_str = local_cooking_dt.strftime('%H:%M')
            cooking_updated_at_str = local_cooking_dt.strftime('%d.%m %H:%M')

            if cooking_mins > 0:
                pickup_dt = local_cooking_dt + timedelta(minutes=cooking_mins)
                pickup_time_str = pickup_dt.strftime('%H:%M')
                arrival_time_str = pickup_dt.strftime('%H:%M')
                pickup_time_full_str = pickup_dt.strftime('%d.%m %H:%M')
            else:
                pickup_time_str = exp_time_str if exp_time_str != "---" else "Уточняется на кухне"
                arrival_time_str = pickup_time_str
                pickup_time_full_str = exp_time_str

            formatted_order = {
                "id": getattr(order, 'id', None),
                "external_number": getattr(order, 'external_number', '---'),
                "order_number": getattr(order, 'external_number', str(getattr(order, 'id', '---'))),
                "total_amount": f"{float(getattr(order, 'total_amount', 0)):.0f}",
                "total_with_discount": f"{float(getattr(order, 'total_with_discount', 0)):.0f}",
                "total_discount": f"{float(getattr(order, 'total_discount', 0)):.0f}",
                "discount_sum": f"{float(getattr(order, 'total_discount', 0)):.0f}",
                "final_price": f"{float(getattr(order, 'total_with_discount', 0)):.0f}",
                "bonus_spent": f"{float(getattr(order, 'bonus_spent', 0)):.0f}",
                "bonus_accrued": f"{float(getattr(order, 'bonus_accrued', 0)):.0f}",
                "delivery_address": addr_str,
                "address": addr_str,
                "city": getattr(order, 'city', ''),
                "street": getattr(order, 'street', ''),
                "house": getattr(order, 'house', ''),
                "flat": getattr(order, 'flat', ''),
                "customer_name": getattr(order, 'customer_name', 'Гость'),
                "customer_phone": getattr(order, 'customer_phone', '---'),
                "comment": getattr(order, 'comment', ''),
                "address_comment": getattr(order, 'address_comment', '') or '',
                "entrance": getattr(order, 'entrance', '') or '',
                "floor": getattr(order, 'floor', '') or '',
                "doorphone": getattr(order, 'doorphone', '') or '',
                "additional_info": getattr(order, 'additional_info', '') or '',
                "other_info": getattr(order, 'other_info', '') or '',
                "courier_notes": getattr(order, 'additional_info', '') or getattr(order, 'other_info', '') or '',
                "notes": getattr(order, 'additional_info', '') or getattr(order, 'other_info', '') or '',
                "status": status_text,
                "raw_status": str(getattr(order, 'status', '')),
                "order_type": getattr(order, 'order_type', '---'),
                "payment_method": getattr(order, 'payment_method', '---'),
                "is_paid": "Оплачен" if getattr(order, 'is_paid', False) else "Не оплачен",
                "courier_name": getattr(order, 'courier_name', '---'),
                "delivery_zone": getattr(order, 'delivery_zone', '---'),
                "expected_time": exp_time_str,
                "delivery_time": exp_time_str,
                "cooking_time_minutes": str(cooking_mins),
                "cooking_time": str(cooking_mins),
                "cooking_set_time": cooking_set_time_str,
                "cooking_updated_at": cooking_updated_at_str,
                "pickup_time": pickup_time_str,
                "arrival_time": arrival_time_str,
                "ready_time": pickup_time_str,
                "pickup_time_full": pickup_time_full_str,
                "items_text": order_items_text,
                "items_summary": order_items_text, # Синоним для удобства
                "customer_info_details": getattr(order, 'customer_info_details', {}) or {}
            }

            # Формируем чистый полный адрес для навигатора (Город, Улица, Дом) без квартиры/комментария
            import urllib.parse
            city_val = getattr(order, 'city', '') or ''
            street_val = getattr(order, 'street', '') or ''
            house_val = getattr(order, 'house', '') or ''
            clean_nav_addr = ", ".join([p for p in [city_val, street_val, house_val] if p]) or addr_str

            if clean_nav_addr and clean_nav_addr not in ("Самовывоз", "---"):
                encoded_addr = urllib.parse.quote_plus(clean_nav_addr)
                formatted_order["map_yandex"] = f"https://yandex.ru/maps/?rtext=~{encoded_addr}&rtt=auto"
                formatted_order["map_2gis"] = f"https://2gis.ru/search/{encoded_addr}"
                formatted_order["yandex_navigator"] = f"https://yandex.ru/maps/?rtext=~{encoded_addr}&rtt=auto"
                formatted_order["map_navigator"] = f"https://yandex.ru/maps/?rtext=~{encoded_addr}&rtt=auto"
            elif getattr(order, 'latitude', None) and getattr(order, 'longitude', None):
                lat = getattr(order, 'latitude')
                lon = getattr(order, 'longitude')
                formatted_order["map_yandex"] = f"https://yandex.ru/maps/?pt={lon},{lat}&z=18&l=map"
                formatted_order["map_2gis"] = f"https://2gis.ru/geo/{lon},{lat}"
                formatted_order["yandex_navigator"] = f"https://yandex.ru/maps/?rtext=~{lat}%2C{lon}&rtt=auto"
                formatted_order["map_navigator"] = f"https://yandex.ru/maps/?rtext=~{lat}%2C{lon}&rtt=auto"
            else:
                formatted_order["map_yandex"] = ""
                formatted_order["map_2gis"] = ""
                formatted_order["yandex_navigator"] = ""
                formatted_order["map_navigator"] = ""

            context = {
                "order": formatted_order,
                "customer": order.customer if hasattr(order, 'customer') else None
            }

            # Стандартное сообщение (fallback), если шаблон не будет найден
            fallback_msg = [
                f"🔔 {status_text} #{formatted_order['external_number']}",
                f"Сумма: {formatted_order['total_with_discount']} руб.",
                f"Клиент: {formatted_order['customer_name']}",
                f"Тип: {formatted_order['order_type']}",
                f"Адрес: {formatted_order['delivery_address']}"
            ]
            
            if formatted_order['comment']:
                fallback_msg.append(f"Коммент: {formatted_order['comment']}")
                
            if formatted_order['courier_name'] and formatted_order['courier_name'] != "Не назначен":
                fallback_msg.append(f"Курьер: {formatted_order['courier_name']}")

            if order_items_text:
                fallback_msg.append("\nСостав заказа:")
                fallback_msg.append(order_items_text)


            context["chain_flags"] = extra_flags

            await vk_notification_router.dispatch_event(
                event_type=event_type, 
                message_text="\n".join(fallback_msg),
                context_data=context,
                **extra_flags
            )
        except Exception as e:
            logger.error(f"Error sending VK notification: {e}")
            import traceback
            logger.error(traceback.format_exc())

    async def _send_shift_vk_notification(self, shift, employee, event_type: str):
        """Вспомогательный метод для уведомлений о сменах"""
        try:
            status_text = "ОТКРЫТА" if event_type == "shift_open" else "ЗАКРЫТА"
            
            # Формируем контекст данных для шаблона
            context = {
                "shift": shift,
                "employee": employee,
                "kitchen_revenue": getattr(shift, "kitchen_revenue", None) or 0.0,
                "hot_revenue": getattr(shift, "hot_revenue", None) or 0.0
            }

            # Fallback сообщение
            msg = [
                f"👤 Смена {status_text}",
                f"Сотрудник: {employee.name}",
                f"Роль: {employee.role or '---'}",
                f"Начало: {shift.date_open.strftime('%d.%m %H:%M')}"
            ]
            if shift.date_close:
                msg.append(f"Конец: {shift.date_close.strftime('%d.%m %H:%M')}")
                msg.append(f"Отработано: {shift.work_hours} ч.")
                if shift.revenue_at_close is not None:
                    msg.append(f"Выручка: {round(shift.revenue_at_close, 2):,.2f} ₽")
                if getattr(shift, "kitchen_revenue", None) or getattr(shift, "hot_revenue", None):
                    if shift.kitchen_revenue:
                        msg.append(f"• Кухня: {round(shift.kitchen_revenue, 2):,.2f} ₽")
                    if shift.hot_revenue:
                        msg.append(f"• Горячий цех: {round(shift.hot_revenue, 2):,.2f} ₽")
            
            await vk_notification_router.dispatch_event(
                event_type=event_type, 
                message_text="\n".join(msg),
                context_data=context
            )
        except Exception as e:
            logger.error(f"Error sending VK shift notification: {e}")

    async def sync_orders(self, session: Session, hours: int = 24, fast_only: bool = False, skip_revision: bool = False):
        from app.models.order import Order, OrderStatus
        """
        Массовая загрузка и синхронизация заказов.
        fast_only: использовать только инкрементальную синхронизацию по ревизиям (быстрее)
        skip_revision: пропустить проверку ревизий и сделать полный опрос за указанный период
        """
        def _get_settings():
            return session.exec(select(IikoSettings)).first()
        settings_db = await asyncio.to_thread(_get_settings)
        
        if not settings_db or not settings_db.organization_id:
            logger.warning("Iiko settings not found, sync aborted")
            return

        # Если разрешена быстрая синхронизация и мы не пропускаем ревизии
        if fast_only and not skip_revision:
            logger.info("Быстрая синхронизация: опрос ревизий + прямая сверка активных заказов iiko...")
            await self.sync_orders_by_revision(session, settings_db.organization_id)
            
            # Гарантированная подгрузка всех активных заказов и предзаказов из iiko
            try:
                active_orders = await self.iiko.get_active_orders(
                    organization_id=settings_db.organization_id,
                    api_login=settings_db.api_login
                )
                if active_orders:
                    logger.info(f"Fast sync fetched {len(active_orders)} active orders directly from iiko")
                    for ord_data in active_orders:
                        try:
                            await self.process_iiko_order(session, ord_data, settings_db.organization_id)
                        except Exception as ord_err:
                            logger.error(f"Error processing active order from fast sync: {ord_err}")
            except Exception as active_err:
                logger.error(f"Error during active orders fetch in fast sync: {active_err}")
            return

        def _init_log():
            l = SyncLog(sync_type="orders", status="running")
            session.add(l)
            session.commit()
            return l
        log = await asyncio.to_thread(_init_log)
        
        try:
            org_id = settings_db.organization_id
        
            # Определяем интервал на основе часового пояса из настроек
            from app.core.datetime_utils import get_tz_name, get_local_now
            tz_name = await asyncio.to_thread(get_tz_name, session)
            now = get_local_now(tz_name)
            
            # В быстром режиме опрашиваем только последние 4 часа, если не указано иное
            if fast_only and hours == 24:
                hours = 4

            # Охватываем диапазон с учетом предзаказов на вечер (+14 часов)
            date_from = now - timedelta(hours=hours)
            date_to = now + timedelta(hours=14)
            
            logger.info(f"Mass sync starting: orders from {date_from} to {date_to} for org {org_id} (fast_only={fast_only})")
            
            all_ids = set()

            # 0. Инкрементальная синхронизация по ревизиям (быстрый catch-up пропущенных вебхуков)
            if not skip_revision:
                try:
                    await self.sync_orders_by_revision(session, org_id)
                except Exception as rev_err:
                    logger.error(f"Revision sync failed, falling back to date polling: {rev_err}")

            # 1. Из iiko Cloud (по датам доставки) - как запасной механизм
            # Мы разбиваем использование интервалов на чанки, так как это снижает вероятность ошибки TOO_MANY_DATA_REQUESTED
            logger.info(f"Starting robust polling in 2-hour chunks for period {date_from} - {date_to}")
            
            cloud_orders = []
            chunk_start = date_from
            while chunk_start < date_to:
                chunk_end = chunk_start + timedelta(hours=2)
                if chunk_end > date_to:
                    chunk_end = date_to
                    
                try:
                    logger.debug(f"Polling chunk: {chunk_start} - {chunk_end}")
                    batch = await self.iiko.get_orders_by_date(
                        date_from=chunk_start,
                        date_to=chunk_end,
                        organization_id=org_id,
                        api_login=settings_db.api_login,
                        log_error=True # Включаем логирование, чтобы видеть подробности ошибок
                    )
                    if batch:
                        logger.info(f"Fetched {len(batch)} orders for period {chunk_start} - {chunk_end}")
                        cloud_orders.extend(batch)
                    
                    # Небольшая пауза между чанками для безопасности
                    await asyncio.sleep(0.5)
                except Exception as chunk_err:
                    logger.error(f"Failed to fetch orders chunk ({chunk_start} - {chunk_end}): {chunk_err}")
                    if "429" in str(chunk_err):
                        await asyncio.sleep(5.0)
                
                chunk_start = chunk_end

            for o in cloud_orders:
                if o.get("id"): all_ids.add(o["id"])
            logger.info(f"Found {len(cloud_orders)} orders in Cloud (via date polling)")
                
            # 2. Из iiko Resto (если настроен)
            if settings_db.resto_url and settings_db.resto_login:
                try:
                    resto_ids = await self.iiko.get_resto_delivery_history(
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
                    
            # 3. Дополнительно: Проверяем все активные заказы из нашей БД
            # Это крайне важно, если iiko Cloud API по датам возвращает некорректные данные или вебхуки пропущены
            try:
                # Включаем все статусы, которые не являются финальными (закрыт/отменен)
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
                
                # Все статусы переводим в верхний регистр на всякий случай, если в БД записаны значения
                active_strings = [s.value for s in active_statuses] + [s.value.upper() for s in active_statuses]
                
                query = select(Order).where(Order.status.in_(active_strings))
                def _get_active_orders():
                    return session.exec(query).all()
                db_active_orders = await asyncio.to_thread(_get_active_orders)
                
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
                    # Добавляем небольшую задержку, чтобы не превышать лимиты API (429) 
                    if success_count > 0 and success_count % 15 == 0:
                        await asyncio.sleep(0.5)

                    # Используем sync_order_by_id для каждого заказа
                    # Мы не хотим, чтобы ошибка в одном заказе прервала весь цикл
                    res = await self.sync_order_by_id(session, order_id, org_id)
                    if res: success_count += 1
                except Exception as e:
                    logger.error(f"Failed to sync order {order_id}: {e}")
                    try:
                        await asyncio.to_thread(session.rollback)
                    except Exception:
                        pass
                    
            logger.info(f"Mass sync finished. Total: {len(all_ids)}, Success: {success_count}")
            def _final_log():
                log.status = "success"
                log.processed_count = success_count
                log.details = f"Успешно синхронизировано {success_count} заказов из {len(all_ids)}"
                session.add(log)
                session.commit()
            await asyncio.to_thread(_final_log)
        
        except Exception as e:
            logger.error(f"Error in mass order sync: {e}", exc_info=True)
            def _error_log_final():
                log.status = "error"
                log.details = str(e)
                session.add(log)
                session.commit()
            await asyncio.to_thread(_error_log_final)

    async def sync_orders_by_revision(self, session: Session, organization_id: str):
        """
        Синхронизация заказов по ревизиям (catch-up).
        Позволяет получить все измененные заказы, которые были пропущены вебхуками, независимо от даты.
        """
        # 0. Защита от слишком частых вызовов (не чаще чем раз в 20 секунд)
        now = datetime.now()
        last_sync = self._last_rev_sync.get(organization_id)
        if last_sync and (now - last_sync).total_seconds() < 20:
            logger.debug(f"Revision sync for {organization_id} skipped (too soon)")
            return
        self._last_rev_sync[organization_id] = now

        def _get_settings():
            return session.exec(
                select(IikoSettings).where(IikoSettings.organization_id == organization_id)
            ).first()
        settings_db = await asyncio.to_thread(_get_settings)
        if not settings_db: return
        
        current_revision = settings_db.last_order_revision or 0
        logger.info(f"Starting revision sync from revision {current_revision} for org {organization_id}")
        
        try:
            # 1. Если ревизия 0 или пустая - инициализируем начальную точку (baseline)
            if current_revision == 0:
                logger.info(f"Revision 0 detected for org {organization_id}. Initializing revision baseline...")
                
                # Получаем актуальную ревизию из Iiko для дальнейших инкрементальных обновлений
                # Мы НЕ вызываем sync_orders рекурсивно здесь, так как mass-sync 
                # (который может быть родителем этого вызова) сам заботится о выгрузке истории по датам.
                new_max = await self.iiko.get_max_revision(
                    organization_id=organization_id,
                    api_login=settings_db.api_login
                )
                if new_max:
                    def _save_baseline():
                        settings_db.last_order_revision = new_max
                        session.add(settings_db)
                        session.commit()
                    await asyncio.to_thread(_save_baseline)
                    logger.info(f"Cold Start successful. New baseline revision: {new_max}")
                return

            # 2. Запрашиваем изменения с последней ревизии
            data = await self.iiko.get_deliveries_by_revision(
                organization_id=organization_id,
                initial_revision=current_revision,
                api_login=settings_db.api_login
            )
            
            # iiko_service.get_deliveries_by_revision возвращает уже распакованный ordersByOrganizations
            orders = data.get("orders", [])
            max_revision = data.get("maxRevision")
            
            if not orders:
                logger.info("No new orders found by revision sync")
                if max_revision and max_revision > current_revision:
                    def _update_rev_empty():
                        settings_db.last_order_revision = max_revision
                        session.add(settings_db)
                        session.commit()
                    await asyncio.to_thread(_update_rev_empty)
                    logger.info(f"Revision updated to {max_revision} even with no orders")
                return

            logger.info(f"Found {len(orders)} orders via revision sync. Processing...")
            
            count = 0
            for order_data in orders:
                try:
                    # Обрабатываем каждый заказ
                    await self.process_iiko_order(session, order_data, organization_id)
                    count += 1
                except Exception as e:
                    logger.error(f"Error processing order from revision: {e}")
                    try:
                        await asyncio.to_thread(session.rollback)
                    except Exception:
                        pass
            
            # Обновляем ревизию в настройках
            if max_revision:
                def _update_rev_final():
                    settings_db.last_order_revision = max_revision
                    session.add(settings_db)
                    session.commit()
                await asyncio.to_thread(_update_rev_final)
                logger.info(f"Revision sync finished. New revision: {max_revision}, Processed: {count}")
                
        except httpx.HTTPStatusError as e:
            # 3. Обрабатываем ошибку "TOO_OLD_REVISION" (Код 400)
            if e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    if error_data.get("error") == "TOO_OLD_REVISION":
                        logger.warning(f"Revision {current_revision} is too old. Starting 'Cold Start' recovery...")
                        
                        # Сбрасываем ревизию, чтобы при следующем вызове (или рекурсивном) сработал Cold Start
                        def _reset_rev():
                            settings_db.last_order_revision = 0
                            session.add(settings_db)
                            session.commit()
                        await asyncio.to_thread(_reset_rev)
                        
                        # Запускаем Cold Start немедленно
                        await self.sync_orders_by_revision(session, organization_id)
                        return 
                except Exception as parse_err:
                    logger.error(f"Failed to handle 400 error: {parse_err}")
            
            logger.error(f"Iiko API error during revision sync: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in sync_orders_by_revision: {e}")

    async def sync_order_by_id(self, session: Session, order_id: str, organization_id: str) -> bool:
        """Синхронизация конкретного заказа по ID (вызывается вебхуками)"""
        def _get_settings():
            return session.exec(select(IikoSettings)).first()
        settings_db = await asyncio.to_thread(_get_settings)
        api_login = settings_db.api_login if settings_db else None
        try:
            order_data = await self.iiko.get_order_by_id(order_id, organization_id, api_login=api_login)
            if order_data:
                await self.process_iiko_order(session, order_data, organization_id)
                return True
        except Exception as e:
            logger.error(f"Failed to sync order {order_id}: {e}")
        return False

    async def sync_delivery_restrictions(self, session: Session) -> Dict[str, Any]:
        """Синхронизация зон и условий доставки из iiko Cloud"""
        def _get_settings():
            return session.exec(select(IikoSettings)).first()
        settings_db = await asyncio.to_thread(_get_settings)
        if not settings_db or not settings_db.organization_id:
            return {"error": "Iiko not configured"}
            
        try:
            data = await iiko_service.get_delivery_restrictions(
                api_login=settings_db.api_login,
                organization_id=settings_db.organization_id
            )
            
            # Обработка ответа iiko может быть {"deliveryRestrictions": [...]} или просто списком
            restrictions_data = []
            if isinstance(data, dict):
                restrictions_data = data.get("deliveryRestrictions", [])
            elif isinstance(data, list):
                restrictions_data = data
            elif isinstance(data, str):
                logger.error(f"iiko API returned string instead of dict/list: {data}")
                return {"error": f"iiko API error: {data}"}
                
            if not restrictions_data:
                logger.warning("Нет данных об ограничениях доставки от iiko")
                return {"success": True, "synced": 0, "message": "No restrictions data"}

            synced_count = 0
            
            for restriction_item in restrictions_data:
                if not isinstance(restriction_item, dict):
                    continue
                    
                # 1. Находим филиал (терминальную группу)
                tg_id = restriction_item.get("terminalGroupId")
                if not tg_id:
                    def _get_first_branch():
                        return session.exec(select(Branch)).first()
                    branch = await asyncio.to_thread(_get_first_branch)
                    logger.warning("restriction_item missing terminalGroupId, using first branch as fallback")
                else:
                    def _get_branch_by_tg():
                        return session.exec(select(Branch).where(Branch.iiko_terminal_id == tg_id)).first()
                    branch = await asyncio.to_thread(_get_branch_by_tg)
                
                if not branch:
                    logger.warning(f"Филиал с iiko_terminal_id {tg_id} не найден в БД, пропускаем ограничения")
                    continue

                # 2. Собираем полигоны из KML для этого филиала/ограничения
                branch_polygons = {}
                map_url = restriction_item.get("deliveryRegionsMapUrl")
                if map_url:
                    logger.info(f"Найдена ссылка на карту для филиала {branch.name}: {map_url}. Загружаем полигоны...")
                    try:
                        kml_zones = await iiko_service.fetch_and_parse_kml(map_url)
                        for kz in kml_zones:
                            # Сохраняем полигон по имени зоны (в нижнем регистре для сопоставления)
                            name_key = kz["name"].lower().strip()
                            branch_polygons[name_key] = kz["coordinates"]
                            logger.info(f"Загружена геометрия для зоны '{kz['name']}' из iiko-карты")
                    except Exception as e:
                        logger.error(f"Ошибка при загрузке полигонов для филиала {branch.name}: {e}")

                # 3. Обрабатываем зоны внутри ограничений
                for res in restriction_item.get("restrictions", []):
                    zone_name = res.get("zone")
                    if not zone_name:
                        continue
                        
                    min_sum = float(res.get("minSum") or 0)
                    delivery_cost = float(res.get("deliveryPrice") or 0)
                    
                    # Используем zoneId из iiko если есть, иначе имя
                    iiko_zone_id = res.get("zoneId") or zone_name
                    
                    # Ищем зону для конкретного филиала
                    def _sync_zone_and_poly():
                        # Используем closure для branch, iiko_zone_id, zone_name, min_sum, delivery_cost, res, branch_polygons, coords
                        z = session.exec(select(DeliveryZone).where(
                            (DeliveryZone.branch_id == branch.id) & 
                            ((DeliveryZone.iiko_id == iiko_zone_id) | (DeliveryZone.name == zone_name))
                        )).first()
                        
                        if not z:
                            z = DeliveryZone(
                                name=zone_name, 
                                branch_id=branch.id, 
                                iiko_id=iiko_zone_id
                            )
                            session.add(z)
                            session.flush() # Получаем ID
                        
                        # Обновляем параметры зоны
                        z.iiko_id = iiko_zone_id
                        z.min_order_amount = min_sum
                        z.delivery_cost = delivery_cost
                        z.min_delivery_time = res.get("minDeliveryTime")
                        z.max_delivery_time = res.get("maxDeliveryTime")
                        z.free_delivery_sum = float(res.get("freeDeliverySum") or 0) if res.get("freeDeliverySum") is not None else None
                        z.priority = int(res.get("priority") or 0)
                        z.is_default = bool(res.get("isDefault"))
                        z.updated_at = datetime.now(timezone.utc)
                        z.is_active = True
                        
                        # 4. Синхронизируем геометрию в CustomPolygon
                        z_key = zone_name.lower().strip()
                        if z_key in branch_polygons:
                            coords = branch_polygons[z_key]
                            # Ищем существующий полигон для этой зоны
                            poly = session.exec(select(CustomPolygon).where(
                                CustomPolygon.delivery_zone_id == z.id
                            )).first()
                            
                            if not poly:
                                poly = CustomPolygon(
                                    name=z.name,
                                    delivery_zone_id=z.id,
                                    branch_id=branch.id,
                                    coordinates=coords,
                                    fill_color="#4caf50",
                                    priority=z.priority,
                                    min_order_amount=z.min_order_amount,
                                    delivery_cost=z.delivery_cost,
                                    is_active=True
                                )
                                session.add(poly)
                            else:
                                # Обновляем координаты и параметры
                                poly.coordinates = coords
                                poly.priority = z.priority
                                poly.min_order_amount = z.min_order_amount
                                poly.delivery_cost = z.delivery_cost
                                poly.is_active = True
                                session.add(poly)
                            
                            # Сохраняем и в текстовое поле зоны (для совместимости)
                            z.polygon_coordinates = json.dumps(coords)
                        
                        z.additional_info = res
                        session.add(z)
                        return z
                    
                    zone = await asyncio.to_thread(_sync_zone_and_poly)
                    synced_count += 1
                
            await asyncio.to_thread(session.commit)
            logger.info(f"Синхронизация ограничений доставки завершена: {synced_count} зон")
            return {"success": True, "synced": synced_count, "message": f"Successfully synced {synced_count} zones"}
            
        except Exception as e:
            await asyncio.to_thread(session.rollback)
            logger.error(f"Ошибка при синхронизации ограничений доставки iiko: {e}", exc_info=True)
            return {"error": str(e)}

    async def get_available_iiko_zones(self, session: Session) -> List[Dict[str, Any]]:
        """Получает список всех доступных зон из iiko Cloud (без сохранения)"""
        def _get_settings():
            return session.exec(select(IikoSettings)).first()
        settings_db = await asyncio.to_thread(_get_settings)
        if not settings_db or not settings_db.organization_id:
            return []
            
        try:
            data = await iiko_service.get_delivery_restrictions(
                api_login=settings_db.api_login,
                organization_id=settings_db.organization_id
            )
            
            # Обработка ответа iiko: может быть {"deliveryRestrictions": [...]} или список
            restrictions_data = []
            if isinstance(data, dict):
                restrictions_data = data.get("deliveryRestrictions", [])
            elif isinstance(data, list):
                restrictions_data = data
            
            unique_zones = {}
            for org_data in restrictions_data:
                if not isinstance(org_data, dict):
                    continue
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

    # Старые методы удалены, так как они дублировали новые версии в начале файла


    async def ensure_super_admin(self, session: Session) -> None:
        """Создание супер-администратора и базовых разрешений"""
        from app.core.security import get_password_hash
        from app.models.role import RolePermissionLink

        def _sync_logic():
            # 1. Создаем базовые разрешения если их нет
            base_perms = [
                ("admin_access", "Доступ в админ-панель"),
                ("users_manage", "Управление пользователями"),
                ("roles_manage", "Управление ролями и правами"),
                ("orders_view", "Просмотр заказов"),
                ("reports_view", "Просмотр отчетов"),
                ("settings_manage", "Управление настройками"),
                ("sync_run", "Запуск синхронизации"),
                ("purchase_view", "Просмотр закупа"),
                ("purchase_manage", "Управление закупом"),
                ("settings_validation_view", "Просмотр настроек валидации телефонов"),
                ("settings_validation_edit", "Изменение настроек валидации и тестирование отправки")
            ]
            
            for code, name in base_perms:
                perm = session.exec(select(Permission).where(Permission.code == code)).first()
                if not perm:
                    session.add(Permission(code=code, name=name))
            
            session.flush()

            # 2. Создаем роль Супер Администратор
            super_role = session.exec(select(Role).where(Role.code == "SUPER_ADMIN")).first()
            if not super_role:
                super_role = Role(name="Супер Администратор", code="SUPER_ADMIN")
                session.add(super_role)
                session.flush()
            
            # Привязываем все разрешения к роли SUPER_ADMIN
            all_perms = session.exec(select(Permission)).all()
            for p in all_perms:
                link = session.exec(select(RolePermissionLink).where(
                    RolePermissionLink.role_id == super_role.id,
                    RolePermissionLink.permission_id == p.id
                )).first()
                if not link:
                    session.add(RolePermissionLink(role_id=super_role.id, permission_id=p.id))

            # 3. Создаем пользователя 0001
            user = session.exec(select(User).where(User.username == "0001")).first()
            if not user:
                user = User(
                    username="0001",
                    email="admin@72roll.ru",
                    hashed_password=get_password_hash("121212"),
                    full_name="Супер Администратор",
                    role_id=super_role.id,
                    is_active=True,
                    is_superuser=True
                )
                session.add(user)
                logger.info("Создан супер-пользователь 0001")
            else:
                user.role_id = super_role.id
            
            session.commit()

        await asyncio.to_thread(_sync_logic)

    async def sync_employees_full(self, session: Session, days: int = 7) -> None:
        """
        Полная синхронизация сотрудников и их смен через iiko RESTO (Office) API.
        """
        def _get_initial_data():
            s = session.exec(select(IikoSettings)).first()
            tz = self._get_tz(session)
            return s, tz
            
        settings_db, tz = await asyncio.to_thread(_get_initial_data)
        
        if not settings_db or not settings_db.resto_url:
            logger.error("Настройки iiko Resto (Office) не найдены. Синхронизация отменена.")
            return

        now_local = datetime.now(tz)
        date_from = now_local - timedelta(days=days)

        # --- Шаг 1: Синхронизация профилей сотрудников ---
        # Параметры подключения берем из БД, а не из ENV
        r_url = settings_db.resto_url
        r_login = settings_db.resto_login
        r_password = settings_db.resto_password
        try:
            logger.info("Запрос списка сотрудников из iiko Resto...")
            iiko_employees = await iiko_service.get_resto_employees(
                resto_url=r_url, resto_login=r_login, resto_password=r_password
            )
            
            def _process_employees():
                from app.models.role import Role
                for emp in iiko_employees:
                    emp_iiko_id = emp.get("id")
                    if not emp_iiko_id: continue
                    
                    name = emp.get("name") or f"{emp.get('firstName', '')} {emp.get('lastName', '')}".strip()
                    role = emp.get("role")
                    rate = emp.get("salary")
                    
                    # Документы и доп. инфо
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
                        return ("курьер" in r_l or "courier" in r_l or r_l in ["cur", "cour"]
                                or "курьер" in n_l or "courier" in n_l)
                    def _flag_admin(r, n=""):
                        r_l = (r or "").lower()
                        return any(k in r_l for k in ["администратор", "оператор", "manager", "старший", "adm", "admin"])

                    # Поиск роли в локальной БД
                    iiko_role_id = emp.get("mainRoleId")
                    local_role = None
                    if iiko_role_id:
                        local_role = session.exec(select(Role).where(Role.iiko_id == iiko_role_id)).first()
                    
                    if not local_role and role:
                        local_role = session.exec(select(Role).where(Role.name == role)).first()
                    
                    role_id = local_role.id if local_role else None

                    if existing:
                        existing.name = name
                        existing.role = role or existing.role
                        existing.phone = emp.get("phone") or existing.phone
                        existing.email = emp.get("email") or existing.email
                        existing.address = emp.get("address") or existing.address
                        existing.rate = rate if rate is not None else existing.rate
                        existing.document_info = doc_info
                        existing.status = "Deleted" if emp.get("deleted") else "Active"
                        existing.is_courier = _flag_courier(existing.role, name)
                        existing.is_admin = _flag_admin(existing.role)
                        existing.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
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
                            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
                            updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
                        )
                        session.add(new_emp)
                
                session.commit()

            await asyncio.to_thread(_process_employees)
            logger.info(f"Успешно синхронизировано {len(iiko_employees)} профилей сотрудников из iiko Resto")
        except Exception as e:
            logger.error(f"Ошибка синхронизации профилей: {e}")
            await asyncio.to_thread(session.rollback)

        # --- Шаг 1.5: Дополнение данными из iiko Cloud (ОТКЛЮЧЕНО по требованию пользователя - старого Server API) ---
        # try:
        #      logger.info("Запрос дополнительных данных из iiko Cloud...")
        #      cloud_employees = await iiko_service.get_employees(api_login=settings_db.api_login, organization_id=settings_db.organization_id)
        #      updated_cloud_c = 0
        #      for c_emp in cloud_employees:
        #          emp_iiko_id = c_emp.get("id")
        #          if not emp_iiko_id: continue
        #          
        #          existing = session.exec(select(Employee).where(Employee.iiko_id == emp_iiko_id)).first()
        #          # Если сотрудника нет из Resto, но он есть в Cloud (например, внешний курьер)
        #          if not existing:
        #              role = ""
        #              if c_emp.get("isCourier"): role = "Курьер (Cloud)"
        #              
        #              new_emp = Employee(
        #                  iiko_id=emp_iiko_id,
        #                  name=c_emp.get("name", "Unknown"),
        #                  role=role,
        #                  phone=c_emp.get("phone"),
        #                  status="Active",
        #                  is_courier=c_emp.get("isCourier", False),
        #                  created_at=datetime.now(timezone.utc),
        #                  updated_at=datetime.now(timezone.utc)
        #              )
        #              session.add(new_emp)
        #              updated_cloud_c += 1
        #          else:
        #              # Дополняем данные, если их нет
        #              if c_emp.get("isCourier") and not existing.is_courier:
        #                  existing.is_courier = True
        #                  session.add(existing)
        #                  updated_cloud_c += 1
        #      session.commit()
        #      logger.info(f"Успешно дополнено {updated_cloud_c} профилей из iiko Cloud")
        # except Exception as e:
        #      logger.error(f"Ошибка при синхронизации профилей из Cloud: {e}")
        #      session.rollback()

        # --- Шаг 2: Синхронизация использования смен через Attendance API ---
        try:
            logger.info(f"Запрос явок (смен) через Attendance API ({date_from.date()} - {now_local.date()})...")
            attendance_records = await iiko_service.get_resto_attendance(
                resto_url=r_url, resto_login=r_login, resto_password=r_password,
                date_from=date_from, date_to=now_local,
                log_error=False
            )

            def _process_shifts():
                from sqlalchemy import func
                from app.models.employee import Shift
                from app.models.olap_revenue import OlapRevenueRecord

                def _parse_to_utc_sync(s):
                    if not s: return None
                    try:
                        return datetime.fromisoformat(str(s)).astimezone(timezone.utc)
                    except Exception:
                        return None

                created_c, updated_c = 0, 0
                notifications = [] # (shift_id, employee_id, type)
                
                for row in attendance_records:
                    emp_iiko_id = row.get("employeeId")
                    if not emp_iiko_id: continue

                    employee = session.exec(select(Employee).where(Employee.iiko_id == emp_iiko_id)).first()
                    if not employee: continue

                    date_open = _parse_to_utc_sync(row.get("dateOpen"))
                    date_close = _parse_to_utc_sync(row.get("dateClose"))
                    if not date_open: continue

                    if not date_close:
                        now_utc = datetime.now(timezone.utc)
                        work_hours = (now_utc - date_open).total_seconds() / 3600.0
                    else:
                        work_hours = (date_close - date_open).total_seconds() / 3600.0

                    work_hours = min(work_hours, 24.0)
                    shift_iiko_id = row.get("id") or f"att_{employee.id}_{date_open.strftime('%Y%m%d%H%M')}"

                    from app.services.shift_service import calculate_shift_metrics

                    # Создаем временную сущность для расчета метрик смены
                    temp_shift = Shift(
                        date_open=date_open,
                        date_close=date_close,
                        employee_id=employee.id
                    )
                    shift_metrics = calculate_shift_metrics(session, temp_shift, employee)
                    revenue_at_close = shift_metrics["total_revenue"]
                    kitchen_revenue = shift_metrics["kitchen_revenue"]
                    hot_revenue = shift_metrics["hot_revenue"]
                    cancelled_orders_count = shift_metrics["cancelled_count"]
                    deliveries_count = shift_metrics["deliveries_count"]

                    existing_shift = session.exec(
                        select(Shift).where(Shift.iiko_id == shift_iiko_id)
                    ).first()

                    if existing_shift:
                        old_status = existing_shift.status
                        existing_shift.date_close = date_close
                        existing_shift.status = "CLOSED" if date_close else "OPEN"
                        existing_shift.work_hours = round(work_hours, 2)
                        existing_shift.revenue_at_close = revenue_at_close
                        existing_shift.kitchen_revenue = kitchen_revenue
                        existing_shift.hot_revenue = hot_revenue
                        existing_shift.cancelled_orders_count = cancelled_orders_count
                        if deliveries_count > 0:
                            existing_shift.deliveries_count = deliveries_count
                        existing_shift.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                        session.add(existing_shift)
                        updated_c += 1
                        
                        if old_status == "OPEN" and existing_shift.status == "CLOSED":
                            notifications.append((existing_shift.id, employee.id, "shift_close"))
                    else:
                        new_shift = Shift(
                            iiko_id=shift_iiko_id,
                            employee_id=employee.id,
                            date_open=date_open,
                            date_close=date_close,
                            status="CLOSED" if date_close else "OPEN",
                            work_hours=round(work_hours, 2),
                            cancelled_orders_count=cancelled_orders_count,
                            deliveries_count=deliveries_count,
                            revenue_at_close=revenue_at_close,
                            kitchen_revenue=kitchen_revenue,
                            hot_revenue=hot_revenue,
                            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
                            updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
                        )
                        session.add(new_shift)
                        session.flush() # Ensure we have new_shift.id
                        created_c += 1
                        
                        if new_shift.status == "OPEN":
                            notifications.append((new_shift.id, employee.id, "shift_open"))

                session.commit()
                return created_c, updated_c, notifications

            res_created, res_updated, pending_notifications = await asyncio.to_thread(_process_shifts)
            
            # Send notifications outside of thread
            for shift_id, emp_id, n_type in pending_notifications:
                # Need objects for the notification method, but session is still open
                def _get_objs():
                    s = session.get(Shift, shift_id)
                    e = session.get(Employee, emp_id)
                    return s, e
                
                s_obj, e_obj = await asyncio.to_thread(_get_objs)
                if s_obj and e_obj:
                    await self._send_shift_vk_notification(s_obj, e_obj, n_type)

            logger.info(f"Успешно: Attendance смены: создано {res_created}, обновлено {res_updated} из {len(attendance_records)} записей")
        except Exception as e:
            logger.error(f"Ошибка синхронизации Attendance смен: {e}", exc_info=True)
            await asyncio.to_thread(session.rollback)

        # --- Шаг 3 (Удален): Синхронизация через personalSessions взамен Attendance ---
        # Личные смены обрабатываются в Шаге 2 через Attendance API,
        # поэтому вызов personalSessions здесь не нужен (он дублирует и выдает 404).
        pass

    async def get_employee_stats(self, session: Session, employee_id: int, mode: str = "calendar") -> Dict[str, Any]:
        """
        Получение статистики сотрудника за период.
        mode: 'calendar' (текущая неделя) или 'sliding' (последние 7 дней)
        """
        def _get_tz_sync():
            return self._get_tz(session)
        
        tz = await asyncio.to_thread(_get_tz_sync)
        now_local = datetime.now(tz)
        
        if mode == "calendar":
            # С понедельника текущей недели
            start_date = (now_local - timedelta(days=now_local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now_local
        else:
            # Последние 7 дней
            start_date = (now_local - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now_local
            
        def _process():
            # Загружаем смены из БД
            shifts = session.exec(
                select(Shift)
                .where(Shift.employee_id == employee_id)
                .where(Shift.date_open >= start_date.astimezone(timezone.utc).replace(tzinfo=None))
                .order_by(Shift.date_open.desc())
            ).all()
            
            total_hours = sum(s.work_hours for s in shifts if s.work_hours)
            total_revenue = sum(float(s.revenue_at_close or 0) for s in shifts)
            
            # Группировка по дням
            daily_stats = {}
            for s in shifts:
                # Переводим время открытия в локальное для группировки по датам
                s_open_utc = s.date_open.replace(tzinfo=timezone.utc)
                s_open_local = s_open_utc.astimezone(tz)
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
                
                # Формируем объект смены для фронтенда
                shift_info = {
                    "id": s.id,
                    "open": s_open_local.isoformat(),
                    "close": s.date_close.replace(tzinfo=timezone.utc).astimezone(tz).isoformat() if s.date_close else None,
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

        return await asyncio.to_thread(_process)

    async def sync_courier_deliveries(self, session: Session, days: int = 14, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> None:
        from app.models.order import Order
        from app.models.employee import Employee, CourierOrder
        from app.models.system_log import SystemLog
        from app.models.iiko_settings import IikoSettings
        """
        Синхронизация детальных доставок курьеров из iiko Resto OLAP.
        Заполняет таблицу courier_orders: зоны, суммы, временные метки, задержки.
        """
        logger.info(f"==> Запуск синхронизации доставок курьеров (days={days}, from={date_from}, to={date_to})")
        
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db or not settings_db.resto_url:
            logger.warning("Resto не настроен, синхронизация доставок пропущена")
            return

        tz = self._get_tz(session)
        now_local = datetime.now(tz)
        
        if not date_from:
            date_from = now_local - timedelta(days=days)
        if not date_to:
            date_to = now_local

        logger.info(f"Синхронизация доставок курьеров из Resto OLAP ({date_from} до {date_to})...")

        org_id = settings_db.organization_id or ""
        try:
            deliveries = await self.iiko.get_resto_detailed_deliveries(
                date_from=date_from,
                date_to=date_to,
                organization_id=org_id,
                resto_url=settings_db.resto_url,
                resto_login=settings_db.resto_login,
                resto_password=settings_db.resto_password
            )
            logger.info(f"Fetched {len(deliveries)} deliveries from OLAP")
        except Exception as e:
            logger.error(f"Ошибка получения данных из iiko: {e}")
            return

        # Кэшируем сотрудников
        all_employees = session.exec(select(Employee)).all()
        courier_by_name: Dict[str, Employee] = {}
        courier_by_id: Dict[str, Employee] = {}
        for emp in all_employees:
            is_c = emp.is_courier or any(k in (emp.role or "").lower() for k in ["курьер", "courier", "cur"])
            if is_c:
                courier_by_name[(emp.name or "").lower().strip()] = emp
                if emp.iiko_id:
                    courier_by_id[emp.iiko_id] = emp

        def _parse_dt_sync(s):
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

        async def _process_delivery(d):
            order_num = str(d.get("Delivery.Number") or d.get("id") or "").strip()
            if not order_num: return None

            courier_emp = None
            courier_info = d.get("courierInfo", {}).get("courier", {}) if isinstance(d.get("courierInfo"), dict) else {}
            
            courier_iiko_id = d.get("Delivery.Courier.Id") or courier_info.get("id")
            if courier_iiko_id:
                courier_emp = courier_by_id.get(courier_iiko_id)
            
            if not courier_emp:
                courier_name_raw = d.get("Delivery.Courier") or courier_info.get("name") or ""
                courier_name_key = courier_name_raw.lower().strip()
                courier_emp = courier_by_name.get(courier_name_key)
                
                if not courier_emp:
                    def _get_meaningful_words(name):
                        words = (name or "").lower().split()
                        return {w for w in words if len(w) > 2 and w not in ["курьер", "courier", "cur"]}
                    
                    target_words = _get_meaningful_words(courier_name_raw)
                    for key, emp in courier_by_name.items():
                        emp_words = _get_meaningful_words(emp.name)
                        if target_words and emp_words and (target_words & emp_words):
                            courier_emp = emp
                            break

            if not courier_emp:
                db_order = await asyncio.to_thread(lambda: session.exec(
                    select(Order).where(Order.external_number == order_num)
                ).first())
                if db_order and db_order.courier_name and db_order.courier_name != "Не назначен":
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

            if not courier_emp: return None

            cooking_done = _parse_dt_sync(d.get("Delivery.CookingFinishTime") or d.get("whenCookingCompleted"))
            expected_dt = _parse_dt_sync(d.get("Delivery.ExpectedTime") or d.get("expectedDeliveryTime"))
            actual_dt = _parse_dt_sync(d.get("Delivery.ActualTime") or d.get("Delivery.SendTime") or d.get("whenDelivered") or d.get("whenConfirmationFinished"))

            delay_min = None
            is_late = False
            if expected_dt and actual_dt:
                diff = (actual_dt - expected_dt).total_seconds() / 60
                delay_min = int(diff)
                is_late = diff > 0

            addr_data = d.get("address") if isinstance(d.get("address"), dict) else {}
            addr_parts = {
                "city": d.get("Delivery.City") or addr_data.get("city"),
                "street": d.get("Delivery.Street") or addr_data.get("street"),
                "house": d.get("Delivery.House") or addr_data.get("house"),
                "flat": d.get("Delivery.Flat") or addr_data.get("flat"),
                "entrance": d.get("Delivery.Entrance") or addr_data.get("entrance"),
                "floor": d.get("Delivery.Floor") or addr_data.get("floor"),
                "doorphone": d.get("Delivery.Doorphone") or addr_data.get("doorphone"),
                "line1": d.get("Delivery.Line1") or d.get("Delivery.Address") or addr_data.get("line1") or addr_data.get("addressString")
            }
            raw_address_str = addr_parts["line1"] or ""
            
            if raw_address_str and (not addr_parts.get("house") or not addr_parts.get("flat")):
                import re
                def find_comp(regex, text):
                    m = re.search(regex, text, re.IGNORECASE)
                    return m.group(1).strip() if m else None
                if not addr_parts.get("house"): addr_parts["house"] = find_comp(r'[,\s](?:д\.|дом|уч\.)[\s]*([^\,\s]+)', raw_address_str)
                if not addr_parts.get("flat"): addr_parts["flat"] = find_comp(r'[,\s](?:кв\.|квартира)[\s]*([^\,\s]+)', raw_address_str)

            db_order_addr = await asyncio.to_thread(lambda: session.exec(select(Order).where(Order.external_number == order_num)).first())
            if db_order_addr and db_order_addr.address_parts:
                for key, val in db_order_addr.address_parts.items():
                    if not addr_parts.get(key) and val: addr_parts[key] = val
            
            city_name = settings_db.city_name if settings_db else "Тюмень"
            address_str = self.format_address(addr_parts, city=city_name, fmt="line1")
            
            zone_name = d.get("Delivery.Zone") or d.get("deliveryZone")
            if not zone_name or zone_name in ["---", "", None]:
                try:
                    zone_info = await self.iiko.check_address_zone(
                        organization_id=org_id, city=addr_parts.get("city") or city_name,
                        street=addr_parts.get("street") or addr_parts.get("line1") or "",
                        house=addr_parts.get("house") or ""
                    )
                    zone_name = zone_info.get("zone") if zone_info else "Вне зоны"
                except Exception: zone_name = "Ошибка определения"

            ref_date = actual_dt or cooking_done or datetime.now(timezone.utc)
            iiko_uid = f"olap_{order_num}_{ref_date.strftime('%Y%m%d')}"
            amount_val = float(d.get("fullSum") or d.get("sum") or 0)

            return {
                "iiko_id": iiko_uid,
                "order_num": order_num,
                "employee_id": courier_emp.id,
                "address": address_str,
                "address_parts": addr_parts,
                "delivery_zone": zone_name,
                "amount": amount_val,
                "cooking_completed_at": cooking_done,
                "expected_delivery_time": expected_dt,
                "actual_delivery_time": actual_dt,
                "delay_minutes": delay_min,
                "is_late": is_late,
                "customer_name": d.get("Delivery.CustomerName") or d.get("customer", {}).get("name"),
                "customer_phone": normalize_phone(d.get("Delivery.Phone") or d.get("customer", {}).get("phone"))
            }

        processed_data = []
        for d in deliveries:
            res = await _process_delivery(d)
            if res: processed_data.append(res)

        async def _save_item(item):
            def _db_op():
                # 1. Обновляем Order
                try:
                    from sqlalchemy import or_
                    db_order = session.exec(select(Order).where(Order.external_number == item["order_num"])).first()
                    if db_order and (not db_order.courier_name or db_order.courier_name == "Не назначен"):
                        courier_emp = session.get(Employee, item["employee_id"])
                        if courier_emp:
                            db_order.courier_name = courier_emp.name
                            if item.get("actual_delivery_time"): db_order.actual_time = item["actual_delivery_time"]
                            session.add(db_order)
                except Exception as e: logger.error(f"Error updating Order: {e}")

                # 2. Обновляем CourierOrder
                existing = session.exec(select(CourierOrder).where(CourierOrder.iiko_id == item["iiko_id"])).first()
                if existing:
                    for key, val in item.items():
                        if hasattr(existing, key) and val is not None: setattr(existing, key, val)
                    existing.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    session.add(existing)
                    return False
                else:
                    session.add(CourierOrder(**item))
                    return True

            return await asyncio.to_thread(_db_op)

        created_c, updated_c = 0, 0
        new_deliveries = []
        try:
            for item in processed_data:
                if await _save_item(item):
                    created_c += 1
                    new_deliveries.append(item)
                else:
                    updated_c += 1
            await asyncio.to_thread(session.commit)
            logger.info(f"Courier sync finished: {created_c} created, {updated_c} updated")
            
            # Отправка уведомлений о назначении доставок курьерам
            for item in new_deliveries:
                try:
                    from app.models.user import User
                    from app.models.employee import Employee
                    from sqlalchemy import cast, String
                    from app.models.admin_notification_settings import AdminNotificationSettings
                    from app.models.push_subscription import PushSubscription
                    from app.core.webpush_utils import send_web_push
                    
                    courier_emp = session.get(Employee, item["employee_id"])
                    if courier_emp:
                        c_user = session.exec(
                            select(User).where(
                                cast(User.iiko_id, String) == cast(courier_emp.iiko_id, String)
                            )
                        ).first()
                        
                        if c_user:
                            # Проверяем настройки курьера
                            c_settings = session.exec(select(AdminNotificationSettings).where(AdminNotificationSettings.user_id == c_user.id)).first()
                            if c_settings and not c_settings.courier_delivery_push_enabled:
                                continue
                                
                            subscriptions = session.exec(select(PushSubscription).where(PushSubscription.user_id == c_user.id)).all()
                            if subscriptions:
                                global_settings = session.exec(select(AdminNotificationSettings).where(AdminNotificationSettings.id == 1)).first()
                                if global_settings and global_settings.vapid_private_key:
                                    payload_data = json.dumps({
                                        "title": "Новая доставка!",
                                        "body": f"Заказ #{item.get('order_num')}. Адрес: {item.get('address')}. Сумма: {item.get('amount')} ₽",
                                        "icon": "/favicon.ico",
                                        "url": "/courier",
                                        "event_type": "courier_delivery"
                                    }, ensure_ascii=False)
                                    
                                    db_changed = False
                                    for sub in subscriptions:
                                        sub_info = {
                                            "endpoint": sub.endpoint,
                                            "keys": {
                                                "p256dh": sub.p256dh,
                                                "auth": sub.auth
                                            }
                                        }
                                        res = send_web_push(sub_info, payload_data, global_settings.vapid_private_key)
                                        if res == "remove":
                                            session.delete(sub)
                                            db_changed = True
                                    if db_changed:
                                        session.commit()
                            
                            # Отправка WebSocket-уведомления на личную страницу курьера
                            try:
                                from app.api.chat import manager
                                ws_payload = {
                                    "type": "courier_delivery",
                                    "order_num": item.get('order_num'),
                                    "address": item.get('address'),
                                    "amount": item.get('amount')
                                }
                                await manager.send_personal_message(ws_payload, c_user.id)
                            except Exception as ws_err:
                                logger.error(f"WebSocket courier alert error: {ws_err}")
                except Exception as courier_err:
                    logger.error(f"Failed to notify courier for delivery {item.get('order_num')}: {courier_err}")
        except Exception as e:
            await asyncio.to_thread(session.rollback)
            logger.error(f"Courier sync save failed: {e}")

    async def sync_courier_deliveries_bg(self, date_from: datetime, date_to: datetime):
        """Вспомогательный метод для запуска синхронизации в бэкграунде (через потоки)"""
        from app.core.database import SessionLocal
        with SessionLocal() as session:
            try:
                await self.sync_courier_deliveries(session, date_from=date_from, date_to=date_to)
            except Exception as e:
                logger.error(f"Error in courier deliveries background sync: {e}")
                session.rollback()

    async def sync_zones_from_external_map(self, session: Session, url: Optional[str] = None) -> Dict[str, Any]:
        """Синхронизация внешних полигонов зон из облачного хранилища"""
        def _get_settings():
            return session.exec(select(IikoSettings)).first()
        
        settings_rec = await asyncio.to_thread(_get_settings)
        if url and settings_rec:
            def _update_url():
                settings_rec.delivery_zones_map_url = url
                session.add(settings_rec)
                session.commit()
            await asyncio.to_thread(_update_url)
            
        map_url = url or (settings_rec.delivery_zones_map_url if settings_rec else None)

        if not map_url:
            return {"success": False, "error": "Ссылка на карту не задана"}
        
        try:
            kml_zones = await self.iiko.fetch_and_parse_kml(map_url)
            if not kml_zones:
                return {"success": False, "error": "Не удалось получить зоны"}
        except Exception as e:
            return {"success": False, "error": f"Ошибка при загрузке: {str(e)}"}
            
        def _process_zones():
            updated_count = 0
            all_zones = session.exec(select(DeliveryZone)).all()
            for kz in kml_zones:
                name = kz["name"].strip()
                matched_zone = next((z for z in all_zones if (z.name or "").lower() == name.lower()), None)
                if matched_zone:
                    matched_zone.polygon_coordinates = json.dumps(kz["points"])
                    matched_zone.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    session.add(matched_zone)
                    updated_count += 1
            session.commit()
            return updated_count
                
        count = await asyncio.to_thread(_process_zones)
        return {"success": True, "updated_count": count}

    async def sync_zones_from_kml_file(self, session: Session, kml_content: str) -> Dict[str, Any]:
        """Синхронизация из загруженного KML файла"""
        try:
            kml_zones = self.iiko.parse_kml_content(kml_content)
            if not kml_zones:
                return {"success": False, "error": "Зоны не найдены"}
        except Exception as e:
            return {"success": False, "error": f"Ошибка парсинга: {str(e)}"}
            
        def _process():
            updated_count = 0
            for kz in kml_zones:
                name = kz["name"].strip()
                matched_zone = session.exec(select(DeliveryZone).where(func.lower(DeliveryZone.name) == name.lower())).first()
                if matched_zone:
                    matched_zone.polygon_coordinates = json.dumps(kz["points"])
                    matched_zone.is_manual_override = True
                    matched_zone.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    session.add(matched_zone)
                    updated_count += 1
            session.commit()
            return updated_count

        try:
            count = await asyncio.to_thread(_process)
            try:
                from app.core.redis import redis_client
                await redis_client.delete("delivery_zones_all")
            except Exception: pass
            return {"success": True, "updated_count": count, "total_from_file": len(kml_zones)}
        except Exception as e:
            await asyncio.to_thread(session.rollback)
            logger.error(f"Ошибка сохранения геометрии зон из файла: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Управление клиентской базой (Очистка и объединение)
    # =========================================================================

    async def find_customers_missing_iiko_data(self, session: Session) -> List[Customer]:
        """Поиск клиентов, у которых отсутствует iiko_id или uid."""
        from sqlalchemy import or_
        def _query():
            statement = select(Customer).where(
                or_(
                    Customer.iiko_id == None,
                    Customer.uid == None,
                    Customer.iiko_id == "",
                    Customer.uid == ""
                )
            )
            return session.exec(statement).all()
        
        customers = await asyncio.to_thread(_query)
        logger.info(f"Найдено {len(customers)} клиентов с отсутствующими ID iiko")
        return customers

    async def merge_customers_by_uid(self, session: Session) -> Dict[str, Any]:
        """Объединение аккаунтов с одинаковыми iiko UID (Неблокирующая версия)"""
        def get_duplicates():
            statement = select(Customer.uid).where(Customer.uid != None, Customer.uid != "").group_by(Customer.uid).having(func.count(Customer.uid) > 1)
            return session.exec(statement).all()
        
        duplicate_uids = await asyncio.to_thread(get_duplicates)
        if not duplicate_uids:
            return {"success": True, "merged_groups": 0, "message": "Дубликаты по UID не найдены"}

        merged_groups_count = 0
        total_deleted = 0
        
        for uid in duplicate_uids:
            def process_group():
                group_statement = select(Customer).where(Customer.uid == uid).order_by(Customer.id)
                group = session.exec(group_statement).all()
                if len(group) < 2: return 0
                
                master = group[0]
                duplicates = group[1:]
                self._merge_customer_group_sync(session, master, duplicates)
                session.commit()
                return len(duplicates)
            
            deleted_count = await asyncio.to_thread(process_group)
            if deleted_count > 0:
                merged_groups_count += 1
                total_deleted += deleted_count
            
        return {"success": True, "merged_groups": merged_groups_count, "total_deleted": total_deleted}

    async def merge_customers_by_phone(self) -> Dict[str, Any]:
        """Объединение аккаунтов с одинаковыми номерами телефонов (Неблокирующая версия)"""
        def do_merge():
            from app.core.database import engine, Session
            with Session(engine) as session:
                statement = select(Customer.phone).group_by(Customer.phone).having(func.count(Customer.phone) > 1)
                duplicate_phones = session.exec(statement).all()
                
                if not duplicate_phones:
                    return 0, 0

                merged_groups_count = 0
                total_deleted = 0
                
                for phone in duplicate_phones:
                    group_statement = select(Customer).where(Customer.phone == phone).order_by(Customer.id)
                    group = session.exec(group_statement).all()
                    if len(group) < 2: continue
                    
                    master = group[0]
                    duplicates = group[1:]
                    self._merge_customer_group_sync(session, master, duplicates)
                    session.commit()
                    
                    merged_groups_count += 1
                    total_deleted += len(duplicates)
                
                return merged_groups_count, total_deleted
        
        merged_groups, total_deleted = await asyncio.to_thread(do_merge)
        return {"success": True, "merged_groups": merged_groups, "total_deleted": total_deleted}

    async def _update_master_from_iiko_async(self, session: Session, phone: str):
        """Обновление данных мастера из iiko Cloud (Асинхронно)"""
        try:
            from app.services.iiko_service import iiko_service
            iiko_data = await iiko_service.get_customer_info(phone)
            if iiko_data and iiko_data.get("id"):
                def update_sync():
                    master = session.exec(select(Customer).where(Customer.phone == phone)).first()
                    if not master: return
                    
                    master.iiko_id = iiko_data.get("id")
                    master.iiko_customer_id = iiko_data.get("id")
                    master.uid = iiko_data.get("id")
                    
                    if iiko_data.get("name") and (not master.name or master.name == "Гость"):
                        master.name = iiko_data["name"]
                    
                    wallets = iiko_data.get("walletBalances", [])
                    if wallets:
                        master.bonus_points = Decimal(str(wallets[0].get("balance", 0)))
                    
                    master.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    session.add(master)
                    session.commit()
                
                await asyncio.to_thread(update_sync)
        except Exception as e:
            logger.error(f"Ошибка обновления мастера {phone}: {e}")

    def _merge_customer_group_sync(self, session: Session, master: Customer, duplicates: List[Customer]):
        """Синхронное слияние группы дублей (выполняется в asyncio.to_thread)"""
        from app.models.order import Order
        from app.models.customer import GuestPhone, GuestAddress, ClientAddressHistory, BonusTransaction, ClientBonusHistory
        from sqlalchemy import update
        
        for dup in duplicates:
            logger.info(f"Слияние дубля ID={dup.id} в мастер ID={master.id}")
            
            # 1. Перепривязка заказов
            session.exec(update(Order).where(Order.customer_id == dup.id).values(customer_id=master.id))
            
            # 2. Перепривязка телефонов
            for p in session.exec(select(GuestPhone).where(GuestPhone.customer_id == dup.id)).all():
                exists = session.exec(select(GuestPhone).where(GuestPhone.customer_id == master.id, GuestPhone.phone == p.phone)).first()
                if not exists and p.phone != master.phone:
                    p.customer_id = master.id
                    session.add(p)
                else:
                    session.delete(p)
            
            # 3. Перепривязка адресов
            for a in session.exec(select(GuestAddress).where(GuestAddress.customer_id == dup.id)).all():
                exists = session.exec(select(GuestAddress).where(GuestAddress.customer_id == master.id, GuestAddress.address == a.address)).first()
                if not exists:
                    a.customer_id = master.id
                    session.add(a)
                else:
                    session.delete(a)
            
            # 4. Перепривязка транзакций и истории
            session.exec(update(BonusTransaction).where(BonusTransaction.customer_id == dup.id).values(customer_id=master.id))
            session.exec(update(ClientBonusHistory).where(ClientBonusHistory.client_id == dup.id).values(client_id=master.id))
            session.exec(update(ClientAddressHistory).where(ClientAddressHistory.client_id == dup.id).values(client_id=master.id))
            
            # 5. Мета-данные
            if not master.vk_user_id and dup.vk_user_id: master.vk_user_id = dup.vk_user_id
            if not master.telegram_id and dup.telegram_id: master.telegram_id = dup.telegram_id
            if not master.email and dup.email: master.email = dup.email
            if not master.name or master.name == "Гость": master.name = dup.name
            if not master.surname and dup.surname: master.surname = dup.surname
            
            # 6. Статистика
            master.total_orders_count = (master.total_orders_count or 0) + (dup.total_orders_count or 0)
            master.total_orders_amount = (master.total_orders_amount or Decimal("0")) + (dup.total_orders_amount or Decimal("0"))
            master.total_purchases_sum = (master.total_purchases_sum or Decimal("0")) + (dup.total_purchases_sum or Decimal("0"))
            
            if dup.last_order_date and (not master.last_order_date or dup.last_order_date > master.last_order_date):
                master.last_order_date = dup.last_order_date
                master.last_iiko_order_id = dup.last_iiko_order_id
            
            # 7. Удаление дубликата
            session.delete(dup)
        

    async def sync_loyalty_items(self, session: Session) -> Dict[str, Any]:
        """
        Синхронизация всех элементов лояльности (программы, купоны, условия, скидки)
        """
        try:
            settings_db = session.exec(select(IikoSettings)).first()
            if not settings_db:
                return {"success": False, "error": "iiko settings not found"}

            api_login = settings_db.api_login
            org_id = settings_db.organization_id

            # 1. Получаем данные из iiko Cloud API
            results = await asyncio.gather(
                self.iiko.get_loyalty_programs(api_login, org_id),
                self.iiko.get_loyalty_coupons_series(api_login, org_id),
                self.iiko.get_loyalty_manual_conditions(api_login, org_id),
                self.iiko.get_discount_types(api_login, org_id),
                return_exceptions=True
            )

            # Распаковываем результаты
            programs_data = results[0] if not isinstance(results[0], Exception) else {"Programs": []}
            coupons_data = results[1] if not isinstance(results[1], Exception) else {"seriesWithNotActivatedCoupons": []}
            manual_data = results[2] if not isinstance(results[2], Exception) else {"manualConditions": []}
            discounts_data = results[3] if not isinstance(results[3], Exception) else []

            # 2. Обработка данных
            items_to_sync = []
            
            # Программы (Ключ "Programs")
            programs_list = programs_data.get("Programs", []) if isinstance(programs_data, dict) else []
            for p in programs_list:
                # Определяем тип программы
                prog_type = p.get("programType")
                is_certificate = (prog_type == 4)
                
                items_to_sync.append({
                    "iiko_id": p["id"],
                    "name": p.get("name") or p.get("caption") or ("Unnamed Certificate Program" if is_certificate else "Unnamed Program"),
                    "type": "certificate" if is_certificate else "program",
                    "description": p.get("description"),
                    "content": p
                })
                
                # Извлекаем маркетинговые акции из программы
                campaigns = p.get("marketingCampaigns", [])
                for campaign in campaigns:
                    items_to_sync.append({
                        "iiko_id": campaign["id"],
                        "name": campaign.get("name") or campaign.get("caption") or "Unnamed Promotion",
                        "type": "promotion",
                        "description": campaign.get("description"),
                        "content": {**campaign, "parent_program_id": p["id"]}
                    })
            
            # Купоны (Ключ "seriesWithNotActivatedCoupons")
            series_list = coupons_data.get("seriesWithNotActivatedCoupons", []) if isinstance(coupons_data, dict) else []
            for s in series_list:
                items_to_sync.append({
                    "iiko_id": s["id"],
                    "name": s.get("name") or s.get("caption") or s.get("number") or "Unnamed Coupon Series",
                    "type": "coupon_series",
                    "description": s.get("description") or s.get("number"),
                    "content": s
                })

            # Ручные условия
            manual_list = manual_data.get("manualConditions", []) if isinstance(manual_data, dict) else []
            for m in manual_list:
                items_to_sync.append({
                    "iiko_id": m["id"],
                    "name": m.get("caption") or m.get("name") or "Unnamed Manual Condition",
                    "type": "manual_condition",
                    "description": None,
                    "content": m
                })

            # Скидки
            for d in (discounts_data if isinstance(discounts_data, list) else []):
                items_to_sync.append({
                    "iiko_id": d["id"],
                    "name": d.get("name", "Unnamed Discount"),
                    "type": "discount",
                    "description": d.get("description"),
                    "content": d
                })

            # 3. Сохранение в БД
            synced_count = 0
            try:
                for item_data in items_to_sync:
                    stmt = select(IikoLoyaltyItem).where(IikoLoyaltyItem.iiko_id == item_data["iiko_id"])
                    existing_result = session.exec(stmt).first()
                    
                    if existing_result:
                        existing = existing_result if isinstance(existing_result, IikoLoyaltyItem) else existing_result[0]
                        existing.name = item_data["name"]
                        existing.type = item_data["type"]
                        existing.description = item_data["description"]
                        existing.content = item_data["content"]
                        existing.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                        session.add(existing)
                    else:
                        new_item = IikoLoyaltyItem(**item_data)
                        session.add(new_item)
                    synced_count += 1
                
                session.commit()
                logger.info(f"Successfully synced {synced_count} loyalty items from iiko Cloud")
            except Exception as e:
                session.rollback()
                logger.error(f"Error during loyalty items DB save: {e}")
                raise e
            
            # Логируем
            from app.models.sync_log import SyncLog
            new_log = SyncLog(
                sync_type="loyalty_items",
                status="success",
                processed_count=synced_count,
                details=f"Synced {synced_count} loyalty items"
            )
            session.add(new_log)
            session.commit()
            
            return {
                "success": True,
                "synced_count": synced_count,
                "message": f"Синхронизировано элементов: {synced_count}"
            }

        except Exception as e:
            logger.error(f"Loyalty sync error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def send_admin_push_notification(self, session: Session, title: str, body: str, url: str, event_type: str, target_user_id: Optional[int] = None, tag: Optional[str] = None, order: Optional[Any] = None):
        """Отправляет push-уведомление всем администраторам, у которых есть подписки с учетом их настроек"""
        try:
            from app.models.admin_notification_settings import AdminNotificationSettings
            from app.models.push_subscription import PushSubscription
            from app.core.webpush_utils import send_web_push
            import json

            # Автоматическая фиксация в ленту центра уведомлений (независимо от браузерных пушей)
            try:
                from app.api.notifications import log_system_notification
                cat = "new_order" if event_type == "new_order" else (
                    "tbank_payment" if event_type == "new_payment" else "order_status"
                )
                b_text = "Новый заказ" if cat == "new_order" else (
                    "Оплата" if cat == "tbank_payment" else "Статус заказа"
                )
                b_color = "success" if cat == "new_order" else (
                    "info" if cat == "tbank_payment" else "warning"
                )
                ord_id = getattr(order, "id", None) if order else None
                amt = float(getattr(order, "total_with_discount", None) or getattr(order, "total_amount", None) or 0.0) if order else None
                ext_key = f"{event_type}_{ord_id}_{tag or int(datetime.now(timezone.utc).timestamp())}" if ord_id else None
                log_system_notification(
                    db=session,
                    title=title,
                    body=body,
                    event_type=event_type,
                    category=cat,
                    url=url,
                    badge_text=b_text,
                    badge_color=b_color,
                    amount=amt,
                    order_id=ord_id,
                    external_key=ext_key
                )
            except Exception as log_err:
                logger.warning(f"Error logging feed notification in iiko_sync_service: {log_err}")

            global_settings = session.exec(select(AdminNotificationSettings).where(AdminNotificationSettings.id == 1)).first()
            if not global_settings or not global_settings.vapid_private_key:
                return
            if getattr(global_settings, 'disable_browser_notifications_all', False):
                logger.info("[Push] Skipped push notifications: disable_browser_notifications_all is True")
                return
                
            subscriptions = session.exec(select(PushSubscription)).all()
            if not subscriptions:
                return
                
            payload_data = json.dumps({
                "title": title,
                "body": body,
                "icon": "/favicon.ico",
                "url": url,
                "event_type": event_type,
                "tag": tag
            }, ensure_ascii=False)
            
            db_changed = False
            notified_users = set()
            from app.models.user import User
            for sub in subscriptions:
                if target_user_id is not None and sub.user_id != target_user_id:
                    continue
                    
                user_obj = session.get(User, sub.user_id)
                is_courier = False
                if user_obj and (user_obj.role_id == 7 or (getattr(user_obj, 'role', None) and getattr(user_obj.role, 'name', '') == "courier")):
                    is_courier = True
                    
                if is_courier and getattr(global_settings, 'disable_browser_notifications_couriers', False):
                    continue
                    
                if is_courier and event_type == "order_delivered":
                    continue

                # Проверяем настройки конкретного пользователя
                user_settings = session.exec(select(AdminNotificationSettings).where(AdminNotificationSettings.user_id == sub.user_id)).first()
                
                # Поведение по умолчанию, если настроек нет
                push_enabled = True
                if user_settings:
                    # Фильтрация по типу заказа для изменений в заказах
                    if event_type in ("order_changed", "order_cancelled", "change_cooking_time", "change_items", "change_amount", "change_payment", "change_address") and order:
                        scope = getattr(user_settings, 'order_changed_scope', 'all') or "all"
                        if scope == "pickup" and order.order_type != "Самовывоз":
                            continue
                        elif scope == "delivery" and order.order_type != "Доставка":
                            continue
                        elif scope == "courier_assigned" and (order.order_type != "Доставка" or not order.courier_name or order.courier_name in ("Не назначен", "")):
                            continue

                    if event_type == "new_order":
                        push_enabled = user_settings.new_order_push_enabled
                    elif event_type == "new_payment":
                        push_enabled = user_settings.new_payment_push_enabled
                    elif event_type == "order_cancelled":
                        push_enabled = user_settings.order_cancelled_push_enabled
                    elif event_type == "order_changed":
                        push_enabled = user_settings.order_changed_push_enabled
                    elif event_type == "chat_message":
                        push_enabled = user_settings.chat_message_push_enabled
                    elif event_type == "courier_delivery":
                        push_enabled = user_settings.courier_delivery_push_enabled
                    elif event_type == "delivery_unassigned":
                        push_enabled = user_settings.delivery_unassigned_push_enabled
                    elif event_type == "delivery_assigned":
                        push_enabled = user_settings.delivery_assigned_push_enabled
                    elif event_type == "order_delivered":
                        push_enabled = getattr(user_settings, 'order_delivered_push_enabled', True) and not is_courier
                    elif event_type == "change_cooking_time":
                        push_enabled = user_settings.change_cooking_time_push_enabled
                    elif event_type == "change_items":
                        push_enabled = user_settings.change_items_push_enabled
                    elif event_type == "change_amount":
                        push_enabled = user_settings.change_amount_push_enabled
                    elif event_type == "change_payment":
                        push_enabled = user_settings.change_payment_push_enabled
                    elif event_type == "change_address":
                        push_enabled = user_settings.change_address_push_enabled
                else:
                    # По умолчанию для order_changed и chat_message выключаем, для остальных включаем
                    if event_type in ("order_changed", "chat_message"):
                        push_enabled = False
                    elif is_courier and event_type not in ("courier_delivery", "delivery_assigned"):
                        push_enabled = False
                
                if not push_enabled:
                    continue
                
                # Сохраняем уведомление в БД для этого пользователя (один раз на пользователя)
                if sub.user_id not in notified_users:
                    try:
                        from app.models.admin_notification import AdminNotification
                        db_notif = AdminNotification(
                            user_id=sub.user_id,
                            title=title,
                            body=body,
                            url=url,
                            event_type=event_type,
                            is_read=False
                        )
                        session.add(db_notif)
                        notified_users.add(sub.user_id)
                    except Exception as db_err:
                        logger.error(f"Failed to log notification to database: {db_err}")
                        
                    # Отправка нативного Push-уведомления ВК Mini App
                    try:
                        from app.models.user import User
                        from app.services.vk_service import send_miniapp_push
                        user_obj = session.get(User, sub.user_id)
                        if user_obj and user_obj.vk_user_id:
                            push_msg = f"{title}: {body}"
                            logger.info(f"[VK Push] Initiating Mini App push to User ID {sub.user_id} (VK ID {user_obj.vk_user_id})")
                            await send_miniapp_push(session, [user_obj.vk_user_id], push_msg, url)
                    except Exception as vk_push_err:
                        logger.error(f"Failed to send VK Mini App Push notification: {vk_push_err}")
                    
                sub_info = {
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh,
                        "auth": sub.auth
                    }
                }
                res = send_web_push(sub_info, payload_data, global_settings.vapid_private_key)
                if res == "remove":
                    session.delete(sub)
                    db_changed = True
                    
            if len(notified_users) > 0 or db_changed:
                session.commit()
        except Exception as e:
            logger.error(f"Failed to send admin push notification: {e}")

    def find_courier_user(self, session: Session, courier_name: Optional[str], courier_iiko_id: Optional[str] = None):
        """Находит объект User курьера по имени или iiko_id"""
        from app.models.user import User
        from app.models.employee import Employee
        from sqlalchemy import cast, String

        if courier_iiko_id:
            u = session.exec(select(User).where(cast(User.iiko_id, String) == str(courier_iiko_id))).first()
            if u:
                return u
            emp = session.exec(select(Employee).where(cast(Employee.iiko_id, String) == str(courier_iiko_id))).first()
            if emp:
                u = session.exec(select(User).where(cast(User.iiko_id, String) == str(emp.iiko_id))).first()
                if u:
                    return u
                if emp.name:
                    u = session.exec(select(User).where(User.full_name == emp.name)).first()
                    if u:
                        return u

        if courier_name and courier_name not in ("Не назначен", "", None):
            clean_name = courier_name.strip()
            # 1. По полному имени в User
            u = session.exec(select(User).where(User.full_name == clean_name)).first()
            if u:
                return u
            # 2. По сотруднику в Employee
            emp = session.exec(select(Employee).where(Employee.name == clean_name)).first()
            if emp and emp.iiko_id:
                u = session.exec(select(User).where(cast(User.iiko_id, String) == str(emp.iiko_id))).first()
                if u:
                    return u
            # 3. Частичное совпадение
            u = session.exec(select(User).where(User.full_name.ilike(f"%{clean_name}%"))).first()
            if u:
                return u
        return None

    async def send_courier_notification(
        self,
        session: Session,
        courier_user_id: int,
        event_type: str,
        title: str,
        body: str,
        order_id: Optional[int] = None,
        order_number: Optional[Any] = None,
        url: str = "/pers/courier",
        extra_data: Optional[Dict[str, Any]] = None,
        order: Optional[Any] = None
    ):
        """
        Отправляет персональное push-, websocket- и колокольчик-уведомление конкретному курьеру
        с учетом индивидуальных настроек курьера (звук, всплывающее окно, Web Push).
        """
        try:
            from app.models.admin_notification_settings import AdminNotificationSettings
            from app.models.push_subscription import PushSubscription
            from app.models.admin_notification import AdminNotification
            from app.core.webpush_utils import send_web_push
            import json

            # 1. Загрузка настроек курьера
            c_settings = session.exec(
                select(AdminNotificationSettings).where(AdminNotificationSettings.user_id == courier_user_id)
            ).first()

            push_enabled = True
            sound_enabled = True
            sound_file = "chime.mp3"

            # Дефолтные звуки для каждого курьерского типа
            default_sounds = {
                "courier_order_assigned": "chime.mp3",
                "courier_cooking_time_set": "bell.mp3",
                "courier_cooking_time_changed": "click.mp3",
                "courier_status_changed": "bell.mp3",
                "courier_amount_changed": "cash.mp3",
                "courier_address_changed": "doorbell.mp3",
                "courier_changed_to_pickup": "branch.mp3",
                "courier_removed_from_delivery": "error.mp3",
                "courier_unassigned": "sonar.mp3",
                "courier_delivery_time_changed": "water.mp3",
            }
            sound_file = default_sounds.get(event_type, "chime.mp3")

            if c_settings:
                push_enabled = getattr(c_settings, f"{event_type}_push_enabled", True)
                if push_enabled is None:
                    push_enabled = True
                sound_enabled = getattr(c_settings, f"{event_type}_sound_enabled", True)
                if sound_enabled is None:
                    sound_enabled = True
                sf = getattr(c_settings, f"{event_type}_sound_file", None)
                if sf:
                    sound_file = sf

            # 2. Сохраняем уведомление в БД (колокольчик)
            try:
                db_notif = AdminNotification(
                    user_id=courier_user_id,
                    title=title,
                    body=body,
                    url=url,
                    event_type=event_type,
                    is_read=False
                )
                session.add(db_notif)
                session.commit()
            except Exception as db_err:
                logger.error(f"Failed to save courier notification to DB: {db_err}")
                try:
                    session.rollback()
                except:
                    pass

            # 3. WebSocket трансляция курьеру в браузер (всплывающее окно + звук)
            ws_payload = {
                "type": event_type,
                "title": title,
                "body": body,
                "order_id": order_id,
                "order_number": str(order_number or ""),
                "url": url,
                "target_user_id": courier_user_id,
                "sound_file": sound_file,
                "sound_enabled": sound_enabled,
                "push_enabled": push_enabled,
                **(extra_data or {})
            }
            self.send_websocket_personal_safe(ws_payload, courier_user_id)
            self.send_websocket_broadcast_safe(ws_payload)

            # 4. Отправка нативного Web Push (VAPID) на устройство курьера
            if push_enabled:
                try:
                    global_settings = session.exec(select(AdminNotificationSettings).where(AdminNotificationSettings.id == 1)).first()
                    if global_settings and global_settings.vapid_private_key:
                        subs = session.exec(
                            select(PushSubscription).where(PushSubscription.user_id == courier_user_id)
                        ).all()

                        if subs:
                            payload_data = json.dumps({
                                "title": title,
                                "body": body,
                                "icon": "/favicon.ico",
                                "url": url,
                                "event_type": event_type,
                                "tag": f"{event_type}-{order_id or int(datetime.now().timestamp())}"
                            }, ensure_ascii=False)

                            db_changed = False
                            for sub in subs:
                                sub_info = {
                                    "endpoint": sub.endpoint,
                                    "keys": {
                                        "p256dh": sub.p256dh,
                                        "auth": sub.auth
                                    }
                                }
                                res = send_web_push(sub_info, payload_data, global_settings.vapid_private_key)
                                if res == "remove":
                                    session.delete(sub)
                                    db_changed = True
                            if db_changed:
                                session.commit()
                except Exception as wp_err:
                    logger.error(f"Failed to send Web Push to courier {courier_user_id}: {wp_err}")

                # 5. VK Mini App Push если привязан аккаунт ВК
                try:
                    from app.models.user import User
                    from app.services.vk_service import send_miniapp_push
                    courier_user = session.get(User, courier_user_id)
                    if courier_user and courier_user.vk_user_id:
                        push_msg = f"{title}: {body}"
                        await send_miniapp_push(session, [courier_user.vk_user_id], push_msg, url)
                except Exception as vk_err:
                    logger.error(f"Failed to send VK push to courier {courier_user_id}: {vk_err}")

        except Exception as e:
            logger.error(f"Error in send_courier_notification: {e}")

    async def sync_kitchen_recipes_and_zones(self, session: Session) -> Dict[str, Any]:
        """Синхронизация техкарт и цехов из iiko Resto (Backoffice) API"""
        logger.info(">>> Запуск синхронизации техкарт и цехов из iiko Resto")
        try:
            from app.models.iiko_settings import IikoSettings
            from app.models.product import Product, KitchenZone, ProductRecipe
            from app.services.iiko_service import iiko_service
            import xml.etree.ElementTree as ET
            import datetime
            
            # Получаем настройки организации
            db_settings = session.exec(select(IikoSettings)).first()
            org_id = db_settings.organization_id if db_settings else None
            
            if not db_settings or not db_settings.resto_url or not db_settings.resto_login:
                raise ValueError("Не настроены параметры подключения к iiko Resto в настройках")
                
            # 1. Скачиваем список продуктов из Resto API для получения цехов приготовления (cookingPlaceType)
            # и построения мапы UUID продукта -> Название ингредиента
            logger.info("Resto API: Запрос /products...")
            products_xml = await iiko_service._resto_request("GET", "/products", organization_id=org_id)
            
            product_names = {}
            product_articles = {}
            product_cooking_places = {}
            
            if isinstance(products_xml, str):
                root = ET.fromstring(products_xml)
                for pDto in root.findall('productDto'):
                    p_id = pDto.findtext('id')
                    p_name = pDto.findtext('name')
                    p_num = pDto.findtext('num') or pDto.findtext('code')
                    cooking_place = pDto.findtext('cookingPlaceType') or pDto.findtext('cookingPlace')
                    
                    if p_id and p_name:
                        product_names[p_id] = p_name
                    if p_id and p_num:
                        product_articles[p_id] = p_num
                    if p_id and cooking_place:
                        product_cooking_places[p_id] = cooking_place
            else:
                logger.warning("Resto API products response is not XML string")
                
            # 2. Получаем технологические карты из Resto API v2/assemblyCharts/getAll
            logger.info("Resto API: Запрос v2/assemblyCharts/getAll...")
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            charts_data = await iiko_service._resto_request(
                "GET", 
                "/v2/assemblyCharts/getAll", 
                organization_id=org_id,
                params={"dateFrom": today_str}
            )
            
            recipes_imported = 0
            zones_created = 0
            
            # Мапа локальных зон (название -> KitchenZone) для кэширования в рамках одной сессии
            local_zones = {z.name: z for z in session.exec(select(KitchenZone)).all()}
            
            if isinstance(charts_data, dict) and "assemblyCharts" in charts_data:
                charts = charts_data["assemblyCharts"]
                logger.info(f"Найдено {len(charts)} техкарт в iiko Resto")
                
                for chart in charts:
                    product_iiko_id = chart.get("assembledProductId")
                    if not product_iiko_id:
                        continue
                        
                    # Ищем продукт в нашей локальной БД по iiko_id
                    prod = session.exec(select(Product).where(Product.iiko_id == product_iiko_id)).first()
                    if not prod:
                        # Продукт отсутствует в каталоге товаров сайта, создаем служебную заготовку
                        ing_name = product_names.get(product_iiko_id, f"Заготовка #{product_iiko_id[:8]}")
                        prod = Product(
                            name=ing_name,
                            price=Decimal("0.00"),
                            is_available=False,
                            iiko_id=product_iiko_id,
                            description="Служебный товар для техкарт (заготовка)",
                            article=product_articles.get(product_iiko_id) or f"SERV-{product_iiko_id[:8].upper()}"
                        )
                        session.add(prod)
                        session.flush()
                        
                    # 2.1. Обработка зоны приготовления (цеха)
                    cooking_place_name = product_cooking_places.get(product_iiko_id)
                    if cooking_place_name:
                        # Находим или создаем цех
                        zone = local_zones.get(cooking_place_name)
                        if not zone:
                            zone = KitchenZone(
                                name=cooking_place_name,
                                color="#2196F3",
                                description=f"Цех импортирован из iiko Office: {cooking_place_name}"
                            )
                            session.add(zone)
                            session.flush()
                            local_zones[cooking_place_name] = zone
                            zones_created += 1
                        
                        # Привязываем продукт к цеху
                        prod.kitchen_zone_id = zone.id
                        session.add(prod)
                        
                    # 2.2. Обработка технологической карты (рецепта)
                    ingredients = []
                    items = chart.get("items") or []
                    for item in items:
                        ing_id = item.get("productId")
                        if not ing_id:
                            continue
                            
                        # Ищем название сырья по мапе из XML продуктов
                        ing_name = product_names.get(ing_id, f"Сырье #{ing_id[:8]}")
                        
                        # amountIn (gross), amountMiddle (net), amountOut (output)
                        gross = float(item.get("amountIn") or 0)
                        net = float(item.get("amountMiddle") or 0)
                        output = float(item.get("amountOut") or 0)
                        
                        # Переведем значения в граммы (умножаем на 1000, если вес дробный < 1.0, чтобы получить граммы)
                        def _to_grams(val):
                            val_f = float(val or 0)
                            if 0 < val_f <= 2.0:
                                return round(val_f * 1000, 1)
                            return round(val_f, 1)
                            
                        ingredients.append({
                            "name": ing_name,
                            "iiko_id": ing_id,
                            "gross": _to_grams(gross),
                            "net": _to_grams(net),
                            "output": _to_grams(output)
                        })
                        
                    technology = chart.get("technologyDescription") or ""
                    appearance = chart.get("appearance") or ""
                    critical_points = chart.get("organoleptic") or chart.get("outputComment") or ""
                    
                    # Проверяем, есть ли уже рецепт у товара
                    recipe = session.exec(select(ProductRecipe).where(ProductRecipe.product_id == prod.id)).first()
                    if not recipe:
                        recipe = ProductRecipe(product_id=prod.id)
                        
                    recipe.ingredients = ingredients
                    recipe.technology = technology
                    recipe.appearance = appearance
                    recipe.critical_points = critical_points
                    recipe.updated_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
                    
                    session.add(recipe)
                    recipes_imported += 1
                    
                session.commit()
                logger.info(f"Успешно импортировано: {recipes_imported} техкарт, {zones_created} новых цехов")
            else:
                logger.warning("Resto API assemblyCharts response is not dict or missing assemblyCharts key")
                
            return {
                "success": True,
                "recipes_imported": recipes_imported,
                "zones_created": zones_created,
                "message": f"Синхронизация завершена: импортировано {recipes_imported} техкарт, создано {zones_created} цехов."
            }
        except Exception as e:
            logger.error(f"Resto Kitchen sync failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Ошибка синхронизации: {str(e)}"
            }

iiko_sync_service = IikoSyncService()

# =========================================================================
# Точки входа для планировщика задач (Entry Points)
# =========================================================================

async def sync_all():
    """Полная синхронизация iiko."""
    from app.core.database import SessionLocal
    with SessionLocal() as session:
        logger.info(">>> Запуск полной синхронизации iiko")
        try:
            # 1. Справочники
            await iiko_sync_service.sync_categories_only(session)
            await iiko_sync_service.sync_menu(session)
            await iiko_sync_service.sync_stop_lists(session)
            await iiko_sync_service.sync_payment_types(session)
            await iiko_sync_service.sync_roles(session)
            await iiko_sync_service.sync_loyalty_items(session)
            
            # 2. Сотрудники и курьеры
            await iiko_sync_service.sync_employees_full(session)
            await iiko_sync_service.sync_courier_deliveries(session)
            
            # 3. Клиенты и выручка
            await iiko_sync_service.merge_customers_by_uid(session)
            from app.services.revenue_sync import revenue_sync_service
            await revenue_sync_service.sync_today_revenue()
            
            logger.info("<<< Полная синхронизация завершена")
        except Exception as e:
            logger.error(f"!!! Ошибка синхронизации: {e}", exc_info=True)

async def sync_orders_task(hours: int = 24):
    """Синхронизация заказов."""
    from app.core.database import SessionLocal
    with SessionLocal() as session:
        try:
            await iiko_sync_service.sync_orders(session, hours=hours)
        except Exception as e:
            logger.error(f"!!! Ошибка синхронизации заказов: {e}", exc_info=True)

async def merge_customers_task():
    """Слияние клиентов."""
    from app.core.database import SessionLocal
    with SessionLocal() as session:
        try:
            await iiko_sync_service.merge_customers_by_uid(session)
            await iiko_sync_service.merge_customers_by_phone()
        except Exception as e:
            logger.error(f"!!! Ошибка слияния клиентов: {e}", exc_info=True)
