import logging
import sys
import os
import json

# Добавляем путь к backend в sys.path для импорта модулей
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import text
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('migrate_add_template_channels_and_bot_selection')

def migrate():
    logger.info('=== STARTING TEMPLATE CHANNELS AND BOT SELECTION MIGRATION ===')
    
    ddl_statements = [
        # 1. Добавление колонок каналов и бота в vk_templates
        'ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS vk_bot_id INTEGER DEFAULT NULL REFERENCES vk_bot_connections(id) ON DELETE SET NULL;',
        'ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS send_vk BOOLEAN DEFAULT TRUE;',
        'ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS send_tg BOOLEAN DEFAULT FALSE;',
        'ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS send_max BOOLEAN DEFAULT FALSE;',
        'ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS send_sms BOOLEAN DEFAULT FALSE;',
        'CREATE INDEX IF NOT EXISTS ix_vk_templates_vk_bot_id ON vk_templates (vk_bot_id);',
        
        # 2. Активация отключенных шаблонов курьера
        "UPDATE vk_templates SET is_active = TRUE WHERE event_type IN ('courier_assigned', 'order_cancelled');",
        
        # 3. Установка дефолтного бота (бот 'Курьеры' ID=2 если существует, иначе ID=1) для курьерских шаблонов
        """
        UPDATE vk_templates 
        SET vk_bot_id = COALESCE(
            (SELECT id FROM vk_bot_connections WHERE vk_group_id = 234266390 OR name ILIKE '%курьер%' LIMIT 1),
            (SELECT id FROM vk_bot_connections WHERE is_main = TRUE LIMIT 1)
        )
        WHERE event_type IN (
            'order_new', 'courier_assigned', 'change_cooking_time', 
            'order_status_update', 'order_amount_changed', 'order_address_changed', 
            'order_time_changed', 'order_cancelled'
        ) AND vk_bot_id IS NULL;
        """
    ]
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            for stmt in ddl_statements:
                logger.info(f'Executing: {stmt.strip()[:80]}...')
                conn.execute(text(stmt))
            
            # 4. Обновление chain_config для order_new с bind параметром
            cfg_order_new = json.dumps({
                "require_courier_assigned": True,
                "resend_on_courier_reassigned": True,
                "require_cooking_time_set": False,
                "require_cooking_time_changed": False,
                "require_amount_changed": False,
                "require_address_changed": False,
                "require_time_changed": False,
                "only_unpaid": False,
                "attach_sbp_qr": True,
                "check_status_in": []
            })
            conn.execute(
                text("UPDATE vk_templates SET chain_config = :cfg WHERE event_type = 'order_new'"),
                {"cfg": cfg_order_new}
            )
            
            # 5. Генерация подписок для всех курьеров на события цепочки
            courier_events = [
                'order_new', 'courier_assigned', 'change_cooking_time', 
                'order_status_update', 'order_amount_changed', 'order_address_changed', 
                'order_time_changed', 'order_cancelled'
            ]
            
            couriers = conn.execute(text("SELECT id, name, use_vk, use_tg, use_max, use_sms FROM vk_bot_accounts WHERE is_courier = TRUE")).fetchall()
            for c in couriers:
                c_id, c_name, use_vk, use_tg, use_max, use_sms = c[0], c[1], c[2], c[3], c[4], c[5]
                for ev in courier_events:
                    exists = conn.execute(
                        text("SELECT id FROM vk_bot_subscriptions WHERE account_id = :acc_id AND event_type = :ev"), 
                        {"acc_id": c_id, "ev": ev}
                    ).fetchone()
                    if not exists:
                        logger.info(f"Adding missing subscription '{ev}' for courier {c_name} (ID: {c_id})")
                        conn.execute(text("""
                            INSERT INTO vk_bot_subscriptions 
                            (account_id, event_type, delivery_mode, interval_minutes, active_start_hour, active_end_hour, send_vk, send_tg, send_max, send_sms)
                            VALUES 
                            (:acc_id, :ev, 'REALTIME', 0, 0, 23, :send_vk, :send_tg, :send_max, :send_sms)
                        """), {
                            "acc_id": c_id,
                            "ev": ev,
                            "send_vk": bool(use_vk),
                            "send_tg": bool(use_tg),
                            "send_max": bool(use_max),
                            "send_sms": bool(use_sms)
                        })
            
            trans.commit()
            logger.info('=== MIGRATION COMPLETED SUCCESSFULLY ===')
        except Exception as e:
            trans.rollback()
            logger.error(f'Migration failed: {e}')
            raise e

if __name__ == '__main__':
    migrate()
