import sys
import os
from sqlmodel import Session, create_engine, select

# Add parent dir to path to import models
sys.path.append(os.getcwd())

from app.models.iiko_loyalty import IikoLoyaltyItem
from app.core.config import settings

engine = create_engine(str(settings.DATABASE_URL))

with Session(engine) as session:
    items = session.exec(select(IikoLoyaltyItem).where(IikoLoyaltyItem.name.like("Unnamed%"))).all()
    print(f"Found {len(items)} unnamed items:")
    for item in items:
        print(f"ID: {item.iiko_id} | Name: {item.name} | Type: {item.type}")
