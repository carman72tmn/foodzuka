"""
API эндпоинты для работы с заказами
"""
import asyncio
import json
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta, date
from app.core.datetime_utils import utc_now
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks, Query
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified
from app.core.database import get_session
from app.models.company import Branch, Company
from app.models.customer import Customer
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.promo_code import PromoCode
from app.models.action import Action
from app.models.iiko_settings import IikoSettings
from app.schemas import OrderCreate, OrderUpdate, OrderResponse, OrderItemResponse
import logging
from app.services.iiko_service import iiko_service
from app.services.iiko_sync_service import iiko_sync_service
from app.services.order_geo_service import geocode_order


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/", response_model=List[OrderResponse])
def get_orders(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[OrderStatus] = None,
    telegram_user_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """
    Получить список заказов

    - **skip**: Количество пропускаемых записей
    - **limit**: Максимальное количество возвращаемых записей
    - **status_filter**: Фильтр по статусу
    - **telegram_user_id**: Фильтр по пользователю Telegram
    """
    query = select(Order).options(
        selectinload(Order.resolved_zone),
        selectinload(Order.customer)
    ).order_by(Order.created_at.desc()).offset(skip).limit(limit)

    if status_filter:
        query = query.where(Order.status == status_filter)

    if telegram_user_id:
        query = query.where(Order.telegram_user_id == telegram_user_id)

    orders = session.exec(query).all()

    # Добавляем позиции к каждому заказу
    result = []
    for order in orders:
        items_query = select(OrderItem).where(OrderItem.order_id == order.id)
        order_dict = order.model_dump()
        order_dict["items"] = list(session.exec(items_query).all())
        # Явно добавляем имя зоны доставки из property
        order_dict["resolved_delivery_zone_name"] = order.resolved_zone_name

        # Индикаторы клиента (приоритет снимку данных в заказе)
        if order.customer_info_details:
            order_dict["customer_is_new"] = order.customer_info_details.get("is_new_guest", False)
            order_dict["customer_is_risk"] = order.customer_info_details.get("is_high_risk", False)
        elif order.customer:
            order_dict["customer_is_new"] = getattr(order.customer, "is_new_guest", False)
            order_dict["customer_is_risk"] = getattr(order.customer, "is_high_risk", False)
        result.append(order_dict)

    return result


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, session: Session = Depends(get_session)):
    """Получить заказ по ID"""
    # Получаем позиции заказа и зону
    items_query = select(OrderItem).where(OrderItem.order_id == order_id)
    order = session.exec(select(Order).options(
        selectinload(Order.resolved_zone),
        selectinload(Order.customer)
    ).where(Order.id == order_id)).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    order_dict = order.model_dump()
    order_dict["items"] = list(session.exec(items_query).all())
    # Явно добавляем имя зоны доставки из property
    order_dict["resolved_delivery_zone_name"] = order.resolved_zone_name

    # Индикаторы клиента (приоритет снимку данных в заказе)
    if order.customer_info_details:
        order_dict["customer_is_new"] = order.customer_info_details.get("is_new_guest", False)
        order_dict["customer_is_risk"] = order.customer_info_details.get("is_high_risk", False)
    elif order.customer:
        order_dict["customer_is_new"] = getattr(order.customer, "is_new_guest", False)
        order_dict["customer_is_risk"] = getattr(order.customer, "is_high_risk", False)

    return order_dict


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):

    """
    Создать новый заказ

    1. Проверяем наличие товаров
    2. Вычисляем общую сумму
    3. Создаем заказ в БД
    4. Отправляем заказ в iiko
    """
    # Проверяем клиента и создаем/обновляем карточку (Черный список)
    order_info = f"Заказ с сайта/бота на адрес: {order_data.delivery_address}"
    if order_data.comment:
        order_info += f" | Коммент: {order_data.comment}"
        
    customer_id = await iiko_sync_service.ensure_customer_from_order(
        phone=order_data.customer_phone,
        name=order_data.customer_name,
        surname=order_data.customer_surname,
        order_info=order_info,
        order_date=datetime.now(),
        telegram_id=order_data.telegram_user_id
    )
    
    customer = await asyncio.to_thread(session.get, Customer, customer_id)
    if not customer:
        # Резервный вариант на случай ошибки в методе
        customer = await asyncio.to_thread(lambda: session.exec(select(Customer).where(Customer.phone == order_data.customer_phone)).first())
    
    if customer.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ваш аккаунт заблокирован. Пожалуйста, свяжитесь с поддержкой."
        )

    # Данные лояльности уже синхронизированы внутри ensure_customer_from_order
    # Обновляем объект из базы, чтобы получить актуальный баланс бонусов и UID
    await asyncio.to_thread(session.refresh, customer)

    # Проверяем возможность списания бонусов
    bonus_spent = Decimal("0.00")
    if order_data.bonus_spent and order_data.bonus_spent > 0:
        if order_data.bonus_spent > customer.bonus_points:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недостаточно бонусов. Доступно: {customer.bonus_points}"
            )
        bonus_spent = order_data.bonus_spent

    # Обработка промокода
    promo_code_id = None
    promo_discount = Decimal("0.00")
    
    if order_data.promo_code:
        promo = await asyncio.to_thread(lambda: session.exec(select(PromoCode).where(PromoCode.code == order_data.promo_code)).first())
        if not promo or not promo.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Промокод не найден или неактивен"
            )
        
        # Проверка дат
        today = utc_now().date()
        if (promo.valid_from and today < promo.valid_from) or (promo.valid_until and today > promo.valid_until):
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Срок действия промокода истек или еще не наступил"
            )
        
        # Проверка лимита использований
        if promo.max_uses is not None and promo.current_uses >= promo.max_uses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Промокод больше не действителен (превышен лимит использований)"
            )
        
        # Проверка "один раз для клиента"
        if promo.usage_type == "single_per_user":
            existing_order = await asyncio.to_thread(lambda: session.exec(
                select(Order).where(Order.customer_id == customer.id, Order.promo_code_id == promo.id)
            ).first())
            if existing_order:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Вы уже использовали этот промокод"
                )
        
        # Проверка "только первый заказ"
        if promo.first_order_only and customer.total_orders_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Промокод доступен только для первого заказа"
            )
        
        promo_code_id = promo.id
        # Логика расчета скидки (процент или фикс) будет ниже после расчета base total

    # Проверяем филиал
    branch = await asyncio.to_thread(session.get, Branch, order_data.branch_id)
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Branch with id {order_data.branch_id} not found"
        )
    if not branch.is_active or not branch.is_accepting_orders:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Branch '{branch.name}' is currently not accepting orders"
        )

    # Проверяем товары и вычисляем сумму
    total_amount = Decimal("0.00")
    order_items_data = []

    for item in order_data.items:
        product = await asyncio.to_thread(session.get, Product, item.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {item.product_id} not found"
            )
        if not product.is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.name}' is not available"
            )

        item_total = product.price * item.quantity
        total_amount += item_total

        order_items_data.append({
            "product_id": product.id,
            "product_name": product.name,
            "quantity": item.quantity,
            "price": product.price,
            "total": item_total
        })

    # Скидка (бонусы + промокод)
    total_discount = bonus_spent
    
    # 1. Применяем промокод
    if promo_code_id:
        promo = await asyncio.to_thread(session.get, PromoCode, promo_code_id)
        if promo.promo_type == "percent":
            promo_discount = (total_amount * promo.discount_value / Decimal("100")).quantize(Decimal("0.01"))
        elif promo.promo_type == "fixed":
            promo_discount = promo.discount_value
        
        # Лимит скидки по промокоду (не может быть больше суммы заказа)
        promo_discount = min(promo_discount, total_amount - total_discount)
        total_discount += promo_discount
        
        # Обновляем счетчик использований промокода
        promo.current_uses += 1
        await asyncio.to_thread(lambda: (session.add(promo), session.flush()))

    # 2. Проверяем наличие подарков по акциям
    actions = session.exec(select(Action).where(Action.is_active == True)).all()
    for action in actions:
        # Простая проверка суммы для примера (gift_product)
        if action.action_type == "gift_product" and action.min_order_amount:
            if total_amount >= action.min_order_amount:
                # Добавляем подарок в позиции заказа
                import json
                try:
                    gift_ids = json.loads(action.gift_product_ids) if action.gift_product_ids else []
                    for g_id in gift_ids:
                        gift_product = await asyncio.to_thread(session.get, Product, g_id)
                        if gift_product:
                            order_items_data.append({
                                "product_id": gift_product.id,
                                "product_name": f"ПОДАРОК: {gift_product.name}",
                                "quantity": 1,
                                "price": Decimal("0.00"),
                                "total": Decimal("0.00")
                            })
                except Exception as e:
                    print(f"Error processing gift action: {e}")

    # Итоговая сумма к оплате не может быть меньше 0
    final_total = max(total_amount - total_discount, Decimal("0.00"))

    # Создаем заказ
    order = Order(
        telegram_user_id=order_data.telegram_user_id,
        telegram_username=order_data.telegram_username,
        branch_id=order_data.branch_id,
        customer_id=customer.id,
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        delivery_address=order_data.delivery_address,
        total_amount=final_total,
        bonus_spent=bonus_spent,
        total_discount=total_discount,
        promo_code_id=promo_code_id,
        comment=order_data.comment,
        status=OrderStatus.new
    )
    def _save_order():
        session.add(order)
        session.commit()
        session.refresh(order)

        # Создаем позиции заказа
        for item_data in order_items_data:
            order_item = OrderItem(order_id=order.id, **item_data)
            session.add(order_item)

        session.commit()
    
    await asyncio.to_thread(_save_order)
    
    # Фоновое геокодирование
    background_tasks.add_task(geocode_order, order.id, lambda: Session(session.bind))


    # Отправляем заказ в iiko (асинхронно, не блокируем ответ)
    try:
        iiko_items = [
            {
                "product_id": item["product_id"],
                "quantity": item["quantity"],
                "price": item["price"]
            }
            for item in order_items_data
        ]

        # Подготавливаем данные для скидок в iiko
        discount_info = None
        if order.bonus_spent > 0:
            discount_info = {
                "discounts": [
                    {
                        "type": "iikoCard",
                        "sum": float(order.bonus_spent)
                    }
                ]
            }

        iiko_response = await iiko_service.create_delivery_order(
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            address=order.delivery_address,
            items=iiko_items,
            comment=order.comment,
            discount_info=discount_info
        )

        # Сохраняем ID заказа из iiko
        if iiko_response.get("orderId"):
            def _update_iiko_id():
                order.iiko_order_id = iiko_response["orderId"]
                order.status = OrderStatus.confirmed
                session.add(order)
                session.commit()
            await asyncio.to_thread(_update_iiko_id)
    except Exception as e:
        # Логируем ошибку, но не блокируем создание заказа
        print(f"Error sending order to iiko: {e}")

    # Получаем позиции для ответа
    items_query = select(OrderItem).where(OrderItem.order_id == order.id)
    order_dict = order.model_dump()
    order_dict["items"] = list(await asyncio.to_thread(lambda: session.exec(items_query).all()))
    # Явно добавляем имя зоны доставки из property
    order_dict["resolved_delivery_zone_name"] = order.resolved_zone_name

    return order_dict


