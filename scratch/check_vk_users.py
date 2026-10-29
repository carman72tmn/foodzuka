# -*- coding: utf-8 -*-
from app.core.database import engine
from sqlmodel import Session, select
from app.models.vk_user import VkUser

def check_users():
    with Session(engine) as session:
        users = session.exec(select(VkUser).where(VkUser.is_linked == True)).all()
        print(f"Найдено связанных пользователей: {len(users)}")
        for u in users:
            print(f"ID VK: {u.vk_id}, Телефон: {u.phone}, Имя: {u.first_name} {u.last_name}")
            print(f"  Подписан: {u.is_subscribed}, Уведомления: {u.notifications_enabled}, Блокирован: {u.is_blocked}")
            print(f"  Аватар: {u.photo_50}, Короткое имя: {u.screen_name}")

if __name__ == "__main__":
    check_users()
