import json
import sys
import os

# Добавляем путь к backend
sys.path.append(os.path.join(os.getcwd(), 'foodzuka', 'foodtech', 'backend'))

from app.core.database import SessionLocal
from app.models import Order, Branch
from sqlmodel import select

def check_order(order_num):
    with SessionLocal() as session:
        order = session.exec(select(Order).where(Order.external_number == order_num)).first()
        if not order:
            # Try partial match
            order = session.exec(select(Order).where(Order.external_number.like(f"%{order_num}"))).first()
        
        if order:
            print(f"--- Order {order.external_number} ---")
            print(f"ID: {order.id}")
            print(f"Address: {order.delivery_address}")
            print(f"Street: {order.street}, House: {order.house}")
            print(f"Terminal Group ID: {order.terminal_group_id}")
            print(f"Terminal Group Name: {order.terminal_group_name}")
            print(f"Branch ID: {order.branch_id}")
        else:
            print(f"Order {order_num} not found")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_order(sys.argv[1])
    else:
        check_order("315")
        print("\n")
        check_order("342")
