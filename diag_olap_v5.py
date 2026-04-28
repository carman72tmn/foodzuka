
import httpx
import json
import asyncio
from datetime import datetime

async def test():
    base_url = "https://dovezzuka-tyumen.iiko.it:9900/api/0"
    # Пытаемся получить токен. В прошлый раз были проблемы с 401.
    # Если 401, попробуем использовать токен из логов если есть, или просто проверим доступность.
    
    login = "superapi"
    # Пароль мы не знаем точно, но в базе он есть.
    # Для теста на VPS мы можем вытащить его из БД или просто прогнать через основной код.
    # Но я хочу проверить именно поля.
    
    # Попробуем сделать запрос через существующий механизм iiko_service если возможно,
    # но на VPS проще запустить отдельный скрипт.
    
    print("Starting field validation...")
    
    # Список полей для проверки
    rows = ["Department", "CashRegister", "OpenDate.Typed"]
    aggs = ["fullSum", "DishDiscountSumInt", "DiscountSum", "UniqOrderId", "ProductCostBase.ProductCost", "ProductCostBase.MarkUp", "ProductCostBase.Percent"]
    
    print(f"Rows: {rows}")
    print(f"Aggs: {aggs}")

if __name__ == "__main__":
    asyncio.run(test())
