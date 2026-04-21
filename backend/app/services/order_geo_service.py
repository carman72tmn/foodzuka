import logging
from sqlmodel import Session, select
from app.models.order import Order
from app.services.yandex_service import yandex_service
from app.models.yandex_settings import YandexSettings

logger = logging.getLogger(__name__)

async def geocode_order(order_id: int, session_factory):
    """
    Фоновая задача для геокодирования адреса заказа и определения зоны доставки.
    """
    with session_factory() as session:
        order = session.get(Order, order_id)
        if not order or not order.delivery_address:
            return

        # Если координаты уже есть, пропускаем (кроме случаев явного сброса)
        if order.latitude and order.longitude and order.resolved_delivery_zone_id:
            return

        yandex_settings = await yandex_service.get_settings(session)
        if not yandex_settings or not yandex_settings.api_key_js:
            logger.warning(f"Yandex API key not configured, skipping geocoding for order {order_id}")
            return

        # 1. Геокодирование
        coords = await yandex_service.geocode_address(order.delivery_address, yandex_settings.api_key_js)
        if not coords:
            logger.warning(f"Could not geocode address '{order.delivery_address}' for order {order_id}")
            return

        order.latitude = coords["lat"]
        order.longitude = coords["lng"]

        # 2. Определение зоны
        zone = await yandex_service.resolve_zone_for_point(order.latitude, order.longitude, session)
        if zone:
            order.resolved_delivery_zone_id = zone.id
            logger.info(f"Order {order_id} resolved to zone: {zone.name}")
        else:
            logger.info(f"Order {order_id} address is outside all delivery zones")

        session.add(order)
        session.commit()
