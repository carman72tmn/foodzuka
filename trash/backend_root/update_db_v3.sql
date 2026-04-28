CREATE TABLE IF NOT EXISTS sync_statuses (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL,
    sync_type VARCHAR(255) NOT NULL,
    total_count INTEGER DEFAULT 0,
    processed_count INTEGER DEFAULT 0,
    added_count INTEGER DEFAULT 0,
    updated_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'running',
    last_error TEXT,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS ix_sync_statuses_task_id ON sync_statuses (task_id);
CREATE INDEX IF NOT EXISTS ix_sync_statuses_sync_type ON sync_statuses (sync_type);

ALTER TABLE customers ADD COLUMN IF NOT EXISTS card_number VARCHAR(50);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS gender VARCHAR(20);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_marketing_consented BOOLEAN DEFAULT TRUE;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_system_notifications_consented BOOLEAN DEFAULT TRUE;
