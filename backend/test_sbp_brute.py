import httpx
import time
import base64
import hmac
import hashlib
from datetime import datetime
import asyncio

MID = "400000001164353"
TID = "42734785"
SECRET_KEY = "LYqV0t7V3FBffuphkOs7oR7Le9Cr994xRjmaGxoVJKY="

def build_signature(payload: dict, secret_key: str, method: str, variant: str) -> str:
    params = payload.copy()
    params.pop('signature', None)
    params.pop('signType', None)
    
    # 1. Секретный ключ (строка vs байты)
    if "raw_key" in variant:
        key_bytes = secret_key.encode('utf-8')
    else:
        try:
            key_bytes = base64.b64decode(secret_key)
        except Exception:
            key_bytes = secret_key.encode('utf-8')
            
    # 2. Наличие method
    if "with_method" in variant:
        params['method'] = method
        
    filtered = {k: v for k, v in params.items() if v is not None and v != ""}
    
    # 3. Формат строки
    if "values_only" in variant:
        # Конкатенация только значений, отсортированных по ключам
        sorted_keys = sorted(filtered.keys())
        string_to_sign = "".join(str(filtered[k]) for k in sorted_keys)
    elif "key_val_amp" in variant:
        # key1=val1&key2=val2...
        sorted_keys = sorted(filtered.keys())
        parts = []
        for k in sorted_keys:
            val = filtered[k]
            if isinstance(val, bool):
                val = str(val).lower()
            elif isinstance(val, (int, float)):
                if k == "totalAmount":
                    val = f"{float(val):.2f}"
                else:
                    val = str(val)
            else:
                val = str(val)
            parts.append(f"{k}={val}")
        string_to_sign = "&".join(parts)
    elif "fixed_order" in variant:
        parts = [
            method,
            filtered.get("mchId", ""),
            filtered.get("terId", ""),
            filtered.get("totalAmount", ""),
            str(filtered.get("outTransactionNo", "")),
            filtered.get("timeStart", "")
        ]
        string_to_sign = "&".join(parts)
    else:
        string_to_sign = ""
        
    msg_bytes = string_to_sign.encode('utf-8')
    sig = hmac.new(key_bytes, msg_bytes, hashlib.sha256).hexdigest()
    return sig, string_to_sign

async def try_variant(variant_name, method, payload_base):
    url = "https://qrpay.tinkoff.ru/qrpay/external/api/v1/operations/QRPAY"
    payload = payload_base.copy()
    
    # Сначала генерируем уникальный outTransactionNo
    payload["outTransactionNo"] = int(time.time() * 100) + hash(variant_name) % 1000
    
    # А потом генерируем подпись!
    sig, string_to_sign = build_signature(payload, SECRET_KEY, method, variant_name)
    payload["signature"] = sig
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.post(url, json=payload)
            res_data = res.json()
            code = res_data.get("code")
            print(f"Variant: {variant_name}")
            print(f"  String to sign: {string_to_sign}")
            print(f"  Result code: {code}, msg: {res_data.get('msg')}")
            if code == "SUCCESS":
                print(f"  !!! SUCCESS !!! outTradeNo: {res_data.get('outTradeNo')}, codeUrl: {res_data.get('codeUrl')}")
                return True
        except Exception as e:
            print(f"Variant: {variant_name} failed with exception: {e}")
    return False

async def main():
    payload_base = {
        "mchId": MID,
        "terId": TID,
        "currency": "643",
        "totalAmount": "10.00",
        "outTransactionNo": 0,  # Заменится
        "subject": "Test SBP Payment",
        "tradeType": "pay.paxpay.native",
        "version": "V1.0",
        "signType": "HMAC_SHA256",
        "timeStart": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    variants = [
        # 1. Сортировка по алфавиту, key1=val1&key2=val2...
        "b64_key_with_method_key_val_amp",
        "raw_key_with_method_key_val_amp",
        "b64_key_without_method_key_val_amp",
        "raw_key_without_method_key_val_amp",
        
        # 2. Значения в одну строку
        "b64_key_with_method_values_only",
        "raw_key_with_method_values_only",
        "b64_key_without_method_values_only",
        "raw_key_without_method_values_only",
        
        # 3. Фиксированный порядок
        "b64_key_fixed_order",
        "raw_key_fixed_order"
    ]
    
    for v in variants:
        success = await try_variant(v, "qrpay", payload_base)
        if success:
            print(f"\nFOUND WORKING CONFIGURATION: {v}")
            break
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())
