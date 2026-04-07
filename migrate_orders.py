"""
Миграция: добавляем недостающие колонки в таблицы orders и delivery_zones.
Запускать: python3 migrate_orders.py
"""
import psycopg2
import sys

DSN = "postgresql://foodtech_user:postgres@localhost:5432/foodtech_db"

ORDERS_COLUMNS = [
    # (column_name, sql_definition)
    ("external_number",       "VARCHAR(100)"),
    ("terminal_group_id",     "VARCHAR(255)"),
    ("terminal_group_name",   "VARCHAR(255)"),
    ("source",                "VARCHAR(100)"),
    ("bonus_accrued",         "NUMERIC(10,2) NOT NULL DEFAULT 0"),
    ("total_with_discount",   "NUMERIC(10,2) NOT NULL DEFAULT 0"),
    ("payment_method",        "VARCHAR(255)"),
    ("order_type",            "VARCHAR(255)"),
    ("courier_name",          "VARCHAR(255)"),
    ("iiko_creation_time",    "TIMESTAMP"),
    ("expected_time",         "TIMESTAMP"),
    ("actual_time",           "TIMESTAMP"),
    ("delay_minutes",         "INTEGER"),
    ("is_on_time",            "BOOLEAN NOT NULL DEFAULT TRUE"),
    ("admin_name",            "VARCHAR(255)"),
    ("city",                  "VARCHAR(255)"),
    ("delivery_zone",         "VARCHAR(255)"),
    ("is_paid",               "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("order_items_details",   "JSONB"),
    ("discounts_details",     "JSONB"),
    ("customer_info_details", "JSONB"),
]

DELIVERY_ZONES_COLUMNS = [
    ("iiko_id", "VARCHAR(255)"),
]

def add_columns_if_missing(cur, table, columns):
    cur.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
        (table,)
    )
    existing = {row[0] for row in cur.fetchall()}
    added = []
    for col_name, col_def in columns:
        if col_name not in existing:
            sql = f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def};"
            print(f"  + ADD COLUMN {table}.{col_name} ({col_def})")
            cur.execute(sql)
            added.append(col_name)
        else:
            print(f"  ✓ {table}.{col_name} already exists")
    return added

def main():
    try:
        conn = psycopg2.connect(DSN)
        conn.autocommit = False
        cur = conn.cursor()
        print("=== Migrating orders table ===")
        added_orders = add_columns_if_missing(cur, "orders", ORDERS_COLUMNS)

        print("\n=== Migrating delivery_zones table ===")
        added_zones = add_columns_if_missing(cur, "delivery_zones", DELIVERY_ZONES_COLUMNS)

        # Add index on orders.iiko_creation_time for performance
        cur.execute("""
            CREATE INDEX IF NOT EXISTS orders_iiko_creation_time_idx 
            ON orders (iiko_creation_time DESC);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS orders_external_number_idx 
            ON orders (external_number);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS orders_terminal_group_id_idx 
            ON orders (terminal_group_id);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS delivery_zones_iiko_id_idx 
            ON delivery_zones (iiko_id);
        """)

        conn.commit()
        print(f"\n✅ Migration complete!")
        print(f"   orders: {len(added_orders)} columns added: {added_orders}")
        print(f"   delivery_zones: {len(added_zones)} columns added: {added_zones}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Migration failed: {e}", file=sys.stderr)
        if 'conn' in dir():
            conn.rollback()
        sys.exit(1)

if __name__ == "__main__":
    main()
