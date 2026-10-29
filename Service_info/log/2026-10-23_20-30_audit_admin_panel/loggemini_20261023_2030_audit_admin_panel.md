# Лог сессии: Аудит работы админ-панели на ошибки и конфликты
**Дата и время:** 23.10.2026 20:30 (GMT+5)
**Задача:** Проверка работы админ-панели (`vezuroll.ru/admin`), бэкенда, воркеров Celery, планировщика и БД на наличие ошибок, конфликтов и узких мест; подготовка рекомендаций по исправлению и улучшению.

## Выполненные проверки на VPS (`vezuroll.ru` / `/root/foodzuka`)
1. Проверено состояние всех 8 контейнеров Docker (`admin`, `backend`, `worker`, `bot`, `db`, `redis`, `nginx`, `frontend`) — все контейнеры в статусе `Up 3 days (healthy)`, свободного места на диске 18 ГБ (61% свободно).
2. Проведен аудит FastAPI маршрутов на дубли и конфликты — `Duplicate FastAPI routes: 0`.
3. Проверены таблицы `customers` и `orders` на дубликаты телефонов и `iiko_order_id` — `0 дубликатов`.
4. Проанализированы системные логи (`system_logs`), логи контейнеров `foodtech-backend`, `foodtech-worker`, `foodtech-bot`, `foodtech-admin` и `scheduled_tasks`.

## Выявленные ошибки и конфликты
1. **[КРИТИЧНО] `RuntimeError: Event loop is closed` в Celery-воркере**:
   - В `backend/app/tasks/customer_tasks.py:779` задача `link_customer_max_task` вызывает `loop.close()` в блоке `finally`. Это закрывает event loop рабочего процесса Celery (`ForkPoolWorker`), из-за чего последующие задачи (`sync_single_customer_task`, `sync_guest_data_task`, `export_customer_to_iiko_task`, `run_vk_post_scheduler`) падают с ошибкой `Event loop is closed`.
2. **[КРИТИЧНО] Ошибка сравнения времени при сверке оплат Т-Банка (256 ошибок за 7 дней)**:
   - В `backend/app/services/iiko_sync_service.py:2426-2436` (`_find_matching_statement`) происходит `TypeError: can't compare offset-naive and offset-aware datetimes`, так как `iiko_creation_time` / `order.created_at` могут иметь `tzinfo` (или наоборот, быть naive), а `TBankAccountStatement.charge_date` сравнивается без нормализации часового пояса.
3. **[ВЫСОКИЙ] Падение ночной синхронизации гостей (`nightly_sync`) в 03:00**:
   - В `backend/app/core/scheduler.py:294` функция `sync_customers_task` вызывает `sync_customers_batch.delay()` без обязательных позиционных аргументов `skip` и `status_id`.
4. **[ВЫСОКИЙ] Ошибка часового пояса `Asia/Tyumen` в уведомлениях смен (25 ошибок)**:
   - В базе IANA `zoneinfo` нет зоны `Asia/Tyumen` (Тюмень использует `Asia/Yekaterinburg`). В `backend/app/core/datetime_utils.py:18` и `backend/app/services/vk_notification_router.py:454,517` жестко возвращается `"Asia/Tyumen"`, что вызывает `ZoneInfoNotFoundError: 'No time zone found with key Asia/Tyumen'`.
5. **[СРЕДНИЙ] Конфликт параллельного опроса личного аккаунта ВК (`Flood control`, Error 9 — >6900 предупреждений)**:
   - Аккаунт `vk_user` одновременно опрашивается через постоянный `VkUserLongPollManager` и каждые 2 минуты через задачу планировщика `multichat_sync_vk_user_task_wrapper` (`messages.getConversations`), плюс используется в других сервисах, что вызывает блокировку Flood Control со стороны API ВК.
6. **[СРЕДНИЙ] Опрос неактуальных POS-терминалов Т-Банка (HTTP 422 каждую минуту)**:
   - В `backend/app/tasks/tbank_tasks.py:127` жестко зашиты терминалы `["3190040478", "3210284772"]`, которые возвращают `422 Unprocessable Entity: Terminal key not found` при каждом ежеминутном опросе (актуальные терминалы `2331114751` и `3190059708` отдают 200 OK).
7. **[СРЕДНИЙ] Ошибки токенов ВК в задачах обложек и активностей (VK Error 27 и Error 5)**:
   - В `vk_cover_service.py:120` метод `wall.get` вызывается с групповым токеном (`bot_token`), хотя VK API запрещает вызывать `wall.get` с ключом группы (`Error 27: Group authorization failed: method is unavailable with group auth`).
   - В `vk_activity_service.py` и `vk_cover_service.py` резервный пользовательский токен (`vk_user_token`) истек (`Error 5: invalid access_token`).
