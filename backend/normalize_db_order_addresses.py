"""
Скрипт нормализации и исправления адресов доставок в существующих заказах БД.
Добавляет недостающие подъезды, этажи, квартиры и коды домофонов в строку delivery_address.
"""
# -*- coding: utf-8 -*-
import sys
import re
import logging
from sqlmodel import Session, select
from app.core.database import engine
from app.models.order import Order
from app.models.iiko_settings import IikoSettings
from app.services.iiko_sync_service import iiko_sync_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("normalize_addresses")

def main():
    updated_count = 0
    total_delivery_orders = 0
    
    with Session(engine) as session:
        settings_db = session.exec(select(IikoSettings)).first()
        addr_fmt = settings_db.address_format if settings_db else "line1"
        city_default = (settings_db.city_name if settings_db else None) or "Тюмень"

        orders = session.exec(
            select(Order)
            .where(Order.order_type == "Доставка")
            .order_by(Order.id.desc())
        ).all()
        
        total_delivery_orders = len(orders)
        logger.info(f"Total delivery orders in DB: {total_delivery_orders}")
        
        for order in orders:
            old_addr = (order.delivery_address or "").strip()
            if not old_addr or old_addr == "Самовывоз" or old_addr == "Адрес не указан":
                continue
                
            addr_data = order.address_parts if isinstance(order.address_parts, dict) else {}
            
            # Сливаем данные из полей заказа и address_parts
            city_val = order.city or addr_data.get("city") or city_default
            street_val = order.street or addr_data.get("street")
            house_val = order.house or addr_data.get("house")
            building_val = addr_data.get("building")
            flat_val = order.flat or addr_data.get("flat")
            entrance_val = order.entrance or addr_data.get("entrance")
            floor_val = order.floor or addr_data.get("floor")
            doorphone_val = order.doorphone or addr_data.get("doorphone")
            
            merged_addr = {
                "city": city_val,
                "street": street_val,
                "house": house_val,
                "building": building_val,
                "flat": flat_val,
                "entrance": entrance_val,
                "floor": floor_val,
                "doorphone": doorphone_val,
                "line1": old_addr
            }
            
            new_addr = iiko_sync_service.format_address(merged_addr, city=city_val, fmt=addr_fmt)
            
            if new_addr and new_addr != old_addr:
                order.delivery_address = new_addr
                session.add(order)
                updated_count += 1
                if updated_count <= 15:
                    logger.info(f"[Order #{order.id} | Ext: {order.external_number}]")
                    logger.info(f"  OLD: {old_addr}")
                    logger.info(f"  NEW: {new_addr}")
                    logger.info(f"  (Ent: {entrance_val}, Flr: {floor_val}, Flt: {flat_val}, Dp: {doorphone_val})")
        
        session.commit()
        logger.info(f"Successfully normalized and updated {updated_count} orders out of {total_delivery_orders} delivery orders.")

if __name__ == "__main__":
    main()
