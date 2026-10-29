from sqlmodel import Session, select
from app.core.database import engine
from app.models.product import Product, ProductModifierGroup, ProductModifier
from app.models.category import Category

with Session(engine) as session:
    prods = session.exec(select(Product)).all()
    cats = session.exec(select(Category)).all()
    mod_groups = session.exec(select(ProductModifierGroup)).all()
    mods = session.exec(select(ProductModifier)).all()
    
    print(f"Total Products: {len(prods)}")
    print(f"Total Categories: {len(cats)}")
    print(f"Total Modifier Groups: {len(mod_groups)}")
    print(f"Total Modifiers: {len(mods)}")
    
    cat_names = {c.id: c.name for c in cats}
    cat_prod_counts = {}
    for p in prods:
        cname = cat_names.get(p.category_id, "Без категории")
        cat_prod_counts[cname] = cat_prod_counts.get(cname, 0) + 1
        
    print("\nProducts per Category:")
    for cname, count in cat_prod_counts.items():
        print(f" - {cname}: {count} products")
