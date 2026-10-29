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

def build_sig(payload: dict, secret_key: str, method: str, config: dict) -> str:
    params = payload.copy()
    params.pop('signature', None)
    params.pop('signType', None)
    
    if config.get("with_method"):
        params['method'] = method
        
    filtered = {k: v for k, v in params.items() if v is not None and v != ""}
    sorted_keys = sorted(filtered.keys())
    
    parts = []
    for k in sorted_keys:
        val = filtered[k]
        if k == "totalAmount":
            if config.get("amount_format") == "kopecks":
                val = "1000"
            elif config.get("amount_format") == "no_dot":
                val = "10"
            else:
                val = "10.00"
        parts.append(f"{k}={val}")
        
    string_to_sign = "&".join(parts)
    
    # Ключ шифрования
    key_type = config.get("key_type")
    if key_type == "b64_bytes":
        key_bytes = base64.b64decode(secret_key)
    elif key_type == "hex_str":
        key_bytes = base64.b64decode(secret_key).hex().encode('utf-8')
    elif key_type == "hex_str_raw":
        key_bytes = base64.b64decode(secret_key).hex()  # Строка
    else:
        key_bytes = secret_key.encode('utf-8')
        
    msg_bytes = string_to_sign.encode('utf-8')
    
    if isinstance(key_bytes, str):
        key_bytes = key_bytes.encode('utf-8')
        
    sig = hmac.new(key_bytes, msg_bytes, hashlib.sha256).hexdigest()
    return sig, string_to_sign

async def try_config(config):
    url = "https://qrpay.tinkoff.ru/qrpay/external/api/v1/operations/QRPAY"
    out_transaction_no = str(int(time.time() * 100))
    
    amount_val = "10.00"
    if config.get("amount_format") == "kopecks":
        amount_val = "1000"
    elif config.get("amount_format") == "no_dot":
        amount_val = "10"
        
    payload = {
        "mchId": MID,
        "terId": TID,
        "currency": config.get("currency"),
        "totalAmount": amount_val,
        "outTransactionNo": out_transaction_no,
        "subject": "Test SBP Payment",
        "tradeType": "pay.paxpay.native",
        "version": "V1.0",
        "signType": "HMAC_SHA256",
        "timeStart": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    sig, string_to_sign = build_sig(payload, SECRET_KEY, "qrpay", config)
    payload["signature"] = sig
    
    config_desc = f"key={config['key_type']}, method={config['with_method']}, currency={config['currency']}, amt={config['amount_format']}"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.post(url, json=payload)
            res_data = res.json()
            code = res_data.get("code")
            print(f"Config: {config_desc}")
            print(f"  String to sign: {string_to_sign}")
            print(f"  Result code: {code}, msg: {res_data.get('msg')}")
            if code == "SUCCESS":
                print(f"  !!! SUCCESS !!! outTradeNo: {res_data.get('outTradeNo')}, codeUrl: {res_data.get('codeUrl')}")
                return True
        except Exception as e:
            print(f"Config: {config_desc} failed with exception: {e}")
    return False

async def main():
    configs = []
    
    for key_type in ["b64_bytes", "raw_str", "hex_str"]:
        for with_method in [True, False]:
            for currency in ["643", "RUB"]:
                for amt_format in ["dot", "kopecks", "no_dot"]:
                    configs.append({
                        "key_type": key_type,
                        "with_method": with_method,
                        "currency": currency,
                        "amount_format": amt_format
                    })
                        
    print(f"Testing {len(configs)} configurations in v5...")
    for idx, cfg in enumerate(configs):
        success = await try_config(cfg)
        if success:
            print(f"\nFOUND WORKING CONFIGURATION AT INDEX {idx}!")
            break
        await asyncio.sleep(0.3)

if __name__ == "__main__":
    asyncio.run(main())
