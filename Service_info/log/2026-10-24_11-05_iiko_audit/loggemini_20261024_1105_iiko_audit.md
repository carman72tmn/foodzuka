# Лог инспекции и аудита интеграции с iiko (FoodZuka Admin & Employee Panel)

- **Дата и время сессии:** 2026-10-24 11:05 (UTC+5)
- **Сессия:** `7002e9cf-0444-4536-84ed-229e7a7ad026`
- **Задача:** Полная техническая инспекция взаимодействия с iiko Cloud API и iiko Server (Resto) API в админ-панели (`vezuroll.ru/admin`) и панели сотрудников (`vezuroll.ru/pers`), выявление причин сбоев кнопок «Доставлен» и «Оплата» в разделе «Курьеры», нестабильной отправки уведомлений в iiko, рассинхрона статусов в разделе «Заказы» и неработающего открытия смен курьерам из админки.
- **Режим работы:** Строго диагностика и аналитический отчет (без внесения изменений в код проекта и БД по прямому указанию пользователя «сам ничего не исправляй!»).

## Проверенные компоненты и файлы
1. `backend/app/services/iiko_service.py` — клиент iiko Cloud API / Resto API.
2. `backend/app/services/iiko_sync_service.py` — сервис синхронизации заказов, смен, сотрудников и лояльности.
3. `backend/app/api/courier.py` — эндпоинты панели курьера и управления сменами/выплатами курьеров.
4. `backend/app/api/orders.py` — эндпоинты раздела «Заказы».
5. `backend/app/api/webhooks.py` — обработчик вебхуков `/api/v1/webhooks/iiko`.
6. `backend/app/core/scheduler.py` — планировщик фоновых задач APScheduler.
7. `backend/app/services/order_status_history_service.py` — сервис истории статусов заказа.
8. `admin/resources/js/pages/employee/courier.vue` — интерфейс курьера и админ-управления курьерами.
9. `admin/resources/js/pages/orders/index.vue` — интерфейс раздела «Заказы».
10. `admin/resources/js/stores/chatStore.js` — обработка WebSocket-событий в реальном времени.
11. Диагностика БД PostgreSQL (`foodtech_db`) и логов контейнера `foodtech-backend` на VPS (`ssh vezuroll`, `/root/foodzuka`).

## Краткая сводка выявленных корневых причин
1. **Открытие смены курьеру из админки (`POST /api/v1/courier/admin/open-shift` и `/open-shift`):**
   - В `clockin_courier_shift` (`iiko_service.py:4276-4300`) не передается обязательный параметр `roleId` (`112da4c3-5323-45a7-a033-bf5265d66608` для роли `CUR`).
   - В `IikoService._request` (`iiko_service.py:371-379`) для всех URL, содержащих `/shift`, в тело запроса принудительно инжектируется массив `"organizationIds": [org_id]` вместо одиночного `"organizationId"`.
   - Эндпоинт `/api/1/employees/shift/clockin` является асинхронной командой (возвращает `correlationId`), но проверка статуса выполнения через `/api/1/commands/status` отсутствует.
   - При возврате словаря ошибки `{"status": "error"}` из `_request` (при HTTP 403/429/401) функции `admin_open_courier_shift` и `open_my_shift` не проверяют `res.get("status") == "error"`, записывают фейковую смену `shift-{emp.id}-{timestamp}` со статусом `OPEN` в локальную БД и возвращают HTTP 200 «Смена курьера открыта в iiko».
   - Подтверждено в БД на VPS: `2026-10-24 05:06:21 UTC` создана фейковая смена `id=1017` (`shift-392-1792818381`), вебхук `PersonalShift` от iiko не пришел; реальная смена `id=1020` открылась только в `05:19:04 UTC` после ручной прокатки карты на кассе iikoFront (с `roleId = 112da4c3-5323-45a7-a033-bf5265d66608`).

2. **Кнопки «Доставлен» и «Оплата» в разделе «Курьеры» (`/pers/courier` и `/courier`):**
   - Блокировка `canShowDelivered(order)` (`courier.vue:206-222, 2340`) скрывает обе кнопки («Доставлен» и «Оплата») на 60 секунд после перехода заказа в `OnWay`, либо навсегда, если в `status_history` нет записи со статусом `delivering`/`onway`.
   - Функция `handleDeliveredClick(order)` (`courier.vue:1115-1162`) проверяет `hasOrderPaymentMethod(order)`. Так как все заказы из iiko приходят с предварительным типом оплаты (`Наличные` или `2. Картой курьеру`), `hasOrderPaymentMethod` всегда возвращает `true`, диалог выбора/подтверждения оплаты пропускается, вызывается `updateStatus(order.id, 'Delivered', true)` с `silent=true`, заказ переводится в `delivered` без подтверждения оплаты и мгновенно исчезает из вкладки «В работе» неоплаченным (`is_paid=False`).
   - При смене типа оплаты (`courier_change_payment_type`, `courier.py:2185-2225`) и закрытии заказа (`close_courier_order`, `courier.py:2266-2306`) сразу после асинхронной команды `change_order_payments` без задержки (0 мс) вызывается `sync_order_by_id`, который скачивает из iiko старое состояние заказа (где платеж еще не применился на кассе и `isProcessedExternally=False`) и перезаписывает в локальной БД `payment_method`, `payments_details`, `is_paid=False` и `left_to_pay` обратно на старые значения.
   - В `_apply_order_payment_to_iiko` (`courier.py:2031-2075`) ошибки HTTP 400 от `/api/1/deliveries/change_payments` (возникающие при попытке сменить оплату у уже доставленного/закрытого заказа или при наличии бонусов `iikoCard`) перехватываются через `except Exception as pe: logger.error(...)` и игнорируются, возвращая `True` (ложный успех).

3. **Нестабильное обновление статусов в разделе «Заказы» (`/orders`):**
   - В `webhooks.py` (`326-353`) при получении вебхука `DeliveryOrderUpdate` полезная нагрузка `eventInfo.order` полностью игнорируется, и запускается `sync_order_by_id` (`/api/1/deliveries/by_id`). При таймаутах сети к `api-ru.iiko.services` (`ConnectTimeout`/`ReadTimeout`) обновление статуса теряется до следующего цикла `sync_orders_task` (раз в 10 минут).
   - В `process_iiko_order` (`iiko_sync_service.py:1499, 2502`) внутри открытой транзакции БД выполняется синхронный HTTP-запрос лояльности `sync_single_customer` (до 30+ сек с ретраями), из-за чего соединение с PostgreSQL разрывается (`psycopg2.OperationalError: server closed the connection unexpectedly` / `PendingRollbackError`) до `session.commit()`, и смена статуса заказа откатывается.
   - В `courier.vue` (`1591`) слушатель WebSocket `order-updated-event` не включает события `order_status_changed` и `order_delivered`.
   - При каждом сохранении заказа в `process_iiko_order` (`2425-2468`) выбрасывается ошибка `Ошибка при сопоставлении платежа Т-Банка: can't compare offset-naive and offset-aware datetimes`, а в уведомлениях ВК о смене падает `ZoneInfoNotFoundError: 'No time zone found with key Asia/Tyumen'`.
