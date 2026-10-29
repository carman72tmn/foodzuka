# Лог сессии: Внедрение мультиканальности (ВКонтакте + MAX от личного номера) для 6 маркетинговых ботов
Дата: 2026-10-25 21:05
Задача: Реализация раздельной настройки и статистики для каналов ВК и MAX (от личного номера через Web Bridge) во всех 6 маркетинговых ботах.

## План:
1. SQL-миграция: добавление колонок max_enabled, vk_enabled, шаблонов max_* и полей channel, customer_phone в таблицы ботов и логов.
2. Бэкенд: обновление vk_marketing_bots_service.py, vk_marketing_endpoints.py, max_bridge_service.py.
3. Фронтенд: обновление VkMarketingBotModal.vue и vk-bots.vue.
4. Выгрузка на VPS, миграция БД, перезапуск backend и worker, пересборка фронтенда.
5. Тестирование и документация.


## Выполненные этапы и результаты:
1. **База данных (PostgreSQL на VPS)**:
   - Выполнена миграция для всех 6 конфигурационных таблиц ботов (`vk_shop_bots`, `vk_retention_bots`, `vk_review_nps_bots`, `vk_wheel_bots`, `vk_smart_broadcasts`, `vk_referral_programs`):
     - Добавлены `vk_enabled`, `max_enabled`, `max_send_mode` (по умолчанию `bridge_only`), `max_daily_limit` (100), `max_delay_seconds` (15), `test_admin_phones` (`["79220079019"]`).
     - Добавлены индивидуальные шаблоны текстов сообщений `max_*` для каждого бота на русском языке в UTF-8.
   - Во все таблицы логов и статистики (`vk_bot_message_logs`, `vk_retention_logs`, `vk_order_nps_reviews`, `vk_wheel_spins`, `vk_referral_links`) добавлены колонки `channel` (`'vk'` / `'max'`) и `customer_phone`, сняты ограничения `NOT NULL` на внешние ключи VK ID для поддержки пользователей без профиля ВК.
2. **Бэкенд (FastAPI, сервисы и шлюз MAX)**:
   - `backend/app/services/vk_marketing_bots_service.py`:
     - Реализован метод `send_marketing_max_personal` с отправкой строго от личного номера Web Bridge (PyMax) по номеру телефона клиента и логированием со статусом `SENT`/`FAILED`.
     - Реализован `handle_max_incoming_message`: автоматический перехват NPS-оценки 1–5 и команд каталога ("1", "меню", "2", "3", "4") в личных сообщениях MAX.
   - `backend/app/services/max_bridge_service.py`:
     - Подключен диспетчер входящих сообщений PyMax на маркетинговые хэндлеры.
   - `backend/app/api/vk_marketing_endpoints.py`:
     - В `get_marketing_bots_config` добавлен статус подключения личного номера MAX (`max_bridge_status`).
     - В `test_send_bot_message` реализована тестовая отправка в канал MAX от личного номера на тестовый телефон `79220079019`.
     - В `get_bot_analytics` реализовано разделение метрик и логов: `metrics_vk`, `metrics_max`, `logs_vk`, `logs_max`.
     - В `count_broadcast_audience` рассчитываются раздельные аудитории: `vk_audience_count` и `max_audience_count`.
3. **Фронтенд админ-панели (Vue 3, Vuetify)**:
   - Создан компонент `admin/resources/js/components/VkMarketingBotMaxSettings.vue` с полным набором полей для настройки канала MAX (тумблер, лимиты, антифлуд-задержки, подсказки и шаблоны текстов).
   - В `admin/resources/js/components/VkMarketingBotModal.vue`:
     - Добавлена вкладка "Канал MAX (Личный №)" для всех 6 ботов.
     - Добавлен фильтр каналов аналитики (`🌐 Все каналы` | `ВКонтакте (VK)` | `MAX (Личный №)`).
     - Добавлены две кнопки тестирования в футере: `Тест в ВК` и `Тест в MAX (с личного №)`.
     - В шапке модалки выведены тумблеры обоих каналов.
   - В `admin/resources/js/pages/marketing/vk-bots.vue`:
     - В карточках всех 6 ботов добавлены раздельные бейджи статуса каналов (`ВК ВКЛ/ВЫКЛ`, `MAX ВКЛ/ВЫКЛ`).
     - В шапку каталога выведен бейдж активности личного аккаунта MAX с номером телефона.
4. **Сборка и развертывание на VPS**:
   - Перезапущены контейнеры `foodtech-backend` и `foodtech-worker`.
   - Выполнена сборка фронтенда админки (`vite build` в `/root/foodzuka/admin` — 0 ошибок, время сборки 1м 38с).
   - Проведена 100% сверка MD5 контрольных сумм всех измененных файлов между локальной средой и сервером.
5. **Живые тесты на VPS (номер 79220079019)**:
   - `POST /api/v1/vk/marketing-bots/test-send/shop/1` с каналом `max` -> статус `200 OK`, сообщение доставлено в MAX клиенту `79220079019` с личного номера, лог зафиксирован в `vk_bot_message_logs` (id 15605, `channel='max'`, `customer_phone='79220079019'`, `status='SENT'`).
   - `GET /api/v1/vk/marketing-bots/analytics/shop/1` -> `metrics_vk: {sent_count: 29}`, `metrics_max: {sent_count: 1}`.
   - `POST /api/v1/vk/marketing-bots/save/shop/1` -> настройки каналов и лимитов успешно сохранены в БД и прочитаны обратно.
   - Входящие сообщения MAX: команда "1" распознана и клиенту доставлено меню.
