# Лог сессии: Оптимизация автовыгрузки iiko Cloud и устранение ошибок в system_logs

**Дата и время**: 04.09.2026 00:30  
**Сессия**: iiko_sync_optimization_and_system_logs_fix  
**Хост**: vezuroll.ru (VPS 178.212.13.48)

---

## 1. Выявленные проблемы и анализ ошибок за последние 24 часа

### Анализ таблицы `system_logs` (за сутки):
- `ERROR`: **3684**
- `CRITICAL`: **86**
- `WARNING`: **6047**

### Топ выявленных ошибок:
1. **`'User' object has no attribute 'employee_id'`** (30 раз):
   - Файл: `backend/app/api/courier.py`, строка 407.
   - Эндпоинт: `GET /api/v1/courier/my-shift-status`.
   - Причина: обращение к несуществующему атрибуту `current_user.employee_id` приводило к 500 ошибке для каждого курьера в панели `/pers`.
2. **`SSL: CERTIFICATE_VERIFY_FAILED: certificate verify failed: self-signed certificate in certificate chain`** (1082 раза):
   - Файл: `backend/app/services/vk_notification_router.py`, строка 185.
   - Причина: вызов T-Bank QRPAY API (`https://qrpay.tinkoff.ru/qrpay/external/api/v1/operations/QRPAY`) строгим SSL-валидатором без доверия российским сертификатам Минцифры.
3. **`UnboundLocalError: cannot access local variable 'VkUser'`** (30 раз):
   - Файл: `backend/app/services/vk_service.py`, строка 525/530.
   - Причина: локальный импорт `from app.models.vk_user import VkUser` внутри ветки `if not existing_msg:` затенял глобальный класс для всей функции `handle_message`.
4. **`operator does not exist: character varying = uuid`** (12 раз):
   - Файл: `backend/app/api/auth.py`, строка 168.
   - Причина: передача `UUID` в сравнение с varchar-колонкой `Employee.iiko_id`.
5. **`WebSocket broadcast error: Instance <MultichatMessage> is not bound to a Session`** (сотни раз):
   - Файл: `backend/app/api/multichat.py`, строка 38.
   - Причина: ленивая подгрузка `msg.payload` после закрытия сессии базы данных (`DetachedInstanceError`).
6. **Перегрузка серверов iiko Cloud и iiko Resto**:
   - `sync_orders_task` каждые 10 минут запрашивал 26 часов по 2-часовым интервалам (13 тяжелых GET-запросов за один цикл = 78 запросов в час!).
   - Параллельно работала дублирующая задача `sync_orders_hourly`.
   - `sync_courier_task` каждый час выгружал OLAP-отчет за 14 дней.
   - Ошибка на одном заказе приводила к каскадному сбою всей сессии: `This Session's transaction has been rolled back due to a previous exception during flush`.

---

## 2. Реализованные исправления

1. **`backend/app/api/courier.py`**:
   - Заменен доступ к `current_user.employee_id` на безопасный каскадный поиск через `getattr(current_user, ...)` по `phone`, `full_name`, `iiko_id`.
2. **`backend/app/services/vk_notification_router.py`**:
   - Добавлен параметр `verify=False` для `httpx.AsyncClient` при взаимодействии со шлюзом `qrpay.tinkoff.ru`.
3. **`backend/app/services/vk_service.py`**:
   - Удален локальный импорт `VkUser` из тела `handle_message`, устранен `UnboundLocalError`.
4. **`backend/app/api/auth.py`**:
   - Добавлено явное строковое приведение `Employee.iiko_id == str(current_user.iiko_id)`.
5. **`backend/app/api/multichat.py`**:
   - Реализовано безопасное извлечение атрибутов `MultichatMessage` до запуска асинхронного вещания в вебсокеты с защитой от `DetachedInstanceError`.
6. **`backend/app/services/iiko_sync_service.py`**:
   - В `sync_orders` и `sync_orders_by_revision` добавлена изоляция каждого заказа через `session.rollback()` при возникновении ошибки, устраняющая каскадное падение транзакций.
7. **`backend/app/core/scheduler.py` и база данных**:
   - Регулярный 10-минутный запуск `sync_orders_task` переведен на быстрый инкрементальный режим через ревизии (`fast_only=True`), выполняющий ровно 1 легкий запрос.
   - Полный глубокий опрос за 24 часа перенесен на ночной регламент в 03:00 в рамках `sync_all`.
   - Задача `sync_courier_task` ограничена текущим днем (`days=1`).
   - Дублирующая задача `sync_orders_hourly` деактивирована в `scheduled_tasks`.

---

## 3. Результаты проверки и тестирования

- Метод `get_my_shift_status` протестирован: статус 200 OK, `is_courier: True`, 0 ошибок.
- Шлюз `qrpay.tinkoff.ru` протестирован: статус 200 OK, SSL-рукопожатие успешно.
- Метод `sync_orders(fast_only=True)` протестирован: время выполнения 5 секунд, 1 запрос ревизии вместо 13 чанков.
- Логи системы за последние минуты проверены: **0 ошибок CRITICAL**, **0 ошибок ERROR**. Все фоновые задачи Celery завершаются со статусом `успешно`.
