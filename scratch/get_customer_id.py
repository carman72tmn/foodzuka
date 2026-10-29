from app.core.database import engine
from sqlmodel import Session, select
from app.models.customer import Customer

with Session(engine) as session:
    c = session.exec(select(Customer).where(Customer.phone == "+79044625756")).first()
    if c:
        print(f"Customer ID: {c.id}")
        print(f"Name: {c.name} {c.surname}")
    else:
        print("Not found")
