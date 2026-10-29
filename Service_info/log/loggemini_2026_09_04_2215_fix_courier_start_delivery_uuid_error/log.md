# Лог задачи: Устранение ошибки 400 (UUID не является сериализируемым для JSON) при нажатии кнопки Начать в курьерской панели
**Дата и время**: 04.09.2026 22:15 - 22:25
**Сессия**: fix_courier_start_delivery_uuid_error
**Задача**: Исправление ошибки сериализации объекта UUID в JSON при нажатии кнопки «Начать» в карточке готового заказа в панели курьера (/pers/courier), корректное назначение курьера в iiko Cloud API через эндпоинт /api/1/deliveries/update_order_courier с полем employeeId, перевод доставки в статус OnWay и фиксация в локальной БД.

## 1. Выявленные проблемы
1. **Ошибка сериализации UUID**:
   В backend/app/api/courier.py при вызове iiko_service.assign_delivery_courier передавался current_user.iiko_id, который в модели User имеет тип uuid.UUID. Стандартный json.dumps внутри httpx не поддерживает uuid.UUID и падал с ошибкой: TypeError: Object of type UUID is not JSON serializable.
   Кроме того, order_id передавался как локальный ID (например, 2808), а не UUID заказа в iiko Cloud (order.iiko_order_id).
2. **Неверный эндпоинт назначения курьера в iiko Cloud API**:
   В backend/app/services/iiko_service.py метод assign_delivery_courier вызывал устаревший эндпоинт /api/1/deliveries/assign_courier с полем courierId. Для текущего аккаунта iiko API возвращал 403/401: Right api/1/deliveries/assign_courier is not allowed for this ApiLogin.
   В актуальном iiko Cloud Transport API эндпоинт называется /api/1/deliveries/update_order_courier с телом:
   organizationId: str, orderId: str, employeeId: str.
3. **Несуществующее поле on_the_way_time в модели Order**:
   В коде производилась попытка присвоить order.on_the_way_time, что вызывало ValueError: Order object has no field on_the_way_time. Время фиксируется в order.status_history.
4. **Неопределенная переменная в vk_notification_router.py**:
   UnboundLocalError: cannot access local variable courier_events при отправке уведомления order_delivering.

## 2. Реализованные исправления
1. **backend/app/services/iiko_service.py**:
   - Добавлен статический метод _sanitize_for_json(obj): рекурсивно преобразует uuid.UUID -> str, Decimal -> float, datetime/date -> isoformat(), словари и списки.
   - В метод _request добавлена обязательная санитизация payload перед вызовом httpx.request.
   - Метод assign_delivery_courier переведен на /api/1/deliveries/update_order_courier с параметрами organizationId, orderId, employeeId.
   - Метод change_delivery_status обновлен с приведением аргументов к str.
2. **backend/app/api/courier.py**:
   - Эндпоинт POST /orders/{order_id}/status:
     - Находит заказ через _find_order(db, order_id).
     - Извлекает реальный UUID заказа iiko_order_uuid = str(order.iiko_order_id).
     - Извлекает организацию заказа org_id.
     - Определяет courier_iiko_id в виде строки str(...).
     - При статусе OnWay назначает курьера в iiko Cloud.
     - Переводит статус заказа в OnWay в iiko Cloud.
     - Обновляет локальный статус delivering, имя курьера и ленту status_history.
     - Отправляет уведомление клиенту order_delivering.
3. **backend/app/services/vk_notification_router.py**:
   - Добавлено определение courier_events перед проверкой флагов цепочки.

## 3. Верификация
- Все измененные файлы проверены через python -m py_compile — 0 ошибок.
- Файлы выгружены на VPS через scp, контрольные суммы SHA-256 проверены и совпадают на 100%.
- Контейнеры foodtech-backend и foodtech-worker перезапущены через docker compose restart.
- Проведен live-тест вызова update_order_status со статусом OnWay для курьера Сергея на заказе №76232 (ID 2808):
  - iiko API вернул 200 OK (correlationId: c565277b-8eba-4c8c-afac-45d960bbbbc2);
  - Локальный заказ перешел в статус delivering с курьером Сергей Доставка;
  - Запись зафиксирована в status_history.
- Документация system_faq.md и sitenav.md актуализирована.
