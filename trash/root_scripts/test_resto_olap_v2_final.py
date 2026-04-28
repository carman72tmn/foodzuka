import asyncio
import httpx
import hashlib
import json
from datetime import datetime, timedelta

async def test_resto_olap_v2_final():
    # Настройки для теста (замените на реальные если нужно, или скрипт возьмет из env)
    url = "https://dovezzuka-tyumen.iiko.it/resto"
    login = "apiuser"
    password = "api12user"
    
    password_sha1 = hashlib.sha1(password.encode()).hexdigest()
    base_url = url.rstrip('/') + "/api"
    
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        # 1. Авторизация
        print(f"--- Авторизация в {base_url}/auth ---")
        auth_response = await client.get(f"{base_url}/auth", params={"login": login, "pass": password_sha1})
        if auth_response.status_code != 200:
            print(f"Ошибка авторизации: {auth_response.text}")
            return
            
        token = auth_response.text.strip().replace('"', '')
        print(f"Токен получен: {token[:10]}...")
        
        # 2. Формирование запроса OLAP v2
        print("\n--- Запрос OLAP v2 (POST /v2/reports/olap) ---")
        
        # Тестируем за сегодня
        date_from = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # Фикс 409 ошибки: прибавляем 1 день к 'to'
        date_to = date_from + timedelta(days=1)
        
        v2_from = date_from.strftime("%Y-%m-%dT00:00:00.000")
        v2_to = date_to.strftime("%Y-%m-%dT00:00:00.000")
        
        payload = {
            "reportType": "SALES",
            "groupByRowFields": ["Department", "OpenDate.Typed"],
            "aggregateFields": [
                "DishSumAfterDiscount.Sum", 
                "DishDiscountSum.Sum", 
                "GuestNum", 
                "DishAmount"
            ],
            "filters": {
                "OpenDate.Typed": {
                    "filterType": "DateRange",
                    "periodType": "CUSTOM",
                    "from": v2_from,
                    "to": v2_to,
                    "includeLow": True,
                    "includeHigh": False
                },
                "OrderDeleted": {
                    "filterType": "IncludeValues",
                    "values": ["NOT_DELETED"]
                }
            }
        }
        
        print(f"Отправляем payload на период: {v2_from} - {v2_to}")
        
        resp = await client.post(
            f"{base_url}/v2/reports/olap", 
            params={"key": token},
            json=payload
        )
        
        print(f"Статус ответа: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            cols = data.get("columnNames", [])
            rows = data.get("data", [])
            
            print(f"Успех! Получено строк: {len(rows)}")
            print(f"Колонки: {cols}")
            
            if rows:
                print("\nПример данных (первая строка):")
                print(dict(zip(cols, rows[0])))
                
                # Проверка корректности полей
                row_dict = dict(zip(cols, rows[0]))
                revenue = row_dict.get("DishSumAfterDiscount.Sum")
                print(f"\nИТОГОВАЯ ВЫРУЧКА: {revenue}")
        else:
            print(f"ОШИБКА: {resp.text}")

if __name__ == "__main__":
    asyncio.run(test_resto_olap_v2_final())
