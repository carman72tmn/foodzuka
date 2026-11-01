from sqlmodel import Session, select
from app.core.database import engine
from app.models.customer import Customer
from app.models.order import Order
from app.utils.phone_utils import normalize_phone

def backfill():
    with Session(engine) as session:
        print("Starting backfill of customer_ids in orders table...")
        # ???????????????? ?????? ????????????, ?? ?????????????? customer_id IS NULL ?? ???????? ??????????????
        orders = session.exec(select(Order).where(Order.customer_id == None).where(Order.customer_phone != None)).all()
        print(f"Found {len(orders)} orders with NULL customer_id")
        
        updated_count = 0
        for order in orders:
            # ???????? ?????????????? ???? ????????????????
            clean_phone = normalize_phone(order.customer_phone)
            if not clean_phone:
                continue
                
            customer = session.exec(select(Customer).where(Customer.phone == clean_phone)).first()
            if customer:
                order.customer_id = customer.id
                session.add(order)
                updated_count += 1
                if updated_count % 100 == 0:
                    session.commit()
                    print(f"Updated {updated_count} orders...")
                    
        session.commit()
        print(f"Backfill completed successfully. Linked {updated_count} orders to customers.")

if __name__ == "__main__":
    backfill()

