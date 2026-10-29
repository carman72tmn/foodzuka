import asyncio
import qrcode
import io
import base64
import sys

async def test():
    try:
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        
        # Public Telegram official desktop API ID/HASH or standard Android credentials
        # Android: API_ID = 6, API_HASH = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
        # Desktop: API_ID = 2040, API_HASH = "b18441a17fa627d41a484f3196e39eab"
        api_id = 6
        api_hash = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
        print(f"Connecting with api_id={api_id}...")
        client = TelegramClient(StringSession(), api_id, api_hash)
        await client.connect()
        print("Connected! Calling qr_login()...")
        qr_login = await client.qr_login()
        print("QR URL:", qr_login.url)
        img = qrcode.make(qr_login.url)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_base64 = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")
        print("Generated base64 len:", len(qr_base64))
        await client.disconnect()
        print("SUCCESS!")
    except Exception as e:
        print("ERROR:", type(e), e)

if __name__ == "__main__":
    asyncio.run(test())
