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
    
    # Метод в подпись
    if config.get("with_method"):
        params['method'] = method
        
    # Выбор полей
    subset = config.get("fields_subset")
    if subset == "mch_ter_amt":
        allowed = ["mchId", "terId", "totalAmount"]
    elif subset == "mch_ter_amt_tx":
        allowed = ["mchId", "terId", "totalAmount", "outTransactionNo"]
    elif subset == "mch_ter_amt_tx_cur":
        allowed = ["mchId", "terId", "totalAmount", "outTransactionNo", "currency"]
    elif subset == "mch_ter_amt_tx_cur_time":
        allowed = ["mchId", "terId", "totalAmount", "outTransactionNo", "currency", "timeStart"]
    elif subset == "mch_ter_amt_tx_cur_time_meth":
        allowed = ["mchId", "terId", "totalAmount", "outTransactionNo", "currency", "timeStart", "method"]
        params['method'] = method
    else:
        # Все поля из запроса
        allowed = list(params.keys())
        
    filtered = {k: v for k, v in params.items() if k in allowed and v is not None and v != ""}
    sorted_keys = sorted(filtered.keys())
    
    # Сборка значений
    vals = []
    for k in sorted_keys:
        val = filtered[k]
        if k == "totalAmount":
            val = f"{float(val):.2f}"
        else:
            val = str(val)
        vals.append((k, val))
        
    algo = config.get("algo")
    
    if algo == "sha256_val":
        # val1val2...password (Обычный SHA256)
        string_to_sign = "".join(v for k, v in vals) + secret_key
        token_hex = hashlib.sha256(string_to_sign.encode('utf-8')).hexdigest()
        return token_hex, string_to_sign
        
    elif algo == "sha256_key_val":
        # key1=val1&key2=val2...&Password=password (Обычный SHA256)
        parts = [f"{k}={v}" for k, v in vals]
        parts.append(f"Password={secret_key}")
        string_to_sign = "&".join(parts)
        token_hex = hashlib.sha256(string_to_sign.encode('utf-8')).hexdigest()
        return token_hex, string_to_sign
        
    elif algo == "hmac_key_val_amp":
        string_to_sign = "&".join(f"{k}={v}" for k, v in vals)
    elif algo == "hmac_val_amp":
        string_to_sign = "&".join(v for k, v in vals)
    elif algo == "hmac_val":
        string_to_sign = "".join(v for k, v in vals)
    else:
        string_to_sign = ""
        
    # Ключ для HMAC
    if config.get("use_b64_key"):
        try:
            key_bytes = base64.b64decode(secret_key)
        except Exception:
            key_bytes = secret_key.encode('utf-8')
    else:
        key_bytes = secret_key.encode('utf-8')
        
    msg_bytes = string_to_sign.encode('utf-8')
    token_hex = hmac.new(key_bytes, msg_bytes, hashlib.sha256).hexdigest()
    return token_hex, string_to_sign

async def try_config(config):
    url = "https://qrpay.tinkoff.ru/qrpay/external/api/v1/operations/QRPAY"
    out_transaction_no = str(int(time.time() * 100))
    
    payload = {
        "mchId": MID,
        "terId": TID,
        "currency": "643",
        "totalAmount": "10.00",
        "outTransactionNo": out_transaction_no,
        "subject": "Test SBP Payment",
        "tradeType": "pay.paxpay.native",
        "version": "V1.0",
        "signType": "HMAC_SHA256",
        "timeStart": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    sig, string_to_sign = build_sig(payload, SECRET_KEY, "qrpay", config)
    payload["signature"] = sig
    
    config_desc = f"algo={config['algo']}, b64key={config['use_b64_key']}, subset={config['fields_subset']}"
    
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
    
    # 1. Проверяем обычный SHA256 (sha256_val и sha256_key_val)
    for algo in ["sha256_val", "sha256_key_val"]:
        for subset in ["all", "mch_ter_amt_tx_cur_time"]:
            configs.append({
                "algo": algo,
                "use_b64_key": False,
                "with_method": False,
                "fields_subset": subset
            })
            
    # 2. Проверяем HMAC на подмножествах полей
    for algo in ["hmac_key_val_amp", "hmac_val_amp", "hmac_val"]:
        for use_b64 in [True, False]:
            for subset in ["mch_ter_amt", "mch_ter_amt_tx", "mch_ter_amt_tx_cur", "mch_ter_amt_tx_cur_time", "mch_ter_amt_tx_cur_time_meth"]:
                configs.append({
                    "algo": algo,
                    "use_b64_key": use_b64,
                    "with_method": (subset == "mch_ter_amt_tx_cur_time_meth"),
                    "fields_subset": subset
                })
                
    print(f"Testing {len(configs)} configurations in v4...")
    for idx, cfg in enumerate(configs):
        success = await try_config(cfg)
        if success:
            print(f"\nFOUND WORKING CONFIGURATION AT INDEX {idx}!")
            break
        await asyncio.sleep(0.3)

if __name__ == "__main__":
    asyncio.run(main())
