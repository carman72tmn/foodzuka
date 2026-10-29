# Журнал задачи: Доработка системных рассылок курьерам (VK, MAX, Telegram)
**Дата создания**: 25.10.2026 23:15
**Модель**: Gemini 3.8 Flash Lite / Antigravity
**Статус**: Завершено успешно

---

## 1. Цель и задачи
1. **QR-код оплаты картинкой**: отправлять динамический QR-код СБП как нативное фото-вложение (ВК, MAX, Telegram), удаляя технический сырой URL из тела текста сообщения.
2. **Ссылки на навигаторы по полному адресу**: переменные `{map_yandex}`, `{map_2gis}`, `{yandex_navigator}` должны кодировать полный текстовый адрес (`https://yandex.ru/maps/?rtext=~{encoded_addr}&rtt=auto`), координаты используются только как запасной вариант.
3. **Интерактивные кнопки действий курьера**:
   - `[🧭 Яндекс.Навигатор]` с полным адресом
   - `[✅ Заказ доставлен]` (если заказ уже оплачен)
   - `[📱 Доставлен (СБП QR)]`, `[💵 Наличные]`, `[💳 Терминал (Картой)]` (если заказ не оплачен)
   - Поддержка текстовых команд в MAX (`Д 101 СБП`, `Д 101 НАЛ`, `Д 101 КАРТА`).
4. **Режим «Одного компактного сообщения» и автосворачивание**:
   - При изменении времени готовности кухни или статуса заказа редактировать ранее отправленное сообщение, а не спамить новыми.
   - Динамический заголовок `⏳ ОЖИДАЕТ ГОТОВНОСТИ • Готов к ЧЧ:ММ (через ~X мин)`.
   - При доставке: автоматическое схлопывание сообщений курьерам во всех каналах (удаление фото QR, удаление кнопок, сохранение компактной информации и ссылок на адреса в навигаторах).
5. **Админ-панель**: добавление 3-х переключателей управления логикой в модальном окне редактирования шаблона (`/settings/vk-notifications`).

---

## 2. Выполненные работы

### База данных (PostgreSQL)
Выполнена миграция в контейнере `foodtech-db`:
```sql
ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS edit_existing_message BOOLEAN DEFAULT TRUE;
ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS collapse_on_delivered BOOLEAN DEFAULT TRUE;
ALTER TABLE vk_templates ADD COLUMN IF NOT EXISTS show_courier_action_buttons BOOLEAN DEFAULT TRUE;
ALTER TABLE courier_order_notifications ADD COLUMN IF NOT EXISTS qr_attachment_id VARCHAR(255) DEFAULT NULL;
ALTER TABLE courier_order_notifications ADD COLUMN IF NOT EXISTS bot_id INTEGER DEFAULT NULL;
ALTER TABLE courier_order_notifications ADD COLUMN IF NOT EXISTS payment_method_selected VARCHAR(100) DEFAULT NULL;
ALTER TABLE courier_order_notifications ADD COLUMN IF NOT EXISTS delivered_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL;
ALTER TABLE courier_order_notifications ADD COLUMN IF NOT EXISTS is_collapsed BOOLEAN DEFAULT FALSE;
```

### Бэкенд (FastAPI / SQLModel)
1. **`backend/app/models/vk_bot.py`**:
   - Модель `VkTemplate` дополнена полями `edit_existing_message`, `collapse_on_delivered`, `show_courier_action_buttons`.
   - Модель `CourierOrderNotification` дополнена полями `qr_attachment_id`, `bot_id`, `payment_method_selected`, `delivered_at`, `is_collapsed`.
2. **`backend/app/api/vk_bot_admin.py`**:
   - Схемы `VkTemplateCreate` и `VkTemplateUpdate` дополнены новыми полями для сохранения настроек через REST API.
3. **`backend/app/services/iiko_sync_service.py`**:
   - Приоритет полного адреса при формировании ссылок `map_yandex`, `map_2gis`, `yandex_navigator`.
   - Сохранена строгая кодировка UTF-8.
4. **`backend/app/services/vk_bot_service.py`**:
   - Сохранение `effective_token` при загрузке фото на сервер ВК.
   - Реализован метод `edit_message` (`messages.edit`) с поддержкой очистки вложений `attachment=""` и сброса клавиатуры.
5. **`backend/app/services/max_service.py`**:
   - Реализован метод `upload_max_bot_image` для Bot API MAX.
   - Методы `send_max_bot_message` и `send_max_message` дополнены поддержкой `image_path` и `image_url`.
   - Реализован метод `edit_max_message` (`PUT /messages?message_id=...`) с поддержкой сброса вложений `attachments: []`.
