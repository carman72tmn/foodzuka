# Лог сессии: Автопривязка аккаунтов MAX и каскадные рассылки
**Дата**: 16.09.2026 19:25
**Задача**: Автоматический поиск и привязка аккаунтов MAX мессенджера через личный аккаунт (Web Bridge / PyMax) при создании клиента и при заказе; отправка каскадных рассылок от имени MAX без ошибок.

## Диагностика
1. Выявлена проблема при отправке через личный аккаунт MAX (`max_bridge_service.py`):
   - Метод `send_bridge_message` передавал `peer_id` (ID пользователя) напрямую как `chat_id` в `WebClient.send_message`.
   - В мессенджере MAX для личных диалогов 1-на-1 ID чата вычисляется формулой `client.get_chat_id(my_user_id, target_user_id)`.
   - Из-за этого отправка падала с исключением, а обработчик ошибок возвращал `{"status": "success", "msg_id": "bridge_saved_..."}` (ложный успех), в результате чего сообщения клиентам не доставлялись.
2. Проведено тестирование вычисления `chat_id` и отправки на тестовом клиенте `+79220079019`:
   - `my_user_id` = 138113613
   - `target_user_id` = 5849132
   - `chat_id` = 140653153
   - Отправка `client.send_message(chat_id=140653153)` успешно доставлена (`id=117281171042686219`).

## Запланированные изменения:
1. `backend/app/services/max_bridge_service.py`:
   - Доработка `send_bridge_message` с вычислением `chat_id` для диалогов.
   - Исключение фиктивного успеха при ошибках.
   - Метод `link_customer_by_phone` для привязки `max_user_id` к карточке клиента.
2. `backend/app/tasks/customer_tasks.py`:
   - Добавление Celery задачи `link_customer_max_task`.
3. `backend/app/api/customers.py`:
   - Вызов `link_customer_max_task` при `create_customer` и `update_customer`.
4. `backend/app/api/orders.py`:
   - Вызов `link_customer_max_task` при `create_order`.
5. `backend/app/services/iiko_sync_service.py`:
   - Вызов привязки в `ensure_customer_from_order` (СТРОГО в UTF-8).
6. `backend/app/services/max_service.py` и `backend/app/services/mailing_cascade_service.py`:
   - Корректная обработка результатов отправки и состояний шагов в каскадных рассылках.
