-- Создание таблиц для Конструктора OLAP и архива выручки и доставок (7+ лет)

CREATE TABLE IF NOT EXISTS olap_presets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(500) DEFAULT '',
    report_type VARCHAR(50) NOT NULL DEFAULT 'SALES',
    group_by_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
    aggregate_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
    filters JSONB NOT NULL DEFAULT '{}'::jsonb,
    default_period VARCHAR(30) NOT NULL DEFAULT 'month',
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_olap_presets_name ON olap_presets(name);
CREATE INDEX IF NOT EXISTS idx_olap_presets_report_type ON olap_presets(report_type);

-- Архив продаж по дням за 7+ лет
CREATE TABLE IF NOT EXISTS olap_daily_sales (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    department VARCHAR(255) NOT NULL DEFAULT '',
    revenue DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    orders_count INTEGER NOT NULL DEFAULT 0,
    average_check DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    discount_sum DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    cost_price DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    markup DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    cash_sum DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    card_sum DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    online_sum DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    bonus_sum DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_olap_daily_sales_date_dept UNIQUE (date, department)
);

CREATE INDEX IF NOT EXISTS idx_olap_daily_sales_date ON olap_daily_sales(date);
CREATE INDEX IF NOT EXISTS idx_olap_daily_sales_dept ON olap_daily_sales(department);

-- Архив доставок курьеров, зон и подзон по дням за 7+ лет
CREATE TABLE IF NOT EXISTS olap_courier_deliveries_daily (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    courier_name VARCHAR(255) NOT NULL DEFAULT '',
    courier_id VARCHAR(100),
    zone VARCHAR(255) NOT NULL DEFAULT 'Без зоны',
    region VARCHAR(255) NOT NULL DEFAULT 'Без района',
    deliveries_count INTEGER NOT NULL DEFAULT 0,
    orders_sum DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    avg_duration_min DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    avg_delay_min DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_olap_courier_deliv_daily UNIQUE (date, courier_name, zone, region)
);

CREATE INDEX IF NOT EXISTS idx_olap_courier_deliv_date ON olap_courier_deliveries_daily(date);
CREATE INDEX IF NOT EXISTS idx_olap_courier_deliv_courier ON olap_courier_deliveries_daily(courier_name);
CREATE INDEX IF NOT EXISTS idx_olap_courier_deliv_zone ON olap_courier_deliveries_daily(zone);
CREATE INDEX IF NOT EXISTS idx_olap_courier_deliv_region ON olap_courier_deliveries_daily(region);

-- Кэш произвольных запросов конструктора
CREATE TABLE IF NOT EXISTS olap_query_cache (
    cache_key VARCHAR(64) PRIMARY KEY,
    report_type VARCHAR(50) NOT NULL,
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,
    rows_data JSONB NOT NULL DEFAULT '[]'::jsonb,
    summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    row_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_olap_query_cache_dates ON olap_query_cache(date_from, date_to);
CREATE INDEX IF NOT EXISTS idx_olap_query_cache_expires ON olap_query_cache(expires_at);

-- Состояние фоновой синхронизации истории 7 лет
CREATE TABLE IF NOT EXISTS olap_sync_state (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(100) NOT NULL DEFAULT 'olap_7_years_sync',
    status VARCHAR(50) NOT NULL DEFAULT 'idle',
    current_year INTEGER NOT NULL DEFAULT 2019,
    current_month INTEGER NOT NULL DEFAULT 1,
    start_year INTEGER NOT NULL DEFAULT 2019,
    end_year INTEGER NOT NULL DEFAULT 2026,
    total_months INTEGER NOT NULL DEFAULT 96,
    completed_months INTEGER NOT NULL DEFAULT 0,
    sales_records_saved INTEGER NOT NULL DEFAULT 0,
    courier_records_saved INTEGER NOT NULL DEFAULT 0,
    current_status_message VARCHAR(500) DEFAULT '',
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
