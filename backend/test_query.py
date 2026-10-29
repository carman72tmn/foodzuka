import httpx
import time
import base64
import hmac
import hashlib
from datetime import datetime
from app.core.tbank_utils import generate_tbank_qrpay_signature

MID = "400000001164353"
TID = "42734785"
SECRET_KEY = "LYqV0t7V3FBffuphkOs7oR7Le9Cr994xRjmaGxoVJKY="

async def test_query(ori_transaction_no, amount_str):
    url = "https://qrpay.tinkoff.ru/qrpay/external/api/v1/operations/QUERY"
    
    out_transaction_no = str(int(time.time() * 100))
    
    payload = {
        "mchId": MID,
        "terId": TID,
        "oriTransactionNo": ori_transaction_no,
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
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.post(url, json=payload)
        print(f"Status Code: {res.status_code}")
        print(f"Response Text: {res.text}")

if __name__ == "__main__":
    import sys
    import asyncio
    # Используем ID транзакции из нашего успешного теста QRPAY: 1723975640
    tx_id = sys.argv[1] if len(sys.argv) > 1 else "1723975640"
    asyncio.run(test_query(tx_id, "10.00"))