@router.patch("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_data: OrderUpdate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):

    """Обновить заказ"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )

    # Обновляем только предоставленные поля
    update_data = order_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(order, key, value)

    session.add(order)
    session.commit()
    session.refresh(order)
    
    # Если адрес изменился, пересчитываем геопозицию
    if order_data.delivery_address:
        background_tasks.add_task(geocode_order, order.id, lambda: Session(session.bind))


    # Получаем позиции для ответа
    items_query = select(OrderItem).where(OrderItem.order_id == order_id)
    order_dict = order.model_dump()
    order_dict["items"] = list(session.exec(items_query).all())

    return order_dict


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(order_id: int, session: Session = Depends(get_session)):
    """Отменить заказ"""
    order = await asyncio.to_thread(session.get, Order, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )

    if order.status in [OrderStatus.delivered, OrderStatus.cancelled]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status {order.status}"
        )

    # Отменяем в iiko
    if order.iiko_order_id:
        try:
            await iiko_service.cancel_order(order.iiko_order_id)
        except Exception as e:
            print(f"Error cancelling order in iiko: {e}")

    # Обновляем статус
    def _update_status():
        order.status = OrderStatus.cancelled
        session.add(order)
        session.commit()
        session.refresh(order)
    await asyncio.to_thread(_update_status)

    # Получаем позиции для ответа
    items_query = select(OrderItem).where(OrderItem.order_id == order_id)
    order_dict = order.model_dump()
    order_dict["items"] = list(session.exec(items_query).all())

    return order_dict
    
@router.get("/by-phone/{phone}", response_model=List[OrderResponse])
def get_orders_by_phone(
    phone: str, 
    skip: int = Query(0, ge=0),
    limit: int = Query(7, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """Получить локальные заказы по номеру телефона клиента с пагинацией"""
    from app.utils.phone_utils import normalize_phone
    normalized = normalize_phone(phone)
    query = select(Order).where(Order.customer_phone == normalized).order_by(Order.created_at.desc()).offset(skip).limit(limit)
    orders = session.exec(query).all()
    
    # Добавляем позиции к каждому заказу
    result = []
    for order in orders:
        items_query = select(OrderItem).where(OrderItem.order_id == order.id)
        order_dict = order.model_dump()
        order_dict["items"] = list(session.exec(items_query).all())
        # Явно добавляем имя зоны доставки из property
        order_dict["resolved_delivery_zone_name"] = order.resolved_zone_name
        result.append(order_dict)
        
    return result


# --- IIKO INTEGRATION ---

@router.post("/webhook/iiko")
async def iiko_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """
    Прием вебхука от iiko Cloud.
    Использует background_tasks для синхронизации, чтобы не блокировать iiko.
    """
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Error parsing webhook JSON: {e}")
        return {"status": "error", "message": "invalid json"}

    if not isinstance(data, list):
        data = [data]
        
    for event in data:
        event_type = event.get("eventType")
        if event_type in ["DeliveryOrderUpdate", "DeliveryOrderCreate", "DeliveryOrderStatusChanged"]:
            event_info = event.get("eventInfo", {})
            org_id = event.get("organizationId")
            
            o_data = event_info.get("order", event_info)
            order_id = o_data.get("id") or event_info.get("id")
            raw_status = o_data.get("status") or event_info.get("creationStatus")
            
            logger.info(f"WEBHOOK: [iiko_webhook] Event: {event_type} | Org: {org_id} | OrderID: {order_id} | Status: {raw_status}")
            
            if event_info:
                # Отправляем в фоновую задачу с новой сессией
                background_tasks.add_task(
                    run_sync_with_session,
                    iiko_sync_service.process_iiko_order,
                    event_info,
                    org_id
                )
                
    return {"status": "success"}

def run_sync_with_session(func, *args, **kwargs):
    """Хелпер для запуска асинхронной функции с новой сессией в фоновом потоке"""
    from app.core.database import engine
    import asyncio as sync_asyncio
    
    with Session(engine) as session:
        loop = sync_asyncio.new_event_loop()
        sync_asyncio.set_event_loop(loop)
        try:
            # Выполняем асинхронную функцию в новом цикле событий
            loop.run_until_complete(func(session, *args, **kwargs))
        except Exception as e:
            logger.error(f"Error in background task {func.__name__}: {e}", exc_info=True)
        finally:
            loop.close()


@router.post("/sync")
def sync_recent_orders(background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """
    Ручная синхронизация заказов из iiko (ревизии + последние 48 часов).
    """
    # Проверяем наличие настроек iiko в БД
    settings_db = session.exec(select(IikoSettings)).first()
    if not settings_db or not settings_db.api_login:
        raise HTTPException(status_code=400, detail="No iiko settings configured")
    
    async def run_sync():
        try:
            with Session(session.bind) as sync_session:
                # Синхронизация заказов (внутри логика по ревизиям и по датам -24h/+24h)
                logger.info("Starting manual order sync (Revision + 48h Window) via API")
                await iiko_sync_service.sync_orders(sync_session)
                logger.info("Manual order sync finished")
        except Exception as e:
            logger.error(f"Error in manual sync background task: {e}", exc_info=True)
    
    try:
        background_tasks.add_task(run_sync)
        return {"status": "accepted", "message": "Order synchronization started in background"}
    except Exception as e:
        logger.error(f"Failed to add manual sync task to background: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start synchronization: {str(e)}")
