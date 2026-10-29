import sys
import os
import httpx
import time
import base64
from sqlmodel import Session, select

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import engine
from app.models.tbank_settings import TBankSettings
from app.core.tbank_utils import generate_tbank_token

async def diag():
    print("=== ЗАПУСК ТЕСТОВОЙ ИНИЦИАЦИИ СБП MERCHANT API ===")
    with Session(engine) as session:
        settings = session.exec(select(TBankSettings)).first()
        if not settings:
            print("ОШИБКА: Настройки Т-Банка не найдены!")
            return
            
        print(f"Terminal Pickup: {settings.terminal_pickup}")
        print(f"Terminal Delivery: {settings.terminal_delivery}")
        print(f"Terminal General: {settings.terminal_key}")
        print(f"Secret Key (Token в БД): {settings.token[:5]}...{settings.token[-5:] if settings.token else ''}")
        
        terminal_key = settings.terminal_delivery or settings.terminal_pickup or settings.terminal_key
        if not terminal_key:
            print("ОШИБКА: Не задан Terminal Key!")
            return
            
        print(f"Выбран Terminal Key: {terminal_key}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Шаг 1: Init
            init_url = "https://securepay.tinkoff.ru/v2/Init"
            init_payload = {
                "TerminalKey": terminal_key,
                "Amount": 1000, # 10 рублей
                "OrderId": f"diag_eacq_{int(time.time())}",
                "Description": "Тестовый платеж СБП Диагностика"
            }
            init_payload["Token"] = generate_tbank_token(init_payload, settings.token)
            
            print(f"Отправляем POST на {init_url}...")
            res = await client.post(init_url, json=init_payload)
            print(f"Статус: {res.status_code}")
            print(f"Тело: {res.text}")
            
            if res.status_code != 200:
                print("ОШИБКА: Запрос Init завершился со статусом", res.status_code)
                return
                
            init_data = res.json()
            if not init_data.get("Success"):
                print("ОШИБКА: Т-Банк отклонил Init:", init_data.get("Message"))
                return
                
            payment_id = init_data.get("PaymentId")
            print(f"УСПЕХ Init! PaymentId: {payment_id}")
            
            # Шаг 2: GetQr PAYLOAD
            qr_url = "https://securepay.tinkoff.ru/v2/GetQr"
            qr_payload = {
                "TerminalKey": terminal_key,
                "PaymentId": payment_id,
                "DataType": "PAYLOAD"
            }
            qr_payload["Token"] = generate_tbank_token(qr_payload, settings.token)
            
            print(f"Отправляем POST на {qr_url} (DataType=PAYLOAD)...")
            res_qr = await client.post(qr_url, json=qr_payload)
            print(f"Статус: {res_qr.status_code}")
            print(f"Тело: {res_qr.text}")
            
            # Шаг 3: GetQr IMAGE
            qr_img_payload = {
                "TerminalKey": terminal_key,
                "PaymentId": payment_id,
                "DataType": "IMAGE"
            }
            qr_img_payload["Token"] = generate_tbank_token(qr_img_payload, settings.token)
            
            print(f"Отправляем POST на {qr_url} (DataType=IMAGE)...")
            res_img = await client.post(qr_url, json=qr_img_payload)
            print(f"Статус: {res_img.status_code}")
            if res_img.status_code == 200:
                content_type = res_img.headers.get("content-type", "")
                print(f"Content-Type: {content_type}")
                if "application/json" in content_type:
                    print(f"JSON-ответ: {res_img.text[:200]}...")
                else:
                    print(f"Бинарный ответ/SVG: {res_img.text[:200]}...")
            else:
                print(f"Тело ошибки IMAGE: {res_img.text}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(diag())
