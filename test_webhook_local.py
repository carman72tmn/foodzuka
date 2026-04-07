import requests
import json
import uuid

# URL локального обработчика (внутри сети докера или через прокси)
# Мы будем тестировать прямо через локальный адрес бэкенда
WEBHOOK_URL = "https://72roll.ru/api/v1/webhooks/iiko"
AUTH_TOKEN = "3f036c75a241bcab428f948484da6691"

def test_webhook():
    print(f"--- Тестирование вебхука: {WEBHOOK_URL} ---")
    
    # Пример реального заказа из iiko (упрощенный)
    # Используем существующий ID заказа из вашей базы, если он есть, 
    # или просто новый UUID для проверки создания записи в логах.
    order_id = str(uuid.uuid4())
    
    payload = {
        "eventType": "DeliveryOrderUpdate",
        "eventId": str(uuid.uuid4()),
        "organizationId": "2704eeae-dc5f-4c9f-9b81-375c454dd5bd",
        "eventInfo": {
            "id": order_id,
            "status": "OnWay",
            "externalNumber": "TEST-WEBHOOK-001"
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=10)
        print(f"Статус ответа: {response.status_code}")
        print(f"Тело ответа: {response.text}")
        
        if response.status_code == 200:
            print("✅ Вебхук успешно принят сервером!")
        else:
            print("❌ Ошибка при отправке вебхука.")
            
    except Exception as e:
        print(f"❌ Ошибка соединения: {e}")

if __name__ == "__main__":
    test_webhook()
