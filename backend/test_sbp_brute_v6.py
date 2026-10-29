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
    params.pop('signature', None)  # signature ВСЕГДА исключается
    
    # signType исключается только если указано в конфиге, иначе участвует!
    if config.get("exclude_sigtype"):
        params.pop('signType', None)
        
    if config.get("with_method"):
        params['method'] = method
        
    if config.get("fields_subset") == "minimal":
        allowed = ["mchId", "terId", "totalAmount", "currency", "outTransactionNo", "timeStart", "method", "signType"]
        params = {k: v for k, v in params.items() if k in allowed}
        
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
    
    # Ключ HMAC
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
    
    amount_val = "10.00"
    if config.get("amount_format") == "kopecks":
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
    
    config_desc = f"b64={config['use_b64_key']}, with_meth={config['with_method']}, subset={config['fields_subset']}, amt={config['amount_format']}, excl_sigtype={config['exclude_sigtype']}"
    
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
    
    # Перебираем варианты, включая signType в подпись
    for exclude_sigtype in [False, True]:
        for use_b64 in [True, False]:
            for with_method in [True, False]:
                for subset in ["all", "minimal"]:
                    for amt_fmt in ["dot", "kopecks"]:
                        configs.append({
                            "exclude_sigtype": exclude_sigtype,
                            "use_b64_key": use_b64,
                            "with_method": with_method,
                            "fields_subset": subset,
                            "amount_format": amt_fmt
                        })
                        
    print(f"Testing {len(configs)} configurations in v6...")
    for idx, cfg in enumerate(configs):
        success = await try_config(cfg)
        if success:
            print(f"\nFOUND WORKING CONFIGURATION AT INDEX {idx}!")
            break
        await asyncio.sleep(0.3)

if __name__ == "__main__":
    asyncio.run(main())
