from app.core.database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)

def check():
    with engine.connect() as conn:
        res = conn.execute(text('SELECT COUNT(*) FROM courier_orders'))
        count = res.scalar()
        print(f"Courier orders count: {count}")
        
        res = conn.execute(text('SELECT MAX(actual_delivery_time) FROM courier_orders'))
        last_time = res.scalar()
        print(f"Last delivery time: {last_time}")
        
        # Проверим заказы за последние 5 дней
        res = conn.execute(text("SELECT date(actual_delivery_time), count(*) FROM courier_orders WHERE actual_delivery_time > now() - interval '7 days' GROUP BY 1 ORDER BY 1 DESC"))
        print("\nOrders per day (last 7 days):")
        for row in res:
            print(f"{row[0]}: {row[1]}")

if __name__ == "__main__":
    check()
