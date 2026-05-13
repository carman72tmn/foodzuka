# Log Gemini - 2026-04-29 17:45 - Customer Fallback Sync

## Задача
Реализовать схему: при добавлении нового гостя или синхронизации, делать поиск в iiko сначала по ID (если есть), затем по номеру телефона. Это обеспечит надежную привязку UID и актуализацию данных лояльности.

## Выполненные изменения

### 1. Бэкенд: iiko_service.py
- Расширен метод `get_customer_info`. Теперь он принимает необязательные параметры `phone` и `customer_id`.
- Добавлена логика формирования payload в зависимости от предоставленного идентификатора (`type: "id"` или `type: "phone"`).
- Улучшена обработка ошибок 400 (не найден): метод возвращает `found: False` вместо выброса исключения, что упрощает логику в вызывающем коде.

### 2. Бэкенд: iiko_sync_service.py
- В методе `sync_single_customer` внедрена fallback-логика:
  1. Попытка поиска по `customer.iiko_customer_id` (если поле не пустое).
  2. В случае неудачи или отсутствия ID — поиск по нормализованному номеру телефона.
- Это гарантирует, что даже при изменении ID в iiko или "битых" ссылках в локальной БД, система сможет восстановить связь с профилем через телефон.

### 3. Бэкенд: api/customers.py (Ранее)
- В эндпоинт `/api/v1/customers/by-phone/{phone}` добавлена автоматическая инициация синхронизации (`sync_single_customer`), если гость не найден локально. Это обеспечивает мгновенное наполнение базы при первом просмотре заказа нового клиента.

### 4. Фронтенд: OrderDetailModal.vue (Ранее)
- Кнопка "Открыть карту клиента" теперь корректно обрабатывает асинхронную загрузку данных. Если клиент только что был синхронизирован (при первом запросе по телефону), модальное окно откроется сразу с актуальным ID.

## Файлы
- [iiko_service.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/services/iiko_service.py)
- [iiko_sync_service.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/services/iiko_sync_service.py)
- [customers.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/api/customers.py)
- [OrderDetailModal.vue](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/components/OrderDetailModal.vue)
- [system_faq.md](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/Service_info/system_faq.md)

## Тестирование (VPS)
1. Выгрузка файлов на сервер.
2. Перезапуск контейнеров `backend` и `worker`.
3. Проверка поиска по телефону для нового гостя.
4. Проверка синхронизации по ID для существующего гостя.

_Лог сформирован: 29.04.2026 17:48_
