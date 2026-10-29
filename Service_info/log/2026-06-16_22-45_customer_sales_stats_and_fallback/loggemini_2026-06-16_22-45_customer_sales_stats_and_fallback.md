# Log Gemini: Customer Sales Statistics Sync and Caching Bypass with Local Fallback

**Дата и время**: 16.06.2026 22:45 (UTC+5)  
**Задача**: Сохранение статистики продаж по клиентам (LTV, количество заказов, средний чек), принудительное обновление (при открытии карточки, ручном запросе) и автоматическое фоновое обновление (при получении нового заказа). Добавлен локальный расчет статистики при сбоях или отсутствии лицензии iiko REST API.

---

## Измененные файлы

1. **[iiko_service.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/services/iiko_service.py)**:
   - Внедрена функция `_get_local_customer_analytics(session, phone)` для расчета LTV, количества заказов, среднего чека, количества товаров и дат на основе локальной таблицы `orders` (по не-отмененным заказам).
   - Изменен метод `get_customer_analytics_olap`: добавлен аргумент `bypass_cache: bool = False`. При `True` кэш игнорируется.
   - Метод возвращает локально рассчитанные показатели, если запрос к iiko OLAP завершился ошибкой (например, из-за лицензий).

2. **[iiko_sync_service.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/services/iiko_sync_service.py)**:
   - Обновлен метод `sync_single_customer`: добавлен `bypass_cache: bool = False` и проброшен в `iiko_service.get_customer_analytics_olap`.
   - В метод `ensure_customer_from_order` (создание/синхронизация при поступлении заказа) в самом конце добавлена фоновая задача `sync_single_customer_task.delay(clean_phone, fast_sync=False, bypass_cache=True)`. Это обеспечивает фоновое обновление показателей клиента сразу при получении заказа.

3. **[customer_tasks.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/tasks/customer_tasks.py)**:
   - Обновлены Celery-задачи `sync_single_customer_task` и `sync_guest_data_task` для поддержки и проброса параметра `bypass_cache`.

4. **[customers.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/api/customers.py)**:
   - В эндпоинте `/olap-stats` добавлен параметр `refresh` (`bypass_cache`).
   - В ручных синхронизациях `/{customer_id}/sync` и `/{customer_id}/sync-premium` теперь передается `bypass_cache=True`.

5. **[CustomerDetailModal.vue](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/components/CustomerDetailModal.vue)**:
   - В fetch-запрос метода `loadOlapStats` добавлен параметр `?refresh=true`.

6. **[system_faq.md](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/Service_info/system_faq.md)** и **[sitenav.md](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/Service_info/sitenav.md)**:
   - Внесены изменения в документацию (добавлен пункт 72 в system_faq, обновлен раздел аналитики в sitenav).

---

## Тестирование и верификация

1. **Сборка фронтенда локально**:
   - Выполнена сборка `npm run build`. Ошибок компиляции нет.
2. **Синхронизация на VPS**:
   - Выполнен скрипт `sync_to_vps.py`. Обновленный фронтенд успешно скомпилирован на сервере, контейнеры бэкенда и воркера перезапущены.
3. **Функциональный тест**:
   - Выполнен тест на тестовом номере `+79220079019` (Сергей, ID 60) с помощью скрипта `test_sync.py`:
     - Первоначальное состояние: `Total orders: 325`, `LTV: 6385.20`.
     - Результат `sync_single_customer(bypass_cache=True)`: `Success: True`, обновленные данные: `Total orders: 327`, `LTV: 6385.20`, дата синхронизации обновилась на текущее время. Кэш Redis успешно сброшен.
     - Результат локального расчета (`_get_local_customer_analytics`): выдает корректные данные (`total_count: 13`, `total_sum: 23680.0` по локальной таблице заказов) и пометку `is_local_fallback: True`.

---

## Инструкция по откату изменений (Rollback)

В случае необходимости отката выполните следующие шаги:

1. Верните сигнатуры методов в [iiko_service.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/services/iiko_service.py) и удалите метод `_get_local_customer_analytics`.
2. В [iiko_sync_service.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/services/iiko_sync_service.py) удалите вызов `sync_single_customer_task.delay(clean_phone, fast_sync=False, bypass_cache=True)` из `ensure_customer_from_order`.
3. Уберите параметры `bypass_cache` из [customer_tasks.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/tasks/customer_tasks.py) и роутов [customers.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/api/customers.py).
4. Уберите параметр `?refresh=true` из [CustomerDetailModal.vue](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/components/CustomerDetailModal.vue).
5. Перезапустите деплой: `python sync_to_vps.py`.
