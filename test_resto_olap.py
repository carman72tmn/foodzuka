import asyncio
import httpx
import hashlib
import json

async def test_resto_olap():
    url = "https://dovezzuka-tyumen.iiko.it/resto"
    login = "apiuser"
    password = "api12user"
    
    # Calculate SHA-1 hash of the password
    password_sha1 = hashlib.sha1(password.encode()).hexdigest()
    
    base_url = url.rstrip('/') + "/api"
    
    print(f"--- Тестирование iiko Office API: {base_url} ---")
    
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        # 1. Auth
        auth_url = f"{base_url}/auth"
        print(f"Авторизация...")
        auth_response = await client.get(auth_url, params={"login": login, "pass": password_sha1})
        if auth_response.status_code != 200:
             print(f"Ошибка SHA1 авторизации: {auth_response.status_code}. Пробуем обычный пароль...")
             auth_response = await client.get(auth_url, params={"login": login, "pass": password})
        
        if auth_response.status_code != 200:
            print(f"Ошибка авторизации: {auth_response.status_code} | {auth_response.text}")
            return
            
        token = auth_response.text.strip().replace('"', '')
        print(f"Успех! Токен: {token[:5]}...")
        
        # 2. OLAP Report (Схема RMS)
        # В iiko Office RMS отчеты OLAP обычно запрашиваются через POST /reports/olap
        # Но формат полей отличается
        # Попробуем структуру:
        payload = {
            "reportType": "SALES",
            "groupByRowFields": ["BusinessDate", "Department"],
            "aggregateFields": ["OrderSum", "DiscountSum", "GuestNum"],
            "filters": {
                "OpenDate.Typed": {
                    "filterType": "Range",
                    "from": "2026-04-07",
                    "to": "2026-04-07"
                }
            }
        }
        
        report_url = f"{base_url}/reports/olap"
        print(f"Запрос отчета...")
        resp = await client.post(report_url, params={"key": token}, json=payload)
        
        print(f"Статус отчета: {resp.status_code}")
        try:
            data = resp.json()
            print("Успех! Полученные данные:", json.dumps(data, indent=2, ensure_ascii=False)[:500])
        except:
            print("Ответ не в формате JSON. Текст:", resp.text[:500])

if __name__ == "__main__":
    asyncio.run(test_resto_olap())
