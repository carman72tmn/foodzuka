-- Исправление кодировки и вставка permissions для Агентов ИИ
SET client_encoding = 'UTF8';

INSERT INTO permissions (name, code, description, category)
VALUES 
    ('Просмотр настроек Агентов ИИ', 'settings_ai_agents_view', 'Доступ к разделу Система -> Агенты ИИ, просмотр статусов и конфигураций', 'Система'),
    ('Управление Агентами ИИ', 'settings_ai_agents_edit', 'Управление прокси-серверами, API-ключами провайдеров и промптами агентов', 'Система')
ON CONFLICT (code) DO UPDATE 
SET name = EXCLUDED.name, description = EXCLUDED.description, category = EXCLUDED.category;

-- Привязка прав к роли Супер-Администратора (is_system = true или name = 'Администратор')
INSERT INTO role_permission_links (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE (r.is_system = TRUE OR r.name = 'Администратор')
  AND p.code IN ('settings_ai_agents_view', 'settings_ai_agents_edit')
ON CONFLICT DO NOTHING;

-- Обновление русских названий в ai_site_agents в чистом UTF-8
UPDATE ai_site_agents 
SET title = 'ИИ-Аналитик статистики и финансов',
    description = 'Анализ выручки, продаж, среднего чека, динамики заказов и себестоимости по данным OLAP и iiko.',
    system_prompt = 'Ты — ведущий финансовый аналитик и эксперт ресторанного бизнеса FoodTech службы доставки «Везу Ролл». Твоя задача — анализировать выручку, средний чек, структуру заказов, динамику продаж и работу курьеров, формулировать практические выводы и давать рекомендации по оптимизации бизнеса.'
WHERE agent_code = 'stats_analyst';

UPDATE ai_site_agents 
SET title = 'ИИ-Менеджер отзывов, NPS и Мультичата',
    description = 'Анализ отзывов гостей, классификация тональности, генерация эмпатичных ответов и подсказки операторам чата.',
    system_prompt = 'Ты — заботливый и доброжелательный менеджер контроля качества доставки еды «Везу Ролл». Ты работаешь с отзывами клиентов (NPS и ВК) и чатами. Твои ответы всегда вежливые, эмпатичные и ориентированы на решение проблемы гостя. Если отзыв негативный, ты проявляешь сочувствие и предлагаешь разобраться в деталях.'
WHERE agent_code = 'feedback_nps';

UPDATE ai_site_agents 
SET title = 'ИИ-Ассистент управления сайтом и маркетингом',
    description = 'Генерация вкусных продающих описаний блюд, текстов акций и постов для автопостинга в соцсетях.',
    system_prompt = 'Ты — талантливый ресторанный маркетолог и шеф-копирайтер службы доставки японской кухни «Везу Ролл». Ты создаешь аппетитные, точные и продающие описания блюд (роллы, сеты, пицца), а также яркие промо-тексты для рассылок и соцсетей.'
WHERE agent_code = 'site_manager';
