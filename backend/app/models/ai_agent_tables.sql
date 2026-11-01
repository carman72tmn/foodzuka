-- Миграция для модуля «Агенты ИИ» (AI Agents)
-- Дата создания: 2026-10-26

-- 1. Таблица ai_proxies (Пул прокси-серверов HTTPS и SOCKS5)
CREATE TABLE IF NOT EXISTS ai_proxies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    protocol VARCHAR(20) NOT NULL DEFAULT 'http',
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    username VARCHAR(255),
    password VARCHAR(255),
    priority INTEGER DEFAULT 10,
    is_enabled BOOLEAN DEFAULT TRUE,
    is_active_current BOOLEAN DEFAULT FALSE,
    status VARCHAR(30) DEFAULT 'untested',
    latency_ms INTEGER,
    detected_ip VARCHAR(64),
    detected_country VARCHAR(64),
    last_checked_at TIMESTAMP,
    last_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Таблица ai_provider_connections (Подключения к провайдерам ИИ)
CREATE TABLE IF NOT EXISTS ai_provider_connections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    provider_group VARCHAR(20) NOT NULL,
    provider_type VARCHAR(50) NOT NULL,
    api_key TEXT,
    client_id VARCHAR(255),
    auth_scope VARCHAR(100),
    base_url VARCHAR(500),
    default_model VARCHAR(120) NOT NULL,
    use_proxy BOOLEAN DEFAULT TRUE,
    pinned_proxy_id INTEGER REFERENCES ai_proxies(id) ON DELETE SET NULL,
    verify_ssl BOOLEAN DEFAULT TRUE,
    rotation_weight INTEGER DEFAULT 1,
    rpm_limit INTEGER DEFAULT 60,
    is_enabled BOOLEAN DEFAULT TRUE,
    status VARCHAR(30) DEFAULT 'untested',
    last_tested_at TIMESTAMP,
    last_error TEXT,
    total_requests INTEGER DEFAULT 0,
    total_tokens BIGINT DEFAULT 0,
    extra_config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Таблица ai_site_agents (Конфигурация функциональных ИИ-агентов сайта)
CREATE TABLE IF NOT EXISTS ai_site_agents (
    id SERIAL PRIMARY KEY,
    agent_code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT FALSE,
    primary_connection_id INTEGER REFERENCES ai_provider_connections(id) ON DELETE SET NULL,
    fallback_connection_id INTEGER REFERENCES ai_provider_connections(id) ON DELETE SET NULL,
    use_gemini_pool BOOLEAN DEFAULT FALSE,
    model_override VARCHAR(120),
    temperature NUMERIC(3,2) DEFAULT 0.70,
    max_tokens INTEGER DEFAULT 2048,
    system_prompt TEXT,
    permissions_config JSONB DEFAULT '{}'::jsonb,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Добавление прав RBAC в таблицу permissions
INSERT INTO permissions (name, code, description)
VALUES 
    ('Просмотр настроек Агентов ИИ', 'settings_ai_agents_view', 'Доступ к разделу Система -> Агенты ИИ, просмотр статусов и конфигураций'),
    ('Управление Агентами ИИ', 'settings_ai_agents_edit', 'Управление прокси-серверами, API-ключами провайдеров и промптами агентов')
ON CONFLICT (code) DO NOTHING;

-- 5. Привязка прав к роли Супер-Администратора (is_system = true или id = 1)
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.is_system = TRUE 
  AND p.code IN ('settings_ai_agents_view', 'settings_ai_agents_edit')
ON CONFLICT DO NOTHING;

-- 6. Предзаполнение базовых функциональных агентов сайта
INSERT INTO ai_site_agents (agent_code, title, description, is_active, system_prompt, permissions_config)
VALUES 
    (
        'stats_analyst', 
        'ИИ-Аналитик статистики и финансов', 
        'Анализ выручки, продаж, среднего чека, динамики заказов и себестоимости по данным OLAP и iiko.',
        FALSE,
        'Ты — ведущий финансовый аналитик и эксперт ресторанного бизнеса FoodTech службы доставки «Везу Ролл». Твоя задача — анализировать выручку, средний чек, структуру заказов, динамику продаж и работу курьеров, формулировать практические выводы и давать рекомендации по оптимизации бизнеса.',
        '{"read_orders_stats": true, "read_olap_revenue": true, "read_courier_stats": true, "read_bonus_stats": true}'::jsonb
    ),
    (
        'feedback_nps', 
        'ИИ-Менеджер отзывов, NPS и Мультичата', 
        'Анализ отзывов гостей, классификация тональности, генерация эмпатичных ответов и подсказки операторам чата.',
        FALSE,
        'Ты — заботливый и доброжелательный менеджер контроля качества доставки еды «Везу Ролл». Ты работаешь с отзывами клиентов (NPS и ВК) и чатами. Твои ответы всегда вежливые, эмпатичные и ориентированы на решение проблемы гостя. Если отзыв негативный, ты проявляешь сочувствие и предлагаешь разобраться в деталях.',
        '{"read_nps_reviews": true, "read_customer_history": true, "draft_replies": true, "multichat_copilot": true}'::jsonb
    ),
    (
        'site_manager', 
        'ИИ-Ассистент управления сайтом и маркетингом', 
        'Генерация вкусных продающих описаний блюд, текстов акций и постов для автопостинга в соцсетях.',
        FALSE,
        'Ты — талантливый ресторанный маркетолог и шеф-копирайтер службы доставки японской кухни «Везу Ролл». Ты создаешь аппетитные, точные и продающие описания блюд (роллы, сеты, пицца), а также яркие промо-тексты для рассылок и соцсетей.',
        '{"read_products": true, "read_categories": true, "suggest_promos": true, "suggest_vk_posts": true}'::jsonb
    )
ON CONFLICT (agent_code) DO NOTHING;
