import httpx
import time
import hashlib

TID = "42734785"
PASSWORD = "LYqV0t7V3FBffuphkOs7oR7Le9Cr994xRjmaGxoVJKY="

def generate_tbank_token(payload: dict, password: str) -> str:
    params = payload.copy()
    keys_to_exclude = ['Token', 'token', 'Receipt', 'DATA', 'DATA_TYPE', 'Shops', 'Receipts', 'DATA_TYPE_QR']
    for key in keys_to_exclude:
        params.pop(key, None)
        
    filtered_params = {}
    for k, v in params.items():
        if not isinstance(v, (dict, list)):
            filtered_params[k] = v
            
    filtered_params['Password'] = password
    sorted_keys = sorted(filtered_params.keys())
    concatenated = "".join(str(filtered_params[k]) for k in sorted_keys)
    print(f"Concatenated string for token: {concatenated}")
    token_hex = hashlib.sha256(concatenated.encode('utf-8')).hexdigest()
    return token_hex

async def test_eacq():
    init_url = "https://securepay.tinkoff.ru/v2/Init"
    order_id = f"TEST_{int(time.time())}"
    
    payload = {
        "TerminalKey": TID,
        "Amount": 1000,  # 10.00 руб (в копейках)
        "OrderId": order_id,
        "Description": "Test SBP via Acquiring API"
    }
    
    payload["Token"] = generate_tbank_token(payload, PASSWORD)
    
    print("\nSending Init request:")
    print(payload)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.post(init_url, json=payload)
        print(f"Init Status Code: {res.status_code}")
        print(f"Init Response: {res.text}")
        
        if res.status_code == 200:
            res_data = res.json()
            if res_data.get("Success") is True:
                payment_id = res_data.get("PaymentId")
                print(f"Success! PaymentId: {payment_id}")
                
                # Try to get SBP QR Code
                await test_get_qr(payment_id)
            else:
                print(f"Init Failed: {res_data.get('Message')}")

async def test_get_qr(payment_id):
    qr_url = "https://securepay.tinkoff.ru/v2/GetQr"
    
    payload = {
        "TerminalKey": TID,
        "PaymentId": str(payment_id),
        "DataType": "PAYLOAD"
    }
    
    payload["Token"] = generate_tbank_token(payload, PASSWORD)
    
    print("\nSending GetQr (PAYLOAD) request:")
    print(payload)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.post(qr_url, json=payload)
        print(f"GetQr Status Code: {res.status_code}")
        print(f"GetQr Response: {res.text}")
        
        # Test GetState
        await test_get_state(payment_id)

async def test_get_state(payment_id):
    state_url = "https://securepay.tinkoff.ru/v2/GetState"
    
    payload = {
        "TerminalKey": TID,
        "PaymentId": str(payment_id)
    }
    
    payload["Token"] = generate_tbank_token(payload, PASSWORD)
    
    print("\nSending GetState request:")
    print(payload)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.post(state_url, json=payload)
        print(f"GetState Status Code: {res.status_code}")
        print(f"GetState Response: {res.text}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_eacq())
