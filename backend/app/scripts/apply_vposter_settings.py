import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.vk_bot_connection import VkBotConnection
from app.models.vk_first_comment_settings import VkFirstCommentSettings
from app.core.datetime_utils import utc_now

# Варианты комментариев
comments = [
    "🍕🍱🍣🍥🥘🍜🍤\nСамые вкусные роллы и нежная пицца, а так же Лапша Вок, Сочный Том-Ям множество вкусностей на\nhttps://довезука.рф\nТюмень\n#Довезука #Роллы #Пицца #ДоставкаТюмень #ТомЯм #ДоставкаПиццы #ВкусныеРоллы\n🍕🍱🍣🍥🥘🍜🍤",
    "🍕🍱🍣🍥🥘🍜🍤\nЗаказать вкусные роллы и пиццу по самым выгодным ценам и с огромными скидками и подарками, всегда на \nhttps://довезука.рф\nТюмень\n#Довезука #Роллы #Пицца #ДоставкаТюмень #ТомЯм #ДоставкаПиццы #ВкусныеРоллы\n🍕🍱🍣🍥🥘🍜🍤",
    "🍕🍱🍣🍥🥘🍜🍤\nОчень вкусная и быстрая доставка в Тюмени, для Вас Роллы , Пицца, Вок, Том-Ям, Закуски и много всего на:\nhttps://довезука.рф\nТюмень\n#Довезука #Роллы #Пицца #ДоставкаТюмень #ТомЯм #ДоставкаПиццы #ВкусныеРоллы\n🍕🍱🍣🍥🥘🍜🍤"
]

def apply():
    with Session(engine) as session:
        # Ищем основное подключение или любое активное
        connection = session.exec(
            select(VkBotConnection).where(VkBotConnection.is_main == True)
        ).first()
        
        if not connection:
            connection = session.exec(
                select(VkBotConnection).where(VkBotConnection.is_active == True)
            ).first()
            
        if not connection:
            print("No active VK bot connection found to apply settings to.")
            return

        print(f"Applying settings to connection: {connection.name} (ID: {connection.id}, Group: {connection.vk_group_id})")

        # Ищем существующие настройки первокоммента
        settings = session.exec(
            select(VkFirstCommentSettings).where(VkFirstCommentSettings.vk_bot_connection_id == connection.id)
        ).first()

        if settings:
            settings.is_active = True
            settings.comments = comments
            settings.updated_at = utc_now()
            print("Updated existing settings.")
        else:
            settings = VkFirstCommentSettings(
                vk_bot_connection_id=connection.id,
                is_active=True,
                comments=comments
            )
            session.add(settings)
            print("Created new settings.")
            
        session.commit()
        print("Settings successfully saved and activated!")

if __name__ == "__main__":
    apply()
