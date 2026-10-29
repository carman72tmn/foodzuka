import asyncio
import json
from sqlmodel import Session, select
from app.core.database import engine
from app.models.iiko_settings import IikoSettings
from app.models.product import Product, ProductSize
from app.models.category import Category
from app.services.iiko_sync_service import iiko_sync_service

async def main():
    print("=== TESTING UTF-8 ENCODING & MENU SYNC ON VPS ===")
    
    # 1. Verify files are UTF-8 readable
    for filepath in ['app/services/iiko_service.py', 'app/services/iiko_sync_service.py']:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"File {filepath}: UTF-8 OK ({len(content)} chars)")

    # 2. Trigger sync_menu
    with Session(engine) as session:
        print("\nStarting iiko_sync_service.sync_menu()...")
        sync_result = await iiko_sync_service.sync_menu(session)
        print("Sync result:", json.dumps(sync_result, indent=2, ensure_ascii=False))

        # 3. Check DB stats after sync
        all_prods = session.exec(select(Product)).all()
        all_cats = session.exec(select(Category)).all()
        print(f"\nTotal Categories in DB: {len(all_cats)}")
        print(f"Total Products in DB: {len(all_prods)}")

        # 4. Check Pizza size section
        pizzas = session.exec(select(Product).where(Product.name.ilike("%пицц%"))).all()
        print(f"\nFound {len(pizzas)} pizza products in DB after sync:")
        for p in pizzas[:10]:
            sizes = session.exec(select(ProductSize).where(ProductSize.product_id == p.id)).all()
            size_info = [(s.name, str(s.price), f"weight={s.weight_grams}", f"is_default={s.is_default}") for s in sizes]
            print(f" - [{p.id}] {p.name}: price={p.price}, sizes_count={len(sizes)} -> {size_info}")

if __name__ == "__main__":
    asyncio.run(main())
