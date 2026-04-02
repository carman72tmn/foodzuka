import re
from typing import Dict, Any
from sqlmodel import Session, select
from app.models.order import Order
from app.models.vk_user import VkUser
from app.models.vk_activity import VkActivity
import httpx
from app.core.config import settings


async def process_vk_event(event_data: Dict[str, Any], db: Session, bot_token: str | None):
    event_type = event_data.get("type")
    obj = event_data.get("object", {})

    if event_type == "message_reply" or event_type == "message_new":
        await handle_message(event_type, obj, db, bot_token)
    elif event_type in ["like_add", "wall_reply_new"]:
        await handle_activity(event_type, obj, db, bot_token)


async def handle_message(event_type: str, obj: Dict[str, Any], db: Session, bot_token: str | None):
    # Depending on API version, message might be directly in obj or obj.message
    message = obj if 'text' in obj else obj.get('message', {})
    text = message.get("text", "")
    vk_id = message.get("peer_id") or obj.get("user_id") or message.get("from_id")
    
    if not vk_id or not text:
        return

    # Extract order number from text, e.g. 'Заказ №12345'
    match = re.search(r'(?:заказ|заказа).*?(?:№|#)?\s*(\d+)'.encode('utf-8').decode('utf-8'), text, re.IGNORECASE)
    if not match:
        return

    order_number = match.group(1)
    
    try:
        # Find order in DB
        result = db.execute(select(Order).where(Order.id == int(order_number)))
        order = result.scalars().first()
        
        if not order:
            return

        # Link profile
        result = db.execute(select(VkUser).where(VkUser.vk_id == vk_id))
        vk_user = result.scalars().first()
        
        if not vk_user:
            vk_user = VkUser(
                vk_id=vk_id,
                phone=order.customer_phone,
                iiko_customer_id=order.customer_id,
                first_name=order.customer_name,
                is_linked=True
            )
            db.add(vk_user)
            db.commit()
            
            # Optionally send a welcome message
            if order.customer_name and bot_token:
                await send_vk_message(
                    vk_id=vk_id, 
                    message=f"Здравствуйте, {order.customer_name}! Ваш профиль успешно привязан к системе лояльности. Мы будем присылать вам уведомления о статусах заказов.",
                    bot_token=bot_token
                )
    except Exception as e:
        print(f"Error handling order binding: {e}")

async def handle_activity(event_type: str, obj: Dict[str, Any], db: Session, bot_token: str | None):
    # Example logic for activity points
    vk_id = obj.get("liker_id") or obj.get("from_id")
    if not vk_id:
        return
        
    item_id = str(obj.get("item_id") or obj.get("post_id") or obj.get("id"))
    
    # Check if user is linked
    result = db.execute(select(VkUser).where(VkUser.vk_id == vk_id))
    vk_user = result.scalars().first()
    
    if not vk_user or not vk_user.is_linked:
        return
        
    # Check if action already recorded
    result = db.execute(
        select(VkActivity)
        .where(VkActivity.vk_id == vk_id)
        .where(VkActivity.action_type == event_type)
        .where(VkActivity.item_id == item_id)
    )
    existing_action = result.scalars().first()
    
    if existing_action:
        return
        
    # Award points
    points = 5 if event_type == "like_add" else 10
    
    activity = VkActivity(
        vk_id=vk_id,
        action_type=event_type,
        item_id=item_id,
        points=points,
        is_synced=False
    )
    db.add(activity)
    
    vk_user.vk_bonus_balance += points
    db.add(vk_user)
    
    db.commit()
    
    # Send notification
    if bot_token:
        await send_vk_message(
            vk_id=vk_id,
            message=f"Вам начислено {points} баллов за активность! Ваш локальный рейтинг: {vk_user.vk_bonus_balance} руб.",
            bot_token=bot_token
        )


async def send_vk_message(vk_id: int, message: str, bot_token: str | None = None):
    if not bot_token:
        print("VK_BOT_TOKEN is not configured")
        return False
        
    url = "https://api.vk.com/method/messages.send"
    import random
    
    params = {
        "user_id": vk_id,
        "message": message,
        "random_id": random.randint(1, 2147483647),
        "access_token": bot_token,
        "v": "5.131"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, data=params)
            data = response.json()
            if "error" in data:
                print(f"VK API Error: {data['error']}")
                return False
            return True
        except Exception as e:
            print(f"Failed to send VK message: {e}")
            return False
