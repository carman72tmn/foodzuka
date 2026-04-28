from app.core.database import SessionLocal
from app.models.order import Order
from app.models.iiko_settings import IikoSettings
from app.services.iiko_sync_service import IikoSyncService
from datetime import datetime, timedelta
import re

def clean_dict_string(s):
    if not s: return ""
    # Если строка содержит {'name': '...'}
    match = re.search(r"{'name':\s*'([^']*)'}", s)
    if match:
        return match.group(1)
    return s

def fix_all_addresses():
    session = SessionLocal()
    sync_service = IikoSyncService()
    try:
        settings = session.query(IikoSettings).first()
        addr_fmt = settings.address_format if settings else "line1"
        
        yesterday = datetime.utcnow() - timedelta(days=2)
        orders = session.query(Order).filter(Order.created_at >= yesterday).all()
        
        print(f"Updating {len(orders)} orders...")
        
        for o in orders:
            city_str = clean_dict_string(o.city) or "Тюмень"
            original_addr = clean_dict_string(o.delivery_address)
            
            addr_obj = {
                "line1": original_addr,
                "street": o.street,
                "house": o.house,
                "flat": o.flat,
                "entrance": o.entrance,
                "floor": o.floor,
                "doorphone": o.doorphone,
                "city": city_str
            }
            
            new_addr = sync_service.format_address(addr_obj, city=city_str, fmt=addr_fmt)
            
            if new_addr != o.delivery_address:
                print(f"ID {o.id}: {o.delivery_address} -> {new_addr}")
                o.delivery_address = new_addr
        
        session.commit()
        print("Done!")
    finally:
        session.close()

if __name__ == "__main__":
    fix_all_addresses()
