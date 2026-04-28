ALTER TABLE olap_revenue_records ADD COLUMN IF NOT EXISTS terminal_name VARCHAR(255);
ALTER TABLE olap_revenue_records ADD COLUMN IF NOT EXISTS cash_sum FLOAT DEFAULT 0.0;
ALTER TABLE olap_revenue_records ADD COLUMN IF NOT EXISTS card_sum FLOAT DEFAULT 0.0;
ALTER TABLE olap_revenue_records ADD COLUMN IF NOT EXISTS online_sum FLOAT DEFAULT 0.0;
ALTER TABLE olap_revenue_records ADD COLUMN IF NOT EXISTS bonus_sum FLOAT DEFAULT 0.0;
ALTER TABLE olap_revenue_records ADD COLUMN IF NOT EXISTS coupon_number VARCHAR(255);
ALTER TABLE olap_revenue_records ADD COLUMN IF NOT EXISTS coupon_series VARCHAR(255);
ALTER TABLE olap_revenue_records ADD COLUMN IF NOT EXISTS discount_name VARCHAR(255);
