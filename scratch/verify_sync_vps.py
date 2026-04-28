import asyncio
import os
import sys

# Add app directory to path
sys.path.append('/app')

from app.core.database import SessionLocal
from app.services.iiko_sync_service import iiko_sync_service
from app.models.product import Product, ProductSize, ProductModifierGroup, ProductModifier
from sqlmodel import select

async def run_sync():
    print("Starting menu sync...")
    with SessionLocal() as session:
        result = await iiko_sync_service.sync_menu(session)
        print(f"Sync result: {result}")
        
        # Verify specific item "Ёсан Кани"
        prod = session.exec(select(Product).where(Product.name == "Ёсан Кани")).first()
        if prod:
            print(f"Product found: {prod.name} (ID: {prod.id})")
            print(f"  Price: {prod.price}")
            print(f"  Nutritions: Cal: {prod.calories}, Prot: {prod.proteins}, Fats: {prod.fats}, Carbs: {prod.carbohydrates}")
            
            sizes = session.exec(select(ProductSize).where(ProductSize.product_id == prod.id)).all()
            print(f"  Sizes ({len(sizes)}): {[s.name for s in sizes]}")
            
            groups = session.exec(select(ProductModifierGroup).where(ProductModifierGroup.product_id == prod.id)).all()
            print(f"  Modifier Groups ({len(groups)}):")
            for g in groups:
                print(f"    - {g.name} (iiko_id: {g.iiko_id})")
                mods = session.exec(select(ProductModifier).where(ProductModifier.group_id == g.id)).all()
                for m in mods:
                    print(f"        * {m.name} (Price: {m.price})")
        else:
            print("Product 'Ёсан Кани' not found in DB after sync!")

if __name__ == "__main__":
    asyncio.run(run_sync())
