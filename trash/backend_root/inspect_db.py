import logging
from sqlalchemy import text
from app.core.database import engine

def inspect():
    with engine.connect() as conn:
        print("\n--- SCHEMA AUDIT ---")
        # Проверка nullable колонок
        query = text("""
            SELECT table_name, column_name, is_nullable, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name IN ('orders', 'order_items', 'customers', 'products') 
            ORDER BY table_name, ordinal_position
        """)
        res = conn.execute(query)
        for row in res:
            print(f"Table: {row[0]:12} | Column: {row[1]:20} | Nullable: {row[2]:5} | Type: {row[3]}")

        print("\n--- INDEX AUDIT ---")
        query_idx = text("""
            SELECT t.relname AS table_name, i.relname AS index_name, a.attname AS column_name
            FROM pg_class t, pg_class i, pg_index ix, pg_attribute a
            WHERE t.oid = ix.indrelid AND i.oid = ix.indexrelid AND a.attrelid = t.oid
            AND a.attnum = ANY(ix.indkey) AND t.relkind = 'r'
            AND t.relname IN ('orders', 'order_items', 'customers', 'products')
            ORDER BY t.relname, i.relname;
        """)
        res_idx = conn.execute(query_idx)
        for row in res_idx:
            print(f"Table: {row[0]:12} | Index: {row[1]:25} | Column: {row[2]}")

if __name__ == "__main__":
    inspect()
