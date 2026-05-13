import asyncio
from sqlmodel import Session, select
from app.core.database import engine
from app.models.customer import Customer
from app.services.iiko_service import iiko_service
from app.api.customers import update_customer_in_iiko

async def test_card_gen():
    customer_id = 62 # +79199325704
    
    # We need a mock session and some customer data
    with Session(engine) as session:
        customer = session.get(Customer, customer_id)
        if not customer:
            print("Customer not found")
            return
        
        print(f"Testing for customer {customer.phone} (ID: {customer.id})")
        print(f"Current card_number: {customer.card_number}")
        
        # Call the update logic
        # We pass an empty dict for customer_data to trigger only iiko update/check
        try:
            result = await update_customer_in_iiko(customer_id, {}, session)
            print("Update call finished")
            
            # Refresh customer from DB
            session.refresh(customer)
            print(f"New card_number in DB: {customer.card_number}")
            
        except Exception as e:
            print(f"Error during test: {e}")

if __name__ == "__main__":
    asyncio.run(test_card_gen())
