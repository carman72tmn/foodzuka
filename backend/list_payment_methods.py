from sqlmodel import Session, select
from app.core.database import engine
from app.models.order import Order

with Session(engine) as session:
    orders = session.exec(select(Order)).all()
    methods = set()
    for o in orders:
        if o.payment_method:
            methods.add(o.payment_method)
        if o.payments_details:
            items = []
            if isinstance(o.payments_details, dict):
                items = o.payments_details.get("items", [])
            elif isinstance(o.payments_details, list):
                items = o.payments_details
            for item in items:
                if isinstance(item, dict) and item.get("name"):
                    methods.add(item.get("name"))
    print("Unique payment methods in DB:")
    for m in sorted(methods):
        print(f" - {m}")
