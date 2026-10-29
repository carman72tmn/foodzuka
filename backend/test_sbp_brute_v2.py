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
        
    # Фильтруем поля по конфигу
    if config.get("fields_subset") == "minimal":
        # Только основные поля
        allowed = ["mchId", "terId", "totalAmount", "currency", "outTransactionNo", "timeStart", "method"]
        params = {k: v for k, v in params.items() if k in allowed}
    elif config.get("fields_subset") == "no_subject":
        # Без subject, но с tradeType и version
        params.pop("subject", None)
        
    filtered = {k: v for k, v in params.items() if v is not None and v != ""}
    
    # Сортировка по алфавиту
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
    
    if config.get("use_b64_key"):
        try:
            key_bytes = base64.b64decode(secret_key)
        except Exception:
            key_bytes = secret_key.encode('utf-8')
    else:
        key_bytes = secret_key.encode('utf-8')
        
    msg_bytes = string_to_sign.encode('utf-8')
    sig = hmac.new(key_bytes, msg_bytes, hashlib.sha256).hexdigest()
    return sig, string_to_sign

async def try_config(config):
    url = "https://qrpay.tinkoff.ru/qrpay/external/api/v1/operations/QRPAY"
    
    out_transaction_no = str(int(time.time() * 100))
    if config.get("out_tx_as_int"):
        out_transaction_no = int(out_transaction_no)
        
    payload = {
        "mchId": MID,
        "terId": TID,
        "currency": "643",
        "totalAmount": "10.00",
        "outTransactionNo": out_transaction_no,
        "subject": "Test SBP Payment",
        "tradeType": "pay.paxpay.native",
        "version": "V1.0",
        "signType": config.get("sign_type"),
        "timeStart": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    sig, string_to_sign = build_sig(payload, SECRET_KEY, "qrpay", config)
    payload["signature"] = sig
    
    config_desc = f"b64key={config['use_b64_key']}, method={config['with_method']}, subset={config['fields_subset']}, tx_int={config['out_tx_as_int']}, sigType={config['sign_type']}"
    
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
    
    # Генерируем комбинации
    for use_b64 in [True, False]:
        for with_method in [True, False]:
            for subset in ["all", "minimal", "no_subject"]:
                for tx_int in [True, False]:
                    for sig_type in ["HMAC_SHA256", "SOFTPOS_SHA256_HMAC"]:
                        configs.append({
                            "use_b64_key": use_b64,
                            "with_method": with_method,
                            "fields_subset": subset,
                            "out_tx_as_int": tx_int,
                            "sign_type": sig_type
                        })
                        
    print(f"Testing {len(configs)} configurations...")
    for idx, cfg in enumerate(configs):
        success = await try_config(cfg)
        if success:
            print(f"\nFOUND WORKING CONFIGURATION AT INDEX {idx}!")
            break
        await asyncio.sleep(0.3)

if __name__ == "__main__":
    asyncio.run(main())
