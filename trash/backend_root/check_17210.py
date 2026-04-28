from app.core.db import get_session
from app.models.customer import Customer
from sqlmodel import select
import sys

def check():
    try:
        with next(get_session()) as session:
            customer = session.exec(select(Customer).where(Customer.id == 17210)).first()
            if customer:
                print(f"ID: {customer.id}")
                print(f"Phone: '{customer.phone}'")
                print(f"Iiko ID: '{customer.iiko_customer_id}'")
                print(f"Name: '{customer.name}'")
            else:
                print("Customer not found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check()
