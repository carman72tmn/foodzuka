import psycopg2
import os
from dotenv import load_dotenv

# Попробуем загрузить .env если он есть
load_dotenv()

db_url = os.getenv("DATABASE_URL", "postgresql://foodtech_user:postgres@localhost:5432/foodtech_db")

try:
    # Если мы запускаем это локально, но база на VPS, нам нужно пробросить порт или запустить на VPS
    # Для начала проверим локальную копию если она есть, но лучше проверить на VPS
    print(f"Checking database at {db_url}")
except Exception as e:
    print(f"Error: {e}")
