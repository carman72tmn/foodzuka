# -*- coding: utf-8 -*-
"""
Миграция: Добавление глобальных переключателей браузерных уведомлений и полей доставки заказа
в таблицу admin_notification_settings, а также отключение общих уведомлений для курьеров по умолчанию.
"""
from sqlmodel import Session, text
from app.core.database import engine

def run_migration():
    with Session(engine) as session:
        print("Starting migration for notification settings...")
        
        # 1. Добавление колонок в admin_notification_settings
        alter_statements = [
            "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS disable_browser_notifications_couriers BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS disable_browser_notifications_all BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS order_delivered_sound_enabled BOOLEAN DEFAULT TRUE;",
            "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS order_delivered_sound_file VARCHAR(255) DEFAULT 'chime.mp3';",
            "ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS order_delivered_push_enabled BOOLEAN DEFAULT TRUE;"
        ]
        
        for sql in alter_statements:
            session.exec(text(sql))
        session.commit()
        print("Columns added successfully.")
        
        # 2. Отключение общих уведомлений для аккаунтов с ролью курьера (role_id = 7)
        courier_disable_sql = """
        UPDATE admin_notification_settings 
        SET new_order_sound_enabled = false,
            new_order_push_enabled = false,
            new_payment_sound_enabled = false,
            new_payment_push_enabled = false,
            chat_message_sound_enabled = false,
            chat_message_push_enabled = false,
            order_cancelled_sound_enabled = false,
            order_cancelled_push_enabled = false,
            delivery_unassigned_sound_enabled = false,
            delivery_unassigned_push_enabled = false,
            order_delivered_sound_enabled = false,
            order_delivered_push_enabled = false,
            order_changed_sound_enabled = false,
            order_changed_push_enabled = false
        WHERE user_id IN (SELECT id FROM users WHERE role_id = 7);
        """
        result = session.exec(text(courier_disable_sql))
        session.commit()
        print(f"Updated courier default settings. Rows affected: {result.rowcount}")

        # 3. Проверка значений
        rows = session.exec(text("SELECT id, user_id, disable_browser_notifications_couriers, disable_browser_notifications_all, order_delivered_sound_enabled, new_order_sound_enabled FROM admin_notification_settings ORDER BY id;")).all()
        for r in rows:
            print(f"Settings ID: {r[0]}, User ID: {r[1]}, Disable Couriers: {r[2]}, Disable All: {r[3]}, Order Delivered: {r[4]}, New Order: {r[5]}")

if __name__ == "__main__":
    run_migration()
