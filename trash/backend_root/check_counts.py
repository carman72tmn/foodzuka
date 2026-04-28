from app.core.database import SessionLocal
from app.models.company import DeliveryZone, Branch
from sqlmodel import select

def check_counts():
    session = SessionLocal()
    branches = session.exec(select(Branch)).all()
    zones = session.exec(select(DeliveryZone)).all()
    print(f"Branches: {len(branches)}")
    for b in branches:
        print(f" - Branch ID {b.id}: {b.name}")
    print(f"Zones: {len(zones)}")
    for z in zones:
        print(f" - Zone: {z.name} (branch_id={z.branch_id}, cost={z.delivery_cost})")
    session.close()

if __name__ == "__main__":
    check_counts()
