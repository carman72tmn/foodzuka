import sys
import os
from sqlalchemy import create_engine, text

# Пробуем разные варианты хоста
hosts = ["db", "localhost", "127.0.0.1"]
db_url_template = "postgresql://foodtech_user:postgres@{}:5432/foodtech_db"

for host in hosts:
    url = db_url_template.format(host)
    print(f"Проверка {url}...")
    try:
        engine = create_engine(url, connect_args={'connect_timeout': 2})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"Успешное подключение к {host}!")
        os.environ["DATABASE_URL"] = url
        break
    except Exception as e:
        print(f"Ошибка подключения к {host}: {e}")
