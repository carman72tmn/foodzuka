[28.04.2026 12:41] TASK: Стабилизация интеграции iiko и карточки клиента.

1. backend/app/services/iiko_service.py:
   - Исправлен маппинг OLAP: Guest.Name -> Customer.Name, Guest.Phone -> Customer.Phone (фикс 400 Bad Request).
   - Добавлена логика Retry для 403 License Forbidden (авто-релогин при ошибке REST_API).
   - Оптимизирована очистка payload (убраны пустые поля).

2. backend/app/services/iiko_sync_service.py:
   - Обновлен маппинг в sync_revenue_olap.
   - Добавлена поддержка новых колонок в БД для отчетов по скидкам (coupon_number, coupon_series, discount_name).
   - Исправлена работа с Attendance API (смены сотрудников).

3. backend/app/api/reports.py:
   - Исправлен маппинг полей в API-эндпоинтах аналитики.

4. admin/resources/js/components/CustomerDetailModal.vue:
   - Внедрена полная безопасность вычисляемых свойств (computed) через optional chaining.
   - Исправлено зависание при открытии карточки ("Ошибка в render" / "null is not an object").

5. backend/app/services/vk_notification_router.py:
   - Исправлен TypeError в dispatch_event (добавлены **kwargs).

СТАТУС: Все изменения выгружены на VPS, сервисы backend, worker, admin перезапущены. Ошибки в логах отсутствуют.
