import httpx
import time
import base64
import hmac
import hashlib
from datetime import datetime
import json
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
        
    # Выбор подмножества полей
    if config.get("fields_subset") == "minimal":
        allowed = ["mchId", "terId", "totalAmount", "currency", "outTransactionNo", "timeStart", "method"]
        params = {k: v for k, v in params.items() if k in allowed}
    elif config.get("fields_subset") == "no_subject":
        params.pop("subject", None)
        
    filtered = {k: v for k, v in params.items() if v is not None and v != ""}
    sorted_keys = sorted(filtered.keys())
    
    # Сборка значений
    vals = []
    for k in sorted_keys:
        val = filtered[k]
        if isinstance(val, bool):
            val = str(val).lower()
        elif isinstance(val, (int, float)):
            if k == "totalAmount":
                if config.get("amount_format") == "kopecks":
                    val = str(int(float(val) * 100))
                elif config.get("amount_format") == "no_dot":
                    val = str(int(val))
                else:
                    val = f"{float(val):.2f}"
            else:
                val = str(val)
        else:
            val = str(val)
        vals.append((k, val))
        
    # Формат строки для подписи
    fmt = config.get("string_format")
    if fmt == "key_val_amp":
        # key1=val1&key2=val2...
        string_to_sign = "&".join(f"{k}={v}" for k, v in vals)
    elif fmt == "values_only_amp":
        # val1&val2...
        string_to_sign = "&".join(v for k, v in vals)
    elif fmt == "values_only":
        # val1val2...
        string_to_sign = "".join(v for k, v in vals)
    elif fmt == "key_val_no_amp":
        # key1val1key2val2...
        string_to_sign = "".join(f"{k}{v}" for k, v in vals)
    elif fmt == "json":
        # Компактный JSON отсортированный по ключам
        string_to_sign = json.dumps(filtered, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    else:
        string_to_sign = ""
        
    # Ключ
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
        
    amount_val = "10.00"
    if config.get("amount_format") == "kopecks":
        # Если в JSON тоже копейки передаем
        amount_val = "1000"
    elif config.get("amount_format") == "no_dot":
        amount_val = "10"
        
    payload = {
        "mchId": MID,
        "terId": TID,
        "currency": "643",
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
    
    config_desc = f"b64key={config['use_b64_key']}, method={config['with_method']}, subset={config['fields_subset']}, fmt={config['string_format']}, amt={config['amount_format']}"
    
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
    
    # Перебираем форматы строки для подписи
    for fmt in ["values_only", "values_only_amp", "key_val_no_amp", "json", "key_val_amp"]:
        for use_b64 in [True, False]:
            for with_method in [True, False]:
                for subset in ["all", "minimal"]:
                    for amt_fmt in ["dot", "kopecks"]:
                        configs.append({
                            "string_format": fmt,
                            "use_b64_key": use_b64,
                            "with_method": with_method,
                            "fields_subset": subset,
                            "amount_format": amt_fmt,
                            "out_tx_as_int": False  # Передаем строку в JSON
                        })
                        
    print(f"Testing {len(configs)} configurations in v3...")
    for idx, cfg in enumerate(configs):
        success = await try_config(cfg)
        if success:
            print(f"\nFOUND WORKING CONFIGURATION AT INDEX {idx}!")
            break
        await asyncio.sleep(0.3)

if __name__ == "__main__":
    asyncio.run(main())
