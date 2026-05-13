import asyncio
import os
import sys

sys.path.append(os.getcwd())

from app.services.iiko_service import IikoService

async def main():
    iiko = IikoService()
    phone = "79220079019"
    try:
        # 1. Получаем текущий статус
        info = await iiko.get_customer_info(phone)
        print(f"Current status for {phone}: shouldBeCheckedForRisk = {info.get('shouldBeCheckedForRisk')}")
        
        # 2. Пробуем обновить
        payload = {
            "phone": phone,
            "shouldBeCheckedForRisk": True
        }
        print(f"Updating with payload: {payload}")
        result = await iiko.create_or_update_customer(payload)
        print(f"Update result: {result}")
        
        # 3. Проверяем снова
        info_after = await iiko.get_customer_info(phone)
        print(f"Status after update: shouldBeCheckedForRisk = {info_after.get('shouldBeCheckedForRisk')}")
        
        # 4. Пробуем isHighRisk (на всякий случай)
        if info_after.get('shouldBeCheckedForRisk') != True:
            print("Trying with isHighRisk field...")
            payload_alt = {
                "phone": phone,
                "isHighRisk": True
            }
            await iiko.create_or_update_customer(payload_alt)
            info_alt = await iiko.get_customer_info(phone)
            print(f"Status after alt update: shouldBeCheckedForRisk = {info_alt.get('shouldBeCheckedForRisk')}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
