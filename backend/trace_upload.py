import asyncio
import httpx
from app.core.database import SessionLocal
from app.models.vk_bot_connection import VkBotConnection

async def trace_upload():
    db = SessionLocal()
    bot1 = db.get(VkBotConnection, 1)
    token = bot1.vk_bot_token
    peer_id = 6875740
    image_path = "/app/media/img/qr/order_2787_1788523846.png"

    async with httpx.AsyncClient() as client:
        # Step 1
        url = "https://api.vk.ru/method/photos.getMessagesUploadServer"
        params = {"access_token": token, "v": "5.131", "peer_id": peer_id}
        r1 = await client.get(url, params=params)
        print("Step 1 response:", r1.json())
        upload_url = r1.json()["response"]["upload_url"]

        # Step 2
        with open(image_path, "rb") as f:
            r2 = await client.post(upload_url, files={"photo": f})
        print("Step 2 upload response:", r2.text)
        up_data = r2.json()

        # Step 3
        save_url = "https://api.vk.ru/method/photos.saveMessagesPhoto"
        save_params = {
            "access_token": token,
            "v": "5.131",
            "photo": up_data.get("photo"),
            "server": up_data.get("server"),
            "hash": up_data.get("hash")
        }
        r3 = await client.post(save_url, data=save_params)
        print("Step 3 save response:", r3.json())

    db.close()

if __name__ == "__main__":
    asyncio.run(trace_upload())
