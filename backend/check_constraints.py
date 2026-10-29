from sqlalchemy import text
from app.core.database import engine

with engine.connect() as conn:
    # Get index/constraint names for vk_cover_bots table
    res = conn.execute(text("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'vk_cover_bots';
    """))
    for row in res:
        print("INDEX:", row[0], "=>", row[1])
        
    res2 = conn.execute(text("""
        SELECT conname, pg_get_constraintdef(oid) 
        FROM pg_constraint 
        WHERE conrelid = 'vk_cover_bots'::regclass;
    """))
    for row in res2:
        print("CONSTRAINT:", row[0], "=>", row[1])
