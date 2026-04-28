from app.core.database import SessionLocal
from app.models.order import Order
from app.models.iiko_settings import IikoSettings
from app.services.iiko_sync_service import IikoSyncService
import re

def clean_dict_string(s):
    if not s: return ""
    if isinstance(s, dict): return s.get("name", "")
    s = str(s)
    match = re.search(r"{'name':\s*'([^']*)'}", s)
    if match: return match.group(1)
    return s

def fix_all_addresses():
    session = SessionLocal()
    sync_service = IikoSyncService()
    try:
        settings = session.query(IikoSettings).first()
        addr_fmt = settings.address_format if settings else "line1"
        
        orders = session.query(Order).order_by(Order.created_at.desc()).limit(100).all()
        print(f"Checking {len(orders)} orders...")
        
        for o in orders:
            city_str = clean_dict_string(o.city) or "Тюмень"
            # Очистка полей от артефактов
            o.city = city_str
            o.street = clean_dict_string(o.street)
            o.house = clean_dict_string(o.house)
            o.flat = clean_dict_string(o.flat)
            o.entrance = clean_dict_string(o.entrance)
            o.floor = clean_dict_string(o.floor)
            o.doorphone = clean_dict_string(o.doorphone)
            
            original_addr = clean_dict_string(o.delivery_address)
            
            addr_obj = {
                "line1": original_addr,
                "street": o.street,
                "house": o.house,
                "flat": o.flat,
                "entrance": o.entrance,
                "floor": o.floor,
                "doorphone": o.doorphone,
                "city": o.city
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
