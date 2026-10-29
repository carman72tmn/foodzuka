# Сессионный лог: Активация цепочек курьера, выбор каналов отправки, мультиботность ВК и MAX Messenger

**Дата и время:** 04.09.2026 17:05 (UTC+5)  
**Сессия:** `2026-09-04_17-05_courier_chains_multichannel_and_max`  
**Ответственный:** AI Assistant (Antigravity)  

---

## 1. Постановка задачи
1. В «Рассылки -> Системные рассылки» добавить возможность выбора каналов для рассылок пользователям (сотрудникам), чтобы каждому можно было выставить по какому каналу слать уведомления (VK, Telegram, MAX, SMS), а также добавить поддержку одинаковых страниц для уведомлений.
2. Выяснить и устранить причину, почему не работали «Рассылки -> Системные рассылки -> Цепочки курьера» (`/settings/vk-notifications`, вкладка `courier_chains`) и не происходила отправка уведомлений курьерам.
3. Обеспечить гарантированную отправку уведомлений о заказах курьерам согласно цепочкам курьера в социальные сети.
4. В цепочках курьера добавить возможность выбора каналов для отправки (`send_vk`, `send_tg`, `send_max`, `send_sms`) для каждого шага.
5. Добавить возможность выбора конкретного подключенного сообщества/бота ВКонтакте (из `vk_bot_connections`), от имени которого отправлять уведомления курьерам (выбор бота «Курьеры» ID=2 вместо основного «Довезука» ID=1).
6. Реализовать отправку уведомлений через MAX Messenger с выбором каналов.

---

## 2. Причины выявленных сбоев отправки курьерам
1. **Отключенные шаблоны**: Шаблоны `courier_assigned` (ID 15) и `order_cancelled` (ID 10) имели `is_active = False` в БД.
2. **Настраиваемое условие времени кухни (`require_cooking_time_set`)**: В шаблоне `order_new` в `chain_config` по умолчанию включено `"require_cooking_time_set": true`. Согласно логике цепочки, оно удерживает отправку уведомления курьеру до момента, пока кухня не выставит время приготовления (>0 мин). Если условие активно — роутер ожидает кухню; если не активно — отправка идет немедленно.
3. **Отсутствие подписок курьеров**: В таблице `vk_bot_subscriptions` у курьеров не было записей на события цепочки.
4. **Блокировка по `is_verified`**: В `vk_notification_router.py` проверка `account.is_verified` отсекала курьеров до первого ручного тестирования, а для MAX Messenger не вызывался метод отправки.
5. **Отсутствие мультиботности**: Все отправки шли только от имени основного бота (`is_main=True`), а курьерский бот («Курьеры», группа ID=2, 234266390) не использовался.
6. **Разрешение сообщений (VK Error 901)**: Курьеры Дмитрий и Владислав еще не нажали «Разрешить сообщения» в диалоге с новым курьерским ботом сообщества.

---

## 3. Внесенные изменения

### База данных (PostgreSQL на VPS)
- Создан и применен миграционный скрипт `backend/app/scripts/migrate_add_template_channels_and_bot_selection.py`:
  - В `vk_templates` добавлены колонки:
    - `vk_bot_id INTEGER REFERENCES vk_bot_connections(id)`
    - `send_vk BOOLEAN DEFAULT TRUE`
    - `send_tg BOOLEAN DEFAULT FALSE`
    - `send_max BOOLEAN DEFAULT FALSE`
    - `send_sms BOOLEAN DEFAULT FALSE`
    - Индекс `ix_vk_templates_vk_bot_id`.
  - Активированы все шаги цепочек курьера (`is_active = True`).
  - Для всех 8 курьерских шаблонов выставлен `vk_bot_id = 2` (бот «Курьеры»).
  - В `order_new` снято требование ожидания времени кухни (`require_cooking_time_set = False`).
  - Сгенерированы подписки `REALTIME` на все курьерские события для аккаунтов курьеров.

### Бэкенд (Python / FastAPI / SQLModel)
- `backend/app/models/vk_bot.py`:
  - В модель `VkTemplate` добавлены поля `vk_bot_id`, `send_vk`, `send_tg`, `send_max`, `send_sms`.
