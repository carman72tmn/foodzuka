# Log Gemini - 26.04.2026 06:00
## Задача: Импорт клиентов, Оптимизация синхронизации, Авто-создание карточек

### Выполненные действия:
1. **Backend**:
    - Модифицирован `sync_customers_batch` (app/tasks/customer_tasks.py): добавлен пропуск существующих клиентов.
    - Создан `ImportService` (app/services/import_service.py): поддержка XLSX/XML.
    - Добавлен эндпоинт `/import` (app/api/customers.py).
    - Внедрена логика авто-создания в `process_iiko_order` (app/services/iiko_sync_service.py).
2. **Database**:
    - Добавлены колонки в `customers` и `sync_statuses`.
3. **Frontend**:
    - Добавлена кнопка "Импорт" в `admin/resources/js/Pages/clients/index.vue`.
    - Выполнен `npm run build` на VPS.
4. **Docs**:
    - Обновлены `system_faq.md`, `sql_faq.md`, `sitenav.md`.

### Локальные файлы обновлены:
- `backend/app/models/customer.py`
- `backend/app/models/sync_log.py`
- `backend/app/tasks/customer_tasks.py`
- `backend/app/services/import_service.py`
- `backend/app/api/customers.py`
- `admin/resources/js/Pages/clients/index.vue`

### Состояние на VPS:
- Файлы выгружены.
- Контейнеры `foodtech-backend` и `foodtech-worker` перезагружены.
- Фронтенд пересобран.
