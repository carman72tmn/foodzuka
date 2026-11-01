import asyncio
from sqlmodel import Session, select
from app.core.database import engine
from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.models.vk_user import VkUser
from app.services.mailing_cascade_service import mailing_cascade_service

async def test():
    with Session(engine) as session:
        # Ищем пользователя VK, у которого привязан телефон и разрешены уведомления
        vk_user = session.exec(select(VkUser).where(
            VkUser.is_linked == True,
            VkUser.is_subscribed == True,
            VkUser.notifications_enabled == True,
            VkUser.is_blocked == False
        ).limit(1)).first()
        
        if not vk_user:
            print("No linked and active VK user found in DB!")
            return
            
        print(f"Testing with VK User: ID={vk_user.vk_id}, Phone={vk_user.phone}")
        
        # Ищем Customer по телефону
        customer = session.exec(select(Customer).where(Customer.phone == vk_user.phone)).first()
        if not customer:
            print(f"Customer not found for phone {vk_user.phone}")
            return
            
        # Убедимся, что vk_user_id записан у клиента
        if customer.vk_user_id != vk_user.vk_id:
            customer.vk_user_id = vk_user.vk_id
            session.add(customer)
            session.commit()
            
        # Ищем заказ клиента
        order = session.exec(select(Order).where(Order.customer_id == customer.id).limit(1)).first()
        if not order:
            # Создаем фейковый заказ для теста
            order = Order(
                customer_id=customer.id,
                customer_phone=customer.phone,
                customer_name=customer.name or "Тестовый Гость",
                status=OrderStatus.ready_for_pickup, # Для триггера order_ready_for_pickup
                order_type="Самовывоз",
                total_amount=150.0,
                total_with_discount=150.0,
                branch_id=1
            )
            session.add(order)
            session.commit()
            session.refresh(order)
            print(f"Created fake order #{order.id} for testing")
        else:
            # Обновим статус заказа для теста
            order.status = OrderStatus.ready_for_pickup
            order.order_type = "Самовывоз"
            session.add(order)
            session.commit()
            session.refresh(order)
            print(f"Using existing order #{order.id} (Status={order.status}, Type={order.order_type})")
            
        print(f"Triggering cascade for order ready (pickup)...")
        # Вызываем trigger_cascade
        # Симулируем поведение при изменении статуса: передаем объект order и событие
        await mailing_cascade_service.trigger_cascade(order, "order_status_update")
        
        # Ждем 2 секунды, чтобы Celery или асинхронные вызовы выполнились (если delay=0m, они выполняются прямо в потоке)
        await asyncio.sleep(2)
        
        # Проверяем логи сообщений
        from app.models.message_log import CustomerMessageLog
        log = session.exec(select(CustomerMessageLog).where(
            CustomerMessageLog.customer_id == customer.id,
            CustomerMessageLog.order_id == order.id
        ).order_by(CustomerMessageLog.id.desc())).first()
        
        if log:
            print(f"Success! Message log created:")
            print(f"- ID: {log.id}")
            print(f"- Channel: {log.channel}")
            print(f"- Address: {log.recipient_address}")
            print(f"- Status: {log.status}")
            print(f"- Error: {log.error_text}")
            print(f"- Text: {log.text}")
        else:
            print("Fail: No message log was created for the cascade step!")

if __name__ == "__main__":
    asyncio.run(test())
