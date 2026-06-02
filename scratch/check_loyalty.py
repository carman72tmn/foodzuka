import json
import os
import sys

sys.path.append("/app")

from sqlmodel import Session, create_engine, select
from app.models.iiko_loyalty import IikoLoyaltyItem
from app.core.config import settings

def check_loyalty():
    engine = create_engine(str(settings.DATABASE_URL))
    with Session(engine) as session:
        statement = select(IikoLoyaltyItem).where(IikoLoyaltyItem.iiko_id == '30ee9e91-36d4-a868-e087-15892defe17c')
        item = session.exec(statement).first()
        if item:
            print(f"Name: {item.name}")
            print(f"Type: {item.type}")
            print(f"Content: {item.content}")
        else:
            print("Item not found in DB")

if __name__ == "__main__":
    check_loyalty()
