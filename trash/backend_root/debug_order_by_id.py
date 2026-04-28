import httpx
import json
import asyncio

login = '86dfd64bd15c42199b789edf6adcb289'
org_id = '2704eeae-dc5f-4c9f-9b81-375c454dd5bd'
order_id = 'b9e66275-5e8e-4d37-bbba-0505cf301a39' # Order 323/73286

async def debug():
    async with httpx.AsyncClient() as client:
        token_resp = await client.post('https://api-ru.iiko.services/api/1/access_token', json={'apiLogin': login})
        token = token_resp.json().get('token')
        
        print(f"Checking order {order_id}...")
        payload = {
            "organizationIds": [org_id],
            "orderIds": [order_id]
        }
        resp = await client.post('https://api-ru.iiko.services/api/1/deliveries/by_id', json=payload, headers={'Authorization': f'Bearer {token}'})
        
        if resp.status_code == 200:
            orders = resp.json().get('orders', [])
            if orders:
                order = orders[0]
                print(f"Order found!")
                print(f"Number: {order.get('externalNumber')}")
                print(f"Status: {order.get('status')}")
                print(f"Full info: {json.dumps(order, indent=2, ensure_ascii=False)}")
            else:
                print("Order not found in deliveries/by_id")
        else:
            print(f"Error {resp.status_code}: {resp.text}")

if __name__ == "__main__":
    asyncio.run(debug())
