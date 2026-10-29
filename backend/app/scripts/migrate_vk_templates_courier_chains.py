import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.database import engine
from sqlalchemy import text

def run_migration():
    print("Running migration for courier chains in vk_templates...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Добавление колонок
            conn.execute(text("ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;"))
            conn.execute(text("ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS include_statuses TEXT DEFAULT NULL;"))
            conn.execute(text("ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS attach_sbp_qr BOOLEAN DEFAULT FALSE;"))
            conn.execute(text("ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS chain_config TEXT DEFAULT NULL;"))
            conn.execute(text("ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS description VARCHAR(500) DEFAULT NULL;"))
            
            print("Columns is_active, include_statuses, attach_sbp_qr, chain_config, description added or already exist.")
            
            # 2. Инициализация начальных значений для ключевых шаблонов курьера
            # Для смены статуса задаем дефолтные целевые статусы
            conn.execute(text("""
                UPDATE vk_templates 
                SET include_statuses = '["cooking", "ready_for_pickup", "delivering", "cancelled"]'
                WHERE event_type = 'order_status_update' AND (include_statuses IS NULL OR include_statuses = '');
            """))
            
            # Для нового заказа курьеру включаем QR СБП по умолчанию
            conn.execute(text("""
                UPDATE vk_templates 
                SET attach_sbp_qr = TRUE 
                WHERE event_type IN ('courier_assigned', 'order_new') AND attach_sbp_qr = FALSE;
            """))

            # 3. Инициализация chain_config для шаблонов курьера
            conn.execute(text("""
                UPDATE vk_templates 
                SET chain_config = '{"require_courier_assigned": true, "resend_on_courier_reassigned": true, "attach_sbp_qr": true, "only_unpaid": false}'
                WHERE event_type = 'order_new' AND (chain_config IS NULL OR chain_config = '');

                UPDATE vk_templates 
                SET chain_config = '{"require_courier_assigned": true, "resend_on_courier_reassigned": true, "attach_sbp_qr": true, "only_unpaid": false}'
                WHERE event_type = 'courier_assigned' AND (chain_config IS NULL OR chain_config = '');

                UPDATE vk_templates 
                SET chain_config = '{"require_courier_assigned": true, "require_cooking_time_set": true, "require_cooking_time_changed": true}'
                WHERE event_type = 'change_cooking_time' AND (chain_config IS NULL OR chain_config = '');

                UPDATE vk_templates 
                SET chain_config = '{"require_courier_assigned": true, "check_status_in": ["cooking", "ready_for_pickup", "delivering", "cancelled"]}'
                WHERE event_type = 'order_status_update' AND (chain_config IS NULL OR chain_config = '');

                UPDATE vk_templates 
                SET chain_config = '{"require_courier_assigned": true, "require_amount_changed": true}'
                WHERE event_type = 'order_amount_changed' AND (chain_config IS NULL OR chain_config = '');

                UPDATE vk_templates 
                SET chain_config = '{"require_courier_assigned": true, "require_address_changed": true}'
                WHERE event_type = 'order_address_changed' AND (chain_config IS NULL OR chain_config = '');

                UPDATE vk_templates 
                SET chain_config = '{"require_courier_assigned": true, "require_time_changed": true}'
                WHERE event_type = 'order_time_changed' AND (chain_config IS NULL OR chain_config = '');
            """))
            
            trans.commit()
            print("Migration completed successfully!")
        except Exception as e:
            trans.rollback()
            print(f"Error executing migration: {e}")
            raise e

if __name__ == "__main__":
    run_migration()
