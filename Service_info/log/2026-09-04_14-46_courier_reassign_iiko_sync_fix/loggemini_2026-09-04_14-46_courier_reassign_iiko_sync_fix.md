# Лог исследования и исправления: Смена курьера в заказах из iiko и отправка уведомлений

**Дата и время**: 2026-09-04 14:46 - 15:30 (UTC+5)
**Сессия**: `2026-09-04_14-46_courier_reassign_iiko_sync_fix`
**Задача**: Выяснить, почему при смене курьера в iiko в заказах и в курьерах в админке не меняются эти данные, а также не приходят уведомления курьерам и сотрудникам согласно настройкам уведомлений и рассылок.

---

## 1. Выявленные причины проблемы

1. **Тип вебхуков iiko**:
   - В кассовой системе iiko Cloud смена курьера чаще всего приходит как событие `DeliveryOrderUpdate` или `DeliveryOrderStatusChanged`, где курьер вложен в `eventInfo -> order -> courierInfo -> courier: {id, name, phone}`.
   - В `backend/app/api/webhooks.py` обработка курьера `process_courier_assigned` вызывалась строго по `event_type == "CourierAssigned"`, из-за чего события `DeliveryOrderUpdate` со сменой курьера не запускали логику переназначения.
2. **Отсутствие сброса статуса принятия (`courier_notification_status`)**:
   - Ни в вебхуках, ни в методе `process_iiko_order` (`iiko_sync_service.py`), ни в эндпоинте ручного назначения курьера `assign_courier` (`orders.py`) не производился сброс `courier_notification_status = None` и меток `courier_accepted_at`, `courier_accepted_source`, `courier_read_at`.
   - Если первый курьер нажал «Принял заказ», кружок становился зеленым (`accepted`). При смене курьера в iiko заказ сохранял старый статус принятия, новый курьер не видел необходимости его принимать, а диспетчер видел ложное подтверждение.
3. **Нестрогое сопоставление курьера в VK роутере**:
   - В `vk_notification_router.py:is_courier_assigned_to_order` сравнение имени шло по строгому совпадению строк (`acc.name.lower() == courier_name.lower()`).
   - Если в iiko курьер назван «Сергей», а в аккаунтах ВК или таблице сотрудников «Курьер Сергей» / «Сергей Доставка», роутер не находил совпадения и блокировал отправку.
4. **Ограничение целевой аудитории шаблона `courier_assigned`**:
   - В таблице `vk_templates` у шаблона 15 был установлен режим `target_mode = 'assigned_only'`. Уведомления уходили только курьеру, отсекая администраторов и управляющих, подписанных на контроль смен курьеров.

---

## 2. Внесенные изменения

### 1) `backend/app/api/webhooks.py`
- Переработана функция `process_courier_assigned`:
  - Извлекает `courierInfo` и ID заказа как из корня `event_info`, так и из `event_info.get("order")`.
  - Сопоставляет курьера с таблицей `Employee` по `courier_iiko_id` (UUID), а затем по имени.
  - При `is_courier_changed`:
    - Обновляет `order.courier_name = canonical_courier_name`.
    - Сбрасывает `order.courier_notification_status = None`, `courier_accepted_at = None`, `courier_accepted_source = None`, `courier_read_at = None`.
    - Создает/обновляет запись в `CourierOrder` с новым `employee_id`.
    - Транслирует WebSocket broadcast: `order_changed` и `courier_status_changed`.
    - Отправляет персональные WS/Push новому курьеру (`delivery_assigned`, `courier_order_assigned`).
    - Отправляет персональные WS/Push старому курьеру (`delivery_unassigned`, `courier_unassigned`).
    - Отправляет системные уведомления в VK/TG/MAX: `courier_assigned` и повторно `order_new` (состав заказа, адрес, СБП QR).
