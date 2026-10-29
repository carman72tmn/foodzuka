# Сессионный лог: Исправление извлечения данных из карточки заказа в рассылках

**Дата и время:** 15.06.2026 20:15 (UTC+5)  
**Задача:** Обеспечить правильную идентификацию и отправку данных о заказе (телефон, баланс бонусов, категории, заметки, адрес) напрямую из карточки заказа (`customer_info_details` и др.) в системных и каскадных рассылках.

## Описание изменений

### 1. Бэкенд (Бизнес-логика)

*   **Файл:** [iiko_sync_service.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/services/iiko_sync_service.py)
    *   В методе `sync_single_customer` расширена структура сохраняемого в заказ снимка (`customer_info_details`). В него добавлены новые поля:
        *   `phone` (телефон клиента)
        *   `categories` (список категорий из iiko)
        *   `notes` (системные заметки о клиенте)
        *   `bonus_points` (баланс бонусов в дополнение к `bonus_balance`)
    *   В методе `_send_order_vk_notification` в словарь `formatted_order` добавлен ключ `"customer_info_details"`, чтобы снимок заказа был доступен в контексте шаблонизатора системных рассылок.

### 2. Шаблонизаторы

*   **Файл:** [vk_notification_router.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/services/vk_notification_router.py)
    *   В методе `render_template` реализовано приоритетное считывание полей клиента из снимка в заказе (`customer_info_details`), если связь `customer` не загружена или пуста.
    *   Добавлены фолбэки на телефон из самого заказа (`customer_phone`) и имя (`customer_name`), а также красивое форматирование категорий через запятую.
*   **Файл:** [mailing_cascade_service.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/services/mailing_cascade_service.py)
    *   В методе `render_template` реализована аналогичная логика приоритетного считывания полей из снимка в заказе (`customer_info_details`).

## Результаты тестирования

На VPS запущен верификационный тест `test_render_from_order.py`, проверяющий рендеринг переменных `{{customer.phone}}`, `{{customer.bonus_points}}`, `{{customer.categories}}`, `{{customer.notes}}`, `{{order.address}}` в условиях отсутствия связи с клиентом в БД (все данные берутся строго из снимка заказа).  
Тест прошел со статусом **Успешно**.
Контейнеры `backend` и `worker` на VPS перезапущены.
