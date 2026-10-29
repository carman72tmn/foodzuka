import httpx
import time
import base64
import hmac
import hashlib
from datetime import datetime

MID = "400000001164353"
TID = "42734785"
SECRET_KEY = "LYqV0t7V3FBffuphkOs7oR7Le9Cr994xRjmaGxoVJKY="

def generate_tbank_qrpay_signature(payload: dict, secret_key: str, method: str) -> str:
    params = payload.copy()
    params.pop('signature', None)
    params.pop('signType', None)
    params['method'] = method
    
    filtered = {}
    for k, v in params.items():
        if v is not None and v != "":
            filtered[k] = v
            
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
        parts.append(f"{k}={val}")
        
    string_to_sign = "&".join(parts)
    print(f"[{method.upper()}] String to sign: {string_to_sign}")
    
    try:
        key_bytes = base64.b64decode(secret_key)
    except Exception:
        key_bytes = secret_key.encode('utf-8')
        
    msg_bytes = string_to_sign.encode('utf-8')
    sig = hmac.new(key_bytes, msg_bytes, hashlib.sha256).hexdigest()
    return sig

async def test_qrpay():
    url = "https://qrpay.tinkoff.ru/qrpay/external/api/v1/operations/QRPAY"
    
    # outTransactionNo must be a unique positive integer
    out_transaction_no = int(time.time() * 100)
    
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
    
    payload["signature"] = generate_tbank_qrpay_signature(payload, SECRET_KEY, "qrpay")
    
    print(f"\nSending QRPAY request to {url}:")
    print(payload)
    
    async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
        res = await client.post(url, json=payload)
        print(f"Status Code: {res.status_code}")
        print(f"Response Headers: {res.headers}")
        print(f"Response Text: {res.text}")
        
        if res.status_code == 200:
            res_data = res.json()
            if res_data.get("code") == "SUCCESS":
                out_trade_no = res_data.get("outTradeNo")
                code_url = res_data.get("codeUrl")
                print(f"\nSuccess! outTradeNo: {out_trade_no}")
                print(f"codeUrl: {code_url}")
                
                # Check status
                await test_query(out_trade_no, "10.00")
            else:
                print(f"API Error: {res_data.get('msg')}")

async def test_query(ori_transaction_no, amount_str):
    url = "https://qrpay.tinkoff.ru/qrpay/external/api/v1/operations/QUERY"
    
    out_transaction_no = int(time.time() * 100) + 1
    
    payload = {
        "mchId": MID,
        "terId": TID,
        "oriTransactionNo": int(ori_transaction_no) if ori_transaction_no.isdigit() else ori_transaction_no,
        "outTransactionNo": out_transaction_no,
        "totalAmount": amount_str,
        "currency": "643",
        "tradeType": "pay.paxpay.native",
        "version": "V1.0",
        "signType": "HMAC_SHA256",
        "timeStart": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    payload["signature"] = generate_tbank_qrpay_signature(payload, SECRET_KEY, "query")
    
    print(f"\nSending QUERY request to {url}:")
    print(payload)
    
    async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
        res = await client.post(url, json=payload)
        print(f"Status Code: {res.status_code}")
        print(f"Response Text: {res.text}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_qrpay())
