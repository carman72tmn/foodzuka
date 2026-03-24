"""
API эндпоинты для работы с заказами
"""
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlmodel import Session, select
from sqlalchemy.orm.attributes import flag_modified
from app.core.database import get_session
from app.models.company import Branch, Company
from app.models.customer import Customer
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.promo_code import PromoCode
from app.models.action import Action
from app.schemas import OrderCreate, OrderUpdate, OrderResponse, OrderItemResponse
import logging
from app.services.iiko_service import iiko_service
from app.services.iiko_sync_service import iiko_sync_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
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
    query = select(Order).order_by(Order.created_at.desc()).offset(skip).limit(limit)

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
        result.append(order_dict)

    return result


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, session: Session = Depends(get_session)):
    """Получить заказ по ID"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )

    # Получаем позиции заказа
    items_query = select(OrderItem).where(OrderItem.order_id == order_id)
    order_dict = order.model_dump()
    order_dict["items"] = list(session.exec(items_query).all())

    return order_dict


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    session: Session = Depends(get_session)
):
    """
    Создать новый заказ

    1. Проверяем наличие товаров
    2. Вычисляем общую сумму
    3. Создаем заказ в БД
    4. Отправляем заказ в iiko
    """
    # Проверяем клиента (Черный список)
    customer = session.exec(select(Customer).where(Customer.phone == order_data.customer_phone)).first()
    if not customer:
        # Создаем нового клиента если не найден
        customer = Customer(
            phone=order_data.customer_phone,
            name=order_data.customer_name,
            telegram_id=order_data.telegram_user_id
        )
        session.add(customer)
        session.commit()
        session.refresh(customer)
    
    if customer.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ваш аккаунт заблокирован. Пожалуйста, свяжитесь с поддержкой."
        )

    # Синхронизируем данные лояльности из iiko
    try:
        iiko_customer = await iiko_service.get_customer_info(customer.phone)
        if iiko_customer.get("id"):
            customer.iiko_customer_id = iiko_customer["id"]
            customer.name = iiko_customer.get("name") or customer.name
            
            # Получаем баланс бонусов (обычно первый кошелек)
            if iiko_customer.get("walletBalances"):
                # Суммируем баланс по всем кошелькам или берем первый основной
                balance = sum(Decimal(str(w.get("balance", 0))) for w in iiko_customer["walletBalances"])
                customer.bonus_points = balance
            
            # TODO: Обновление статуса лояльности на основе данных из iiko
            
            session.add(customer)
            session.commit()
            session.refresh(customer)
    except Exception as e:
        # Ошибка синхронизации с iiko не должна блокировать заказ, если это не критично
        print(f"Iiko loyalty sync error: {e}")

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
        promo = session.exec(select(PromoCode).where(PromoCode.code == order_data.promo_code)).first()
        if not promo or not promo.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Промокод не найден или неактивен"
            )
        
        # Проверка дат
        today = datetime.utcnow().date()
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
            existing_order = session.exec(
                select(Order).where(Order.customer_id == customer.id, Order.promo_code_id == promo.id)
            ).first()
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
    branch = session.get(Branch, order_data.branch_id)
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
        product = session.get(Product, item.product_id)
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
        promo = session.get(PromoCode, promo_code_id)
        if promo.promo_type == "percent":
            promo_discount = (total_amount * promo.discount_value / Decimal("100")).quantize(Decimal("0.01"))
        elif promo.promo_type == "fixed":
            promo_discount = promo.discount_value
        
        # Лимит скидки по промокоду (не может быть больше суммы заказа)
        promo_discount = min(promo_discount, total_amount - total_discount)
        total_discount += promo_discount
        
        # Обновляем счетчик использований промокода
        promo.current_uses += 1
        session.add(promo)

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
                        gift_product = session.get(Product, g_id)
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
        status=OrderStatus.NEW
    )
    session.add(order)
    session.commit()
    session.refresh(order)

    # Создаем позиции заказа
    for item_data in order_items_data:
        order_item = OrderItem(order_id=order.id, **item_data)
        session.add(order_item)

    session.commit()

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
            order.iiko_order_id = iiko_response["orderId"]
            order.status = OrderStatus.CONFIRMED
            session.add(order)
            session.commit()
    except Exception as e:
        # Логируем ошибку, но не блокируем создание заказа
        print(f"Error sending order to iiko: {e}")

    # Получаем позиции для ответа
    items_query = select(OrderItem).where(OrderItem.order_id == order.id)
    order_dict = order.model_dump()
    order_dict["items"] = list(session.exec(items_query).all())

    return order_dict


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
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

    # Получаем позиции для ответа
    items_query = select(OrderItem).where(OrderItem.order_id == order_id)
    order_dict = order.model_dump()
    order_dict["items"] = list(session.exec(items_query).all())

    return order_dict


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(order_id: int, session: Session = Depends(get_session)):
    """Отменить заказ"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )

    if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
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
    order.status = OrderStatus.CANCELLED
    session.add(order)
    session.commit()
    session.refresh(order)

    # Получаем позиции для ответа
    items_query = select(OrderItem).where(OrderItem.order_id == order_id)
    order_dict = order.model_dump()
    order_dict["items"] = list(session.exec(items_query).all())

    return order_dict


# --- IIKO INTEGRATION ---

@router.post("/webhook/iiko")
async def iiko_webhook(request: Request, session: Session = Depends(get_session)):
    """
    Webhook для получения статусов заказов из iiko.
    Принимает массив событий (DeliveryOrderUpdate и др.)
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON text")

    if not isinstance(data, list):
        data = [data]

    for event in data:
        event_type = event.get("eventType")
        if event_type == "DeliveryOrderUpdate":
            event_info = event.get("eventInfo", {})
            org_id = event.get("organizationId")
            if event_info:
                await iiko_sync_service.process_iiko_order(session, event_info, org_id)
                
    return {"status": "success"}


@router.post("/sync")
async def sync_recent_orders(background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """
    Ручная синхронизация заказов из iiko за последние 24 часа.
    """
    # Получаем все активные филиалы организаций iiko
    companies = session.exec(select(Company).where(Company.iiko_organization_id != None)).all()
    if not companies:
        raise HTTPException(status_code=400, detail="No iiko organizations configured")
    
    date_to = datetime.utcnow()
    date_from = date_to - timedelta(hours=24)
    
    async def run_sync():
        with Session(session.bind) as sync_session:
            # Ручная синхронизация за последние 30 дней (720 часов)
            await iiko_sync_service.sync_orders(sync_session, hours=720)
    
    background_tasks.add_task(run_sync)
    return {"status": "accepted", "message": "Order synchronization started in background"}
