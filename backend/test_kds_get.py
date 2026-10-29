from app.core.database import engine
from sqlmodel import Session
from app.api.kitchen import get_kitchen_orders

session = Session(engine)
res = get_kitchen_orders(zone_ids=None, session=session, current_user=None)
print("Orders count:", len(res))
for r in res:
    print(f"ID: {r['id']}, Status: {r['status']}, Items: {[i['product_name'] for i in r['items']]}")