- В роутере `iiko_webhook` добавлен вызов `process_courier_assigned` для любых событий с `courierInfo` (`DeliveryOrderUpdate`, `DeliveryOrderStatusChanged`).

### 2) `backend/app/services/iiko_sync_service.py`
- В `process_iiko_order`:
  - Добавлено сопоставление курьера со справочником `Employee` по `iiko_id` и имени при извлечении заказа.
  - При `is_courier_reassigned` добавлен сброс полей `courier_notification_status = None`, `courier_accepted_at = None`, `courier_accepted_source = None`, `courier_read_at = None` и трансляция WebSocket broadcast.
- Сохранен строго в кодировке **UTF-8** без BOM.

### 3) `backend/app/services/vk_notification_router.py`
- В `is_courier_assigned_to_order` реализовано интеллектуальное сопоставление курьера:
  - По UUID курьера (`courier_iiko_id` <-> `employee.iiko_id`).
  - По имени привязанного сотрудника `acc.employee.name`.
  - По пересечению ключевых слов имени (например, `"Сергей"` совпадает с `"Сергей Доставка"`).

### 4) `backend/app/api/orders.py`
- В эндпоинте ручного назначения `assign_courier` добавлен сброс `courier_notification_status = None`, очистка меток принятия и трансляция WebSocket broadcast.

### 5) База данных PostgreSQL
- Выполнен запрос:
  ```sql
  UPDATE vk_templates SET target_mode = 'assigned_and_admins' WHERE event_type = 'courier_assigned';
  ```

---

## 3. Сверка контрольных сумм (MD5)

| Файл | MD5 локально | MD5 на сервере VPS | Статус |
| :--- | :--- | :--- | :--- |
| `backend/app/api/webhooks.py` | `e97ef69721121fcd028fc2d0473c3e9e` | `e97ef69721121fcd028fc2d0473c3e9e` | Совпадает |
| `backend/app/api/orders.py` | `89dc963d8f91e507154b8fc95ad4400c` | `89dc963d8f91e507154b8fc95ad4400c` | Совпадает |
| `backend/app/services/iiko_sync_service.py` | `87722969386bd7b33b2e9df612e29208` | `87722969386bd7b33b2e9df612e29208` | Совпадает |
| `backend/app/services/vk_notification_router.py` | `8bd4161d7d458b35db2f6c3c6d9ea1ec` | `8bd4161d7d458b35db2f6c3c6d9ea1ec` | Совпадает |

---

## 4. Результаты тестирования на VPS

1. **Контейнеры перезапущены**:
   - `docker compose restart backend worker` -> статус обоих контейнеров `Started`.
2. **Скрипт проверки (`test_reassign_flow.py`)**:
   - Симуляция смены курьера на заказе #2784 (внешний #76209):
     - `INITIAL`: `courier_name='Курьер Дмитрий'`, `notif_status=accepted`.
     - `RESULT 1` (смена на Дмитрия): `courier_name='Курьер Дмитрий'`, `notif_status=unread`.
     - `RESULT 2` (смена на Сергея): `courier_name='Сергей'`, `notif_status=unread`, `courier_accepted_at=None`.
3. **Логи отправки сообщений ВКонтакте**:
   - `Log #13142 [evt=courier_assigned] acc_id=5 status=MessageStatus.SENT vk_msg_id=38119` («Назначен курьер Сергей на заказ #76209...»).
   - `Log #13143 [evt=order_new] acc_id=5 status=MessageStatus.SENT vk_msg_id=38120`.
   - `Log #13144 [evt=order_new] acc_id=6 status=MessageStatus.SENT vk_msg_id=38121`.
4. **Логи таблицы `courier_order_notifications`**:
   - Записи #8, #9 созданы со статусом `unread`, ожидают подтверждения от курьера.
5. **Таблица `courier_orders`**:
   - Создана/обновлена запись `CO #1186` с `emp_id=387` (курьер Сергей).

Все требования выполнены в полном объеме.
