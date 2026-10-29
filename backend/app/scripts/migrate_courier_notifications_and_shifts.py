import logging
from sqlalchemy import text
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    with engine.begin() as conn:
        logger.info("Starting migration for courier notifications and shift fields...")

        # 1. Add fields to orders
        order_columns = [
            ("courier_notification_status", "VARCHAR(50)"),
            ("courier_accepted_at", "TIMESTAMP WITH TIME ZONE"),
            ("courier_accepted_source", "VARCHAR(50)"),
            ("courier_read_at", "TIMESTAMP WITH TIME ZONE"),
            ("courier_notification_channel", "VARCHAR(50)"),
            ("courier_last_message_text", "TEXT"),
        ]
        for col_name, col_type in order_columns:
            try:
                conn.execute(text(f"ALTER TABLE orders ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                logger.info(f"Column orders.{col_name} checked/added.")
            except Exception as e:
                logger.warning(f"Error adding orders.{col_name}: {e}")

        # 2. Add is_courier to vk_bot_accounts
        try:
            conn.execute(text("ALTER TABLE vk_bot_accounts ADD COLUMN IF NOT EXISTS is_courier BOOLEAN DEFAULT FALSE;"))
            logger.info("Column vk_bot_accounts.is_courier checked/added.")
        except Exception as e:
            logger.warning(f"Error adding vk_bot_accounts.is_courier: {e}")

        # 3. Create courier_order_notifications table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS courier_order_notifications (
            id SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            account_id INTEGER REFERENCES vk_bot_accounts(id) ON DELETE SET NULL,
            courier_name VARCHAR(255),
            channel VARCHAR(50) NOT NULL,
            external_message_id VARCHAR(100),
            external_chat_id VARCHAR(100),
            status VARCHAR(50) DEFAULT 'unread',
            reaction VARCHAR(100),
            reply_text TEXT,
            error_text TEXT,
            sent_at TIMESTAMP WITH TIME ZONE,
            read_at TIMESTAMP WITH TIME ZONE,
            accepted_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS ix_courier_notifications_order_id ON courier_order_notifications(order_id);
        CREATE INDEX IF NOT EXISTS ix_courier_notifications_account_id ON courier_order_notifications(account_id);
        CREATE INDEX IF NOT EXISTS ix_courier_notifications_ext_msg ON courier_order_notifications(channel, external_message_id);
        CREATE INDEX IF NOT EXISTS ix_courier_notifications_chat_id ON courier_order_notifications(channel, external_chat_id);
        """
        try:
            conn.execute(text(create_table_sql))
            logger.info("Table courier_order_notifications created/checked.")
        except Exception as e:
            logger.warning(f"Error creating courier_order_notifications: {e}")

        # 4. Automatically set is_courier = True for accounts where linked employee is courier
        auto_update_sql = """
        UPDATE vk_bot_accounts 
        SET is_courier = TRUE 
        WHERE employee_id IN (
            SELECT id FROM employees WHERE is_courier = TRUE OR LOWER(role) LIKE '%курьер%' OR LOWER(role) LIKE '%driver%'
        ) OR LOWER(name) LIKE '%курьер%';
        """
        try:
            res = conn.execute(text(auto_update_sql))
            logger.info(f"Updated {res.rowcount} vk_bot_accounts with is_courier = TRUE based on employees.")
        except Exception as e:
            logger.warning(f"Error auto-updating vk_bot_accounts.is_courier: {e}")

        logger.info("Migration completed successfully.")

if __name__ == '__main__':
    migrate()
