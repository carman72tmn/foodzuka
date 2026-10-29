import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.database import engine
from sqlalchemy import text

def run_migration():
    print("Running migration for courier notification settings in admin_notification_settings...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            columns = [
                # 1. Назначен заказ на доставку
                ("courier_order_assigned_sound_enabled", "BOOLEAN DEFAULT TRUE"),
                ("courier_order_assigned_sound_file", "VARCHAR(255) DEFAULT 'chime.mp3'"),
                ("courier_order_assigned_push_enabled", "BOOLEAN DEFAULT TRUE"),

                # 2. Установление времени приготовления заказа
                ("courier_cooking_time_set_sound_enabled", "BOOLEAN DEFAULT TRUE"),
                ("courier_cooking_time_set_sound_file", "VARCHAR(255) DEFAULT 'bell.mp3'"),
                ("courier_cooking_time_set_push_enabled", "BOOLEAN DEFAULT TRUE"),

                # 3. Изменение времени приготовления заказа
                ("courier_cooking_time_changed_sound_enabled", "BOOLEAN DEFAULT TRUE"),
                ("courier_cooking_time_changed_sound_file", "VARCHAR(255) DEFAULT 'click.mp3'"),
                ("courier_cooking_time_changed_push_enabled", "BOOLEAN DEFAULT TRUE"),

                # 4. Изменение статуса заказа (только готов или отменен)
                ("courier_status_changed_sound_enabled", "BOOLEAN DEFAULT TRUE"),
                ("courier_status_changed_sound_file", "VARCHAR(255) DEFAULT 'bell.mp3'"),
                ("courier_status_changed_push_enabled", "BOOLEAN DEFAULT TRUE"),

                # 5. Изменение суммы заказа
                ("courier_amount_changed_sound_enabled", "BOOLEAN DEFAULT TRUE"),
                ("courier_amount_changed_sound_file", "VARCHAR(255) DEFAULT 'cash.mp3'"),
                ("courier_amount_changed_push_enabled", "BOOLEAN DEFAULT TRUE"),

                # 6. Изменение адреса доставки
                ("courier_address_changed_sound_enabled", "BOOLEAN DEFAULT TRUE"),
                ("courier_address_changed_sound_file", "VARCHAR(255) DEFAULT 'doorbell.mp3'"),
                ("courier_address_changed_push_enabled", "BOOLEAN DEFAULT TRUE"),

                # 7. Изменение способа доставки заказа (изменили на самовывоз)
                ("courier_changed_to_pickup_sound_enabled", "BOOLEAN DEFAULT TRUE"),
                ("courier_changed_to_pickup_sound_file", "VARCHAR(255) DEFAULT 'branch.mp3'"),
                ("courier_changed_to_pickup_push_enabled", "BOOLEAN DEFAULT TRUE"),

                # 8. Заказ убран из доставки
                ("courier_removed_from_delivery_sound_enabled", "BOOLEAN DEFAULT TRUE"),
                ("courier_removed_from_delivery_sound_file", "VARCHAR(255) DEFAULT 'error.mp3'"),
                ("courier_removed_from_delivery_push_enabled", "BOOLEAN DEFAULT TRUE"),

                # 9. Заказ убран из списка доставок выбранного курьера
                ("courier_unassigned_sound_enabled", "BOOLEAN DEFAULT TRUE"),
                ("courier_unassigned_sound_file", "VARCHAR(255) DEFAULT 'sonar.mp3'"),
                ("courier_unassigned_push_enabled", "BOOLEAN DEFAULT TRUE"),

                # 10. Изменение времени доставки заказа
                ("courier_delivery_time_changed_sound_enabled", "BOOLEAN DEFAULT TRUE"),
                ("courier_delivery_time_changed_sound_file", "VARCHAR(255) DEFAULT 'water.mp3'"),
                ("courier_delivery_time_changed_push_enabled", "BOOLEAN DEFAULT TRUE"),
            ]

            for col_name, col_type in columns:
                conn.execute(text(f"ALTER TABLE admin_notification_settings ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))

            # Обновление null-значений для существующих строк
            for col_name, col_type in columns:
                default_val = col_type.split("DEFAULT ")[-1]
                conn.execute(text(f"UPDATE admin_notification_settings SET {col_name} = {default_val} WHERE {col_name} IS NULL;"))

            trans.commit()
            print("Migration for courier notification settings completed successfully.")
        except Exception as e:
            trans.rollback()
            print(f"Error during migration: {e}")
            raise e

if __name__ == "__main__":
    run_migration()
