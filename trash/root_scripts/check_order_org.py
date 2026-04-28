from app.core.database import SessionLocal
from app.models.order import Order
from sqlmodel import select

with SessionLocal() as db:
    orders = db.exec(select(Order).order_by(Order.created_at.desc()).limit(5)).all()
    print("Recent orders details:")
    for o in orders:
        print(f"ID: {o.iiko_order_id} | TerminalGroup: {o.terminal_group_id} | Org: {o.organization_id if hasattr(o, 'organization_id') else 'N/A'}")
