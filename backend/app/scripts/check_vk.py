import asyncio
import json
import ssl
import websockets

async def test_oneme_gateway():
    ssl_context = ssl._create_unverified_context()
    uri = "wss://api.oneme.ru/websocket"
    
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri, ssl=ssl_context) as ws:
            print("Connected to OneMe gateway!")
            
            # Test sending opcode 112
            pkt = {
                "opcode": 112,
                "payload": {"type": 0},
                "seq": 1
            }
            await ws.send(json.dumps(pkt))
            print("Sent opcode 112...")
            
            resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
            print("Response to opcode 112:", resp)
            
    except Exception as e:
        print("OneMe WS test error:", e)

if __name__ == "__main__":
    asyncio.run(test_oneme_gateway())