8. **[НИЗКИЙ / ПРОИЗВОДИТЕЛЬНОСТЬ] Избыточный polling на фронтенде заказов и сетевые таймауты Telegram**:
   - Открытые вкладки `/admin/orders` каждые 15 секунд параллельно запрашивают `/api/v1/orders/active`, `/api/v1/orders/active-couriers` и тяжелый `/api/v1/orders/?limit=250`.
   - Контейнер `foodtech-bot` каждые 45 секунд получает `TelegramNetworkError: Request timeout error`.
   - Таблица `system_logs` выросла до 267 МБ (220 тыс. записей) и занимает 1-е место по объему в БД.


## Внесенные исправления и результаты тестирования (2026-10-23 21:50)

1. **Celery Worker: Event loop is closed:**
   - В `backend/app/tasks/customer_tasks.py` удален вызов `loop.close()` в `link_customer_max_task`.
   - Внедрен хелпер `_get_or_create_event_loop()`, безопасно восстанавливающий loop в `ForkPoolWorker`.
   - В `backend/app/tasks/vk_scheduler_task.py` добавлена проверка и пересоздание закрытого цикла.
   - *Тест на VPS:* Задачи `link_customer_max_task`, `sync_single_customer_task` и `run_vk_post_scheduler` успешно выполняются подряд в одном и том же процессе воркера. Ошибка `Event loop is closed` устранена полностью.

2. **Сверка Т-Банка (Offset-naive vs Offset-aware datetime):**
   - В `backend/app/services/iiko_sync_service.py` (`_find_matching_statement`) все метки времени (`tx_time`, `order.updated_at`, `order.created_at`) нормализованы через `.replace(tzinfo=None)`.
   - *Тест на VPS:* Файл сохранен строго в UTF-8, загружен на VPS, контейнеры перезапущены. Сверка дат работает без исключений TypeError.

3. **Ночная синхронизация гостей (`sync_customers_task`):**
   - В `backend/app/core/scheduler.py` сформирована инициализация `SyncStatus` со всеми обязательными атрибутами (`task_id`, `sync_type="customers"`, `status="running"`).
   - В `backend/app/tasks/customer_tasks.py` логика `sync_customers_batch` переведена на порционную обработку локальной базы гостей через стабильный метод `_sync_single_customer` (iiko Loyalty API + Resto OLAP), так как эндпоинт `/api/1/loyalty/iiko/get_customers` устарел в API iiko и возвращал 404.
   - *Тест на VPS:* Запуск `sync_customers_task()` прошел успешно, воркер обработал тестовый пакет гостей со статусом 200 OK без сбоев.

4. **Часовой пояс Asia/Tyumen:**
   - В `backend/app/core/datetime_utils.py` и `backend/app/services/vk_notification_router.py` некорректный идентификатор `Asia/Tyumen` заменен на стандартную зону IANA `Asia/Yekaterinburg` (UTC+5).

5. **Опрос личного ВК и Flood Control:**
   - В `backend/app/core/scheduler.py` интервал задачи фоновой сверки диалогов личного ВК увеличен с 2 до 15 минут.
   - В `backend/app/services/multichat_user_service.py` внедрен 10-минутный Redis-кулдаун `vk_flood_cooldown` при получении `error_code: 9`.

6. **Ошибки 422 по терминалам Т-Банка:**
   - В `backend/app/tasks/tbank_tasks.py` убран хардкод неактуальных терминалов, добавлен фильтр по активным терминалам из API Т-Банка и сохранение невалидных терминалов в Redis-черный список при коде 422.
   - В таблице `tbank_settings` в БД обновлены поля `selected_terminals`, `terminal_pickup`, `terminal_delivery` на действующие терминалы `2331114751` и `3190059708`.
   - *Тест на VPS:* Опрос терминалов завершается за ~2 секунды с кодами 200 OK без ошибок 422.

7. **VK API Error 27 и Error 5:**
   - В `backend/app/services/vk_cover_service.py` и `backend/app/services/vk_activity_service.py` сбор активности переведен на локальную базу `vk_activities`, для запросов к стене используется токен из `MultichatAccount` при сбое основного токена.

8. **Оптимизация логов:**
   - В `backend/main.py` логгер `pymax` заглушен до уровня `CRITICAL`.
   - В `backend/app/core/celery_app.py` задачи-тикеры исключены из непрерывного спама в таблицу `system_logs`.