- `backend/app/api/vk_bot_admin.py`:
  - `VkTemplateCreate` и `VkTemplateUpdate` дополнены новыми полями.
  - Добавлен `POST /templates/{template_id}/toggle-channel` — быстрое переключение канала шага цепочки.
  - Добавлен `POST /templates/{template_id}/set-bot` — выбор сообщества/бота ВК для шаблона.
  - Добавлен `POST /templates/bulk-toggle-chains` — массовая активация/деактивация шагов курьера.
- `backend/app/services/vk_notification_router.py`:
  - Извлечение API-токена выбранного бота: если у шаблона указан `template.vk_bot_id`, токен берется из соответствующей записи `VkBotConnection` и передается как `bot_token_override` в `vk_bot_service.send_message`.
  - Фильтрация каналов по шаблону: `tpl_send_vk`, `tpl_send_tg`, `tpl_send_max`, `tpl_send_sms`.
  - Снята предварительная блокировка по `is_verified` (отправка разрешена, если канал включен в шаблоне и у аккаунта).
  - Интегрирована отправка в MAX Messenger через `send_max_message_helper` с логированием в `vk_bot_message_logs`.
  - Гарантированная адресация назначенному курьеру заказа даже при отсутствии записи в подписках.

### Фронтенд (Vue 3 / Vuetify)
- `admin/resources/js/pages/settings/vk-notifications_utf8.vue`:
  - В баннере таба «Цепочки курьера» добавлены кнопки: «Активировать все шаги» и «Отключить все» (`bulkToggleCourierChains`).
  - Добавлены кнопки быстрого открытия диалога с ботами ВКонтакте (`vk.com/im?sel=-...`) для разрешения курьерами входящих сообщений.
  - На каждой карточке шага цепочки добавлен блок переключения каналов (`[VK]`, `[MAX]`, `[TG]`, `[SMS]`) и выпадающий список выбора сообщества/бота ВК.
  - В модальном окне редактирования шаблона добавлены чекбоксы каналов и селект выбора бота ВК.
  - Выполнена сборка `npm run build` (`vk-notifications_utf8-C8vMHiUE.js`).

---

## 4. Сверка контрольных сумм SHA256 (Локально vs VPS)
- `backend/app/models/vk_bot.py`:
  `9E93E45EE29CEA50B9EF3A4767C4E0FBFF3040719FC2441A4A6D75CA3B8D4C52` (Совпадает)
- `backend/app/api/vk_bot_admin.py`:
  `13DCDF61505CAEED2B588F9B43AF375F72CE3B041EA69D8B5914A1CCF12B5126` (Совпадает)
- `backend/app/services/vk_notification_router.py`:
  `B9FF19C9E836115F4A5D2C6298324F672DD93093634ACE947681934B5D1AEDEC` (Совпадает)
- `admin/resources/js/pages/settings/vk-notifications_utf8.vue`:
  `E02CFF888BF36B9AD26CE3BF2E63C2CCEE7C126AD2F8D0A57BADD13C5F9F4AE9` (Совпадает)
- `admin/public/build/assets/vk-notifications_utf8-C8vMHiUE.js`:
  `AD26FC0535F7CDE9A41827CC1F9DFD5C163E8C472E987E85308575C14712995C` (Совпадает)

---

## 5. Результаты тестирования на VPS
1. **API эндпоинты**:
   - `POST /api/v1/vk-bot/templates/15/toggle-channel` -> `{"status":"success","template_id":15,"channel":"max","enabled":true}` (200 OK)
   - `POST /api/v1/vk-bot/templates/15/set-bot` -> `{"status":"success","template_id":15,"vk_bot_id":2}` (200 OK)
   - `POST /api/v1/vk-bot/templates/bulk-toggle-chains` -> `{"status":"success","count":8,"enabled":true}` (200 OK)
2. **Сквозная отправка через `dispatch_event`**:
   - Шаблоны курьера активны и привязаны к боту «Курьеры» (ID=2).
   - Уведомления в VK успешно отправлены со статусом `SENT` (записи `id=13155`, `id=13161`, получены `vk_message_id=5`, `vk_message_id=6`).
   - Отправка в MAX Messenger вызывается штатно для аккаунтов с активным каналом MAX.
   - Для курьеров без предварительного диалога с группой бот фиксирует ошибку VK 901 «Can't send messages for users without permission», для чего в интерфейс выведены прямые кнопки перехода в диалог.
