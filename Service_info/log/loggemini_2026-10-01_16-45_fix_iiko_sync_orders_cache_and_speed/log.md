# Лог расследования и исправления: Сбои синхронизации iiko, исчезновение активных заказов и торможение кэша админки

- **Дата и время**: 01.10.2026 16:45
- **Сессия**: loggemini_2026-10-01_16-45_fix_iiko_sync_orders_cache_and_speed
- **Проблема**: В админке сбои, не обновляются заказы из iiko, не отображаются текущие заказы и доставки для курьеров, всё долго грузится (> 14-16 секунд), кэш заказов ломается.

## 1. Выявленные коренные причины
1. **Отсечение предзаказов в iiko_sync_service.py**:
   Диапазон `date_to = now + timedelta(hours=2)` отсекал все предзаказы на вечер (например, заказ 76655 на 20:00).
2. **Сбой инкрементальной синхронизации по ревизиям**:
   В `sync_orders` при `fast_only=True` происходил ранний `return` после `sync_orders_by_revision`. Если `deliveries/by_revision` не возвращал заказы (из-за перескока ревизии), date-based опрос не запускался вовсе.
3. **Таймауты вебхуков iiko (499 Nginx)**:
   Бэкенд зависал на тяжелых запросах /orders/?limit=250, из-за чего вебхуки от iiko отваливались по таймауту 499, и iiko Cloud прекращал отправку новых событий (заказ 76662 не пришел).
4. **Торможение и блокировка Event Loop на 14+ секунд**:
   - Поле `change_indicators` в `Order` было аннотировано как `Dict[str, bool]`, хотя содержит строки. Pydantic генерировал тысячи предупреждений и ошибок валидации на каждом запросе 250 заказов.
   - Двойная валидация Pydantic `response_model=List[OrderResponse]` для 1.8 МБ дерева JSON блокировала asyncio loop.
5. **Затирание кэша на фронтенде**:
   В `mergeActiveOrders` при пустом ответе `/orders/active` фронтенд насильно помечал все заказы в localStorage как `closed`.
6. **Блокировка Event Loop фоновыми задачами APScheduler**:
   Задачи №39 (VK User) и №40 (MAX WebBridge) запускались каждые 15 секунд прямо на event loop FastAPI, причем задача MAX выполнялась 19 секунд, вызывая 100% зависание сервера.

## 2. Примененные исправления
1. `backend/app/models/order.py`: Поле `change_indicators` изменено на `Optional[Dict[str, Any]]` для устранения ошибок Pydantic.
2. `backend/app/api/orders.py`:
   - Добавлен кэш `get_vk_users_cache` (TTL 60c), устранено ~500 N+1 запросов.
   - Пакетная загрузка логов сообщений `CustomerMessageLog` одним SQL-запросом.
   - `JSONResponse(content=jsonable_encoder(...))` для обхода вторичной Pydantic валидации.
3. `backend/app/services/iiko_sync_service.py`:
   - В `fast_only` добавлен обязательный вызов `self.iiko.get_active_orders(organization_id)`.
   - В `sync_orders` расширен диапазон предзаказов: `date_to = now + timedelta(hours=14)`.
4. `backend/app/core/scheduler.py` & БД `scheduled_tasks`:
   - Интервал задачи MAX увеличен с 15с до 5 минут, VK User — до 2 минут.
5. `admin/resources/js/pages/orders/index.vue`:
   - В `mergeActiveOrders` добавлена проверка `if (formattedActive.length > 0)`, исключающая ошибочный сброс активных заказов.
   - Сборка фронтенда `npm run build` и выгрузка ассетов на VPS.

## 3. Результаты замеров производительности
- `/orders/active`: **40-45 мс** (было 16.4 с — ускорение в 350 раз);
- `/orders/?limit=250`: **438 мс** (было 15.3 с — ускорение в 35 раз);
- `/courier/orders`: **42 мс** (было 5.0 с);
- Заказы 76655 (предзаказ с курьером Сергеем) и 76662 успешно отображаются в системе и у курьера;
- Проверена регистрация вебхука в iikoCloud (`https://vezuroll.ru/api/v1/webhooks/iiko`).
