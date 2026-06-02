# Log: Implementation of Role-Based Access Control (RBAC)
Дата: 2026-05-01
Время: 06:15
Сессия: rbac_implementation

## Описание задачи
Внедрение системы разграничения прав доступа (RBAC) в админ-панель FoodZuka.

## Выполненные действия
1. **Backend**:
    - Создан скрипт `backend/app/scripts/seed_rbac.py` для инициализации прав и ролей.
    - В `backend/app/api/deps.py` добавлена проверка прав через `require_permission`.
    - Обновлены эндпоинты в `users.py` и `orders.py` для использования гранулярных прав.
    - Реализована синхронизация ролей из iiko Resto в `iiko_sync_service.py`.
2. **Frontend**:
    - В `admin/resources/js/utils/auth.js` добавлен хелпер `hasPermission`.
    - Обновлен `admin/resources/js/layouts/components/NavItems.vue` для фильтрации меню.
3. **Документация**:
    - (Планируется) Обновление `system_faq.md` и `sql_faq.md`.

## Статус
Завершено внедрение основных компонентов. Требуется проверка на VPS.
