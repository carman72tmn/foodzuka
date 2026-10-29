# Лог сессии: Исправление ошибки 500 при добавлении получателя, активация цепочек курьеров и разделение каналов отправки

**Дата и время:** 04.09.2026 17:50 (МСК+2)  
**Имя задачи:** loggemini_20260904_1750_courier_notifications_and_channels  

---

## 1. Проблема 1: Ошибка 500 (Internal Server Error) при сохранении нового получателя
- **Причина:** В эндпоинте `POST /api/v1/vk-bot/accounts` (`backend/app/api/vk_bot_admin.py`) при создании базовых подписок для нового сотрудника использовалось перечисление `DeliveryMode.REALTIME`, однако импорт `DeliveryMode` отсутствовал в модуле, что вызывало `NameError: name 'DeliveryMode' is not defined`.
- **Исправление:** Добавлен импорт `DeliveryMode` из `app.models.vk_bot` в `backend/app/api/vk_bot_admin.py`.
- **Тестирование:** Проведено создание и валидация тестового получателя через API на VPS. Успешно создается аккаунт и 9 дефолтных подписок.

---

## 2. Проблема 2: Не отправлялись QR-коды и курьерские уведомления в цепочках, пустые переменные
- **Причины:**
  1. Шаблон `courier_assigned` (ID: 15) в БД имел `is_active = False`, из-за чего системное назначение курьера на заказ никогда не отправлялось.
  2. У курьера «Сергей Доставка» (ID аккаунта: 12) в таблице `vk_bot_subscriptions` отсутствовали записи подписок.
  3. В шаблонах и `iiko_sync_service.py` отсутствовали переменные `yandex_navigator`, `map_navigator`, а при нулевом времени кухни `pickup_time` возвращал `---`.
  4. Токен сообщества «Курьеры» (ID: 2, группа VK `234266390`) в настройках сообщества VK не имел разрешенного scope `photos` (VK API выдает ошибку 15 / 1133 при вызове `photos.getMessagesUploadServer`). При попытке отправить картинку от имени бота 2 с фото, загруженным ботом 1, VK отсекает вложения.
- **Исправления:**
  1. Шаблон 15 (`courier_assigned`) активирован в БД (`is_active = True`).
  2. Шаблону 7 (`order_items_changed`) назначен `vk_bot_id = 2`.
  3. Для курьера «Сергей Доставка» (ID: 12) созданы активные подписки на все курьерские события.
  4. В `backend/app/services/vk_notification_router.py` и `backend/app/services/iiko_sync_service.py` реализована расширенная генерация переменных:
     - `order.map_yandex`: прямая ссылка по координатам или поиску по адресу с URL-кодированием.
     - `order.map_2gis`: гео-ссылка по координатам или поиск по адресу.
     - `order.yandex_navigator` / `order.map_navigator`: прямая ссылка для запуска маршрута в Яндекс.Навигаторе.
     - `order.pickup_time`: расчетное время прибытия курьера на кухню.
     - `order.cooking_time`: время приготовления заказа.
  5. Генерация QR-кода СБП сохраняет брендированную карточку заказа (номер, адрес, сумма) в `/app/media/img/qr/...` и гарантированно внедряет кликабельную ссылку `💳 QR-код на оплату СБП: https://vezuroll.ru/media/img/qr/...` прямо в текст сообщения (открывается в 1 тап во всех клиентах VK, TG, MAX, SMS).

---

## 3. Проблема 3: Разделение каналов отправки (курьеры vs остальные уведомления)
- **Реализация:**
  - Все курьерские события (`order_new`, `courier_assigned`, `change_cooking_time`, `order_status_update`, `order_amount_changed`, `order_items_changed`, `order_address_changed`, `order_time_changed`, `order_cancelled`) маршрутизируются на сообщество курьеров (Бот ID: 2, «Курьеры»).
  - Все общие системные уведомления (`shift_open`, `shift_close`, `bonus_order`, `system_alert`, `purchase_list_sent` и др.) маршрутизируются на основное сообщество, выбранное во вкладке «Настройки каналов» (`is_main = True`, Бот ID: 1, «Довезука»).

---

## 4. Сверка файлов и перезапуск на VPS
- Локальные файлы проверены на компиляцию Python и кодировку UTF-8.
- SHA-256 файлов на VPS полностью совпадает с локальными:
  - `backend/app/api/vk_bot_admin.py`: `5c903c7f9f093137267c7ee1165876d820f1879cb3c849e99b338b5dc5e54c02`
  - `backend/app/services/vk_notification_router.py`: `88bbb9bb5ef192d8c4814ebfd564970b30ae08893f9d027aab1229a350fbd3f4`
  - `backend/app/services/iiko_sync_service.py`: `26cdd59c5e6ed6b7dc3bc7e132daf91a44f8d094cee222159823e4a4b5aff3c7`
- Контейнеры `foodtech-backend` и `foodtech-worker` перезапущены и работают без ошибок.
