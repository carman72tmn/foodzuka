import os
import psycopg2
from urllib.parse import urlparse

# DATABASE_URL = "postgresql://foodtech_user:FoodZuka_Secure_2026!@localhost:5432/foodtech_db"
# We don't have DATABASE_URL here, but we can try to get it from backend/app/core/config.py or common defaults
# Actually, the user rule says "БД: foodtech_db, Пользователь: foodtech_user, Пароль: FoodZuka_Secure_2026!"
# Host is likely localhost if we run it from here (if port 5432 is forwarded)

def check_db():
    try:
        conn = psycopg2.connect(
            dbname="foodtech_db",
            user="foodtech_user",
            password="FoodZuka_Secure_2026!",
            host="localhost",
            port="5432"
        )
        cur = conn.cursor()
        
        for table in ['users', 'employees']:
            print(f"Table: {table}")
            cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}';")
            for row in cur.fetchall():
                print(f"  {row[0]}: {row[1]}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