6. **`backend/app/services/max_bridge_service.py`**:
   - Интеграция PyMax `Photo(path=...)` для прикрепления картинок QR-кода при отправке от личного номера.
7. **`backend/app/services/vk_notification_router.py`**:
   - Функция `build_order_status_header(order, event_type)`: интеллектуальные динамические статусы с расчетом оставшихся минут приготовления.
   - Функция `build_courier_action_keyboards(order)`: генерация inline-кнопок для ВК, Telegram и MAX.
   - Функция `build_collapsed_delivered_text(order, payment_label)`: формирование компактного финального текста с сохранением ссылок на навигаторы по адресу.
   - Функция `collapse_order_notifications_on_delivery(order_id, payment_label, session)`: каскадное авто-редактирование и удаление QR-кода/кнопок во всех соцсетях при закрытии заказа.
   - Функция `handle_courier_order_action(order_id, payment_code, channel, actor_identifier)`: обработка нажатий кнопок курьерами.
   - Обновлен метод `dispatch_event`: авто-редактирование одного существующего сообщения курьеру (`edit_existing_message`), прикрепление фото QR, вырезание сырого URL из текста.
8. **Обработчики Webhook**:
   - `backend/app/services/vk_service.py`: callback-события `cmd == "courier_deliver"`.
   - `backend/app/api/max.py`: callback-события `cdeliv:...` и текстовые команды `Д {num} {pay}`.
   - `backend/app/api/validation.py`: callback-события `callback_query` с префиксом `cdeliv:...` для Telegram.

### Фронтенд (Vue 3 / Vite)
- **`admin/resources/js/pages/settings/vk-notifications_utf8.vue`**:
  - Добавлены 3 переключателя в модальном окне редактирования шаблона:
    1. «Обновлять существующее сообщение (без дублей)» (`edit_existing_message`)
    2. «Сворачивать сообщение после доставки заказа» (`collapse_on_delivered`)
    3. «Показывать интерактивные кнопки курьера» (`show_courier_action_buttons`)
  - Выполнена сборка `npm run build` на VPS:
    - Сборка завершена за 1м 44с без ошибок.
    - Сгенерирован ассет `public/build/assets/vk-notifications_utf8-oF7U0-Cr.js`.

---

## 3. Результаты верификации на VPS
1. **Контрольные суммы (MD5)**: 100% совпадение локальных и серверных файлов.
2. **Тестирование роутера и форматирования ссылок**:
   - Ссылка `map_yandex`: `https://yandex.ru/maps/?rtext=~%D0%B3.+%D0%A2%D1%8E%D0%BC%D0%B5%D0%BD%D1%8C%2C+%D1%83%D0%BB.+%D0%9B%D0%B5%D0%BD%D0%B8%D0%BD%D0%B0%2C+%D0%B4.+10&rtt=auto`
   - Ссылка `map_2gis`: `https://2gis.ru/search/%D0%B3.+%D0%A2%D1%8E%D0%BC%D0%B5%D0%BD%D1%8C%2C+%D1%83%D0%BB.+%D0%9B%D0%B5%D0%BD%D0%B8%D0%BD%D0%B0%2C+%D0%B4.+10`
   - Ссылка `yandex_navigator`: `https://yandex.ru/maps/?rtext=~%D0%B3.+%D0%A2%D1%8E%D0%BC%D0%B5%D0%BD%D1%8C%2C+%D1%83%D0%BB.+%D0%9B%D0%B5%D0%BD%D0%B8%D0%BD%D0%B0%2C+%D0%B4.+10&rtt=auto`
3. **Заголовки и статус готовности**:
   - При готовке: `⏳ ОЖИДАЕТ ГОТОВНОСТИ • Готов к 04:45 (через ~331 мин)`
   - При доставке: `✅ ЗАКАЗ #99999 ДОСТАВЛЕН`
4. **Схлопывание текста**:
   - `✅ ЗАКАЗ №99999 ДОСТАВЛЕН (23:13)`
   - `💰 Сумма: 1450 ₽ • Оплата: СБП QR`
   - `📞 Клиент: +79220079019`
   - `📍 Адрес: г. Тюмень, ул. Ленина, д. 10`
   - `🧭 Яндекс.Навигатор: https://yandex.ru/maps/...`
5. **Клавиатуры (ВК, MAX, Telegram)**:
   - VK: 3 ряда кнопок (Навигатор, СБП QR, Наличные, Терминал).
   - Telegram: 3 ряда inline-кнопок.
   - MAX: 3 ряда кнопок + текстовые команды-подсказки.
6. **Контейнеры**: `foodtech-backend` и `foodtech-worker` успешно перезапущены.
