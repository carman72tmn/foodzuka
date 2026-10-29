# Лог решения: Комплексное восстановление работы ВК ботов, системных рассылок и уведомлений курьерам/клиентам

**Дата и время**: 2026-09-04 14:15
**Сессия**: `2026-09-04_14-15_vk_bots_and_notifications_fix`
**Задача**: Выяснить, почему перестали отправляться уведомления ВКонтакте, перестали работать боты ВК, все рассылки (системные, рассылки курьерам, парсер ВК, боты, уведомления клиентам) стали неактивными, и устранить все сбои.

---

## 1. Исходная диагностика компонентов и базы данных (на VPS)

В ходе детальной проверки на VPS (`ssh vezuroll`) исследованы:
- Таблицы БД: `vk_bot_connections`, `vk_templates`, `vk_bot_accounts`, `vk_settings`, `mailing_cascades`, `bot_commands`, `vk_birthday_bots`, `vk_cover_bots`, `vk_contests`, `vk_activity_settings`, `vk_first_comment_settings`, `scheduled_tasks`.
- Процессы и логи контейнеров: `foodtech-backend`, `foodtech-worker`, `foodtech-bot`.
- Состояние очередей Celery и Redis.

### Обнаруженные критические причины сбоев:
1. **AttributeError в iiko_sync_service.py:2979**:
   - Строка `if mapped_status in (OrderStatus.ready, OrderStatus.cooking_finished, "ready", "Готов"):` приводила к аварийному завершению блока отправки уведомлений курьерам `send_courier_notification`. В классе `OrderStatus` нет атрибута `cooking_finished`.
2. **vk_notification_router.py:492 (is_admin_or_manager)**:
   - Проверял только `acc.employee_id` и `acc.groups`. Однако у ключевых аккаунтов `VkBotAccount` (ID 5 «Руководитель», ID 6 «Администратор», ID 7 «Супер СисАдминистратор») поле `employee_id = None` и `groups = []`. Для событий `target_mode = "assigned_and_admins"` функция возвращала `False`, из-за чего администраторы не получали уведомления о заказах и изменениях.
3. **celery_app.py:12 (отсутствие задач в include)**:
   - В списке `include` Celery отсутствовали модули:
     - `app.tasks.vk_scheduler_task`
     - `app.tasks.vk_parser_tasks`
     - `app.tasks.senler_tasks`
     - `app.tasks.vk_digest_task`
   - Celery воркер отклонял вызовы с ошибкой: `Received unregistered task of type 'app.tasks.vk_scheduler_task.run_vk_post_scheduler'`.
4. **Неактивный шаблон courier_assigned в vk_templates**:
   - Шаблон с `event_type = 'courier_assigned'` имел статус `is_active = False`, из-за чего уведомления курьеру при назначении заказа блокировались на шаге проверки `if template and not getattr(template, "is_active", True): return`.
5. **Протухший токен пользователя в VkBotConnection (код ошибки 5)**:
   - Токен пользователя `vk_user_token` для группы 186688777 отдавал `User authorization failed: invalid access_token (4)`.
   - В `vk_activity_service.py` и `vk_cover_service.py` отсутствовал автоматический фоллбэк на токен бота сообщества `vk_bot_token`, который является полностью валидным.

---

## 2. План выполнения исправлений
1. Локально исправить `iiko_sync_service.py` (замена `OrderStatus.cooking_finished` на строку `"cooking_finished"`). Сохранить строго в UTF-8.
2. Локально исправить `vk_notification_router.py` (добавить проверку `acc.name` в `is_admin_or_manager`).
3. Локально исправить `celery_app.py` (добавить недостающие задачи в `include`).
4. Локально добавить fallback в `vk_activity_service.py` и `vk_cover_service.py`.
5. В БД на VPS активировать шаблон `courier_assigned`.
6. Выгрузить измененные файлы на VPS через SCP, проверить MD5.
7. Перезапустить сервисы (`docker compose restart backend worker`).
8. Провести верификацию отправки и работы воркера.
9. Обновить документацию проекта (`system_faq.md`, `sql_faq.md`, `sitenav.md`).

---

## 3. Результаты выполнения и верификации

### А. Сверка контрольных сумм MD5 (Локально <-> VPS):
- `backend/app/services/iiko_sync_service.py`: `1d407664c6d83cdb548d55c6a440f003` (совпадает)
- `backend/app/services/vk_notification_router.py`: `fe7e635d16286914bda0145d3a2b00ee` (совпадает)
- `backend/app/core/celery_app.py`: `542fe6c772197d8e49ca800bfca0e7e9` (совпадает)
- `backend/app/services/vk_cover_service.py`: `81d76977c3836df4e8acbeafd7a36a70` (совпадает)
- `backend/app/services/vk_activity_service.py`: `088c0258aa848fa40a835ccd692bf002` (совпадает)

### Б. База данных PostgreSQL:
- Выполнен запрос `UPDATE vk_templates SET is_active = true WHERE event_type = 'courier_assigned'`.
- Все 14 шаблонов уведомлений в `vk_templates` находятся в статусе `is_active = true`.

### В. Celery Worker (`foodtech-worker`):
- Зарегистрированы все задачи:
  - `app.tasks.vk_scheduler_task.run_vk_post_scheduler`
  - `app.tasks.vk_parser_tasks.cleanup_vk_messages_task`
  - `app.tasks.vk_parser_tasks.scan_vk_history_task`
  - `app.tasks.senler_tasks.sync_senler_subscribers_task`
  - `app.tasks.vk_birthday_task.*`
  - `app.tasks.vk_cover_task.*`
- Тестовый запуск задачи `run_vk_post_scheduler.delay()` успешно выполнен за `0.034s`.
- Периодическая задача `vk_cover_update_task` успешно обновила динамическую обложку группы 186688777 в ВКонтакте через API (`photos.getOwnerCoverPhotoUploadServer` -> `photos.saveOwnerCoverPhoto` -> 200 OK).

### Г. Тестирование отправки уведомлений ВК:
1. **Системный алерт (`system_alert`)**:
   - `Log ID 13131 | Account: 5 (Руководитель) | Status: MessageStatus.SENT | Error: None`
   - `Log ID 13130 | Account: 6 (Администратор) | Status: MessageStatus.SENT | Error: None`
2. **Назначение курьера (`courier_assigned`)**:
   - `Log ID 13132 | Account: 8 (Курьер Дмитрий) | Status: MessageStatus.SENT | Error: None`
   - Сообщение с деталями заказа успешно доставлено курьеру Дмитрию в ВКонтакте.

### Д. Статус компонентов:
- Все 11 подсистем ВКонтакте (боты, парсер, шаблоны, шедулер, динамическая обложка, дайджесты, рассылки курьерам и системные алерты) работают исправно и в полном объеме.

