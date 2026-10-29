# ИСПРАВЛЕНИЕ ОШИБКИ СОХРАНЕНИЯ НАСТРОЕК МАРКЕТИНГОВЫХ БОТОВ
Дата: 24.10.2026 20:53 (UTC+5)

1. Причина ошибки:
При сохранении настроек для нового подключения (connection_id = 2) происходил INSERT в таблицу vk_shop_bots. В запросе присутствовало поле card_button_2_mode, отсутствовавшее в структуре таблицы PostgreSQL (psycopg2.errors.UndefinedColumn: column  card_button_2_mode does not exist).
Также в таблице vk_smart_broadcasts колонка title имела ограничение NOT NULL без дефолтного значения.

2. Принятые меры:
1) Добавлены недостающие колонки в таблицы БД на VPS:
   - vk_shop_bots: card_button_2_mode VARCHAR(50)
   - vk_retention_bots: newbie_message_template, sleeping_message_template, lost_vip_message_template (TEXT)
   - vk_smart_broadcasts: broadcast_text, broadcast_photo_url, segment_verification, segment_bonus_min, segment_days_last_order, segment_avg_check_min, exclude_last_touched_days
   - vk_referral_programs: antifraud_prevent_same_phone_address (BOOLEAN)
2) Снято ограничение NOT NULL с title и message_text в vk_smart_broadcasts.
3) В backend/app/api/vk_marketing_endpoints.py внедрена динамическая интроспекция колонок таблицы через information_schema.columns: теперь бэкенд фильтрует любые лишние ключи и автоматически сопоставляет синонимы, исключая ошибку UndefinedColumn в будущем.
4) В VkMarketingBotModal.vue улучшена обработка ошибок (вывод точного текста ошибки бэкенда в toast).
5) Фронтенд пересобран (npm run build), контейнеры перезапущены.
6) Проведено тестирование сохранения всех 6 ботов для подключений 1 и 2 — все запросы вернули 200 OK.
