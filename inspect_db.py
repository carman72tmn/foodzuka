import sys
import json
from sqlmodel import Session, select
from app.core.database import engine
from app.models.customer import Customer
from app.models.order import Order
from app.models.mailing_cascade import MailingCascade, MailingCascadeStep
from app.models.message_log import CustomerMessageLog
from app.models.vk_user import VkUser

def inspect():
    with Session(engine) as session:
        print("=== CASCADES ===")
        cascades = session.exec(select(MailingCascade)).all()
        for c in cascades:
            print(f"Cascade ID: {c.id}, Name: {c.name}, Trigger: {c.trigger_event}, Active: {c.is_active}, OrderType: {c.order_type}")
            for s in sorted(c.steps, key=lambda x: x.priority):
                print(f"  -> Step ID: {s.id}, Priority: {s.priority}, Channel: {s.channel}, Delay: {s.delay_minutes}m, Condition: {s.condition}")
        
        print("\n=== RECENT MESSAGE LOGS ===")
        logs = session.exec(select(CustomerMessageLog).order_by(CustomerMessageLog.id.desc()).limit(15)).all()
        for l in logs:
            print(f"Log ID: {l.id}, CustomerID: {l.customer_id}, OrderID: {l.order_id}, Channel: {l.channel}, Status: {l.status}, Error: {l.error_text}, SentAt: {l.sent_at}")
            
        print("\n=== LINKED VK USERS ===")
        vk_users = session.exec(select(VkUser).where(VkUser.is_linked == True).limit(10)).all()
        for v in vk_users:
            print(f"VK ID: {v.vk_id}, Phone: {v.phone}, Linked: {v.is_linked}, Subscribed: {v.is_subscribed}, Notifications: {v.notifications_enabled}, Blocked: {v.is_blocked}")

        print("\n=== RECENT ORDERS WITH VK_USER_ID ===")
        orders = session.exec(select(Order).where(Order.customer_id != None).order_by(Order.id.desc()).limit(10)).all()
        for o in orders:
            cust = session.get(Customer, o.customer_id)
            vk_id = cust.vk_user_id if cust else None
            print(f"Order ID: {o.id}, Number: {o.external_number}, Status: {o.status}, CustID: {o.customer_id}, Phone: {o.customer_phone}, VK ID: {vk_id}")

if __name__ == "__main__":
    inspect()
