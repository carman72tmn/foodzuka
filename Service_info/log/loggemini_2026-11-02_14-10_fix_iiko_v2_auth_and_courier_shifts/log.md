# Лог выполнения задачи: Восстановление связи с iiko Cloud и исправление ошибок работы курьеров

**Дата/Время:** 2026-11-02 14:10
**Сессия:** loggemini_2026-11-02_14-10_fix_iiko_v2_auth_and_courier_shifts
**Статус:** Успешно завершено / Протестировано на VPS

---

### 1. Проблема
1. **Ошибка связи с iiko:**
   - Сервер iiko Cloud перевел API-логин на Transport API v2, начав возвращать HTTP `403 Forbidden`:
     `{"errorDescription": "This API key does not support /api/1/access_token. Please use /api/v2/access_token instead."}`
   - Запросы к iiko Cloud не могли получить токен авторизации.
2. **Курьеры перестали отображаться и падали с ошибками:**
   - При открытии списка курьеров и смен вызывался эндпоинт `GET /api/v1/courier/all-couriers-shifts`.
   - Происходило исключение Python `AttributeError: 'Employee' object has no attribute 'code'` в `backend/app/api/courier.py:677`.
   - В результате фронтенд получал HTTP 500 Internal Server Error и не мог отобразить список курьеров и их статус.
3. **Ошибки закрытия заказов курьерами:**
   - В методах закрытия и смены оплаты при обращении к заказу iiko отсутствовала безопасная распаковка словаря `order_body = (iiko_order.get("order") or iiko_order) if isinstance(iiko_order, dict) else {}`.

---

### 2. Внесенные изменения

#### А. `backend/app/services/iiko_service.py`
- Метод `_get_access_token` переработан:
  1. Первично обращается к `/api/v2/access_token` с передачей `apiLogin`, `appId` и `clientSecret` (из настроек `IikoSettings` БД либо предустановленных ключей разработчика).
  2. При получении токена кэширует его на 50 минут (3000 секунд), чтобы исключить лишние обращения к iiko и не нарываться на rate limit.
  3. Сохранен безопасный fallback на `/api/1/access_token` на случай совместимости со старыми ключами.
- Метод проверен компилятором `py_compile` и строгой кодировкой UTF-8.

#### Б. `backend/app/api/courier.py`
- В строке 677 заменено прямое обращение `emp.code` на безопасный вызов:
  `code = getattr(emp, "code", None) or getattr(emp, "iiko_id", None)`
- В методах `_apply_order_payment_to_iiko` и `courier_change_payment_type` добавлена строгая проверка и распаковка ответа `iiko_order`.

---

### 3. Развертывание и тестирование на VPS
1. Файлы `backend/app/services/iiko_service.py` и `backend/app/api/courier.py` скопированы на VPS в `/root/foodzuka/backend/`.
2. Контрольные суммы SHA256 сверены (байт-в-байт идентичны).
3. Перезапущены контейнеры `foodtech-backend` и `foodtech-worker`.
4. Тестирование внутри контейнера `foodtech-backend`:
   - `iiko_service._get_access_token()` -> `TOKEN_SUCCESS: True`
   - `iiko_service.get_active_couriers(org_id)` -> 2 активных курьера с геопозицией.
   - `get_all_couriers_with_shifts(db)` -> статус `success`, возвращено 11 курьеров.
5. Запросы от фронтенда `GET /api/v1/orders/active-couriers` и `GET /api/v1/orders/active` возвращают `200 OK`.
